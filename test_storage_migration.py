from pathlib import Path


def test_storage_has_v1_to_v2_migration():
    source = Path("custom_components/app_papas/storage.py").read_text(encoding="utf-8")
    assert "class AppPapasStorage(Store[dict[str, Any]])" in source
    assert "old_major_version < 2" in source
    assert 'data.setdefault("emergency_meals", [])' in source
    assert 'settings.setdefault("adult_name", "Papá")' in source
