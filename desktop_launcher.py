"""Windows desktop launcher for Lumia ScriptorRAG."""

from __future__ import annotations

import os
import socket
import sys
import time
import webbrowser
import logging
import traceback
from pathlib import Path
from threading import Thread

import uvicorn


HOST = "127.0.0.1"
DEFAULT_PORT = 8080
LOG_DIR: Path | None = None
LOG_FILE: Path | None = None

UVICORN_LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "logging.Formatter",
            "format": "%(asctime)s %(levelname)s %(message)s",
        },
        "access": {
            "()": "logging.Formatter",
            "format": "%(asctime)s %(levelname)s %(message)s",
        },
    },
    "handlers": {
        "default": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "stream": "ext://sys.stderr",
        },
        "access": {
            "class": "logging.StreamHandler",
            "formatter": "access",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        "uvicorn": {"handlers": ["default"], "level": "INFO", "propagate": False},
        "uvicorn.error": {"level": "INFO"},
        "uvicorn.access": {"handlers": ["access"], "level": "INFO", "propagate": False},
    },
}


def _runtime_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def _app_data_root() -> Path:
    local_app_data = Path(os.environ.get("LOCALAPPDATA", str(Path.home())))
    return local_app_data / "Lumia ScriptorRAG"


def configure_environment() -> None:
    global LOG_DIR, LOG_FILE
    data_root = _app_data_root()
    upload_dir = data_root / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    LOG_DIR = data_root / "logs"
    LOG_FILE = LOG_DIR / "launcher.log"
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("SCRIPTOR_RAG_DATA_DIR", str(data_root))
    os.environ.setdefault("OCR_HARNESS_DATA_DIR", str(data_root))
    os.environ.setdefault("SCRIPTOR_RAG_UPLOAD_DIR", str(upload_dir))
    os.chdir(_runtime_root())


def configure_stdio() -> None:
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w", encoding="utf-8")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w", encoding="utf-8")


def configure_transformers_compatibility() -> None:
    try:
        import transformers.utils.import_utils as import_utils

        import_utils._torchvision_available = False
    except Exception:
        pass


def configure_logging() -> None:
    if LOG_FILE is None:
        raise RuntimeError("Logging is not configured.")
    logging.basicConfig(
        filename=str(LOG_FILE),
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )


def wait_for_port(host: str, port: int, timeout_seconds: int = 60) -> bool:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.5)
            if sock.connect_ex((host, port)) == 0:
                return True
        time.sleep(0.2)
    return False


def pick_port(host: str, preferred_port: int) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        if sock.connect_ex((host, preferred_port)) != 0:
            return preferred_port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        return int(sock.getsockname()[1])


def main() -> None:
    configure_environment()
    configure_stdio()
    configure_transformers_compatibility()
    configure_logging()
    logging.info("Launcher starting")
    from src.web.app import app
    logging.info("Imported backend app")
    port = pick_port(HOST, int(os.environ.get("SCRIPTOR_RAG_PORT", os.environ.get("OCR_HARNESS_PORT", str(DEFAULT_PORT)))))
    url = f"http://{HOST}:{port}"
    logging.info("Using port %s", port)

    config = uvicorn.Config(
        app=app,
        host=HOST,
        port=port,
        log_level="warning",
        reload=False,
        access_log=False,
        log_config=UVICORN_LOG_CONFIG,
    )
    server = uvicorn.Server(config)
    server_error: list[str] = []

    def run_server() -> None:
        try:
            server.run()
        except Exception:
            server_error.append(traceback.format_exc())
            logging.exception("Server thread failed")

    thread = Thread(target=run_server, daemon=True)
    thread.start()
    logging.info("Server thread started")

    if not wait_for_port(HOST, port):
        if server_error:
            logging.error("Server error before port opened:\n%s", server_error[0])
        raise RuntimeError("Lumia ScriptorRAG backend did not start in time.")

    logging.info("Server is ready, opening browser")
    webbrowser.open(url)
    thread.join()


if __name__ == "__main__":
    main()
