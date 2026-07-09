import sys, asyncio, time
sys.path.insert(0, ".")
from src.engines.surya_engine import SuryaEngine

async def main():
    e = SuryaEngine({"gpu": True})
    pdf = r"C:\Users\35160\Desktop\中医RAG系统\data\books\《图表注释金匮要略新义》余无言编.pdf"
    print("Starting Surya GPU OCR...", flush=True)
    t0 = time.time()
    try:
        r = await asyncio.wait_for(e.convert(pdf), timeout=300)
        dt = time.time() - t0
        print(f"Done! {dt:.1f}s success={r.success} md_len={len(r.markdown) if r.markdown else 0}", flush=True)
        if r.error:
            print(f"Error: {r.error}", flush=True)
        if r.markdown:
            print(f"First 400:\n{r.markdown[:400]}", flush=True)
    except asyncio.TimeoutError:
        print(f"TIMEOUT after 300s", flush=True)
    except Exception as ex:
        print(f"Exception: {ex}", flush=True)
        import traceback
        traceback.print_exc()

asyncio.run(main())
