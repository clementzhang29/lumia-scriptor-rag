import sys, asyncio, time
sys.path.insert(0, ".")
from src.engines.surya_engine import SuryaEngine

async def test():
    e = SuryaEngine({"gpu": True})
    pdf = r"C:\Users\35160\Desktop\中医RAG系统\data\books\《图表注释金匮要略新义》余无言编.pdf"
    print("Starting Surya OCR (GPU)...")
    t0 = time.time()
    r = await e.convert(pdf)
    dt = time.time() - t0
    print(f"Done in {dt:.1f}s, success={r.success}, md_len={len(r.markdown) if r.markdown else 0}")
    if r.error:
        print("Error:", r.error)
    if r.markdown:
        print("First 300:", r.markdown[:300])
asyncio.run(test())
