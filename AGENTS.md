# Windows Hook Adapter

Convert bash-based AI coding agent hooks to Windows-compatible formats. If you're dealing with hooks that fail on Windows — CRLF corruption, missing jq, CP1252 encoding crashes, chmod doing nothing — this skill has the conversion patterns and an auto-converter script for Python, Node.js, and PowerShell targets.

<available_skills>
<skill>
  <name>windows-hook-adapter</name>
  <description>Convert bash shell hooks (.sh) to Windows-compatible Python (.py), Node.js (.mjs), or PowerShell (.ps1). Handles jq-to-native JSON parsing, exit codes, stderr output, env vars, file checks, conditionals. Auto-converter script for 20 common patterns. Reference docs for CRLF, CP1252, path separators, npx shim workaround. Use when bash hooks break on Windows 10/11.</description>
  <location>skills/windows-hook-adapter</location>
  <invoke>openskills read windows-hook-adapter</invoke>
</skill>
</available_skills>

---

## Installation

### Claude Code (plugin)
```bash
claude plugin add axcrockett/windows-hook-adapter
```

### OpenSkills (universal -- Codex, Cursor, Amp, OpenCode, etc.)
```bash
npx openskills install axcrockett/windows-hook-adapter
```

### Manual
```bash
git clone https://github.com/axcrockett/windows-hook-adapter
cp -r skills/windows-hook-adapter ~/.claude/skills/
```

---

## Quick Reference

**Converter script:**
```
python skills/windows-hook-adapter/scripts/convert-hook.py --python hook.sh > hook.py
python skills/windows-hook-adapter/scripts/convert-hook.py --mjs hook.sh > hook.mjs
python skills/windows-hook-adapter/scripts/convert-hook.py --ps1 hook.sh > hook.ps1
```

**Reference docs:**
- `references/bash-to-python.md` — Pattern mapping table with code examples
- `references/bash-to-mjs.md` — Node.js conversion patterns
- `references/bash-to-ps1.md` — PowerShell conversion patterns
- `references/common-gotchas.md` — CRLF, CP1252, npx shim, path separators
