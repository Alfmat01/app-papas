from pathlib import Path
import json

ROOT = Path(__file__).parents[1]

def test_manifest_metadata():
    manifest = json.loads((ROOT / "custom_components/app_papas/manifest.json").read_text())
    assert manifest["codeowners"] == ["Alfmat01"]
    assert manifest["config_flow"] is True
    assert manifest["documentation"] == "https://github.com/Alfmat01/app-papas"
    assert manifest["issue_tracker"] == "https://github.com/Alfmat01/app-papas/issues"
    assert manifest["version"] == "1.3.1"

def test_frontend_exists():
    assert (ROOT / "custom_components/app_papas/frontend/app-papas.js").exists()
    assert (ROOT / "custom_components/app_papas/frontend/app-papas-card.js").exists()


def test_shopping_contains_ternera_alias():
    text = (ROOT / "custom_components/app_papas/shopping.py").read_text()
    assert '"Ternera"' in text
    assert '"ternera"' in text

def test_dashboard_has_no_complete_checklist_quick_action():
    text = (ROOT / "custom_components/app_papas/frontend/app-papas.js").read_text()
    assert '<button class="secondary" id="complete-check">Completar checklist</button>' not in text
    assert '<button class="secondary" id="complete-check">Marcar todo</button>' in text


def test_frontend_has_recipe_tab_and_quantity_copy():
    text = (ROOT / "custom_components/app_papas/frontend/app-papas.js").read_text()
    assert '["recetas","📖 Recetas"]' in text
    assert 'data-recipe=' in text
    assert 'cantidades' in text
    assert 'Buscar' in text
    assert 'TheMealDB' in text
