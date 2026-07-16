#!/usr/bin/env python3
"""
Dump the BlockBT FastAPI OpenAPI schema to frontend/openapi.json.

Usage:
    python scripts/generate_openapi.py

The generated file is consumed by openapi-typescript to produce
frontend/src/services/api.d.ts (run `npm run generate-api` in /frontend).
"""

import json
import sys
from pathlib import Path

# Ensure the project src is on the Python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.main import app  # noqa: E402

OUTPUT_PATH = PROJECT_ROOT / "frontend" / "openapi.json"


def main() -> None:
    schema = app.openapi()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(schema, indent=2))
    print(f"✅  OpenAPI schema written to: {OUTPUT_PATH}")
    print(f"    Paths discovered: {list(schema.get('paths', {}).keys())}")


if __name__ == "__main__":
    main()
