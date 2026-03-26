# Bash to PowerShell Conversion Reference

Pattern mapping for converting bash-based agent hooks to PowerShell (`.ps1`) format.

## Boilerplate

```powershell
# Requires: PowerShell 5.1+
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
```

The encoding lines prevent CP1252 corruption, same problem as Python.

## Pattern Mapping

| Bash | PowerShell | Notes |
|------|-----------|-------|
| `#!/usr/bin/env bash` | *(remove)* | No shebang needed |
| `cat /dev/stdin` | `[Console]::In.ReadToEnd()` | Then pipe to `ConvertFrom-Json` |
| `echo "$X" \| jq -r '.field'` | `$X.field` | Property access |
| `echo "msg" >&2` | `Write-Error "msg"` | Stderr output |
| `exit 0` | `exit 0` | Same syntax |
| `exit 2` | `exit 2` | Same syntax |
| `$VAR` | `$env:VAR` | Env var read |
| `${VAR:-default}` | `if ($env:VAR) { $env:VAR } else { "default" }` | No ternary in PS 5.1 |
| `[ -f "$path" ]` | `Test-Path $path` | File existence check |
| `[ -z "$VAR" ]` | `-not $VAR` | Empty check |
| `grep -q pattern file` | `Select-String -Pattern pattern -Path file` | Pattern match |
| `# comment` | `# comment` | Same syntax |

## JSON Stdin Parsing

```bash
INPUT=$(cat /dev/stdin)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name')
```

```powershell
$INPUT = [Console]::In.ReadToEnd() | ConvertFrom-Json
$TOOL_NAME = $INPUT.tool_name
```

## Conditional Logic

```bash
if [ -z "$TOOL_NAME" ]; then
  echo "Missing" >&2
  exit 0
fi
```

```powershell
if (-not $TOOL_NAME) {
    Write-Error "Missing"
    exit 0
}
```

## Invocation Pattern

PowerShell hooks need an explicit execution policy bypass:

```
powershell.exe -ExecutionPolicy Bypass -NoProfile -File "path/to/hook.ps1"
```

This is the standard pattern for hooks.json commands on Windows.

## When to Use PS1

- Enterprise Windows environments where Python/Node aren't available
- You need deep Windows API access (registry, services, COM objects)
- Your team already uses PowerShell for automation

Downsides: PS1 hooks have the slowest cold start (~1.5s) and the most encoding pitfalls.
