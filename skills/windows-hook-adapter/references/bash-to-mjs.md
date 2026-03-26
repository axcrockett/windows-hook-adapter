# Bash to Node.js/MJS Conversion Reference

Pattern mapping for converting bash-based agent hooks to ES module (`.mjs`) format.

## Boilerplate

```javascript
#!/usr/bin/env node
import { readFileSync, existsSync } from 'fs';
```

## Pattern Mapping

| Bash | MJS | Notes |
|------|-----|-------|
| `#!/usr/bin/env bash` | `#!/usr/bin/env node` | |
| `cat /dev/stdin` | `readFileSync('/dev/stdin', 'utf-8')` | Then `JSON.parse()` |
| `echo "$X" \| jq -r '.field'` | `X.field \|\| ''` | Property access |
| `echo "msg" >&2` | `console.error("msg")` | Stderr output |
| `exit 0` | `process.exit(0)` | Allow |
| `exit 2` | `process.exit(2)` | Block |
| `$VAR` | `process.env.VAR \|\| ''` | Env var read |
| `${VAR:-default}` | `process.env.VAR \|\| 'default'` | Env var with fallback |
| `[ -f "$path" ]` | `existsSync(path)` | File existence check |
| `[ -z "$VAR" ]` | `!VAR` | Empty check |
| `grep -q pattern` | `str.match(/pattern/)` | Regex test |
| `# comment` | `// comment` | Comment syntax |

## JSON Stdin Parsing

```bash
# Bash
INPUT=$(cat /dev/stdin)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name')
```

```javascript
// MJS
const INPUT = JSON.parse(readFileSync('/dev/stdin', 'utf-8'));
const TOOL_NAME = INPUT.tool_name || '';
```

## Conditional Logic

```bash
if [ -z "$TOOL_NAME" ]; then
  echo "Missing" >&2
  exit 0
fi
```

```javascript
if (!TOOL_NAME) {
  console.error("Missing");
  process.exit(0);
}
```

## Case Statements

```bash
case "$TOOL_NAME" in
  Write|Edit)
    echo "blocked" >&2
    exit 2
    ;;
esac
```

```javascript
if (['Write', 'Edit'].includes(TOOL_NAME)) {
  console.error("blocked");
  process.exit(2);
}
```

## When to Use MJS Over Python

- Your hook ecosystem is already Node.js (npm-based plugins)
- You need to call npm packages from within the hook
- `node` is available but `python` is not
- You want synchronous file I/O without async complications

MJS hooks start faster than Python on Windows (~200ms vs ~800ms cold start).
