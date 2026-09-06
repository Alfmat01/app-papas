from __future__ import annotations

from .const import DAYS, MEALS, SHOPPING_CATEGORIES, PLAN_FIELDS
from .recipes import default_recipes


def default_menu() -> dict:
    values = {
        ("lunes", "desayuno"): ("2 huevos revueltos (sin pan)", "1 huevo revuelto + tostada con mantequilla"),
        ("lunes", "almuerzo"): ("Pollo asado y ensalada verde", "Pollo desmenuzado + arroz y zanahoria"),
        ("lunes", "cena"): ("Restos de pollo y brócoli salteado", "Sopita de verduras con pan"),
        ("martes", "desayuno"): ("Yogur griego y plátano", "Avena con leche y plátano"),
        ("martes", "almuerzo"): ("Sándwich de atún (sin pan blanco)", "Sándwich de pavo y queso"),
        ("martes", "cena"): ("Carne picada con arroz y verduras", "Carne picada con puré de patata"),
        ("miercoles", "desayuno"): ("Avena sin azúcar", "Cereal (poca azúcar) con leche"),
        ("miercoles", "almuerzo"): ("Restos de carne picada", "Pasta con salsa de tomate y queso"),
        ("miercoles", "cena"): ("Ensalada de atún y aguacate", "Tortilla francesa con jamón"),
        ("jueves", "desayuno"): ("Batido de proteína con plátano", "Yogur con frutas"),
        ("jueves", "almuerzo"): ("2 sándwiches de pavo", "Macarrones con queso"),
        ("jueves", "cena"): ("Revuelto de huevos con tostadas", "Revuelto de huevos con tostadas (sin picante)"),
        ("viernes", "desayuno"): ("Yogur", "Tostada con aguacate"),
        ("viernes", "almuerzo"): ("Pollo, arroz y brócoli", "Salchichas con puré"),
        ("viernes", "cena"): ("SALIDA (hamburguesa sin patatas ni refresco)", "SALIDA (hamburguesa infantil con patatas pequeñas y agua)"),
        ("sabado", "desayuno"): ("Huevos", "Tortitas (plátano y avena)"),
        ("sabado", "almuerzo"): ("Pizza con las niñas (2 rebanadas y ensalada)", "Pizza (2 rebanadas y palitos de zanahoria)"),
        ("sabado", "cena"): ("Ensalada de pollo", "Sándwich de pollo"),
        ("domingo", "desayuno"): ("Huevos revueltos", "Huevos revueltos con bacon"),
        ("domingo", "almuerzo"): ("Cocina olla de arroz y frijoles para la semana", "Arroz y frijoles con aguacate (en un tazón)"),
        ("domingo", "cena"): ("Pollo asado con verduras", "Pollo asado con patatas"),
    }
    recipe_links = {
        ("lunes", "desayuno"): "huevos_revueltos", ("lunes", "almuerzo"): "pollo_arroz_zanahoria", ("lunes", "cena"): "pollo_brocoli",
        ("martes", "desayuno"): "yogur_platano", ("martes", "almuerzo"): "sandwich_pavo_queso", ("martes", "cena"): "carne_arroz_verduras",
        ("miercoles", "desayuno"): "avena_platano", ("miercoles", "almuerzo"): "macarrones_queso", ("miercoles", "cena"): "ensalada_atun_aguacate",
        ("jueves", "desayuno"): "batido_proteina", ("jueves", "almuerzo"): "sandwich_pavo_queso", ("jueves", "cena"): "huevos_tostadas",
        ("viernes", "desayuno"): "yogur_platano", ("viernes", "almuerzo"): "pollo_brocoli",
        ("viernes", "cena"): "pizza_familiar",
        ("sabado", "desayuno"): "huevos_revueltos", ("sabado", "almuerzo"): "pizza_familiar", ("sabado", "cena"): "ensalada_pollo",
        ("domingo", "desayuno"): "huevos_revueltos", ("domingo", "almuerzo"): "arroz_frijoles_aguacate", ("domingo", "cena"): "pollo_patatas",
    }
    result = {}
    for day_key, _ in DAYS:
        result[day_key] = {}
        for meal_key, _ in MEALS:
            papa, ninas = values[(day_key, meal_key)]
            result[day_key][meal_key] = {"papa": papa, "ninas": ninas, "recipe_id": recipe_links.get((day_key, meal_key))}
    return result


def default_shopping() -> dict:
    items = [
        ("proteina", "1 docena de huevos"),
        ("proteina", "3 latas de atún"),
        ("proteina", "1 pollo entero asado (del súper)"),
        ("proteina", "1 kg de carne picada"),
        ("proteina", "2 yogures griegos grandes"),
        ("carbohidratos", "1 bolsa de arroz precocido"),
        ("carbohidratos", "Avena"),
        ("carbohidratos", "Pan integral o de semillas"),
        ("carbohidratos", "Pasta"),
        ("verduras_frutas", "1 bolsa de espinacas"),
        ("verduras_frutas", "1 bolsa de verduras congeladas (brócoli/coliflor)"),
        ("verduras_frutas", "Plátanos"),
        ("verduras_frutas", "Manzanas"),
        ("verduras_frutas", "Zanahorias"),
        ("extras", "Aceite de oliva"),
        ("extras", "Nueces (para picar en el coche)"),
        ("extras", "Salsa de soya"),
        ("extras", "Queso rallado para ellas"),
    ]
    result = {category: [] for category, _ in SHOPPING_CATEGORIES}
    for index, (category, name) in enumerate(items, start=1):
        result[category].append({"id": f"item_{index}", "name": name, "checked": False, "source": "default"})
    return result


def default_data() -> dict:
    return {
        "schema_version": 2,
        "plan": {key: "" for key in PLAN_FIELDS},
        "menu": default_menu(),
        "days": {},
        "shopping": default_shopping(),
        "settings": {
            "theme": "system",
            "active_tab": "hoy",
            "adult_name": "Papá",
            "children": ["Niñas"],
        },
        "emergency_meals": [],
        "recipes": default_recipes(),
    }
