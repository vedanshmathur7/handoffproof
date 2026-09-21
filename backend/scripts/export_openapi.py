import json
from pathlib import Path

from app.main import app

OUTPUT = Path(__file__).resolve().parents[2] / "docs" / "openapi.json"
OUTPUT.write_text(json.dumps(app.openapi(), indent=2) + "\n")
print(f"Wrote {OUTPUT}")
