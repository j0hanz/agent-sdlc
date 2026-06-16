import os
from check_locality import run_locality_check
from detect_bleed import run_bleed_detection


def test_check_locality_cycles(tmp_path):
    # Setup circular dependency: a -> b -> c -> a
    (tmp_path / "a.ts").write_text("import { b } from './b';")
    (tmp_path / "b.ts").write_text("import { c } from './c';")
    (tmp_path / "c.ts").write_text("import { a } from './a';")

    cycles, fan_out = run_locality_check(str(tmp_path))

    assert len(cycles) == 1
    cycle_files = [os.path.basename(f) for f in cycles[0]]
    assert "a.ts" in cycle_files
    assert "b.ts" in cycle_files
    assert "c.ts" in cycle_files


def test_detect_bleed(tmp_path):
    domain_ts = tmp_path / "domain.ts"
    domain_ts.write_text(
        "import express from 'express';\nexport const handler = () => {};"
    )

    result = run_bleed_detection(str(tmp_path), ["express"])

    assert len(result) == 1
    assert os.path.basename(result[0]["file"]) == "domain.ts"
    assert result[0]["violation"] == "express"


def test_check_locality_python(tmp_path):
    # Setup circular dependency in Python: a -> b -> a
    (tmp_path / "a.py").write_text("from .b import something")
    (tmp_path / "b.py").write_text("from .a import something")

    cycles, fan_out = run_locality_check(str(tmp_path))

    assert len(cycles) == 1
    cycle_files = [os.path.basename(f) for f in cycles[0]]
    assert "a.py" in cycle_files
    assert "b.py" in cycle_files
