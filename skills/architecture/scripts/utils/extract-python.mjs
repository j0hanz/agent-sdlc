/**
 * Extract import targets from Python source.
 * Handles:
 *   import os
 *   import os.path
 *   from os import path
 *   from os.path import join, exists
 *   from .relative import something
 *   from ..parent import something
 *   from . import sibling
 */
export function extractPythonImports(fileContent) {
  const imports = [];

  // `import X` and `import X as Y` — capture the module name
  const importRegex = /^import\s+([\w.]+)/gm;
  // `from X import ...` — capture X (handles relative dots)
  const fromRegex = /^from\s+(\.{0,2}[\w.]*)\s+import/gm;

  let match;
  while ((match = importRegex.exec(fileContent)) !== null) {
    imports.push(match[1]);
  }
  while ((match = fromRegex.exec(fileContent)) !== null) {
    // Relative imports start with '.' — preserve the dot so callers can detect them
    imports.push(match[1] || '.');
  }

  return imports;
}

/**
 * Return the top-level package name from a Python import string.
 * e.g. "os.path" -> "os", "sqlalchemy.orm" -> "sqlalchemy"
 */
export function topLevelPackage(imp) {
  if (imp.startsWith('.')) return imp; // keep relative as-is
  return imp.split('.')[0];
}
