from __future__ import annotations

from typing import Any

from .defaults import default_shopping

# Tuples: canonical name, category, aliases/search terms.
# Matching is intentionally conservative: it extracts common ingredients
# and foods, not arbitrary words from the user's menu sentences.
INGREDIENT_CATALOG: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("Huevos", "proteina", ("huevo", "huevos")),
    ("Pollo", "proteina", ("pollo", "pollo asado", "pollo desmenuzado")),
    ("Ternera", "proteina", ("ternera", "carne de ternera", "vacuno", "carne vacuna", "res", "bistec de ternera")),
    ("Carne picada", "proteina", ("carne picada", "carne molida", "picada", "carne")),
    ("Atún", "proteina", ("atún", "atun")),
    ("Pavo", "proteina", ("pavo", "fiambre de pavo")),
    ("Jamón", "proteina", ("jamón", "jamon")),
    ("Salchichas", "proteina", ("salchicha", "salchichas")),
    ("Bacon", "proteina", ("bacon", "beicon")),
    ("Yogur griego", "proteina", ("yogur griego", "yogurt griego")),
    ("Yogur", "proteina", ("yogur", "yogurt")),
    ("Leche", "extras", ("leche",)),
    ("Queso", "extras", ("queso", "quesos")),
    ("Mantequilla", "extras", ("mantequilla",)),
    ("Aceite de oliva", "extras", ("aceite de oliva", "aceite")),
    ("Salsa de soya", "extras", ("salsa de soya", "salsa de soja", "soya", "soja")),
    ("Salsa", "extras", ("salsa",)),
    ("Nueces", "extras", ("nueces",)),
    ("Arroz", "carbohidratos", ("arroz",)),
    ("Avena", "carbohidratos", ("avena",)),
    ("Pan", "carbohidratos", ("pan", "tostada", "tostadas")),
    ("Pasta", "carbohidratos", ("pasta", "macarrón", "macarrones", "espagueti", "espaguetis")),
    ("Patatas", "carbohidratos", ("patata", "patatas")),
    ("Pizza", "carbohidratos", ("pizza",)),
    ("Frijoles", "carbohidratos", ("frijol", "frijoles", "judías", "judias")),
    ("Brócoli", "verduras_frutas", ("brócoli", "brocoli")),
    ("Coliflor", "verduras_frutas", ("coliflor",)),
    ("Espinacas", "verduras_frutas", ("espinaca", "espinacas")),
    ("Zanahorias", "verduras_frutas", ("zanahoria", "zanahorias")),
    ("Aguacate", "verduras_frutas", ("aguacate",)),
    ("Tomate", "verduras_frutas", ("tomate", "tomates")),
    ("Maíz", "verduras_frutas", ("maíz", "maiz")),
    ("Plátanos", "verduras_frutas", ("plátano", "plátanos", "platano", "platanos")),
    ("Manzanas", "verduras_frutas", ("manzana", "manzanas")),
)


def _detect(menu: dict[str, Any]) -> dict[str, set[str]]:
    detected = {"proteina": set(), "carbohidratos": set(), "verduras_frutas": set(), "extras": set()}
    texts: list[str] = []
    for day in menu.values():
        if not isinstance(day, dict):
            continue
        for meal in day.values():
            if not isinstance(meal, dict):
                continue
            texts.extend([str(meal.get("papa", "")), str(meal.get("ninas", ""))])

    # Longest aliases first avoids a generic alias (e.g. "carne")
    # winning before a more specific one (e.g. "carne picada").
    for text in texts:
        low = text.casefold()
        for canonical, category, aliases in INGREDIENT_CATALOG:
            if any(alias.casefold() in low for alias in sorted(aliases, key=len, reverse=True)):
                detected[category].add(canonical)
    return detected


def sync_menu_shopping(store: Any) -> bool:
    """Synchronize generated shopping items with the current weekly menu.

    Default items and manually-added items are preserved. Generated menu items
    are rebuilt so removed ingredients disappear and checked state is preserved
    for ingredients that remain on the menu.
    """
    current = store.data.get("shopping", {})
    detected = _detect(store.data.get("menu", {}))
    base = default_shopping()

    existing_generated: dict[str, dict[str, dict[str, Any]]] = {}
    for category, items in current.items():
        for item in items or []:
            if item.get("source") == "menu":
                existing_generated.setdefault(category, {})[str(item.get("name", "")).casefold()] = item

    result = {category: list(items) for category, items in base.items()}
    for category, items in current.items():
        for item in items or []:
            if item.get("source") in ("manual", "custom"):
                result.setdefault(category, []).append(item)

    for category, names in detected.items():
        for name in sorted(names):
            old = existing_generated.get(category, {}).get(name.casefold())
            result[category].append({
                "id": old.get("id", f"menu_{category}_{name.casefold().replace(' ', '_')}"),
                "name": name,
                "checked": bool(old.get("checked", False)) if old else False,
                "source": "menu",
            })

    changed = result != current
    store.data["shopping"] = result
    return changed
