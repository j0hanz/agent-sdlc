import { spawnSync } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';

const pluginRoot =
  process.env.CLAUDE_PLUGIN_ROOT ||
  path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const projectDir = process.env.CLAUDE_PROJECT_DIR || process.cwd();

export async function lintAgentsMd() {
  const script = path.join(pluginRoot, 'skills', 'agents-maintainer', 'scripts', 'run.py');
  const agentsMd = path.join(projectDir, 'AGENTS.md');

  const result = spawnSync('python', [script, 'lint-agents-md', agentsMd], {
    encoding: 'utf-8',
    env: { ...process.env, CLAUDE_PLUGIN_ROOT: pluginRoot },
    stdio: ['ignore', 'pipe', 'pipe'],
  });

  const output = ((result.stdout || '') + (result.stderr || '')).trim();
  if (output && result.status !== 0) {
    return {
      hookSpecificOutput: {
        hookEventName: 'InstructionsLoaded',
        additionalContext: `[agents-maintainer lint]\n${output}`,
      },
    };
  }

  return null;
}
