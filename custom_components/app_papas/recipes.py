from __future__ import annotations

from copy import deepcopy
from typing import Any


def recipe(
    rid: str,
    name: str,
    category: str,
    description: str,
    prep: int,
    cook: int,
    ingredients: list[dict[str, Any]],
    steps: list[str],
    aliases: tuple[str, ...] = (),
) -> dict[str, Any]:
    return {
        "id": rid,
        "name": name,
        "category": category,
        "description": description,
        "prep_minutes": prep,
        "cook_minutes": cook,
        "servings": 1,
        "ingredients": ingredients,
        "steps": steps,
        "aliases": list(aliases),
    }


RECIPES: tuple[dict[str, Any], ...] = (
    recipe("huevos_revueltos", "Huevos revueltos", "Desayuno", "Desayuno rápido y adaptable para adulto y niños.", 3, 5, [
        {"name": "Huevos", "qty": 2, "unit": "ud", "category": "proteina"},
        {"name": "Aceite de oliva", "qty": 5, "unit": "ml", "category": "extras"},
        {"name": "Pan integral", "qty": 1, "unit": "rebanada", "category": "carbohidratos", "optional": True},
    ], ["Bate los huevos con una pizca de sal.", "Calienta el aceite en una sartén a fuego medio.", "Añade los huevos y remueve hasta que estén cuajados pero jugosos.", "Sirve con pan si se desea."], ("huevo", "huevos revueltos")),
    recipe("pollo_ensalada", "Pollo asado con ensalada", "Almuerzo", "Plato base sencillo que permite adaptar la guarnición.", 10, 5, [
        {"name": "Pollo asado", "qty": 180, "unit": "g", "category": "proteina"},
        {"name": "Ensalada variada", "qty": 150, "unit": "g", "category": "verduras_frutas"},
        {"name": "Aceite de oliva", "qty": 10, "unit": "ml", "category": "extras"},
    ], ["Desmenuza o corta el pollo.", "Lava y corta la ensalada.", "Aliña con aceite de oliva y sirve."], ("pollo asado", "pollo y ensalada", "ensalada de pollo")),
    recipe("pollo_arroz_zanahoria", "Pollo con arroz y zanahoria", "Almuerzo", "Comida familiar de una sola base.", 10, 20, [
        {"name": "Pollo", "qty": 150, "unit": "g", "category": "proteina"},
        {"name": "Arroz", "qty": 70, "unit": "g", "category": "carbohidratos"},
        {"name": "Zanahoria", "qty": 80, "unit": "g", "category": "verduras_frutas"},
        {"name": "Aceite de oliva", "qty": 5, "unit": "ml", "category": "extras"},
    ], ["Cuece el arroz según el paquete.", "Cocina el pollo hasta que esté hecho.", "Saltea o cuece la zanahoria.", "Sirve los tres elementos por separado o en un bol."], ("pollo desmenuzado", "pollo con arroz", "arroz y zanahoria")),
    recipe("sopa_verduras", "Sopa de verduras", "Cena", "Sopa rápida con verduras y caldo.", 10, 20, [
        {"name": "Verduras variadas", "qty": 250, "unit": "g", "category": "verduras_frutas"},
        {"name": "Caldo de verduras", "qty": 300, "unit": "ml", "category": "extras"},
        {"name": "Pan integral", "qty": 1, "unit": "rebanada", "category": "carbohidratos", "optional": True},
    ], ["Trocea las verduras.", "Ponlas en una olla con el caldo.", "Cuece hasta que estén tiernas.", "Tritura o deja con trozos y sirve."], ("sopa de verduras", "sopita de verduras")),
    recipe("yogur_platano", "Yogur griego con plátano", "Desayuno", "Desayuno sin cocina y listo en dos minutos.", 2, 0, [
        {"name": "Yogur griego", "qty": 200, "unit": "g", "category": "proteina"},
        {"name": "Plátano", "qty": 1, "unit": "ud", "category": "verduras_frutas"},
        {"name": "Nueces", "qty": 15, "unit": "g", "category": "extras", "optional": True},
    ], ["Sirve el yogur en un bol.", "Añade el plátano en rodajas.", "Termina con nueces si se desea."], ("yogur griego", "yogurt griego", "yogur y plátano")),
    recipe("avena_platano", "Avena con leche y plátano", "Desayuno", "Avena sencilla para preparar en pocos minutos.", 2, 6, [
        {"name": "Avena", "qty": 50, "unit": "g", "category": "carbohidratos"},
        {"name": "Leche", "qty": 200, "unit": "ml", "category": "extras"},
        {"name": "Plátano", "qty": 1, "unit": "ud", "category": "verduras_frutas"},
    ], ["Pon la avena y la leche en un cazo.", "Cocina a fuego suave removiendo hasta espesar.", "Sirve con el plátano en rodajas."], ("avena con leche", "avena y plátano")),
    recipe("sandwich_atun", "Sándwich de atún", "Almuerzo", "Sándwich rápido de atún y pan.", 5, 0, [
        {"name": "Atún", "qty": 100, "unit": "g", "category": "proteina"},
        {"name": "Pan integral", "qty": 2, "unit": "rebanada", "category": "carbohidratos"},
        {"name": "Tomate", "qty": 60, "unit": "g", "category": "verduras_frutas", "optional": True},
    ], ["Escurre el atún.", "Monta el sándwich con pan y tomate.", "Corta y sirve."], ("sándwich de atún", "sandwich de atún", "atún")),
    recipe("sandwich_pavo_queso", "Sándwich de pavo y queso", "Almuerzo", "Sándwich familiar sencillo.", 5, 0, [
        {"name": "Pavo", "qty": 80, "unit": "g", "category": "proteina"},
        {"name": "Queso", "qty": 30, "unit": "g", "category": "extras"},
        {"name": "Pan integral", "qty": 2, "unit": "rebanada", "category": "carbohidratos"},
    ], ["Coloca el pavo y el queso entre el pan.", "Tuesta si se desea.", "Sirve."], ("pavo y queso", "sándwich de pavo")),
    recipe("carne_arroz_verduras", "Carne picada con arroz y verduras", "Almuerzo", "Salteado sencillo de carne, arroz y verduras.", 10, 20, [
        {"name": "Carne picada", "qty": 160, "unit": "g", "category": "proteina"},
        {"name": "Arroz", "qty": 70, "unit": "g", "category": "carbohidratos"},
        {"name": "Verduras variadas", "qty": 150, "unit": "g", "category": "verduras_frutas"},
    ], ["Cuece el arroz.", "Dora la carne hasta que esté hecha.", "Añade las verduras y cocina hasta que estén tiernas.", "Sirve con el arroz."], ("carne picada", "carne con arroz", "carne molida")),
    recipe("carne_pure_patata", "Carne picada con puré de patata", "Cena", "Versión familiar de carne con puré.", 10, 25, [
        {"name": "Carne picada", "qty": 160, "unit": "g", "category": "proteina"},
        {"name": "Patatas", "qty": 220, "unit": "g", "category": "carbohidratos"},
        {"name": "Leche", "qty": 30, "unit": "ml", "category": "extras"},
        {"name": "Aceite de oliva", "qty": 5, "unit": "ml", "category": "extras"},
    ], ["Cuece las patatas hasta que estén blandas.", "Cocina la carne hasta que esté hecha.", "Chafa las patatas con la leche y el aceite.", "Sirve la carne con el puré."], ("carne picada con puré", "puré de patata")),
    recipe("ensalada_atun_aguacate", "Ensalada de atún y aguacate", "Cena", "Cena fría de preparación rápida.", 8, 0, [
        {"name": "Atún", "qty": 100, "unit": "g", "category": "proteina"},
        {"name": "Aguacate", "qty": 100, "unit": "g", "category": "verduras_frutas"},
        {"name": "Tomate", "qty": 100, "unit": "g", "category": "verduras_frutas"},
        {"name": "Aceite de oliva", "qty": 5, "unit": "ml", "category": "extras"},
    ], ["Escurre el atún.", "Corta aguacate y tomate.", "Mezcla y aliña."], ("ensalada de atún", "atún y aguacate")),
    recipe("tortilla_jamon", "Tortilla francesa con jamón", "Cena", "Cena rápida de sartén.", 4, 6, [
        {"name": "Huevos", "qty": 2, "unit": "ud", "category": "proteina"},
        {"name": "Jamón", "qty": 50, "unit": "g", "category": "proteina"},
        {"name": "Aceite de oliva", "qty": 5, "unit": "ml", "category": "extras"},
    ], ["Bate los huevos.", "Añade el jamón.", "Cuaja la tortilla en una sartén con aceite."], ("tortilla francesa", "tortilla con jamón")),
    recipe("batido_proteina", "Batido de proteína con plátano", "Desayuno", "Desayuno rápido de vaso.", 3, 0, [
        {"name": "Leche", "qty": 250, "unit": "ml", "category": "extras"},
        {"name": "Plátano", "qty": 1, "unit": "ud", "category": "verduras_frutas"},
        {"name": "Proteína en polvo", "qty": 30, "unit": "g", "category": "proteina"},
    ], ["Añade todos los ingredientes al vaso de batidora.", "Tritura hasta obtener una mezcla homogénea.", "Sirve inmediatamente."], ("batido de proteína", "batido de proteina")),
    recipe("macarrones_queso", "Macarrones con queso", "Almuerzo", "Receta sencilla para toda la familia.", 5, 15, [
        {"name": "Pasta", "qty": 80, "unit": "g", "category": "carbohidratos"},
        {"name": "Queso", "qty": 40, "unit": "g", "category": "extras"},
        {"name": "Leche", "qty": 60, "unit": "ml", "category": "extras"},
    ], ["Cuece la pasta.", "Calienta la leche y añade el queso.", "Mezcla la salsa con la pasta y sirve."], ("macarrones con queso", "pasta con queso")),
    recipe("huevos_tostadas", "Huevos revueltos con tostadas", "Desayuno", "Versión más completa de los huevos del desayuno.", 4, 6, [
        {"name": "Huevos", "qty": 2, "unit": "ud", "category": "proteina"},
        {"name": "Pan integral", "qty": 2, "unit": "rebanada", "category": "carbohidratos"},
        {"name": "Aceite de oliva", "qty": 5, "unit": "ml", "category": "extras"},
    ], ["Tuesta el pan.", "Bate y cuaja los huevos.", "Sirve juntos."], ("huevos con tostadas", "revuelto de huevos con tostadas")),
    recipe("pollo_brocoli", "Pollo con brócoli", "Cena", "Cena sencilla con proteína y verdura.", 8, 12, [
        {"name": "Pollo", "qty": 180, "unit": "g", "category": "proteina"},
        {"name": "Brócoli", "qty": 180, "unit": "g", "category": "verduras_frutas"},
        {"name": "Aceite de oliva", "qty": 5, "unit": "ml", "category": "extras"},
    ], ["Corta el pollo.", "Cocina el pollo con aceite hasta dorarlo.", "Cuece o saltea el brócoli.", "Sirve juntos."], ("pollo y brócoli", "pollo y brocoli", "brócoli")),
    recipe("pizza_familiar", "Pizza familiar", "Comida", "Pizza para compartir con guarnición sencilla.", 5, 12, [
        {"name": "Pizza", "qty": 0.5, "unit": "ud", "category": "carbohidratos"},
        {"name": "Zanahorias", "qty": 80, "unit": "g", "category": "verduras_frutas", "optional": True},
    ], ["Prepara o calienta la pizza según el envase.", "Corta la cantidad deseada.", "Sirve con zanahoria u otra verdura si se desea."], ("pizza",)),
    recipe("ensalada_pollo", "Ensalada de pollo", "Cena", "Ensalada completa y rápida.", 10, 0, [
        {"name": "Pollo", "qty": 160, "unit": "g", "category": "proteina"},
        {"name": "Ensalada variada", "qty": 180, "unit": "g", "category": "verduras_frutas"},
        {"name": "Aceite de oliva", "qty": 10, "unit": "ml", "category": "extras"},
    ], ["Corta el pollo.", "Prepara la ensalada.", "Mezcla y aliña."], ("ensalada de pollo",)),
    recipe("sandwich_pollo", "Sándwich de pollo", "Cena", "Sándwich de aprovechamiento.", 5, 0, [
        {"name": "Pollo", "qty": 100, "unit": "g", "category": "proteina"},
        {"name": "Pan integral", "qty": 2, "unit": "rebanada", "category": "carbohidratos"},
        {"name": "Tomate", "qty": 50, "unit": "g", "category": "verduras_frutas", "optional": True},
    ], ["Desmenuza el pollo.", "Monta el sándwich con pan y tomate.", "Sirve."], ("sándwich de pollo", "sandwich de pollo")),
    recipe("arroz_frijoles_aguacate", "Arroz y frijoles con aguacate", "Almuerzo", "Base económica para preparar con antelación.", 10, 25, [
        {"name": "Arroz", "qty": 70, "unit": "g", "category": "carbohidratos"},
        {"name": "Frijoles", "qty": 120, "unit": "g", "category": "carbohidratos"},
        {"name": "Aguacate", "qty": 80, "unit": "g", "category": "verduras_frutas"},
    ], ["Cuece el arroz.", "Calienta los frijoles.", "Corta el aguacate.", "Sirve en un bol."], ("arroz y frijoles", "arroz con frijoles")),
    recipe("pollo_patatas", "Pollo asado con patatas", "Cena", "Cena familiar de horno.", 10, 35, [
        {"name": "Pollo", "qty": 180, "unit": "g", "category": "proteina"},
        {"name": "Patatas", "qty": 180, "unit": "g", "category": "carbohidratos"},
        {"name": "Verduras variadas", "qty": 120, "unit": "g", "category": "verduras_frutas", "optional": True},
        {"name": "Aceite de oliva", "qty": 10, "unit": "ml", "category": "extras"},
    ], ["Precalienta el horno a 200 °C.", "Corta las patatas y mézclalas con aceite.", "Añade el pollo y hornea hasta que esté bien cocinado.", "Añade verduras si se desea y sirve."], ("pollo asado con patatas",)),
    recipe("ternera_arroz_brocoli", "Ternera con arroz y brócoli", "Almuerzo", "Receta específica para que una entrada como “ternera con arroz” tenga cantidades reales.", 10, 15, [
        {"name": "Ternera", "qty": 180, "unit": "g", "category": "proteina"},
        {"name": "Arroz", "qty": 70, "unit": "g", "category": "carbohidratos"},
        {"name": "Brócoli", "qty": 180, "unit": "g", "category": "verduras_frutas"},
        {"name": "Aceite de oliva", "qty": 5, "unit": "ml", "category": "extras"},
    ], ["Cuece el arroz.", "Corta la ternera en tiras.", "Saltea la ternera con el aceite hasta el punto deseado.", "Cuece o saltea el brócoli.", "Sirve todo junto."], ("ternera con arroz", "ternera arroz", "ternera", "vacuno")),
)


def default_recipes() -> list[dict[str, Any]]:
    return deepcopy(list(RECIPES))


def recipe_map(recipes: list[dict[str, Any]] | None = None) -> dict[str, dict[str, Any]]:
    return {str(r["id"]): r for r in (recipes if recipes is not None else default_recipes())}
