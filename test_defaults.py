import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_manifest_is_valid_json():
    data = json.loads((ROOT / "custom_components/app_papas/manifest.json").read_text())
    assert data["domain"] == "app_papas"
    assert data["version"] == "1.1.0"
    assert data["config_flow"] is True


def test_hacs_is_valid_json():
    data = json.loads((ROOT / "hacs.json").read_text())
    assert data["name"]
    assert "homeassistant" in data


def test_frontend_exists():
    assert (ROOT / "custom_components/app_papas/frontend/app-papas.js").stat().st_size > 1000
