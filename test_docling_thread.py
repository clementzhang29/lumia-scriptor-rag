import sys, time, concurrent.futures
sys.path.insert(0, ".")

def convert_sync():
    from src.engines.docling_engine import DoclingEngine
    import asyncio
    e = DoclingEngine({"gpu": False})
    pdf = r"C:\Users\35160\Desktop\中医RAG系统\data\books\《图表注释金匮要略新义》余无言编.pdf"
    t0 = time.time()
    r = asyncio.run(e.convert(pdf))
    dt = time.time() - t0
    print(f"Docling: success={r.success} md_len={len(r.markdown) if r.markdown else 0} time={dt:.1f}s", flush=True)
    if r.error:
        print(f"error: {r.error}", flush=True)
    return r

print("Starting Docling in thread pool...", flush=True)
with concurrent.futures.ThreadPoolExecutor() as pool:
    fut = pool.submit(convert_sync)
    try:
        r = fut.result(timeout=120)
        print("Done!", flush=True)
    except concurrent.futures.TimeoutError:
        print("TIMEOUT after 120s", flush=True)
    except Exception as ex:
        print(f"Exception: {ex}", flush=True)
