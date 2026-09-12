from __future__ import annotations

import re
from typing import Any

from aiohttp import ClientError, ClientSession

from .const import TRANSLATION_URL

LOCAL_TERMS = {
    "chicken": "pollo", "beef": "ternera", "pork": "cerdo", "turkey": "pavo", "lamb": "cordero",
    "fish": "pescado", "salmon": "salmón", "tuna": "atún", "egg": "huevo", "eggs": "huevos",
    "ham": "jamón", "bacon": "bacon", "sausage": "salchicha", "sausages": "salchichas",
    "shrimp": "gambas", "prawn": "gamba", "rice": "arroz", "pasta": "pasta", "bread": "pan",
    "potato": "patata", "potatoes": "patatas", "flour": "harina", "oats": "avena", "oat": "avena",
    "noodles": "fideos", "broccoli": "brócoli", "spinach": "espinacas", "carrot": "zanahoria",
    "carrots": "zanahorias", "tomato": "tomate", "tomatoes": "tomates", "onion": "cebolla",
    "onions": "cebollas", "pepper": "pimiento", "peppers": "pimientos", "lettuce": "lechuga",
    "avocado": "aguacate", "apple": "manzana", "apples": "manzanas", "banana": "plátano", "bananas": "plátanos",
    "lemon": "limón", "lime": "lima", "vegetables": "verduras", "vegetable": "verdura", "salad": "ensalada",
    "olive oil": "aceite de oliva", "milk": "leche", "cheese": "queso", "yogurt": "yogur", "yoghurt": "yogur",
    "honey": "miel", "garlic": "ajo", "butter": "mantequilla", "salt": "sal", "sugar": "azúcar",
    "stock": "caldo", "cream": "nata", "cooked": "cocido", "baked": "al horno", "fried": "frito",
    "grilled": "a la parrilla", "dessert": "postre", "breakfast": "desayuno", "side": "acompañamiento",
    "starter": "entrante", "main": "principal", "snack": "tentempié",
}

CATEGORY_ES = {
    "Beef": "Ternera", "Breakfast": "Desayuno", "Chicken": "Pollo", "Dessert": "Postre", "Lamb": "Cordero",
    "Miscellaneous": "Varios", "Pasta": "Pasta", "Pork": "Cerdo", "Seafood": "Marisco", "Side": "Acompañamiento",
    "Starter": "Entrante", "Vegan": "Vegano", "Vegetarian": "Vegetariano", "Goat": "Cabra", "Soup": "Sopa",
}
AREA_ES = {"Spain": "España", "United Kingdom": "Reino Unido", "Italy": "Italia", "France": "Francia", "Mexico": "México",
           "Canada": "Canadá", "American": "Estados Unidos", "Indian": "India", "Chinese": "China", "Japanese": "Japón",
           "Greek": "Grecia", "Irish": "Irlanda", "Thai": "Tailandia", "Turkish": "Turquía", "Jamaican": "Jamaica"}


def quick_translate(text: str) -> str:
    result = str(text or "")
    for src, dst in sorted(LOCAL_TERMS.items(), key=lambda x: len(x[0]), reverse=True):
        result = re.sub(rf"(?i)\b{re.escape(src)}\b", dst, result)
    return result


def translate_label(text: str, mapping: dict[str, str]) -> str:
    return mapping.get(text, quick_translate(text))


def _chunks(text: str, max_bytes: int = 450) -> list[str]:
    if len(text.encode("utf-8")) <= max_bytes:
        return [text]
    parts = re.split(r"(?<=[.!?])\s+|\n+", text.strip())
    chunks: list[str] = []
    current = ""
    for part in parts:
        if not part:
            continue
        if current and len(f"{current} {part}".encode("utf-8")) > max_bytes:
            chunks.append(current)
            current = part
        else:
            current = f"{current} {part}".strip()
    if current:
        chunks.append(current)
    return chunks or [text]


async def translate_text(session: ClientSession, text: str, *, source: str = "en", target: str = "es") -> str:
    text = str(text or "").strip()
    if not text or source == target:
        return text
    chunks = _chunks(text)
    translated: list[str] = []
    for chunk in chunks:
        try:
            async with session.get(TRANSLATION_URL, params={"q": chunk, "langpair": f"{source}|{target}", "mt": "1"}, timeout=15) as resp:
                if resp.status != 200:
                    translated.append(quick_translate(chunk))
                    continue
                payload = await resp.json(content_type=None)
                value = ((payload.get("responseData") or {}).get("translatedText") or "").strip()
                translated.append(value or quick_translate(chunk))
        except (ClientError, TimeoutError, ValueError):
            translated.append(quick_translate(chunk))
    return " ".join(translated).strip()


async def translate_recipe(session: ClientSession, recipe: dict[str, Any]) -> dict[str, Any]:
    translated = dict(recipe)
    translated["original_name"] = recipe.get("name", "")
    translated["original_category"] = recipe.get("category", "")
    translated["original_area"] = recipe.get("area", "")
    translated["original_description"] = recipe.get("description", "")
    translated["original_steps"] = list(recipe.get("steps", []))
    translated["name"] = await translate_text(session, str(recipe.get("name", "")))
    translated["category"] = translate_label(str(recipe.get("category", "")), CATEGORY_ES)
    translated["area"] = translate_label(str(recipe.get("area", "")), AREA_ES)
    translated["description"] = await translate_text(session, str(recipe.get("description", "")))
    ingredients: list[dict[str, Any]] = []
    for item in recipe.get("ingredients", []):
        row = dict(item)
        row["original_name"] = item.get("name", "")
        row["name"] = await translate_text(session, str(item.get("name", "")))
        if item.get("measure"):
            row["original_measure"] = item.get("measure", "")
            row["measure"] = await translate_text(session, str(item.get("measure", "")))
        ingredients.append(row)
    translated["ingredients"] = ingredients
    translated["steps"] = [await translate_text(session, str(step)) for step in recipe.get("steps", [])]
    translated["language"] = "es"
    return translated
