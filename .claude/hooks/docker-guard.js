#!/usr/bin/env node

/**
 * PreToolUse hook: Prevents running runtime commands directly on the host.
 * Lint/test tools (ruff, pytest, npx tsc, npx vitest, npx eslint) run NATIVELY.
 * Only runtime commands (alembic, python app, npm start) require Docker.
 */

const DOCKER_COMMANDS = ['alembic'];
const ALLOWED_PREFIXES = ['docker ', 'docker-compose ', 'which ', 'node .claude/', 'cd backend', 'cd frontend', 'cd /home/chris'];

function main() {
  const input = process.argv[2];
  if (!input) process.exit(0);

  let data;
  try {
    data = JSON.parse(input);
  } catch {
    process.exit(0);
  }

  if (data.tool_name !== 'Bash') process.exit(0);

  const command = (data.tool_input?.command || '').trim();
  if (!command) process.exit(0);

  // Allow if the command starts with known-safe prefixes
  for (const prefix of ALLOWED_PREFIXES) {
    if (command.startsWith(prefix)) process.exit(0);
  }

  // Allow native dev tools (ruff, pytest, npx, npm run test, .venv/bin/*)
  if (command.includes('.venv/bin/')) process.exit(0);
  if (command.startsWith('ruff ')) process.exit(0);
  if (command.startsWith('pytest ')) process.exit(0);
  if (command.startsWith('npx ')) process.exit(0);
  if (command.startsWith('npm ')) process.exit(0);
  if (command.startsWith('make ')) process.exit(0);

  // Block if command runs a runtime tool directly on host (should use Docker)
  for (const cmd of DOCKER_COMMANDS) {
    if (command.startsWith(cmd) || command.includes(`| ${cmd}`) || command.includes(`&& ${cmd}`)) {
      console.error(`BLOCKED: "${cmd.trim()}" must run inside Docker.`);
      console.error(`Use: docker exec -t visionarias_brain_dev bash -c "${command}"`);
      process.exit(2);
    }
  }

  process.exit(0);
}

main();
