#!/usr/bin/env bash
# Sample PreToolUse hook — blocks dangerous file writes
set -euo pipefail

INPUT=$(cat /dev/stdin)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name')
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

if [ -z "$TOOL_NAME" ]; then
  echo "No tool name found" >&2
  exit 0
fi

PROTECTED_DIR="${PROTECTED_DIR:-/etc}"

if [ -f "$FILE_PATH" ]; then
  echo "File exists: $FILE_PATH" >&2
fi

case "$TOOL_NAME" in
  Write|Edit)
    if echo "$FILE_PATH" | grep -q "^${PROTECTED_DIR}"; then
      echo "BLOCKED: Cannot write to protected directory $PROTECTED_DIR" >&2
      exit 2
    fi
    ;;
esac

exit 0
