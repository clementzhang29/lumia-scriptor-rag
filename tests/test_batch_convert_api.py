import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient


class BatchConvertApiTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base = Path(self.temp_dir.name)
        self.uploads = self.base / "uploads"
        self.rag_db = self.base / "rag_db"
        self.kb_mounts = self.base / "kb_mounts"

        import src.web.app as web_app

        self.web_app = web_app
        self.web_app.UPLOAD_DIR = self.uploads
        self.web_app.RAG_DB_DIR = self.rag_db
        self.web_app.KB_MOUNT_DIR = self.kb_mounts
        self.web_app.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        self.web_app.RAG_DB_DIR.mkdir(parents=True, exist_ok=True)
        self.web_app.KB_MOUNT_DIR.mkdir(parents=True, exist_ok=True)
        self.web_app.tasks.clear()
        self.client = TestClient(self.web_app.app)

    def tearDown(self):
        try:
            self.web_app.rag_engine.close()
        except Exception:
            pass
        self.temp_dir.cleanup()

    def test_batch_convert_creates_tasks_and_preserves_relative_paths(self):
        def _drop_task(coro):
            coro.close()
            return None

        with patch.object(self.web_app.asyncio, "create_task", side_effect=_drop_task):
            response = self.client.post(
                "/api/convert/batch",
                files=[
                    ("files", ("books/classic/a.pdf", b"%PDF-1.4 a", "application/pdf")),
                    ("files", ("books/modern/b.pdf", b"%PDF-1.4 b", "application/pdf")),
                ],
                data={"strategy": "auto", "preferred_engine": "surya"},
            )

        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertEqual(data["count"], 2)
        self.assertEqual(len(data["task_ids"]), 2)

        batch_status = self.client.get(f"/api/batch/{data['batch_id']}")
        self.assertEqual(batch_status.status_code, 200, batch_status.text)
        batch_data = batch_status.json()
        self.assertEqual(batch_data["count"], 2)
        self.assertEqual(batch_data["counts"]["queued"], 2)

        filenames = {task["filename"] for task in batch_data["tasks"]}
        self.assertIn("books/classic/a.pdf", filenames)
        self.assertIn("books/modern/b.pdf", filenames)

        stored_paths = [task["stored_path"] for task in batch_data["tasks"]]
        self.assertTrue(any("books\\classic\\a.pdf" in path or "books/classic/a.pdf" in path for path in stored_paths))


if __name__ == "__main__":
    unittest.main()
