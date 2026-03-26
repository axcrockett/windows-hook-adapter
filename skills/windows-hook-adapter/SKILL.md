---
name: windows-hook-adapter
description: >-
  Convert bash-based AI coding agent hooks to Windows-compatible formats.
  Supports three conversion targets: Python (.py), Node.js (.mjs), and
  PowerShell (.ps1). Handles jq-to-native JSON parsing, exit codes, stderr
  output, environment variables, file checks, and conditional logic.
  Use when bash hooks fail on Windows due to CRLF, encoding, or missing
  Unix utilities. Works with Claude Code, Cursor, Codex, Amp, and any
  agent that uses shell-based hooks.
license: Apache-2.0
compatibility: >-
  Python 3.8+ (for converter script). Target hooks run on Windows 10/11.
  Git Bash not required for converted hooks.
metadata:
  author: axcrockett
  version: "1.0.0"
---

# Windows Hook Adapter

Convert bash hooks to Python, Node.js, or PowerShell so they work on Windows.

## When to Use This

You have a bash hook (`.sh`) that works on macOS/Linux but fails on Windows. Common failure modes: CRLF corruption, missing `jq`, CP1252 encoding crashes, `chmod` doing nothing.

## Conversion Workflow

1. **Identify the hook** — find the `.sh` file and understand what it does (stdin parsing, exit codes, stderr messages)
2. **Choose a target** — Python (recommended default), MJS (for npm ecosystems), PS1 (for enterprise Windows)
3. **Run the converter** — `python convert-hook.py --python input.sh > output.py`
4. **Review the output** — check for `# TODO: manual conversion required` comments on complex constructs
5. **Update hooks.json** — change the command from `bash script.sh` to `python script.py`

## Auto-Converter

The converter script handles 20 common bash patterns via line-by-line regex:

```
python skills/windows-hook-adapter/scripts/convert-hook.py --python hook.sh > hook.py
python skills/windows-hook-adapter/scripts/convert-hook.py --mjs hook.sh > hook.mjs
python skills/windows-hook-adapter/scripts/convert-hook.py --ps1 hook.sh > hook.ps1
```

Stdin input: `echo "bash content" | python convert-hook.py --python -`

## What It Converts

- `jq` JSON parsing to native (`json.load`, `JSON.parse`, `ConvertFrom-Json`)
- Exit codes (`exit N` to `sys.exit(N)`, `process.exit(N)`)
- Stderr output (`>&2` to `file=sys.stderr`, `console.error`, `Write-Error`)
- Environment variables (`$VAR` to `os.environ.get`, `process.env`, `$env:`)
- File checks (`[ -f ]` to `os.path.isfile`, `existsSync`, `Test-Path`)
- Conditionals and case statements

## What It Doesn't Convert

Heredocs, process substitution, pipes, arrays, brace expansion, arithmetic. These get a TODO comment.

## Reference Docs

- [bash-to-python.md](references/bash-to-python.md) — Full pattern table with code examples
- [bash-to-mjs.md](references/bash-to-mjs.md) — Node.js conversion patterns
- [bash-to-ps1.md](references/bash-to-ps1.md) — PowerShell conversion patterns
- [common-gotchas.md](references/common-gotchas.md) — CRLF, CP1252, npx shim, and more
