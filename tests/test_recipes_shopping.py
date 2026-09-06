import importlib.util
import sys
from pathlib import Path
import types

ROOT = Path(__file__).parents[1]
PACKAGE = "custom_components.app_papas"

# Load the pure-Python recipe/shopping modules without importing the integration __init__.
pkg = types.ModuleType(PACKAGE)
pkg.__path__ = [str(ROOT / "custom_components/app_papas")]
sys.modules[PACKAGE] = pkg

def _load(name):
    path = ROOT / "custom_components/app_papas" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"{PACKAGE}.{name}", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module

const = _load("const")
recipes = _load("recipes")
defaults = _load("defaults")
shopping = _load("shopping")


class DummyStore:
    def __init__(self):
        self.data = defaults.default_data()


def test_recipe_quantities_are_aggregated():
    store = DummyStore()
    store.data["menu"]["lunes"]["almuerzo"]["recipe_id"] = "ternera_arroz_brocoli"
    store.data["menu"]["martes"]["almuerzo"]["recipe_id"] = "ternera_arroz_brocoli"
    changed, result = shopping.sync_menu_shopping(store)
    assert changed
    ternera = next(x for x in result["proteina"] if x.get("name") == "Ternera")
    assert ternera["qty"] == 720
    assert ternera["unit"] == "g"
    assert ternera["source"] == "recipe"


def test_legacy_text_ternera_gets_estimate():
    store = DummyStore()
    store.data["menu"]["miercoles"]["cena"]["recipe_id"] = ""
    store.data["menu"]["miercoles"]["cena"]["papa"] = "Ternera"
    store.data["menu"]["miercoles"]["cena"]["ninas"] = "Ternera"
    items = shopping._manual_menu_items(store)
    item = next(x for x in items if x.get("name") == "Ternera")
    assert item["qty"] > 0
    assert item["unit"] == "g"
