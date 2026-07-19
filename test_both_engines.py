import sys, asyncio, time
sys.path.insert(0, ".")
from src.engines import DoclingEngine, MinerUEngine

P1 = r"C:\Users\35160\Desktop\中医RAG系统\data\books\《图表注释金匮要略新义》余无言编.pdf"

async def test_docling():
    e = DoclingEngine({"gpu": False})
    print("[Docling] Starting...", flush=True)
    t0 = time.time()
    try:
        r = await e.convert(P1)
        print(f"[Docling] success={r.success} md_len={len(r.markdown) if r.markdown else 0} time={time.time()-t0:.1f}s", flush=True)
        if r.error:
            print(f"[Docling] error: {r.error}", flush=True)
    except Exception as ex:
        print(f"[Docling] exception: {ex}", flush=True)

async def test_mineru():
    e = MinerUEngine({"gpu": False})
    print("[MinerU] Starting...", flush=True)
    t0 = time.time()
    try:
        r = await e.convert(P1)
        print(f"[MinerU] success={r.success} md_len={len(r.markdown) if r.markdown else 0} time={time.time()-t0:.1f}s", flush=True)
        if r.error:
            print(f"[MinerU] error: {r.error}", flush=True)
    except Exception as ex:
        print(f"[MinerU] exception: {ex}", flush=True)

async def main():
    # Test Docling first (faster)
    await test_docling()
    # Then test MinerU
    await test_mineru()

asyncio.run(main())
