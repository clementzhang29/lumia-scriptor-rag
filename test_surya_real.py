import sys, asyncio
sys.path.insert(0, ".")
from src.engines import SuryaEngine
import time

async def test():
    e = SuryaEngine({"gpu": False})
    pdf = r"C:\Users\35160\Desktop\中医RAG系统\data\books\《图表注释金匮要略新义》余无言编.pdf"
    print("Starting Surya OCR...")
    t0 = time.time()
    try:
        r = await e.convert(pdf)
        dt = time.time() - t0
        print(f"Done in {dt:.1f}s")
        print(f"Success: {r.success}")
        print(f"MD length: {len(r.markdown)}")
        if r.markdown:
            print(f"First 200 chars: {r.markdown[:200]}")
    except Exception as ex:
        print(f"Error: {ex}")
        import traceback
        traceback.print_exc()

asyncio.run(test())
