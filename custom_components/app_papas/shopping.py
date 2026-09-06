from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from copy import deepcopy
from typing import Any

from .defaults import default_shopping
from .recipes import recipe_map

# Canonical ingredient, category, aliases, fallback quantity per portion.
INGREDIENT_CATALOG: tuple[tuple[str, str, tuple[str, ...], float, str], ...] = (
    ("Huevos", "proteina", ("huevo", "huevos"), 2, "ud"),
    ("Pollo", "proteina", ("pollo", "pollo asado", "pollo desmenuzado"), 150, "g"),
    ("Ternera", "proteina", ("ternera", "carne de ternera", "vacuno", "carne vacuna", "res", "bistec de ternera"), 180, "g"),
    ("Carne picada", "proteina", ("carne picada", "carne molida", "picada"), 160, "g"),
    ("Atún", "proteina", ("atún", "atun"), 100, "g"),
    ("Pavo", "proteina", ("pavo", "fiambre de pavo"), 80, "g"),
    ("Jamón", "proteina", ("jamón", "jamon"), 50, "g"),
    ("Salchichas", "proteina", ("salchicha", "salchichas"), 2, "ud"),
    ("Bacon", "proteina", ("bacon", "beicon"), 40, "g"),
    ("Yogur griego", "proteina", ("yogur griego", "yogurt griego"), 200, "g"),
    ("Yogur", "proteina", ("yogur", "yogurt"), 125, "g"),
    ("Proteína en polvo", "proteina", ("proteína en polvo", "proteina en polvo"), 30, "g"),
    ("Leche", "extras", ("leche",), 200, "ml"),
    ("Queso", "extras", ("queso", "quesos"), 30, "g"),
    ("Mantequilla", "extras", ("mantequilla",), 10, "g"),
    ("Aceite de oliva", "extras", ("aceite de oliva", "aceite"), 5, "ml"),
    ("Salsa de soya", "extras", ("salsa de soya", "salsa de soja", "soya", "soja"), 10, "ml"),
    ("Nueces", "extras", ("nueces",), 15, "g"),
    ("Arroz", "carbohidratos", ("arroz",), 70, "g"),
    ("Avena", "carbohidratos", ("avena",), 50, "g"),
    ("Pan integral", "carbohidratos", ("pan integral", "pan de semillas", "pan", "tostada", "tostadas"), 2, "rebanada"),
    ("Pasta", "carbohidratos", ("pasta", "macarrón", "macarrones", "espagueti", "espaguetis"), 80, "g"),
    ("Patatas", "carbohidratos", ("patata", "patatas"), 200, "g"),
    ("Pizza", "carbohidratos", ("pizza",), 0.5, "ud"),
    ("Frijoles", "carbohidratos", ("frijol", "frijoles", "judías", "judias"), 120, "g"),
    ("Verduras variadas", "verduras_frutas", ("verduras", "verdura", "verduras variadas", "ensalada", "ensalada variada", "vegetales"), 150, "g"),
    ("Brócoli", "verduras_frutas", ("brócoli", "brocoli"), 180, "g"),
    ("Coliflor", "verduras_frutas", ("coliflor",), 180, "g"),
    ("Espinacas", "verduras_frutas", ("espinaca", "espinacas"), 80, "g"),
    ("Zanahorias", "verduras_frutas", ("zanahoria", "zanahorias"), 80, "g"),
    ("Aguacate", "verduras_frutas", ("aguacate",), 80, "g"),
    ("Tomate", "verduras_frutas", ("tomate", "tomates"), 80, "g"),
    ("Maíz", "verduras_frutas", ("maíz", "maiz"), 80, "g"),
    ("Plátano", "verduras_frutas", ("plátano", "plátanos", "platano", "platanos"), 1, "ud"),
    ("Manzana", "verduras_frutas", ("manzana", "manzanas"), 1, "ud"),
)


def _norm(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", text.casefold()) if not unicodedata.combining(c))


def _ingredient_lookup() -> dict[str, tuple[str, str, float, str]]:
    result: dict[str, tuple[str, str, float, str]] = {}
    for canonical, category, aliases, fallback_qty, unit in INGREDIENT_CATALOG:
        for alias in aliases:
            result[_norm(alias)] = (canonical, category, fallback_qty, unit)
    return result


LOOKUP = _ingredient_lookup()


def _number_before(text: str, alias: str) -> tuple[float | None, str | None]:
    pattern = re.compile(
        rf"(?<!\w)(\d+(?:[\.,]\d+)?)\s*(kg|g|ml|cl|l|ud|unidad|unidades|rebanada|rebanadas|docena)?\s*(?:de\s+)?{re.escape(alias)}\b",
        re.IGNORECASE,
    )
    match = pattern.search(text)
    if not match:
        return None, None
    qty = float(match.group(1).replace(",", "."))
    unit = match.group(2)
    if unit:
        unit = unit.lower()
    return qty, unit


def _convert(qty: float, unit: str | None, target: str) -> float:
    if not unit:
        return qty
    u = unit.lower()
    if u == target:
        return qty
    if target == "g" and u == "kg":
        return qty * 1000
    if target == "ml" and u == "l":
        return qty * 1000
    if target == "ml" and u == "cl":
        return qty * 10
    if target == "ud" and u in {"unidad", "unidades", "ud"}:
        return qty
    if target == "rebanada" and u in {"rebanada", "rebanadas"}:
        return qty
    if target == "ud" and u == "docena":
        return qty * 12
    return qty


def detect_from_text(text: str, portions: int = 1) -> list[dict[str, Any]]:
    text_norm = _norm(text)
    found: list[dict[str, Any]] = []
    # Longest aliases first so "yogur griego" wins over "yogur".
    seen: set[str] = set()
    aliases = sorted(LOOKUP, key=len, reverse=True)
    for alias_norm in aliases:
        if not re.search(rf"(?<!\w){re.escape(alias_norm)}(?!\w)", text_norm):
            continue
        canonical, category, fallback_qty, target_unit = LOOKUP[alias_norm]
        if canonical in seen:
            continue
        # Search original-ish text using an accent-insensitive whitespace pattern.
        qty, source_unit = _number_before(_norm(text), alias_norm)
        amount = _convert(qty, source_unit, target_unit) if qty is not None else fallback_qty * portions
        found.append({
            "ingredient_id": _norm(canonical).replace(" ", "_"),
            "name": canonical,
            "category": category,
            "qty": amount,
            "unit": target_unit,
            "source": "menu_estimate" if qty is None else "menu_explicit",
        })
        seen.add(canonical)
    return found


def _menu_portions(store: Any) -> int:
    children = store.data.get("settings", {}).get("children", ["Niñas"])
    if not isinstance(children, list):
        children = ["Niñas"]
    return max(1, 1 + len(children))


def _recipe_items(store: Any) -> list[dict[str, Any]]:
    recipes = recipe_map(store.data.get("recipes", []))
    portions = _menu_portions(store)
    result = []
    for day in store.data.get("menu", {}).values():
        if not isinstance(day, dict):
            continue
        for meal in day.values():
            if not isinstance(meal, dict):
                continue
            rid = meal.get("recipe_id")
            recipe = recipes.get(str(rid)) if rid else None
            if not recipe:
                continue
            for ing in recipe.get("ingredients", []):
                if ing.get("optional"):
                    continue
                result.append({**ing, "qty": float(ing.get("qty", 0)) * portions, "source": "recipe"})
    return result


def _manual_menu_items(store: Any) -> list[dict[str, Any]]:
    children = store.data.get("settings", {}).get("children", ["Niñas"])
    child_count = max(1, len(children)) if isinstance(children, list) else 1
    result = []
    for day in store.data.get("menu", {}).values():
        if not isinstance(day, dict):
            continue
        for meal in day.values():
            if not isinstance(meal, dict):
                continue
            # If a complete recipe is associated, its exact quantities take priority.
            if meal.get("recipe_id"):
                continue
            result.extend(detect_from_text(str(meal.get("papa", "")), portions=1))
            result.extend(detect_from_text(str(meal.get("ninas", "")), portions=child_count))
    return result


def _format_num(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else f"{value:.1f}".rstrip("0").rstrip(".")


def sync_menu_shopping(store: Any) -> bool:
    current = store.data.get("shopping", {})
    base = default_shopping()
    aggregates: dict[tuple[str, str], dict[str, Any]] = {}

    for item in _recipe_items(store) + _manual_menu_items(store):
        key = (item["category"], item["name"])
        if key not in aggregates:
            aggregates[key] = deepcopy(item)
        elif aggregates[key]["unit"] == item["unit"]:
            aggregates[key]["qty"] += item["qty"]

    old_generated = {}
    for category, items in current.items():
        for item in items or []:
            if item.get("source", "").startswith("menu") or item.get("source") == "recipe":
                old_generated[(category, str(item.get("ingredient_id", item.get("name", ""))).casefold())] = item

    result = {category: list(items) for category, items in base.items()}
    for category, items in current.items():
        for item in items or []:
            if item.get("source") in ("manual", "custom"):
                result.setdefault(category, []).append(item)

    for (category, name), item in sorted(aggregates.items()):
        ingredient_id = item.get("ingredient_id") or _norm(name).replace(" ", "_")
        old = old_generated.get((category, ingredient_id.casefold()))
        result.setdefault(category, []).append({
            "id": old.get("id", f"menu_{category}_{ingredient_id}") if old else f"menu_{category}_{ingredient_id}",
            "name": name,
            "qty": round(float(item["qty"]), 2),
            "unit": item["unit"],
            "checked": bool(old.get("checked", False)) if old else False,
            "source": "recipe" if item["source"] == "recipe" else "menu_estimate",
            "ingredient_id": ingredient_id,
        })

    return result != current, result
