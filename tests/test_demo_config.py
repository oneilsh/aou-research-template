from pathlib import Path

from utilities.config import effective_config

ROOT = Path(__file__).resolve().parent.parent


def test_demo_effective_config():
    cfg = effective_config(
        ROOT / "docs" / "experiments" / "0001-demo.md",
        ROOT / "experiments" / "defaults",
    )
    assert cfg["entrypoint"] == "Rscript analysis/demo_effect.R"
    assert cfg["sql_file"] == "analysis/demo_cohort.sql"
    assert cfg["group"] == "demo"
