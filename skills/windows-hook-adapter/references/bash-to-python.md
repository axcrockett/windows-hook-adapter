# Bash to Python Conversion Reference

Pattern mapping for converting bash-based agent hooks to Python 3.

## Boilerplate

Every converted Python hook needs this at the top:

```python
#!/usr/bin/env python3
import io
import json
import os
import re
import sys

sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
```

The `io.TextIOWrapper` line prevents CP1252 encoding crashes on Windows.

## Pattern Mapping

| Bash | Python | Notes |
|------|--------|-------|
| `#!/usr/bin/env bash` | `#!/usr/bin/env python3` | Plus UTF-8 wrapper |
| `cat /dev/stdin` | `json.load(sys.stdin)` | Returns dict directly |
| `echo "$INPUT" \| jq -r '.field'` | `INPUT.get('field', '')` | Dict access |
| `echo "$INPUT" \| jq -r '.a.b // empty'` | `INPUT.get('a', {}).get('b', '')` | Nested access |
| `echo "msg" >&2` | `print("msg", file=sys.stderr)` | Stderr output |
| `exit 0` | `sys.exit(0)` | Allow |
| `exit 2` | `sys.exit(2)` | Block |
| `$VAR` | `os.environ.get('VAR', '')` | Env var read |
| `${VAR:-default}` | `os.environ.get('VAR', 'default')` | Env var with fallback |
| `[ -f "$path" ]` | `os.path.isfile(path)` | File existence check |
| `[ -z "$VAR" ]` | `not VAR` | Empty string check |
| `grep -q pattern file` | `re.search(r'pattern', open(file).read())` | Pattern match |
| `$(command)` | `subprocess.run(['command'], capture_output=True).stdout` | Command substitution |
| `set -euo pipefail` | *(skip)* | No direct equivalent needed |

## JSON Stdin Parsing

Bash hooks typically parse JSON from stdin using `jq`. In Python, replace the entire jq pipeline:

```bash
# Bash
INPUT=$(cat /dev/stdin)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name')
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
```

```python
# Python
INPUT = json.load(sys.stdin)
TOOL_NAME = INPUT.get('tool_name', '')
FILE_PATH = INPUT.get('tool_input', {}).get('file_path', '')
```

## Conditional Logic

```bash
# Bash
if [ -z "$TOOL_NAME" ]; then
  echo "Missing tool name" >&2
  exit 0
fi
```

```python
# Python
if not TOOL_NAME:
    print("Missing tool name", file=sys.stderr)
    sys.exit(0)
```

## Case Statements

```bash
# Bash
case "$TOOL_NAME" in
  Write|Edit)
    echo "Write operation" >&2
    exit 2
    ;;
esac
```

```python
# Python
if TOOL_NAME in ('Write', 'Edit'):
    print("Write operation", file=sys.stderr)
    sys.exit(2)
```

## Unsupported Constructs

These require manual conversion:
- Heredocs (`<<EOF`)
- Process substitution (`<(...)`)
- Pipes with multiple stages (`cmd1 | cmd2 | cmd3`)
- Bash arrays and associative arrays
- Brace expansion (`{a,b,c}`)
- Arithmetic expressions (`$((...))`)

The converter marks these with `# TODO: manual conversion required`.
