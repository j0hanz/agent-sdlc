import fs from 'node:fs';
import path from 'node:path';
import { extractImports, detectLang } from './utils/extractor.mjs';
import { walkDir } from './utils/walk.mjs';

const defaultExclude = [
  'node_modules',
  '.test.',
  '.spec.',
  '.git',
  '.svn',
  '.hg',
  '.pytest_cache',
  '.tox',
  '__pycache__',
  '.venv',
  'venv',
  '.env',
  'dist',
  'build',
  'coverage',
  '.coverage',
  '.next',
  '.nuxt',
  '.cache',
  '.parcel',
  '.npm',
  '.yarn',
  'target',
  '.gradle',
  '.m2',
  '.pytest',
  '.mypy_cache',
  '.ruff_cache',
  '.vscode',
  '.idea',
  '.DS_Store',
];

export function runBleedDetection(targetDir, infraPackages) {
  const files = walkDir(targetDir, defaultExclude);
  const violations = [];

  for (const file of files) {
    const content = fs.readFileSync(file, 'utf8');
    const lang = detectLang(file);
    const lines = content.split('\n');

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      const imports = extractImports(line, lang);

      for (const imp of imports) {
        if (infraPackages.includes(imp) || infraPackages.some((pkg) => imp.startsWith(`${pkg}/`))) {
          violations.push({
            file,
            violation: imp,
            line: i + 1,
            code: line.trim(),
          });
        }
      }
    }
  }
  return violations;
}

// CLI entry point
if (
  process.argv[1] &&
  (process.argv[1] === new URL(import.meta.url).pathname ||
    process.argv[1].endsWith('detect-bleed.mjs'))
) {
  const dir = process.argv[2] || 'src/domain';
  const infraArg = process.argv[3] || 'express,typeorm,prisma,fs,path,react,mongoose';
  const infraPackages = infraArg.split(',');

  console.log(`Checking ${dir} for infrastructure bleeds (${infraPackages.join(', ')})...`);

  try {
    const violations = runBleedDetection(path.resolve(process.cwd(), dir), infraPackages);

    console.log('\n--- Infrastructure Leaks (Seam Test Failures) ---');
    if (violations.length === 0) {
      console.log('None found. Domain looks pure.');
    } else {
      console.table(
        violations.map((v) => ({
          File: path.relative(process.cwd(), v.file),
          Leak: v.violation,
          Line: v.line,
        })),
      );
    }
  } catch (e) {
    if (e.code === 'ENOENT') {
      console.error(`Directory not found: ${dir}`);
    } else {
      console.error(e);
    }
  }
}
