# windows-hook-adapter

Convert bash-based AI coding agent hooks to Windows-compatible Python, Node.js, or PowerShell.

The #1 Windows hook killer is CRLF line endings. Git checks out your `.sh` file with `\r\n` instead of `\n`. The shebang becomes `#!/usr/bin/env bash\r`. Bash looks for an interpreter called `bash\r`, doesn't find it, and your hook silently fails. You stare at a valid file path in a "No such file or directory" error and question your sanity.

This skill fixes that. It converts bash hooks to native Windows formats that don't depend on Unix tools, don't break on line endings, and don't crash on CP1252 encoding.

## Install

**Claude Code:**
```bash
claude plugin add axcrockett/windows-hook-adapter
```

**OpenSkills (Codex, Cursor, Amp, OpenCode):**
```bash
npx openskills install axcrockett/windows-hook-adapter
```

**Manual:**
```bash
git clone https://github.com/axcrockett/windows-hook-adapter
cp -r skills/windows-hook-adapter ~/.claude/skills/
```

## Usage

Feed it a bash hook, get back a working Windows hook:

```bash
python skills/windows-hook-adapter/scripts/convert-hook.py --python hook.sh > hook.py
python skills/windows-hook-adapter/scripts/convert-hook.py --mjs hook.sh > hook.mjs
python skills/windows-hook-adapter/scripts/convert-hook.py --ps1 hook.sh > hook.ps1
```

Read from stdin:
```bash
cat hook.sh | python convert-hook.py --python - > hook.py
```

## What Gets Converted

20 common bash patterns, line by line:

- **JSON parsing:** `jq '.field'` becomes `json.load(sys.stdin)['field']` (Python), `JSON.parse(...)` (MJS), `ConvertFrom-Json` (PS1)
- **Exit codes:** `exit 2` becomes `sys.exit(2)` / `process.exit(2)` / `exit 2`
- **Stderr:** `echo "msg" >&2` becomes `print("msg", file=sys.stderr)` / `console.error("msg")` / `Write-Error "msg"`
- **Env vars:** `${VAR:-default}` becomes `os.environ.get('VAR', 'default')` / `process.env.VAR || 'default'`
- **File checks:** `[ -f "$path" ]` becomes `os.path.isfile(path)` / `existsSync(path)` / `Test-Path $path`
- **Conditionals:** `if/then/fi`, `case/esac` become native equivalents

Unsupported constructs (heredocs, process substitution, arrays, pipes) get a `# TODO: manual conversion required` comment. No wrong code generated.

Python output automatically includes the UTF-8 stdin wrapper (`io.TextIOWrapper`) that prevents CP1252 crashes.

## Reference Docs

| Doc | What's In It |
|-----|-------------|
| [bash-to-python.md](skills/windows-hook-adapter/references/bash-to-python.md) | Full pattern table, JSON parsing, conditionals, case statements |
| [bash-to-mjs.md](skills/windows-hook-adapter/references/bash-to-mjs.md) | Node.js patterns, when to choose MJS over Python |
| [bash-to-ps1.md](skills/windows-hook-adapter/references/bash-to-ps1.md) | PowerShell patterns, execution policy, invocation |
| [common-gotchas.md](skills/windows-hook-adapter/references/common-gotchas.md) | CRLF, CP1252, path separators, npx shim, chmod, timeouts |

## Which Target Should I Pick?

**Python** (default): Best all-around. Cross-platform. Most patterns supported. Slower cold start on Windows (~800ms).

**Node.js/MJS**: Fastest cold start (~200ms). Good if your ecosystem is already npm-based. Use when `node` is available.

**PowerShell**: Native Windows. Slowest cold start (~1.5s). Use in enterprise environments where Python/Node aren't installed.

## Tests

```bash
python -m pytest skills/windows-hook-adapter/tests/ -v
```

10 test cases covering Python conversion, MJS conversion, and unsupported pattern handling.

## Contributing

Found a bash pattern that converts wrong? Open an issue with the input and expected output. PRs welcome.

## License

Apache-2.0
