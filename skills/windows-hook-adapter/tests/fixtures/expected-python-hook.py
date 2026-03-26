#!/usr/bin/env python3
"""Converted from bash hook by windows-hook-adapter."""
import io
import json
import os
import re
import sys

sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")

INPUT = json.load(sys.stdin)
TOOL_NAME = INPUT.get("tool_name", "")
FILE_PATH = INPUT.get("tool_input", {}).get("file_path", "")

if not TOOL_NAME:
    print("No tool name found", file=sys.stderr)
    sys.exit(0)

PROTECTED_DIR = os.environ.get("PROTECTED_DIR", "/etc")

if os.path.isfile(FILE_PATH):
    print(f"File exists: {FILE_PATH}", file=sys.stderr)

if TOOL_NAME in ("Write", "Edit"):
    if re.search(f"^{re.escape(PROTECTED_DIR)}", FILE_PATH):
        print(
            f"BLOCKED: Cannot write to protected directory {PROTECTED_DIR}",
            file=sys.stderr,
        )
        sys.exit(2)

sys.exit(0)
