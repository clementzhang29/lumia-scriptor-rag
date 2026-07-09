#!/usr/bin/env python3
"""TCM PDF batch OCR - Harness Layer 2."""

import argparse, asyncio, json, os, re, sys, time
from pathlib import Path

os.environ["CUDA_VISIBLE_DEVICES"] = ""
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.engines import DoclingEngine, SuryaEngine, MinerUEngine
from src.qa import QualityScorer
from src.formatter import MarkdownCleaner

BOOKS_DIR = Path(r"C:\Users\35160\Desktop\中医RAG系统\data\books")
OCR_DIR = BOOKS_DIR / "pdf_ocr"
EXTRACT_DIR = BOOKS_DIR / "doc_extracts"
QUALITY_THRESHOLD = 0.85
LOG_FILE = BOOKS_DIR / "batch_log.jsonl"



async def load_baselines(pdf_stem):
    """Fuzzy match existing extractions."""
    results = []
    stem_lower = pdf_stem.lower()
    kw_match = re.findall(r"[\u4e00-\u9fff\w]{2,}", pdf_stem)
    keywords = [k for k in kw_match if len(k) >= 2]

    def score_match(fname):
        fn_lower = fname.lower()
        if stem_lower in fn_lower or fn_lower in stem_lower:
            return 4
        if pdf_stem[:max(3, len(pdf_stem)//2)] in fn_lower:
            return 3
        for kw in keywords:
            if len(kw) >= 3 and kw.lower() in fn_lower:
                return 2
        return 0

    candidates = []
    if OCR_DIR.exists():
        for f in OCR_DIR.iterdir():
            if f.suffix == '.md':
                candidates.append((score_match(f.stem), str(f.relative_to(BOOKS_DIR)), f, 'existing_md'))
    for f in BOOKS_DIR.iterdir():
        if f.suffix == '.txt':
            candidates.append((score_match(f.stem), str(f.relative_to(BOOKS_DIR)), f, 'existing_txt'))
    if EXTRACT_DIR.exists():
        for f in EXTRACT_DIR.iterdir():
            if f.suffix == '.txt':
                candidates.append((score_match(f.stem), str(f.relative_to(BOOKS_DIR)), f, 'doc_extract'))

    best_score = max((s for s,_,_,_ in candidates), default=0)
    if best_score >= 2:
        for score, source, fpath, engine in candidates:
            if score >= best_score - 1:
                txt = fpath.read_text(encoding='utf-8', errors='replace')
                results.append({'source': source, 'text': txt, 'engine': engine})
    return results


async def best_from_baselines(baselines, scorer):
    best_text, best_score, best_source = "", 0.0, ""
    for bl in baselines:
        q = await scorer.score(bl["text"])
        score = q["total"]
        if score > best_score:
            best_score, best_text, best_source = score, bl["text"], bl["source"]
    return best_text, best_score, best_source


async def process_pdf(pdf_path, engines, scorer, cleaner, override=False, compare=False, baselines=None):
    result = {
        "file": pdf_path.name,
        "status": "pending",
        "engine_used": "",
        "quality": 0.0,
        "md_len": 0,
        "processing_time": 0.0,
        "baseline_best": "",
        "baseline_score": 0.0,
        "md_path": "",
    }
    start = time.time()

    if baselines is None:
        baselines = await load_baselines(pdf_path.stem)

    # Step 0: check baselines
    if baselines:
        bl_text, bl_score, bl_source = await best_from_baselines(baselines, scorer)
        result["baseline_score"] = round(bl_score, 3)
        result["baseline_best"] = bl_source
        if not override and bl_score >= QUALITY_THRESHOLD:
            result["status"] = "skipped_baseline"
            result["quality"] = bl_score
            result["md_len"] = len(bl_text)
            result["processing_time"] = time.time() - start
            return result

    # Step 1: OCR engines
    priority = ["surya", "docling", "mineru"]
    markdown, engine_name = "", ""
    for ename in priority:
        if ename not in engines:
            continue
        eng = engines[ename]
        if not await eng.is_available():
            continue
        try:
            ocr_result = await eng.convert(str(pdf_path))
            if ocr_result.success and len(ocr_result.markdown) > 0:
                markdown = ocr_result.markdown
                engine_name = ename
                break
        except Exception as e:
            print("  [" + ename + "] error:", e)

    # Step 2: fallback to baselines when engine fails
    if not markdown and baselines:
        bl_text, bl_score, bl_source = await best_from_baselines(baselines, scorer)
        if bl_text and bl_score > 0:
            markdown = bl_text
            bl_short = bl_source.split('/')[-1]
            engine_name = "baseline(" + bl_short + ")"
            print("  [engine failed, fallback to baseline] " + bl_source + " quality " + str(bl_score))

    if not markdown:
        result["status"] = "failed_no_engine"
        result["processing_time"] = time.time() - start
        return result

    quality = await scorer.score(markdown)
    if quality["total"] < QUALITY_THRESHOLD:
        for ename in priority:
            if ename == engine_name or ename not in engines:
                continue
            eng = engines[ename]
            if not await eng.is_available():
                continue
            try:
                ocr_result = await eng.convert(str(pdf_path))
                if ocr_result.success and len(ocr_result.markdown) > 0:
                    alt_q = await scorer.score(ocr_result.markdown)
                    if alt_q["total"] > quality["total"]:
                        markdown = ocr_result.markdown
                        quality = alt_q
                        engine_name = engine_name + "+" + ename
            except:
                continue

    # Step 3: compare with baselines, keep best
    if compare and baselines:
        bl_text, bl_score, bl_source = await best_from_baselines(baselines, scorer)
        if bl_score > quality["total"]:
            markdown = bl_text
            quality = await scorer.score(markdown)
            bl_short = bl_source.split("/")[-1]
            engine_name = "baseline(" + bl_short + ")"

    # Step 4: format and write
    markdown = cleaner.clean(markdown)
    final_score = quality["total"]
    OCR_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r'[\\/:*?"<>| ]', '_', pdf_path.stem)[:80]
    eng_tag = engine_name.split('+')[0].split('(')[0].strip()
    md_path = OCR_DIR / (safe_name + "_" + eng_tag + ".md")
    md_path.write_text(markdown, encoding="utf-8")

    result.update({
        "status": "completed",
        "engine_used": engine_name,
        "quality": round(final_score, 3),
        "md_len": len(markdown),
        "md_path": str(md_path.relative_to(BOOKS_DIR)),
        "processing_time": round(time.time() - start, 1),
    })
    return result


async def main():
    import argparse
    parser = argparse.ArgumentParser(description='TCM PDF batch OCR')
    parser.add_argument("--override", action="store_true")
    parser.add_argument("--compare", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    pdfs = sorted(BOOKS_DIR.glob('*.pdf'))
    if args.limit > 0:
        pdfs = pdfs[:args.limit]
    if not pdfs:
        print("[fatal] no PDFs found")
        return 1

    print("Found " + str(len(pdfs)) + " PDFs, compare=" + str(args.compare))
    print("Initializing engines...")

    engines = {
        "docling": DoclingEngine({"gpu": False}),
        "surya": SuryaEngine({"gpu": False}),
        "mineru": MinerUEngine({"gpu": False}),
    }
    scorer = QualityScorer()
    cleaner = MarkdownCleaner()
    baselines_cache = {}
    docs = []

    for p in pdfs:
        baselines_cache[p.name] = await load_baselines(p.stem)
        best_bl = await best_from_baselines(baselines_cache[p.name], scorer) if baselines_cache[p.name] else ('', 0.0, '')
        if not args.override and best_bl[1] >= QUALITY_THRESHOLD:
            print("  [skip] " + p.name + " (baseline quality " + str(round(best_bl[1],3)) + ")")
            continue
        docs.append(p)

    print("To process: " + str(len(docs)) + "/" + str(len(pdfs)))
    if not docs:
        print("All done.")
        return 0

    log_entries = []
    for i, pdf_path in enumerate(docs):
        print("[" + str(i+1) + "/" + str(len(docs)) + "] " + pdf_path.name + " ...")
        result = await process_pdf(pdf_path, engines, scorer, cleaner, args.override, args.compare, baselines_cache.get(pdf_path.name))
        print("  engine: " + result["engine_used"].ljust(25) + " quality: " + str(result["quality"]) + " chars: " + str(result["md_len"]))
        log_entries.append(result)
    with open(str(LOG_FILE), "a", encoding="utf-8") as lf:
            lf.write(json.dumps(result, ensure_ascii=False) + chr(10))

    completed = [e for e in log_entries if e['status'] == 'completed']
    skipped = [e for e in log_entries if e['status'] == 'skipped_baseline']
    print("")
    print("Done. New: " + str(len(completed)) + ", Skipped: " + str(len(skipped)))
    if completed:
        avg_q = sum(e['quality'] for e in completed) / len(completed)
        print("Avg quality: " + str(round(avg_q, 3)))
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))