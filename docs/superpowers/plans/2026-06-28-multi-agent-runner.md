# Multi-Agent Runner Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a stateful CLI helper harness `bin/multi-agent-runner.mjs` to orchestrate parallel multi-agent executions and check gates.

**Architecture:** A Node.js CLI script using built-in modules (`fs`, `path`, `child_process`). It reads/writes state in `.claude/multi_agent_state.json` and evaluates task transitions sequentially or in parallel based on file-disjoint constraints.

**Tech Stack:** Node.js (ESM), native `node --test` runner.

## Global Constraints

- Must run on Node.js ≥ 22.
- Use ESM import/export syntax only.
- Zero external dependencies; use built-in modules only.
- Commit frequently with exact attribution: `Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>`.

---

### Task 1: Initialization & Plan Parser

**Files:**
- Create: `bin/multi-agent-runner.mjs`
- Test: `tests/multi-agent-runner-parser.test.mjs`

**Interfaces:**
- Produces: `initPlan(filePath)` and `saveState(state)` functions inside `bin/multi-agent-runner.mjs`.

- [ ] **Step 1: Write failing parser tests**

Create the test file `tests/multi-agent-runner-parser.test.mjs`:
```javascript
import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const runnerPath = path.resolve(__dirname, '../bin/multi-agent-runner.mjs');

test('parses markdown plan correctly', async () => {
  const planContent = `# Plan
- [ ] Task 1: Touch \`src/auth.ts\` and \`tests/auth.test.ts\` (depends on: none)
- [ ] Task 2: Touch \`src/db.ts\` (depends on: Task 1)
`;
  const tmpPlan = path.resolve(__dirname, 'tmp-plan.md');
  fs.writeFileSync(tmpPlan, planContent, 'utf-8');

  try {
    const { initPlan } = await import(runnerPath + '?t=' + Date.now());
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `node --test tests/multi-agent-runner-parser.test.mjs`
Expected output: FAIL (Module not found or functions not exported)

- [ ] **Step 3: Implement minimal parser code**

Create `bin/multi-agent-runner.mjs`:
```javascript
#!/usr/bin/env node
import fs from 'fs';
import path from 'path';

export function initPlan(filePath) {
  const content = fs.readFileSync(filePath, 'utf-8');
  const lanes = [];
  const lines = content.split('\n');
  let idCounter = 1;

  for (const line of lines) {
    if (line.trim().startsWith('- [ ]')) {
      const titleMatch = line.match(/- \[ \]\s*([^:]+):?/);
      const title = titleMatch ? titleMatch[1].trim() : `Task ${idCounter}`;
      
      // Extract code blocks / files
      const filesTouched = [];
      const codeMatches = line.matchAll(/`([^`]+)`/g);
      for (const m of codeMatches) {
        filesTouched.push(m[1]);
      }

      // Extract dependencies
      const dependsOn = [];
      const depMatch = line.match(/\(depends on:\s*([^)]+)\)/i);
      if (depMatch) {
        const deps = depMatch[1].split(',').map(d => d.trim()).filter(Boolean);
        for (const dep of deps) {
          if (dep.toLowerCase() !== 'none') {
            // Find existing task by title index or ID
            const matchIndex = dep.match(/\d+/);
            if (matchIndex) {
              dependsOn.push(`lane-${matchIndex[0]}`);
            }
          }
        }
      }

      lanes.push({
        id: `lane-${idCounter++}`,
        title,
        filesTouched,
        dependsOn,
        status: 'PENDING',
        role: 'Writer',
        verdict: null,
        commit: null,
        reviews: {
          spec: { verdict: null, runs: 0 },
          quality: { verdict: null, runs: 0 }
        }
      });
    }
  }

  return {
    planPath: filePath,
    status: 'IN_PROGRESS',
    lanes,
    history: [{ timestamp: new Date().toISOString(), event: 'INIT', message: `Initialized with ${lanes.length} lanes` }]
  };
}

export function saveState(state) {
  const stateDir = path.resolve('.claude');
  if (!fs.existsSync(stateDir)) {
    fs.mkdirSync(stateDir, { recursive: true });
  }
  const statePath = path.join(stateDir, 'multi_agent_state.json');
  fs.writeFileSync(statePath, JSON.stringify(state, null, 2), 'utf-8');
}

// CLI entrypoint handling
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const [,, command, arg] = process.argv;
  if (command === 'init' && arg) {
    const state = initPlan(arg);
    saveState(state);
    console.log(`Initialized multi-agent state in .claude/multi_agent_state.json`);
  }
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `node --test tests/multi-agent-runner-parser.test.mjs`
Expected output: PASS

- [ ] **Step 5: Commit changes**

```bash
git add bin/multi-agent-runner.mjs tests/multi-agent-runner-parser.test.mjs
git commit -m "feat: add multi-agent plan parser and initialization" -m "Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```

---

### Task 2: State Machine Transition Engine & step Command

**Files:**
- Modify: `bin/multi-agent-runner.mjs`
- Test: `tests/multi-agent-runner-transitions.test.mjs`

**Interfaces:**
- Produces: `evaluateStep(state)` and `updateState(state, update)` functions.

- [ ] **Step 1: Write transition tests**

Create the test file `tests/multi-agent-runner-transitions.test.mjs`:
```javascript
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { evaluateStep, updateState } from '../bin/multi-agent-runner.mjs';

test('finds ready pending tasks with met dependencies', () => {
  const state = {
    lanes: [
      { id: 'lane-1', status: 'PENDING', dependsOn: [], filesTouched: ['f1.js'] },
      { id: 'lane-2', status: 'PENDING', dependsOn: ['lane-1'], filesTouched: ['f2.js'] }
    ]
  };

  const nextActions = evaluateStep(state);
  assert.strictEqual(nextActions.length, 1);
  assert.strictEqual(nextActions[0].laneId, 'lane-1');
  assert.strictEqual(nextActions[0].action, 'DISPATCH_IMPLEMENTER');
});

test('applies updates and advances state machine', () => {
  let state = {
    lanes: [
      {
        id: 'lane-1',
        status: 'PENDING',
        dependsOn: [],
        filesTouched: ['f1.js'],
        reviews: { spec: { verdict: null, runs: 0 }, quality: { verdict: null, runs: 0 } }
      }
    ]
  };

  // 1. Move to RUNNING
  const actions = evaluateStep(state);
  assert.strictEqual(actions[0].action, 'DISPATCH_IMPLEMENTER');
  state.lanes[0].status = 'RUNNING';

  // 2. Complete implementation callback
  state = updateState(state, {
    laneId: 'lane-1',
    phase: 'implementation',
    verdict: 'DONE',
    commit: 'c1',
    files: ['f1.js']
  });

  assert.strictEqual(state.lanes[0].status, 'SPEC_REVIEW');
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `node --test tests/multi-agent-runner-transitions.test.mjs`
Expected output: FAIL

- [ ] **Step 3: Implement minimal state machine transition code**

Modify `bin/multi-agent-runner.mjs` to export and implement `evaluateStep` and `updateState`:
```javascript
export function evaluateStep(state) {
  const actions = [];
  const runningLanes = state.lanes.filter(l => ['RUNNING', 'SPEC_REVIEW', 'QUALITY_REVIEW', 'MERGE_WAIT'].includes(l.status));
  
  if (runningLanes.length >= 3) {
    return actions; // at concurrency limit
  }

  for (const lane of state.lanes) {
    if (lane.status === 'PENDING') {
      const depsCompleted = lane.dependsOn.every(depId => {
        const depLane = state.lanes.find(l => l.id === depId);
        return depLane && depLane.status === 'COMPLETED';
      });

      // Check for file touch conflicts with currently running lanes
      const hasConflict = runningLanes.some(rl => 
        rl.filesTouched.some(f => lane.filesTouched.includes(f))
      );

      if (depsCompleted && !hasConflict && (runningLanes.length + actions.length < 3)) {
        actions.push({
          laneId: lane.id,
          action: 'DISPATCH_IMPLEMENTER',
          prompt: `SCOPE:\n  Files IN scope: ${lane.filesTouched.join(', ')}\nOBJECTIVE:\n  ${lane.title}\nCONTEXT:\n  Last commit: HEAD\nOUTPUT:\n  VERDICT: DONE | BLOCKED | NEEDS_CONTEXT`
        });
      }
    } else if (lane.status === 'SPEC_REVIEW' && lane.reviews.spec.verdict === null) {
      actions.push({
        laneId: lane.id,
        action: 'DISPATCH_SPEC_REVIEWER',
        prompt: `SCOPE:\n  Files changed: ${lane.filesTouched.join(', ')}\nOBJECTIVE:\n  Verify ${lane.title} matches spec.`
      });
    } else if (lane.status === 'QUALITY_REVIEW' && lane.reviews.quality.verdict === null) {
      actions.push({
        laneId: lane.id,
        action: 'DISPATCH_QUALITY_REVIEWER',
        prompt: `SCOPE:\n  Files changed: ${lane.filesTouched.join(', ')}\nOBJECTIVE:\n  Review code quality.`
      });
    }
  }

  return actions;
}

export function updateState(state, update) {
  const lane = state.lanes.find(l => l.id === update.laneId);
  if (!lane) return state;

  if (update.phase === 'implementation') {
    lane.verdict = update.verdict;
    lane.commit = update.commit;
    if (update.files) lane.filesTouched = update.files;
    
    if (update.verdict === 'DONE' || update.verdict === 'DONE_WITH_CONCERNS') {
      lane.status = 'SPEC_REVIEW';
    } else {
      lane.status = 'BLOCKED';
    }
  } else if (update.phase === 'spec-review') {
    lane.reviews.spec.verdict = update.verdict;
    lane.reviews.spec.runs++;
    
    if (update.verdict === 'SPEC_PASS') {
      lane.status = 'QUALITY_REVIEW';
    } else {
      if (lane.reviews.spec.runs < 2) {
        lane.status = 'RUNNING';
        lane.reviews.spec.verdict = null; // reset for next run
      } else {
        lane.status = 'BLOCKED';
      }
    }
  } else if (update.phase === 'quality-review') {
    lane.reviews.quality.verdict = update.verdict;
    lane.reviews.quality.runs++;

    if (update.verdict === 'QUALITY_PASS' || update.verdict === 'MINOR') {
      lane.status = 'COMPLETED'; // Assume merge succeeds; conflicts handled in Task 3
    } else {
      if (lane.reviews.quality.runs < 2) {
        lane.status = 'RUNNING';
        lane.reviews.quality.verdict = null; // reset for next run
      } else {
        lane.status = 'BLOCKED';
      }
    }
  }

  state.history.push({
    timestamp: new Date().toISOString(),
    event: 'UPDATE',
    message: `Updated lane ${update.laneId} in phase ${update.phase} with verdict ${update.verdict}`
  });

  return state;
}

// CLI execution handling
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const [,, command, arg] = process.argv;
  if (command === 'init' && arg) {
    const state = initPlan(arg);
    saveState(state);
    console.log(`Initialized multi-agent state in .claude/multi_agent_state.json`);
  } else if (command === 'step') {
    const statePath = path.resolve('.claude/multi_agent_state.json');
    if (!fs.existsSync(statePath)) {
      console.error('Error: State file not found. Run init first.');
      process.exit(1);
    }
    let state = JSON.parse(fs.readFileSync(statePath, 'utf-8'));
    
    if (process.argv.includes('--update')) {
      const payloadIndex = process.argv.indexOf('--update') + 1;
      const payload = JSON.parse(process.argv[payloadIndex]);
      state = updateState(state, payload);
      saveState(state);
    }

    const actions = evaluateStep(state);
    console.log(JSON.stringify(actions, null, 2));
  }
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `node --test tests/multi-agent-runner-transitions.test.mjs`
Expected output: PASS

- [ ] **Step 5: Commit changes**

```bash
git add bin/multi-agent-runner.mjs tests/multi-agent-runner-transitions.test.mjs
git commit -m "feat: implement state machine transitions and CLI step command" -m "Co-Authored-By: Claude Haiku 4.5 <noreply@anthreply.com>"
```

---

### Task 3: Status & Report Format

**Files:**
- Modify: `bin/multi-agent-runner.mjs`
- Test: `tests/multi-agent-runner-report.test.mjs`

**Interfaces:**
- Produces: `renderStatusTable(state)` function.

- [ ] **Step 1: Write status report tests**

Create the test file `tests/multi-agent-runner-report.test.mjs`:
```javascript
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { renderStatusTable } from '../bin/multi-agent-runner.mjs';

test('renders state table as clean Markdown', () => {
  const state = {
    lanes: [
      {
        id: 'lane-1',
        title: 'Auth Check',
        status: 'COMPLETED',
        verdict: 'DONE',
        reviews: { spec: { verdict: 'SPEC_PASS' }, quality: { verdict: 'QUALITY_PASS' } }
      }
    ]
  };

  const output = renderStatusTable(state);
  assert.ok(output.includes('| Lane | Title | Status | Spec | Quality |'));
  assert.ok(output.includes('| lane-1 | Auth Check | COMPLETED | SPEC_PASS | QUALITY_PASS |'));
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `node --test tests/multi-agent-runner-report.test.mjs`
Expected output: FAIL

- [ ] **Step 3: Implement status printing logic**

Modify `bin/multi-agent-runner.mjs` to export and implement `renderStatusTable`:
```javascript
export function renderStatusTable(state) {
  let table = '| Lane | Title | Status | Spec | Quality |\n';
  table += '| :--- | :--- | :--- | :--- | :--- |\n';
  
  for (const lane of state.lanes) {
    const spec = lane.reviews.spec.verdict || '-';
    const quality = lane.reviews.quality.verdict || '-';
    table += `| ${lane.id} | ${lane.title} | ${lane.status} | ${spec} | ${quality} |\n`;
  }
  return table;
}

// Add inside CLI block
if (command === 'status') {
  const statePath = path.resolve('.claude/multi_agent_state.json');
  if (!fs.existsSync(statePath)) {
    console.error('Error: State file not found.');
    process.exit(1);
  }
  const state = JSON.parse(fs.readFileSync(statePath, 'utf-8'));
  console.log(renderStatusTable(state));
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `node --test tests/multi-agent-runner-report.test.mjs`
Expected output: PASS

- [ ] **Step 5: Commit changes**

```bash
git add bin/multi-agent-runner.mjs tests/multi-agent-runner-report.test.mjs
git commit -m "feat: implement status command and markdown reporting" -m "Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```
