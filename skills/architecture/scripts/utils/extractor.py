import re
from typing import List, Dict, Optional


def extract_python_imports_with_positions(content: str) -> List[Dict]:
    results = []
    # import X and import X as Y
    import_regex = re.compile(r"^import\s+([\w.]+)", re.MULTILINE)
    # from X import ...
    from_regex = re.compile(r"^from\s+(\.{0,2}[\w.]*)\s+import", re.MULTILINE)

    for match in import_regex.finditer(content):
        results.append({"specifier": match.group(1), "index": match.start()})

    for match in from_regex.finditer(content):
        results.append({"specifier": match.group(1) or ".", "index": match.start()})

    return results


def extract_go_imports_with_positions(content: str) -> List[Dict]:
    results = []
    # Block form: import ( ... )
    block_regex = re.compile(r"import\s*\(([\s\S]*?)\)")
    for m in block_regex.finditer(content):
        inner = m.group(1)
        inner_start = m.start() + m.group(0).find(inner)
        str_regex = re.compile(r'(?:[\w.]+\s+)?"([^"]+)"')
        for s in str_regex.finditer(inner):
            results.append({"specifier": s.group(1), "index": inner_start + s.start()})

    # Single form: import "pkg"
    single_regex = re.compile(r'import\s+(?:[\w.]+\s+)?"([^"]+)"')
    for m in single_regex.finditer(content):
        # Ensure it's not part of a block (simplified check)
        # Actually the JS version had a comment about this.
        # If the block regex already matched it, we might double count if not careful.
        # But singleRegex in JS was carefully constructed.
        results.append({"specifier": m.group(1), "index": m.start()})

    return results


def extract_js_imports_with_positions(content: str) -> List[Dict]:
    results = []
    # import ... from '...' or import '...'
    import_regex = re.compile(
        r'import(?:[\s.*{},_a-zA-Z0-9]+from\s+)?[\'"](.*?)[\'"]', re.DOTALL
    )
    # require('...')
    require_regex = re.compile(r'require\([\'"](.*?)[\'"]\)')

    for match in import_regex.finditer(content):
        results.append({"specifier": match.group(1), "index": match.start()})

    for match in require_regex.finditer(content):
        results.append({"specifier": match.group(1), "index": match.start()})

    return results


def detect_lang(file_path: str) -> str:
    if file_path.endswith(".py"):
        return "py"
    if file_path.endswith(".go"):
        return "go"
    return "js"


def extract_imports_with_positions(
    content: str, lang: Optional[str] = None
) -> List[Dict]:
    if lang == "py":
        return extract_python_imports_with_positions(content)
    if lang == "go":
        return extract_go_imports_with_positions(content)
    return extract_js_imports_with_positions(content)


def extract_imports(content: str, lang: Optional[str] = None) -> List[str]:
    return [m["specifier"] for m in extract_imports_with_positions(content, lang)]


def top_level_package(imp: str) -> str:
    if imp.startswith("."):
        return imp
    return imp.split(".")[0]
