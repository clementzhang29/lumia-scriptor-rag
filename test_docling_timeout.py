import sys, asyncio, time
sys.path.insert(0, ".")
from src.engines import DoclingEngine

P1 = r"C:\Users\35160\Desktop\中医RAG系统\data\books\《图表注释金匮要略新义》余无言编.pdf"

async def main():
    e = DoclingEngine({"gpu": False})
    print("Calling convert with timeout...", flush=True)
    # Use asyncio.wait_for to limit time
    try:
        r = await asyncio.wait_for(e.convert(P1), timeout=60)
        print(f"success={r.success} md_len={len(r.markdown) if r.markdown else 0}", flush=True)
        if r.error:
            print(f"error: {r.error}", flush=True)
    except asyncio.TimeoutError:
        print("TIMEOUT after 60s - Docling stuck on model download", flush=True)
    except Exception as ex:
        print(f"exception: {ex}", flush=True)

asyncio.run(main())
