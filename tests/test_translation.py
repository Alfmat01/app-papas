from custom_components.app_papas.translation import quick_translate, translate_label, CATEGORY_ES, AREA_ES


def test_quick_food_translation():
    assert quick_translate("chicken with rice and broccoli") == "pollo with arroz and brócoli"


def test_labels():
    assert translate_label("Chicken", CATEGORY_ES) == "Pollo"
    assert translate_label("Spain", AREA_ES) == "España"
