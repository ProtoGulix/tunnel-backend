"""Export le schéma OpenAPI de l'application FastAPI en JSON et YAML."""
import json
import sys
from pathlib import Path

import yaml

# Ajouter la racine du projet au path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from api.app import app  # noqa: E402


def export():
    schema = app.openapi()

    json_path = ROOT / "openapi.json"
    yaml_path = ROOT / "openapi.yaml"

    json_path.write_text(json.dumps(schema, indent=2, ensure_ascii=False), encoding="utf-8")
    yaml_path.write_text(yaml.dump(schema, allow_unicode=True, sort_keys=False, default_flow_style=False), encoding="utf-8")

    print(f"openapi.json  ({json_path.stat().st_size:,} bytes)")
    print(f"openapi.yaml  ({yaml_path.stat().st_size:,} bytes)")


if __name__ == "__main__":
    export()
