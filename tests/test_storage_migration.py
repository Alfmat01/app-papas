from pathlib import Path


def test_storage_uses_stable_store_version_and_schema_migration():
    source = Path("custom_components/app_papas/storage.py").read_text(encoding="utf-8")
    const = Path("custom_components/app_papas/const.py").read_text(encoding="utf-8")
    assert "class AppPapasStorage(Store[dict[str, Any]])" in source
    assert "def _migrate_schema" in source
    assert 'data.setdefault("emergency_meals", [])' in source
    assert 'settings.setdefault("adult_name", "Papá")' in source
    assert "STORAGE_VERSION = 1" in const
