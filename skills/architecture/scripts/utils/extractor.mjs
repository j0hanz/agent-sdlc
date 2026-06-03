import { extractPythonImports } from './extract-python.mjs';

/**
 * Extract import specifiers from source content.
 * @param {string} fileContent
 * @param {'js'|'py'} [lang] - auto-detected if omitted
 */
export function extractImports(fileContent, lang) {
  if (lang === 'py') return extractPythonImports(fileContent);

  const imports = [];
  // Match `import ... from '...'` or `import '...'`
  const importRegex = /import(?:[\s.*{},_a-zA-Z0-9]+from\s+)?['"](.*?)['"]/g;
  // Match `require('...')`
  const requireRegex = /require\(['"](.*?)['"]\)/g;

  let match;
  while ((match = importRegex.exec(fileContent)) !== null) {
    imports.push(match[1]);
  }
  while ((match = requireRegex.exec(fileContent)) !== null) {
    imports.push(match[1]);
  }
  return imports;
}

/** Detect language from file extension. Returns 'js' or 'py'. */
export function detectLang(filePath) {
  return filePath.endsWith('.py') ? 'py' : 'js';
}
