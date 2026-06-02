import test from 'node:test';
import assert from 'node:assert';
import path from 'node:path';
import { walkDir } from './walk.mjs';

test('walkDir recursively finds JS/TS files in fixtures directory', () => {
  const fixtureDir = path.join(process.cwd(), 'skills/architecture/scripts/fixtures');
  const files = walkDir(fixtureDir, ['exclude-pattern']);
  const basenames = files.map((f) => path.basename(f));

  assert.ok(basenames.includes('a.ts'));
  assert.ok(basenames.includes('domain.ts'));
});

test('walkDir respects exclude patterns', () => {
  const fixtureDir = path.join(process.cwd(), 'skills/architecture/scripts/fixtures');
  const files = walkDir(fixtureDir, ['domain.ts']);
  const basenames = files.map((f) => path.basename(f));

  assert.ok(basenames.includes('a.ts'));
  assert.ok(!basenames.includes('domain.ts'));
});
