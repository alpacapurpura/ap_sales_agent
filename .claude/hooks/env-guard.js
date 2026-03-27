#!/usr/bin/env node

/**
 * PreToolUse hook: Blocks reading/writing sensitive files (.env, credentials, keys).
 */

const BLOCKED_PATTERNS = [
  /^\.env($|\.)/,
  /credentials/i,
  /\.pem$/,
  /\.key$/,
  /secret/i,
];

function main() {
  const input = process.argv[2];
  if (!input) process.exit(0);

  let data;
  try {
    data = JSON.parse(input);
  } catch {
    process.exit(0);
  }

  const tool = data.tool_name;
  if (!['Write', 'Edit', 'Read'].includes(tool)) process.exit(0);

  const filePath = data.tool_input?.file_path || data.tool_input?.path || '';
  const fileName = filePath.split('/').pop() || '';

  for (const pattern of BLOCKED_PATTERNS) {
    if (pattern.test(fileName)) {
      console.error(`BLOCKED: Cannot ${tool.toLowerCase()} "${fileName}" — sensitive file.`);
      console.error('If you need to reference env vars, ask the user to provide the values.');
      process.exit(2);
    }
  }

  process.exit(0);
}

main();
