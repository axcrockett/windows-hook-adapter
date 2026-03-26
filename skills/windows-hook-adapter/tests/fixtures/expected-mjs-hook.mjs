#!/usr/bin/env node
// Converted from bash hook by windows-hook-adapter.
import { readFileSync, existsSync } from 'fs';

const INPUT = JSON.parse(readFileSync('/dev/stdin', 'utf-8'));
const TOOL_NAME = INPUT.tool_name || '';
const FILE_PATH = (INPUT.tool_input || {}).file_path || '';

if (!TOOL_NAME) {
  console.error("No tool name found");
  process.exit(0);
}

const PROTECTED_DIR = process.env.PROTECTED_DIR || '/etc';

if (existsSync(FILE_PATH)) {
  console.error(`File exists: ${FILE_PATH}`);
}

if (['Write', 'Edit'].includes(TOOL_NAME)) {
  if (FILE_PATH.startsWith(PROTECTED_DIR)) {
    console.error(`BLOCKED: Cannot write to protected directory ${PROTECTED_DIR}`);
    process.exit(2);
  }
}

process.exit(0);
