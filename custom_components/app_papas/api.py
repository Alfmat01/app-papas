from __future__ import annotations

from datetime import date
from http import HTTPStatus
from typing import Any
from uuid import uuid4

from aiohttp import ClientError, ClientSession, web
from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import dt as dt_util

from .const import API_URL, CONF_MEALDB_API_KEY, DEFAULT_MEALDB_API_KEY, DOMAIN
from .recipes import normalize_external_meal
from .shopping import sync_menu_shopping
from .translation import AREA_ES, CATEGORY_ES, quick_translate, translate_recipe, translate_text, translate_label
from .storage import AppPapasStore


def _get_store(hass: HomeAssistant) -> AppPapasStore | None:
    return next(iter(hass.data.get(DOMAIN, {}).values()), None)


def _api_key(hass: HomeAssistant) -> str:
    for entry in hass.config_entries.async_entries(DOMAIN):
        return str(entry.options.get(CONF_MEALDB_API_KEY, entry.data.get(CONF_MEALDB_API_KEY, DEFAULT_MEALDB_API_KEY)))
    return DEFAULT_MEALDB_API_KEY


class AppPapasDataView(HomeAssistantView):
    url = f"{API_URL}/data"
    name = "api:app_papas:data"
    requires_auth = True

    async def get(self, request: web.Request) -> web.Response:
        store = _get_store(request.app["hass"])
        if store is None:
            return self.json_message("Integración no configurada", HTTPStatus.NOT_FOUND)
        return self.json(store.data)

    async def post(self, request: web.Request) -> web.Response:
        store = _get_store(request.app["hass"])
        if store is None:
            return self.json_message("Integración no configurada", HTTPStatus.NOT_FOUND)
        try:
            payload = await request.json()
        except (TypeError, ValueError):
            return self.json_message("JSON inválido", HTTPStatus.BAD_REQUEST)
        if not isinstance(payload, dict):
            return self.json_message("El cuerpo debe ser un objeto", HTTPStatus.BAD_REQUEST)
        old_menu = store.data.get("menu")
        store.data = store._merge(store.data, payload)
        if "menu" in payload and payload.get("menu") != old_menu:
            changed, new_shopping = sync_menu_shopping(store)
            if changed:
                store.data["shopping"] = new_shopping
        await store.async_save()
        return self.json(store.data)


class AppPapasDayView(HomeAssistantView):
    url = f"{API_URL}/day/{{day}}"
    name = "api:app_papas:day"
    requires_auth = True

    async def get(self, request: web.Request, day: str) -> web.Response:
        store = _get_store(request.app["hass"])
        if store is None:
            return self.json_message("Integración no configurada", HTTPStatus.NOT_FOUND)
        try:
            date.fromisoformat(day)
        except ValueError:
            return self.json_message("Fecha inválida", HTTPStatus.BAD_REQUEST)
        return self.json(store.get_day(day))

    async def post(self, request: web.Request, day: str) -> web.Response:
        store = _get_store(request.app["hass"])
        if store is None:
            return self.json_message("Integración no configurada", HTTPStatus.NOT_FOUND)
        try:
            date.fromisoformat(day)
            payload = await request.json()
        except (TypeError, ValueError):
            return self.json_message("Fecha o JSON inválido", HTTPStatus.BAD_REQUEST)
        if not isinstance(payload, dict):
            return self.json_message("El cuerpo debe ser un objeto", HTTPStatus.BAD_REQUEST)
        current = store.get_day(day)
        for key in ("desayuno", "almuerzo", "cena", "notas"):
            if key in payload:
                current[key] = str(payload.get(key, ""))
        if isinstance(payload.get("checklist"), dict):
            current["checklist"] = {str(k): bool(v) for k, v in payload["checklist"].items()}
        await store.async_save()
        return self.json(current)


class AppPapasStatsView(HomeAssistantView):
    url = f"{API_URL}/stats"
    name = "api:app_papas:stats"
    requires_auth = True

    async def get(self, request: web.Request) -> web.Response:
        store = _get_store(request.app["hass"])
        if store is None:
            return self.json_message("Integración no configurada", HTTPStatus.NOT_FOUND)
        today = dt_util.now().date()
        history = store.history(today, 14)
        return self.json({
            "today_score": store.score(today.isoformat()),
            "streak": store.streak(today),
            "history": history,
            "shopping_pending": store.shopping_pending(),
        })


class AppPapasRecipeSearchView(HomeAssistantView):
    url = f"{API_URL}/recipes/search"
    name = "api:app_papas:recipes_search"
    requires_auth = True

    async def get(self, request: web.Request) -> web.Response:
        hass: HomeAssistant = request.app["hass"]
        store = _get_store(hass)
        if store is None:
            return self.json_message("Integración no configurada", HTTPStatus.NOT_FOUND)
        query = str(request.query.get("q", "")).strip()
        category = str(request.query.get("category", "")).strip()
        area = str(request.query.get("area", "")).strip()
        ingredient = str(request.query.get("ingredient", "")).strip()
        source = str(request.query.get("source", "all")).strip().lower()
        try:
            limit = min(max(int(request.query.get("limit", 30)), 1), 50)
        except ValueError:
            limit = 30

        local = store.data.get("recipes", [])
        local_results = []
        qnorm = query.casefold()
        for rec in local:
            hay = " ".join([str(rec.get("name", "")), str(rec.get("description", "")), *map(str, rec.get("aliases", []))]).casefold()
            if qnorm and qnorm not in hay:
                continue
            if category and str(rec.get("category", "")).casefold() != category.casefold():
                continue
            local_results.append(self._summary(rec, "local"))

        remote_results: list[dict[str, Any]] = []
        if source != "local" and (query or category or area or ingredient):
            try:
                session: ClientSession = async_get_clientsession(hass)
                key = _api_key(hass)
                base = f"https://www.themealdb.com/api/json/v1/{key}"
                params: dict[str, str] = {}
                if ingredient and not query and not category and not area:
                    params["i"] = ingredient
                    url = f"{base}/filter.php"
                elif category and not query and not ingredient and not area:
                    params["c"] = category
                    url = f"{base}/filter.php"
                elif area and not query and not ingredient and not category:
                    params["a"] = area
                    url = f"{base}/filter.php"
                else:
                    search_term = query or category or ingredient or area
                    if search_term:
                        translated_query = await translate_text(session, search_term)
                        params["s"] = translated_query if translated_query and translated_query.casefold() != search_term.casefold() else search_term
                    url = f"{base}/search.php"
                async with session.get(url, params=params, timeout=15) as resp:
                    if resp.status == 200:
                        payload = await resp.json(content_type=None)
                        meals = payload.get("meals") or []
                        for meal in meals[:limit]:
                            remote_results.append(self._summary_remote(meal))
            except (ClientError, TimeoutError, ValueError):
                remote_results = []

        combined = local_results + remote_results
        return self.json({"results": combined[:limit], "source": source, "online_available": bool(remote_results)})

    @staticmethod
    def _summary(rec: dict[str, Any], source: str) -> dict[str, Any]:
        return {
            "id": rec.get("id"), "name": rec.get("name"), "category": rec.get("category", ""),
            "area": rec.get("area", ""), "description": rec.get("description", ""),
            "prep_minutes": rec.get("prep_minutes", 0), "cook_minutes": rec.get("cook_minutes", 0),
            "servings": rec.get("servings", 1), "image": rec.get("image", ""), "source": source,
            "source_id": rec.get("source_id", ""), "ingredients_count": len(rec.get("ingredients", [])),
        }

    @staticmethod
    def _summary_remote(meal: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": f"mealdb_{meal.get('idMeal')}", "source_id": str(meal.get("idMeal", "")),
            "name": quick_translate(str(meal.get("strMeal", ""))), "original_name": meal.get("strMeal", ""),
            "category": translate_label(str(meal.get("strCategory", "")), CATEGORY_ES), "original_category": meal.get("strCategory", ""),
            "area": translate_label(str(meal.get("strArea", "")), AREA_ES), "original_area": meal.get("strArea", ""), "description": "", "prep_minutes": 0,
            "cook_minutes": 0, "servings": 1, "image": meal.get("strMealThumb", ""),
            "ingredients_count": 0, "source": "online",
        }


class AppPapasRecipeDetailView(HomeAssistantView):
    url = f"{API_URL}/recipes/detail/{{recipe_id}}"
    name = "api:app_papas:recipes_detail"
    requires_auth = True

    async def get(self, request: web.Request, recipe_id: str) -> web.Response:
        hass: HomeAssistant = request.app["hass"]
        store = _get_store(hass)
        if store is None:
            return self.json_message("Integración no configurada", HTTPStatus.NOT_FOUND)
        local = next((r for r in store.data.get("recipes", []) if r.get("id") == recipe_id), None)
        if local:
            return self.json(local)
        if not recipe_id.startswith("mealdb_"):
            return self.json_message("Receta no encontrada", HTTPStatus.NOT_FOUND)
        meal_id = recipe_id.split("_", 1)[1]
        try:
            session = async_get_clientsession(hass)
            key = _api_key(hass)
            url = f"https://www.themealdb.com/api/json/v1/{key}/lookup.php"
            async with session.get(url, params={"i": meal_id}, timeout=15) as resp:
                if resp.status != 200:
                    return self.json_message("No se pudo consultar TheMealDB", HTTPStatus.BAD_GATEWAY)
                payload = await resp.json(content_type=None)
                meal = (payload.get("meals") or [None])[0]
                if not meal:
                    return self.json_message("Receta no encontrada", HTTPStatus.NOT_FOUND)
                normalized = normalize_external_meal(meal)
                cache = hass.data.setdefault(DOMAIN, {}).setdefault("translation_cache", {})
                cache_key = f"mealdb:{meal_id}:es"
                if cache_key not in cache:
                    cache[cache_key] = await translate_recipe(session, normalized)
                return self.json(cache[cache_key])
        except (ClientError, TimeoutError, ValueError):
            return self.json_message("No se pudo consultar TheMealDB", HTTPStatus.BAD_GATEWAY)


class AppPapasRecipeMetaView(HomeAssistantView):
    url = f"{API_URL}/recipes/meta"
    name = "api:app_papas:recipes_meta"
    requires_auth = True

    async def get(self, request: web.Request) -> web.Response:
        hass: HomeAssistant = request.app["hass"]
        try:
            session = async_get_clientsession(hass)
            key = _api_key(hass)
            base = f"https://www.themealdb.com/api/json/v1/{key}"
            result: dict[str, Any] = {}
            for param, endpoint, field in (("c", "categories.php", "categories"), ("a", "list.php", "areas"), ("i", "list.php", "ingredients")):
                params = {param: "list"} if endpoint == "list.php" else {}
                async with session.get(f"{base}/{endpoint}", params=params, timeout=15) as resp:
                    if resp.status != 200:
                        continue
                    data = await resp.json(content_type=None)
                    key_name = "meals" if endpoint == "list.php" else field
                    rows = data.get(key_name) or []
                    if param == "c":
                        result[field] = [x.get("strCategory") for x in rows if x.get("strCategory")]
                    elif param == "a":
                        result[field] = [x.get("strArea") for x in rows if x.get("strArea")]
                    else:
                        result[field] = [x.get("strIngredient") for x in rows if x.get("strIngredient")]
            return self.json(result)
        except (ClientError, TimeoutError, ValueError):
            return self.json({"categories": [], "areas": [], "ingredients": []})


class AppPapasRecipeLibraryView(HomeAssistantView):
    url = f"{API_URL}/recipes/library"
    name = "api:app_papas:recipes_library"
    requires_auth = True

    async def post(self, request: web.Request) -> web.Response:
        store = _get_store(request.app["hass"])
        if store is None:
            return self.json_message("Integración no configurada", HTTPStatus.NOT_FOUND)
        payload = await request.json()
        recipe_data = payload.get("recipe") if isinstance(payload, dict) else None
        if not isinstance(recipe_data, dict):
            return self.json_message("Receta inválida", HTTPStatus.BAD_REQUEST)
        recipe_data = dict(recipe_data)
        recipe_data["id"] = recipe_data.get("id") or f"custom_{uuid4().hex}"
        recipe_data["source"] = "local"
        recipes = store.data.setdefault("recipes", [])
        recipes = [r for r in recipes if r.get("id") != recipe_data["id"]]
        recipes.append(recipe_data)
        store.data["recipes"] = recipes
        await store.async_save()
        return self.json(recipe_data)

    async def delete(self, request: web.Request) -> web.Response:
        store = _get_store(request.app["hass"])
        if store is None:
            return self.json_message("Integración no configurada", HTTPStatus.NOT_FOUND)
        rid = str(request.query.get("id", "")).strip()
        if not rid:
            return self.json_message("Falta id", HTTPStatus.BAD_REQUEST)
        store.data["recipes"] = [r for r in store.data.get("recipes", []) if r.get("id") != rid]
        for meals in store.data.get("menu", {}).values():
            for meal in meals.values():
                if isinstance(meal, dict) and meal.get("recipe_id") == rid:
                    meal["recipe_id"] = ""
        await store.async_save()
        return self.json({"ok": True})


async def async_setup_api(hass: HomeAssistant) -> None:
    if hass.data.get(f"{DOMAIN}_api_registered"):
        return
    for view in (
        AppPapasDataView(), AppPapasDayView(), AppPapasStatsView(),
        AppPapasRecipeSearchView(), AppPapasRecipeDetailView(), AppPapasRecipeMetaView(), AppPapasRecipeLibraryView(),
    ):
        hass.http.register_view(view)
    hass.data[f"{DOMAIN}_api_registered"] = True
