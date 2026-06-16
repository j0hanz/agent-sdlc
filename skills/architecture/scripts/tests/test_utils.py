import os
from utils.walk import walk_dir
from utils.extractor import extract_imports
from utils.graph import find_cycles


def test_walk_dir(tmp_path):
    # Create dynamic fixtures
    d = tmp_path / "sub"
    d.mkdir()
    (d / "a.ts").write_text("import { b } from './b';")
    (tmp_path / "domain.ts").write_text("import express from 'express';")
    (tmp_path / "exclude.txt").write_text("should be ignored")

    files = walk_dir(str(tmp_path), exclude=["exclude-pattern"])
    basenames = [os.path.basename(f) for f in files]

    assert "a.ts" in basenames
    assert "domain.ts" in basenames
    assert "exclude.txt" not in basenames


def test_walk_dir_respects_exclude(tmp_path):
    (tmp_path / "a.ts").write_text("content")
    (tmp_path / "domain.ts").write_text("content")

    files = walk_dir(str(tmp_path), exclude=["domain.ts"])
    basenames = [os.path.basename(f) for f in files]

    assert "a.ts" in basenames
    assert "domain.ts" not in basenames


def test_extract_imports_named():
    content = "import { a } from './a';"
    imports = extract_imports(content, "js")
    assert imports == ["./a"]


def test_extract_imports_type():
    content = "import type { B } from '../b';"
    imports = extract_imports(content, "js")
    assert imports == ["../b"]


def test_extract_imports_default():
    content = "import defaultExport from 'package';"
    imports = extract_imports(content, "js")
    assert imports == ["package"]


def test_extract_imports_require():
    content = "const fs = require('fs');"
    imports = extract_imports(content, "js")
    assert imports == ["fs"]


def test_find_cycles():
    graph = {
        "a.ts": ["b.ts"],
        "b.ts": ["c.ts"],
        "c.ts": ["a.ts"],
        "d.ts": ["a.ts"],
    }
    cycles = find_cycles(graph)
    assert len(cycles) == 1
    assert sorted(cycles[0]) == sorted(["a.ts", "b.ts", "c.ts"])


def test_no_cycles():
    graph = {
        "a.ts": ["b.ts"],
        "b.ts": ["c.ts"],
        "c.ts": [],
    }
    cycles = find_cycles(graph)
    assert len(cycles) == 0
