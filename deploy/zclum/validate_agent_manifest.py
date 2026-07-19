import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "deploy" / "zclum" / "ocr-harness-agent.json"
APP = ROOT / "src" / "web" / "app.py"


def normalize_route(path: str) -> str:
    return re.sub(r"\{[^}]+\}", "{}", path)


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    app_source = APP.read_text(encoding="utf-8")
    declared = {
        (route["method"].lower(), normalize_route(route["path"]))
        for route in manifest["routes"]
    }
    implemented = set()
    for match in re.finditer(r"@app\.(get|post|put|delete)\(\"([^\"]+)\"", app_source):
        implemented.add((match.group(1), normalize_route(match.group(2))))

    missing = sorted(declared - implemented)
    if missing:
        for method, path in missing:
            print(f"missing route: {method.upper()} {path}")
        raise SystemExit(1)

    required = ["app_id", "name", "base_url_placeholder", "routes", "required_env", "frontend_cards"]
    for key in required:
        if key not in manifest:
            raise SystemExit(f"missing manifest field: {key}")

    print(f"ok: {len(manifest['routes'])} routes validated")


if __name__ == "__main__":
    main()
