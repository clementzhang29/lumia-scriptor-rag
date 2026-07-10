import tempfile
import unittest
from pathlib import Path

from src.rag import UniversalRAGEngine


class TestRAGEngine(unittest.TestCase):
    def test_index_and_retrieve_across_multiple_documents(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = UniversalRAGEngine(str(Path(tmpdir) / "rag_db"))
            docs = []
            for idx in range(6):
                docs.append(
                    {
                        "title": f"黄帝内经 第{idx + 1}卷",
                        "source": f"book_{idx + 1}.md",
                        "content": (
                            f"第{idx + 1}章\n\n"
                            "关于脉象、气血、阴阳和经络的经典论述。"
                            " 这一段包含中医核心概念，以便检索命中。"
                        ),
                    }
                )
            stats = engine.index_documents(docs)
            self.assertEqual(stats["documents"], 6)
            self.assertGreater(stats["chunks"], 0)

            refs = engine.retrieve("脉象 气血 阴阳 经络", top_k=5)
            self.assertGreaterEqual(len(refs), 5)
            self.assertGreaterEqual(len({ref["source_key"] for ref in refs}), 5)

            answer = engine.fallback_answer(refs)
            self.assertIn("检索依据", answer)
            self.assertIn("黄帝内经", answer)
            engine.close()


if __name__ == "__main__":
    unittest.main()
