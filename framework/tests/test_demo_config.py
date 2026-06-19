from pathlib import Path
from utilities.config import effective_config

ROOT = Path(__file__).resolve().parent.parent.parent


def test_demo_effective_config():
    cfg = effective_config(
        ROOT / "experiments" / "0001-demo",
        ROOT / "experiments" / "_defaults.yaml",
    )
    assert cfg["entrypoint"] == "Rscript experiments/0001-demo/demo_effect.R"
    assert cfg["sql_file"] == "experiments/0001-demo/demo_cohort.sql"
    assert cfg["seed"] == 42
