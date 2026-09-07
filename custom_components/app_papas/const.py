from __future__ import annotations

DOMAIN = "app_papas"
NAME = "Alimentación para Papás"
VERSION = "1.3.0"
STORAGE_VERSION = 1
DATA_SCHEMA_VERSION = 3
STORAGE_KEY = DOMAIN
PANEL_PATH = DOMAIN
STATIC_URL = f"/api/{DOMAIN}/static"
API_URL = f"/api/{DOMAIN}"

CONF_TITLE = "title"
CONF_ADULT_NAME = "adult_name"
CONF_CHILDREN = "children"
CONF_NOTIFICATIONS = "notifications_enabled"
CONF_NOTIFY_SERVICE = "notify_service"
CONF_THEME = "theme"
CONF_THEME_OPTIONS = "theme_options"
CONF_THEMENAME = "theme_name"
CONF_THEME_AUTO = "theme_auto"
CONF_MEALDB_API_KEY = "mealdb_api_key"
DEFAULT_TITLE = "Alimentación familiar"
DEFAULT_ADULT_NAME = "Papá"
DEFAULT_CHILDREN = "Niñas"
DEFAULT_MEALDB_API_KEY = "1"

MEALDB_BASE_URL = "https://www.themealdb.com/api/json/v1"

DAYS = [
    ("lunes", "Lunes"), ("martes", "Martes"), ("miercoles", "Miércoles"),
    ("jueves", "Jueves"), ("viernes", "Viernes"), ("sabado", "Sábado"),
    ("domingo", "Domingo"),
]
MEALS = [("desayuno", "Desayuno"), ("almuerzo", "Almuerzo"), ("cena", "Cena")]
SHOPPING_CATEGORIES = [
    ("proteina", "Proteína"), ("carbohidratos", "Carbohidratos"),
    ("verduras_frutas", "Verduras / Frutas"), ("extras", "Extras"),
]
PLAN_FIELDS = [
    "d1_problema", "d1_cuando", "d2_proteinas", "d3_bebida", "d4_rapida1",
    "d4_rapida2", "d4_rapida3", "d5_pedido", "d6_reinicio", "d7_problema", "d7_bebida",
]
CHECKLIST_ITEMS = [
    ("proteina", "¿Construí mis comidas principales alrededor de una proteína?"),
    ("agua", "¿Bebí suficiente agua hoy?"),
    ("calorias_liquidas", "¿Limité las calorías líquidas innecesarias?"),
    ("fruta_verdura", "¿Comí alguna fruta o verdura hoy?"),
    ("respaldo", "¿Tenía una comida de respaldo fácil disponible?"),
    ("comer_fuera", "¿Tomé al menos una mejor decisión al comer fuera?"),
    ("satisfecho", "¿Dejé de comer cuando estaba satisfecho en lugar de repleto?"),
    ("reinicio", "Si me salí del camino, ¿volví a él con mi siguiente comida?"),
]
PLATFORMS = ["sensor"]

SERVICE_RESET_TODAY = "reset_today"
SERVICE_GENERATE_SHOPPING = "generate_shopping"
SERVICE_COPY_WEEK = "copy_week"
SERVICE_ADD_SHOPPING_ITEM = "add_shopping_item"
SERVICE_COMPLETE_CHECKLIST = "complete_checklist"
SERVICE_NOTIFY_TODAY = "notify_today"
SERVICE_SET_MENU_RECIPE = "set_menu_recipe"

SENSOR_TYPES = {
    "checklist": "Checklist hoy",
    "shopping_pending": "Compra pendiente",
    "streak": "Racha actual",
    "today_score": "Puntuación de hoy",
    "next_meal": "Próxima comida",
}
