import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const runnerPath = pathToFileURL(path.resolve(__dirname, '../bin/multi-agent-runner.mjs')).href;

test('parses markdown plan correctly', async () => {
  const planContent = `# Plan
- [ ] Task 1: Touch \`src/auth.ts\` and \`tests/auth.test.ts\` (depends on: none)
- [ ] Task 2: Touch \`src/db.ts\` (depends on: Task 1)
`;
  const tmpPlan = path.resolve(__dirname, 'tmp-plan.md');
  fs.writeFileSync(tmpPlan, planContent, 'utf-8');

  try {
    const { initPlan } = await import(`${runnerPath}?t=${Date.now()}`);
    const state = initPlan(tmpPlan);

    assert.strictEqual(state.lanes.length, 2);
    assert.strictEqual(state.lanes[0].id, 'lane-1');
    assert.deepEqual(state.lanes[0].filesTouched, ['src/auth.ts', 'tests/auth.test.ts']);
    assert.deepEqual(state.lanes[0].dependsOn, []);

    assert.strictEqual(state.lanes[1].id, 'lane-2');
    assert.deepEqual(state.lanes[1].filesTouched, ['src/db.ts']);
    assert.deepEqual(state.lanes[1].dependsOn, ['lane-1']);
  } finally {
    if (fs.existsSync(tmpPlan)) fs.unlinkSync(tmpPlan);
  }
});
