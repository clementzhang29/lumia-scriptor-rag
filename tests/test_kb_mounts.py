import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient


def _create_local_docs(base: Path) -> Path:
    docs_dir = base / "sample_docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "classic_a.md").write_text("# 黄帝内经\n\n脾胃者，仓廪之官。", encoding="utf-8")
    (docs_dir / "classic_b.md").write_text("# 伤寒论\n\n辨太阳病脉证并治。", encoding="utf-8")
    (docs_dir / "modern_note.txt").write_text("这是测试知识源，用于验证挂载建库流程。", encoding="utf-8")
    return docs_dir


class KnowledgeMountFlowTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base = Path(self.temp_dir.name)
        self.uploads = self.base / "uploads"
        self.rag_db = self.base / "rag_db"
        self.kb_mounts = self.base / "kb_mounts"
        self.docs_dir = _create_local_docs(self.base)

        import src.web.app as web_app

        self.web_app = web_app
        self.web_app.UPLOAD_DIR = self.uploads
        self.web_app.RAG_DB_DIR = self.rag_db
        self.web_app.KB_MOUNT_DIR = self.kb_mounts
        self.web_app.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        self.web_app.RAG_DB_DIR.mkdir(parents=True, exist_ok=True)
        self.web_app.KB_MOUNT_DIR.mkdir(parents=True, exist_ok=True)
        self.web_app.kb_mount_manager = self.web_app.KnowledgeMountManager(self.kb_mounts)
        self.web_app.document_parser = self.web_app.DocumentParser()
        self.web_app.rag_engine = self.web_app.UniversalRAGEngine(str(self.rag_db))
        self.client = TestClient(self.web_app.app)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_kb_source_crud_sync_and_rebuild(self):
        create_resp = self.client.post(
            "/api/kb-sources",
            json={
                "name": "docs-sample",
                "type": "local_dir",
                "enabled": True,
                "config": {"root_path": str(self.docs_dir)},
            },
        )
        self.assertEqual(create_resp.status_code, 200, create_resp.text)
        source = create_resp.json()["source"]
        source_id = source["id"]
        self.assertEqual(source["name"], "docs-sample")

        list_resp = self.client.get("/api/kb-sources")
        self.assertEqual(list_resp.status_code, 200)
        self.assertEqual(len(list_resp.json()["sources"]), 1)

        webdav_resp = self.client.post(
            "/api/kb-sources",
            json={
                "name": "webdav-archive",
                "type": "webdav",
                "enabled": True,
                "config": {
                    "base_url": "https://dav.example.com",
                    "root_path": "/books",
                    "username": "tester",
                    "password": "super-secret-password",
                },
            },
        )
        self.assertEqual(webdav_resp.status_code, 200, webdav_resp.text)
        webdav_id = webdav_resp.json()["source"]["id"]

        update_resp = self.client.put(
            f"/api/kb-sources/{webdav_id}",
            json={
                "name": "webdav-archive-v2",
                "config": {
                    "base_url": "https://dav.example.com",
                    "root_path": "/books-v2",
                    "username": "tester",
                    "password": "",
                },
            },
        )
        self.assertEqual(update_resp.status_code, 200, update_resp.text)
        stored = self.web_app.kb_mount_manager.get_source(webdav_id)
        self.assertEqual(stored["config"]["password"], "super-secret-password")

        sync_resp = self.client.post(f"/api/kb-sources/{source_id}/sync")
        self.assertEqual(sync_resp.status_code, 200, sync_resp.text)
        sync_data = sync_resp.json()
        self.assertGreaterEqual(sync_data["total_files"], 3)
        self.assertTrue(Path(sync_data["local_cache_dir"]).exists())

        rebuild_resp = self.client.post(
            "/api/rag/rebuild-mounted",
            json={"source_ids": [source_id], "sync_first": False},
        )
        self.assertEqual(rebuild_resp.status_code, 200, rebuild_resp.text)
        rebuild_data = rebuild_resp.json()
        self.assertGreaterEqual(rebuild_data["documents"], 2)
        self.assertGreaterEqual(rebuild_data["chunks"], 2)

        status_resp = self.client.get("/api/rag/status")
        self.assertEqual(status_resp.status_code, 200)
        status_data = status_resp.json()
        self.assertGreaterEqual(status_data["documents"], 2)

        delete_resp = self.client.delete(f"/api/kb-sources/{source_id}")
        self.assertEqual(delete_resp.status_code, 200, delete_resp.text)
        remaining = self.client.get("/api/kb-sources").json()["sources"]
        self.assertEqual(len(remaining), 1)


if __name__ == "__main__":
    unittest.main()
