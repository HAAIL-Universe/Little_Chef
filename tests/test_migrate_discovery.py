from pathlib import Path

from app.db import migrate


def test_migration_discovery_orders_and_parses_versions(tmp_path: Path):
    mig_dir = tmp_path / "db" / "migrations"
    mig_dir.mkdir(parents=True)

    (mig_dir / "0002_dummy.sql").write_text("select 2;")
    (mig_dir / "0001_init.sql").write_text("select 1;")

    files = migrate.discover_migration_files(mig_dir)
    names = [p.name for p in files]
    versions = [migrate.parse_version(p) for p in files]

    assert names == ["0001_init.sql", "0002_dummy.sql"]
    assert versions == ["0001", "0002"]
