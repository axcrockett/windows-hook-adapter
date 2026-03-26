# Common Gotchas: Bash Hooks on Windows

These are the things that break when you try to run bash hooks on Windows. Ranked by how often they bite.

## 1. CRLF Line Endings (The #1 Killer)

Git on Windows defaults to `core.autocrlf=true`. This converts LF to CRLF on checkout. Bash shebangs break because the shell looks for `bash\r` instead of `bash`.

**Symptoms:**
- `No such file or directory` on a valid script path
- Hook silently does nothing
- YAML frontmatter hook commands corrupt variable values

**Detection:**
```bash
python -c "print(open('hook.sh','rb').read().count(b'\r'))"
```

**Fix:**
```bash
python -c "p='hook.sh';open(p,'wb').write(open(p,'rb').read().replace(b'\r\n',b'\n'))"
```

**Prevention:**
```
# .gitattributes
*.sh text eol=lf
*.py text eol=lf
*.mjs text eol=lf
```

## 2. CP1252 Encoding

Windows Terminal defaults to CP1252. Python's `sys.stdin` inherits this. If hook JSON contains non-ASCII characters (common in user-generated content), Python crashes with `UnicodeDecodeError`.

**Fix for Python hooks:**
```python
import io, sys
sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
```

**Fix for PowerShell:**
```powershell
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
```

Node.js handles UTF-8 by default when you specify the encoding in `readFileSync`.

## 3. Path Separators

Bash uses `/`, Windows uses `\`. Git Bash translates most paths, but not all.

**Safe pattern:** Always use forward slashes in hook scripts. Python's `os.path` handles both. Node's `path.resolve()` normalizes automatically.

**Dangerous:** Hardcoded `/dev/null` won't work in PowerShell. Use `$null` instead.

## 4. The npx Shim Problem

`npx` on Windows is a `.cmd` shim, not a binary. You cannot invoke it directly as a command in hooks.json or MCP configs.

**Wrong:**
```json
{"command": "npx", "args": ["some-tool"]}
```

**Right:**
```json
{"command": "cmd", "args": ["/c", "npx", "some-tool"]}
```

This applies to any `.cmd` shim: `npm`, `npx`, `yarn`, `pnpm`.

## 5. chmod Doesn't Exist

`chmod +x script.py` does nothing on Windows. File executability is determined by the file extension and system PATH, not permission bits.

**Impact:** Shebangs are cosmetic on Windows. The hook runner must explicitly invoke the interpreter: `python script.py`, not `./script.py`.

## 6. Process Spawning Differences

Bash command substitution and backticks don't work outside bash. Each language has its own subprocess pattern:

| Language | Subprocess Pattern |
|----------|-----------|
| Python | `subprocess.run(['cmd', 'arg'], capture_output=True)` |
| Node.js | `execFileSync('cmd', ['arg'], { encoding: 'utf-8' })` |
| PowerShell | `& cmd arg` or `Start-Process` |

Always use array-based argument passing (not string concatenation) to avoid injection and escaping issues.

## 7. Tilde Expansion

`~` expands in Git Bash but not CMD, PowerShell, or Python. Use `os.path.expanduser('~')` (Python), `os.homedir()` (Node), `$HOME` (PowerShell).

## 8. Hook Timeout on Cold Start

Python cold start on Windows is 500-1000ms. Set hook timeout to 15s for Python hooks. Node.js starts in ~200ms, so 5s is fine.
