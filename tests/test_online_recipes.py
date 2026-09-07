import importlib.util
import sys
from pathlib import Path
import types

ROOT = Path(__file__).parents[1]
PACKAGE = "custom_components.app_papas"
pkg = types.ModuleType(PACKAGE)
pkg.__path__ = [str(ROOT / "custom_components/app_papas")]
sys.modules[PACKAGE] = pkg

path = ROOT / "custom_components/app_papas/recipes.py"
spec = importlib.util.spec_from_file_location(f"{PACKAGE}.recipes_online", path)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
assert spec.loader is not None
spec.loader.exec_module(mod)


def test_normalize_themealdb_recipe_keeps_complete_fields():
    meal = {
        "idMeal": "52772",
        "strMeal": "Teriyaki Chicken Casserole",
        "strCategory": "Chicken",
        "strArea": "Japanese",
        "strInstructions": "Step one.\nStep two.",
        "strMealThumb": "https://example.test/meal.jpg",
        "strYoutube": "https://youtube.test/video",
        "strIngredient1": "chicken breasts",
        "strMeasure1": "2",
        "strIngredient2": "brown rice",
        "strMeasure2": "3 cups",
        "strIngredient3": "",
        "strMeasure3": "",
    }
    recipe = mod.normalize_external_meal(meal)
    assert recipe["id"] == "mealdb_52772"
    assert recipe["source_name"] == "TheMealDB"
    assert recipe["name"] == "Teriyaki Chicken Casserole"
    assert len(recipe["ingredients"]) == 2
    assert recipe["steps"] == ["Step one.", "Step two."]
