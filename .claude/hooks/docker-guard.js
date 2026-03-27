#!/usr/bin/env node

/**
 * PreToolUse hook: Prevents running dev commands directly on the host.
 * Forces usage of Docker containers for pytest, ruff, alembic, npm, npx, python.
 */

const DOCKER_COMMANDS = ['pytest', 'ruff', 'alembic', 'npm ', 'npx ', 'python '];
const ALLOWED_PREFIXES = ['docker ', 'docker-compose ', 'which ', 'node .claude/'];

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

  // Allow if the command starts with docker/docker-compose
  for (const prefix of ALLOWED_PREFIXES) {
    if (command.startsWith(prefix)) process.exit(0);
  }

  // Block if command runs a dev tool directly on host
  for (const cmd of DOCKER_COMMANDS) {
    if (command.startsWith(cmd) || command.includes(`| ${cmd}`) || command.includes(`&& ${cmd}`)) {
      const container = cmd.trim() === 'npm' || cmd.trim() === 'npx'
        ? 'visionarias_client_dev'
        : 'visionarias_brain_dev';
      console.error(`BLOCKED: "${cmd.trim()}" must run inside Docker.`);
      console.error(`Use: docker exec -t ${container} ${command}`);
      process.exit(2);
    }
  }

  process.exit(0);
}

main();
