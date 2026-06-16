// Stop handler — scans the session's uncommitted diff for leftover debug
// artifacts (console.log, debugger, breakpoints, test .only) and injects a
// warning so the agent cleans them up before completing.

import { sh, debug as dbg } from '../io.mjs';

const PROBES = [
  { re: /\bconsole\.(log|debug|trace)\s*\(/, label: 'console.log' },
  { re: /\bdebugger\s*;?/, label: 'debugger statement' },
  { re: /\b(?:describe|it|test)\.only\s*\(/, label: 'test .only (focused test)' },
  { re: /\b(?:fdescribe|fit)\s*\(/, label: 'focused test (fdescribe/fit)' },
  { re: /\b(?:pdb\.set_trace|breakpoint)\s*\(/, label: 'python breakpoint' },
  { re: /\/\/\s*@ts-nocheck/, label: 'ts-nocheck suppression' },
];

/** Stop: scan added lines in the working diff for debug artifacts. */
export function scan(input = {}) {
  if (input.stop_hook_active) return null;

  const diff = sh('git', ['diff', '--unified=0', '--no-color'], { timeout: 8000 });
  if (!diff) return null;

  let currentFile = '';
  const findings = [];
  for (const line of diff.split('\n')) {
    if (line.startsWith('+++ b/')) {
      currentFile = line.slice(6);
      continue;
    }
    if (!line.startsWith('+') || line.startsWith('+++')) continue; // added lines only
    const added = line.slice(1);
    for (const probe of PROBES) {
      if (probe.re.test(added)) {
        findings.push({ file: currentFile, kind: probe.label, line: added.trim().slice(0, 120) });
        break;
      }
    }
  }

  if (!findings.length) return null;

  dbg(`debug scan: ${findings.length} artifact(s) in working diff`);

  const list = findings.map((f) => `  - ${f.file}: ${f.kind} ("${f.line}")`).join('\n');
  return `Warning: ${findings.length} debug artifact(s) in uncommitted changes:\n${list}\nClean these up before completing the task.`;
}
