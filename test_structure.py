from pathlib import Path
import json

ROOT = Path(__file__).parents[1]

def test_manifest_metadata():
    manifest = json.loads((ROOT / "custom_components/app_papas/manifest.json").read_text())
    assert manifest["codeowners"] == ["Alfmat01"]
    assert manifest["config_flow"] is True
    assert manifest["documentation"] == "https://github.com/Alfmat01/app-papas"
    assert manifest["issue_tracker"] == "https://github.com/Alfmat01/app-papas/issues"
    assert manifest["version"] == "1.1.0"

def test_frontend_exists():
    assert (ROOT / "custom_components/app_papas/frontend/app-papas.js").exists()
    assert (ROOT / "custom_components/app_papas/frontend/app-papas-card.js").exists()
