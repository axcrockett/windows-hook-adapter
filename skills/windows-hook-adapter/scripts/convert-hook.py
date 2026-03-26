#!/usr/bin/env python3
"""
convert-hook.py — Convert bash-based agent hooks to Windows-compatible formats.

Targets: --python (default), --mjs, --ps1
Usage:   python convert-hook.py --python input.sh > output.py
         echo '#!/usr/bin/env bash\nexit 0' | python convert-hook.py --python -

Line-by-line regex-based converter. Handles the 20 most common bash patterns.
Unsupported constructs get a TODO comment instead of wrong code.
"""
import argparse
import re
import sys


# ---------------------------------------------------------------------------
# Unsupported pattern detectors (generate TODO instead of bad output)
# ---------------------------------------------------------------------------
UNSUPPORTED_PATTERNS = [
    (r"<<\s*\w+", "heredoc"),
    (r"<\(", "process substitution"),
    (r"\$\(\(", "arithmetic expression"),
    (r"\{[a-zA-Z0-9_]+,", "brace expansion"),
    (r"declare\s+-[aA]", "bash array declaration"),
]


def is_unsupported(line):
    """Return description if line contains an unsupported pattern, else None."""
    stripped = line.strip()
    for pattern, desc in UNSUPPORTED_PATTERNS:
        if re.search(pattern, stripped):
            return desc
    return None


# ---------------------------------------------------------------------------
# Python conversion
# ---------------------------------------------------------------------------
PYTHON_HEADER = '''#!/usr/bin/env python3
"""Converted from bash hook by windows-hook-adapter."""
import io
import json
import os
import re
import sys

sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
'''


def convert_to_python(lines):
    """Convert bash lines to Python lines."""
    out = [PYTHON_HEADER]
    skip_next_fi = 0
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Skip empty lines and comments (preserve comments)
        if not stripped:
            out.append("")
            i += 1
            continue
        if stripped.startswith("#") and not stripped.startswith("#!"):
            out.append(stripped)
            i += 1
            continue

        # Skip shebang (already in header)
        if stripped.startswith("#!"):
            i += 1
            continue

        # Skip set -euo pipefail (no Python equivalent needed)
        if stripped.startswith("set "):
            i += 1
            continue

        # Check for unsupported patterns
        unsup = is_unsupported(stripped)
        if unsup:
            out.append(f"# TODO: manual conversion required — {unsup}: {stripped}")
            i += 1
            continue

        # --- Pattern: INPUT=$(cat /dev/stdin) ---
        if re.match(r"^(\w+)=\$\(cat\s+/dev/stdin\)", stripped):
            var = re.match(r"^(\w+)=", stripped).group(1)
            out.append(f"{var} = json.load(sys.stdin)")
            i += 1
            continue

        # --- Pattern: VAR=$(echo "$X" | jq -r '.field') ---
        m = re.match(
            r'^(\w+)=\$\(echo\s+["\$]+(\w+)["\s]*\|\s*jq\s+-r\s+[\'"]\.(\w+)[\'"]\)',
            stripped,
        )
        if m:
            var, src, field = m.group(1), m.group(2), m.group(3)
            out.append(f"{var} = {src}.get('{field}', '')")
            i += 1
            continue

        # --- Pattern: VAR=$(echo "$X" | jq -r '.field.subfield // empty') ---
        m = re.match(
            r'^(\w+)=\$\(echo\s+["\$]+(\w+)["\s]*\|\s*jq\s+-r\s+[\'"]\.(\w+)\.(\w+)\s*//\s*empty[\'"]\)',
            stripped,
        )
        if m:
            var, src, f1, f2 = m.group(1), m.group(2), m.group(3), m.group(4)
            out.append(f"{var} = {src}.get('{f1}', {{}}).get('{f2}', '')")
            i += 1
            continue

        # --- Pattern: VAR=$(echo "$X" | jq -r '.field // empty') ---
        m = re.match(
            r'^(\w+)=\$\(echo\s+["\$]+(\w+)["\s]*\|\s*jq\s+-r\s+[\'"]\.(\w+)\s*//\s*empty[\'"]\)',
            stripped,
        )
        if m:
            var, src, field = m.group(1), m.group(2), m.group(3)
            out.append(f"{var} = {src}.get('{field}', '')")
            i += 1
            continue

        # --- Pattern: exit N ---
        m = re.match(r"^exit\s+(\d+)", stripped)
        if m:
            out.append(f"sys.exit({m.group(1)})")
            i += 1
            continue

        # --- Pattern: echo "msg" >&2 ---
        m = re.match(r'^echo\s+"([^"]+)"\s*>&2', stripped)
        if m:
            msg = m.group(1)
            # Convert $VAR references in the message
            msg = re.sub(r"\$\{?(\w+)\}?", r"{\1}", msg)
            if "{" in msg:
                out.append(f'print(f"{msg}", file=sys.stderr)')
            else:
                out.append(f'print("{msg}", file=sys.stderr)')
            i += 1
            continue

        # --- Pattern: VAR="${VAR:-default}" (env var with default) ---
        m = re.match(r'^(\w+)="\$\{(\w+):-([^}]*)\}"', stripped)
        if m:
            var, env_var, default = m.group(1), m.group(2), m.group(3)
            out.append(f"{var} = os.environ.get('{env_var}', '{default}')")
            i += 1
            continue

        # --- Pattern: VAR=$ENV_VAR ---
        m = re.match(r"^(\w+)=\$(\w+)$", stripped)
        if m:
            var, env_var = m.group(1), m.group(2)
            out.append(f"{var} = os.environ.get('{env_var}', '')")
            i += 1
            continue

        # --- Pattern: if [ -z "$VAR" ]; then ---
        m = re.match(r'^if\s+\[\s+-z\s+"\$(\w+)"\s+\];\s*then', stripped)
        if m:
            out.append(f"if not {m.group(1)}:")
            skip_next_fi += 1
            i += 1
            continue

        # --- Pattern: if [ -f "$path" ]; then ---
        m = re.match(r'^if\s+\[\s+-f\s+"\$(\w+)"\s+\];\s*then', stripped)
        if m:
            out.append(f"if os.path.isfile({m.group(1)}):")
            skip_next_fi += 1
            i += 1
            continue

        # --- Pattern: if echo "$VAR" | grep -q "pattern"; then ---
        m = re.match(
            r'^if\s+echo\s+"\$(\w+)"\s*\|\s*grep\s+-q\s+"?\^?\$\{(\w+)\}"?;\s*then',
            stripped,
        )
        if m:
            var, pat_var = m.group(1), m.group(2)
            out.append(f'if re.search(f"^{{re.escape({pat_var})}}", {var}):')
            skip_next_fi += 1
            i += 1
            continue

        # --- Pattern: if echo "$VAR" | grep -q "literal"; then ---
        m = re.match(
            r'^if\s+echo\s+"\$(\w+)"\s*\|\s*grep\s+-q\s+"([^"]+)";\s*then', stripped
        )
        if m:
            var, pattern = m.group(1), m.group(2)
            out.append(f'if re.search(r"{pattern}", {var}):')
            skip_next_fi += 1
            i += 1
            continue

        # --- Pattern: case "$VAR" in ---
        m = re.match(r'^case\s+"\$(\w+)"\s+in', stripped)
        if m:
            # Collect case patterns until esac
            case_var = m.group(1)
            i += 1
            first_case = True
            while i < len(lines) and lines[i].strip() != "esac":
                case_line = lines[i].strip()
                # Pattern: value1|value2)
                cm = re.match(r"^([^)]+)\)", case_line)
                if cm:
                    patterns = cm.group(1).strip()
                    values = [
                        p.strip().strip('"').strip("'") for p in patterns.split("|")
                    ]
                    values_str = ", ".join(f"'{v}'" for v in values)
                    keyword = "if" if first_case else "elif"
                    out.append(f"{keyword} {case_var} in ({values_str}):")
                    first_case = False
                    i += 1
                    # Collect body lines until ;;
                    while i < len(lines) and lines[i].strip() != ";;":
                        body = lines[i].strip()
                        if body:
                            # Recursively convert the body line
                            body_converted = convert_single_line(body)
                            out.append(f"    {body_converted}")
                        i += 1
                    i += 1  # skip ;;
                    continue
                i += 1
            i += 1  # skip esac
            continue

        # --- Pattern: fi ---
        if stripped == "fi":
            if skip_next_fi > 0:
                skip_next_fi -= 1
            i += 1
            continue

        # --- Pattern: esac (handled by case above) ---
        if stripped == "esac":
            i += 1
            continue

        # --- Pattern: then / else ---
        if stripped == "then":
            i += 1
            continue
        if stripped == "else":
            out.append("else:")
            i += 1
            continue

        # --- Default: unknown line, pass through as comment ---
        out.append(f"# TODO: manual conversion required — {stripped}")
        i += 1

    return "\n".join(out) + "\n"


def convert_single_line(line):
    """Convert a single bash line to Python (for use inside case blocks)."""
    stripped = line.strip()

    # echo "msg" >&2
    m = re.match(r'^echo\s+"([^"]+)"\s*>&2', stripped)
    if m:
        msg = m.group(1)
        msg = re.sub(r"\$\{?(\w+)\}?", r"{\1}", msg)
        if "{" in msg:
            return f'print(f"{msg}", file=sys.stderr)'
        return f'print("{msg}", file=sys.stderr)'

    # exit N
    m = re.match(r"^exit\s+(\d+)", stripped)
    if m:
        return f"sys.exit({m.group(1)})"

    return f"# TODO: manual conversion required — {stripped}"


# ---------------------------------------------------------------------------
# MJS conversion
# ---------------------------------------------------------------------------
MJS_HEADER = """#!/usr/bin/env node
// Converted from bash hook by windows-hook-adapter.
import { readFileSync, existsSync } from 'fs';
import { resolve } from 'path';
"""


def convert_to_mjs(lines):
    """Convert bash lines to Node.js/MJS lines."""
    out = [MJS_HEADER]
    i = 0
    skip_closing = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            out.append("")
            i += 1
            continue
        if stripped.startswith("#") and not stripped.startswith("#!"):
            out.append(f"// {stripped[1:].strip()}")
            i += 1
            continue
        if stripped.startswith("#!"):
            i += 1
            continue
        if stripped.startswith("set "):
            i += 1
            continue

        unsup = is_unsupported(stripped)
        if unsup:
            out.append(f"// TODO: manual conversion required — {unsup}: {stripped}")
            i += 1
            continue

        # INPUT=$(cat /dev/stdin)
        if re.match(r"^(\w+)=\$\(cat\s+/dev/stdin\)", stripped):
            var = re.match(r"^(\w+)=", stripped).group(1)
            out.append(
                f"const {var} = JSON.parse(readFileSync('/dev/stdin', 'utf-8'));"
            )
            i += 1
            continue

        # VAR=$(echo "$X" | jq -r '.field // empty')
        m = re.match(
            r'^(\w+)=\$\(echo\s+["\$]+(\w+)["\s]*\|\s*jq\s+-r\s+[\'"]\.(\w+)\.(\w+)\s*//\s*empty[\'"]\)',
            stripped,
        )
        if m:
            var, src, f1, f2 = m.group(1), m.group(2), m.group(3), m.group(4)
            out.append(f"const {var} = ({src}.{f1} || {{}}).{f2} || '';")
            i += 1
            continue

        m = re.match(
            r'^(\w+)=\$\(echo\s+["\$]+(\w+)["\s]*\|\s*jq\s+-r\s+[\'"]\.(\w+)\s*//\s*empty[\'"]\)',
            stripped,
        )
        if m:
            var, src, field = m.group(1), m.group(2), m.group(3)
            out.append(f"const {var} = {src}.{field} || '';")
            i += 1
            continue

        # VAR=$(echo "$X" | jq -r '.field')
        m = re.match(
            r'^(\w+)=\$\(echo\s+["\$]+(\w+)["\s]*\|\s*jq\s+-r\s+[\'"]\.(\w+)[\'"]\)',
            stripped,
        )
        if m:
            var, src, field = m.group(1), m.group(2), m.group(3)
            out.append(f"const {var} = {src}.{field} || '';")
            i += 1
            continue

        # exit N
        m = re.match(r"^exit\s+(\d+)", stripped)
        if m:
            out.append(f"process.exit({m.group(1)});")
            i += 1
            continue

        # echo "msg" >&2
        m = re.match(r'^echo\s+"([^"]+)"\s*>&2', stripped)
        if m:
            msg = m.group(1)
            msg = re.sub(r"\$\{?(\w+)\}?", r"${\1}", msg)
            if "${" in msg:
                out.append(f"console.error(`{msg}`);")
            else:
                out.append(f'console.error("{msg}");')
            i += 1
            continue

        # VAR="${VAR:-default}"
        m = re.match(r'^(\w+)="\$\{(\w+):-([^}]*)\}"', stripped)
        if m:
            var, env_var, default = m.group(1), m.group(2), m.group(3)
            out.append(f"const {var} = process.env.{env_var} || '{default}';")
            i += 1
            continue

        # if [ -z "$VAR" ]; then
        m = re.match(r'^if\s+\[\s+-z\s+"\$(\w+)"\s+\];\s*then', stripped)
        if m:
            out.append(f"if (!{m.group(1)}) {{")
            skip_closing += 1
            i += 1
            continue

        # if [ -f "$path" ]; then
        m = re.match(r'^if\s+\[\s+-f\s+"\$(\w+)"\s+\];\s*then', stripped)
        if m:
            out.append(f"if (existsSync({m.group(1)})) {{")
            skip_closing += 1
            i += 1
            continue

        # if echo ... | grep -q ...; then
        m = re.match(
            r'^if\s+echo\s+"\$(\w+)"\s*\|\s*grep\s+-q\s+"?\^?\$\{(\w+)\}"?;\s*then',
            stripped,
        )
        if m:
            var, pat_var = m.group(1), m.group(2)
            out.append(f"if ({var}.startsWith({pat_var})) {{")
            skip_closing += 1
            i += 1
            continue

        m = re.match(
            r'^if\s+echo\s+"\$(\w+)"\s*\|\s*grep\s+-q\s+"([^"]+)";\s*then', stripped
        )
        if m:
            var, pattern = m.group(1), m.group(2)
            out.append(f"if ({var}.match(/{pattern}/)) {{")
            skip_closing += 1
            i += 1
            continue

        # case "$VAR" in
        m = re.match(r'^case\s+"\$(\w+)"\s+in', stripped)
        if m:
            case_var = m.group(1)
            i += 1
            first_case = True
            while i < len(lines) and lines[i].strip() != "esac":
                case_line = lines[i].strip()
                cm = re.match(r"^([^)]+)\)", case_line)
                if cm:
                    patterns = cm.group(1).strip()
                    values = [
                        p.strip().strip('"').strip("'") for p in patterns.split("|")
                    ]
                    values_str = ", ".join(f"'{v}'" for v in values)
                    keyword = "if" if first_case else "} else if"
                    out.append(f"{keyword} ([{values_str}].includes({case_var})) {{")
                    first_case = False
                    i += 1
                    while i < len(lines) and lines[i].strip() != ";;":
                        body = lines[i].strip()
                        if body:
                            body_converted = convert_single_line_mjs(body)
                            out.append(f"  {body_converted}")
                        i += 1
                    i += 1
                    continue
                i += 1
            out.append("}")
            i += 1
            continue

        # fi
        if stripped == "fi":
            if skip_closing > 0:
                out.append("}")
                skip_closing -= 1
            i += 1
            continue

        if stripped == "then":
            i += 1
            continue
        if stripped == "else":
            out.append("} else {")
            i += 1
            continue
        if stripped == "esac":
            i += 1
            continue

        out.append(f"// TODO: manual conversion required — {stripped}")
        i += 1

    return "\n".join(out) + "\n"


def convert_single_line_mjs(line):
    """Convert a single bash line to MJS."""
    stripped = line.strip()

    m = re.match(r'^echo\s+"([^"]+)"\s*>&2', stripped)
    if m:
        msg = m.group(1)
        msg = re.sub(r"\$\{?(\w+)\}?", r"${\1}", msg)
        if "${" in msg:
            return f"console.error(`{msg}`);"
        return f'console.error("{msg}");'

    m = re.match(r"^exit\s+(\d+)", stripped)
    if m:
        return f"process.exit({m.group(1)});"

    return f"// TODO: manual conversion required — {stripped}"


# ---------------------------------------------------------------------------
# PS1 conversion
# ---------------------------------------------------------------------------
PS1_HEADER = """# Converted from bash hook by windows-hook-adapter.
# Requires: PowerShell 5.1+
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
"""


def convert_to_ps1(lines):
    """Convert bash lines to PowerShell lines."""
    out = [PS1_HEADER]
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            out.append("")
            i += 1
            continue
        if stripped.startswith("#") and not stripped.startswith("#!"):
            out.append(stripped)
            i += 1
            continue
        if stripped.startswith("#!") or stripped.startswith("set "):
            i += 1
            continue

        unsup = is_unsupported(stripped)
        if unsup:
            out.append(f"# TODO: manual conversion required — {unsup}: {stripped}")
            i += 1
            continue

        # INPUT=$(cat /dev/stdin)
        if re.match(r"^(\w+)=\$\(cat\s+/dev/stdin\)", stripped):
            var = re.match(r"^(\w+)=", stripped).group(1)
            out.append(f"${var} = [Console]::In.ReadToEnd() | ConvertFrom-Json")
            i += 1
            continue

        # VAR=$(echo "$X" | jq ...)
        m = re.match(
            r'^(\w+)=\$\(echo\s+["\$]+(\w+)["\s]*\|\s*jq\s+-r\s+[\'"]\.(\w+)[\'"]\)',
            stripped,
        )
        if m:
            var, src, field = m.group(1), m.group(2), m.group(3)
            out.append(f"${var} = ${src}.{field}")
            i += 1
            continue

        # exit N
        m = re.match(r"^exit\s+(\d+)", stripped)
        if m:
            out.append(f"exit {m.group(1)}")
            i += 1
            continue

        # echo "msg" >&2
        m = re.match(r'^echo\s+"([^"]+)"\s*>&2', stripped)
        if m:
            msg = m.group(1)
            msg = re.sub(r"\$\{?(\w+)\}?", r"$\1", msg)
            out.append(f'Write-Error "{msg}"')
            i += 1
            continue

        # VAR="${VAR:-default}"
        m = re.match(r'^(\w+)="\$\{(\w+):-([^}]*)\}"', stripped)
        if m:
            var, env_var, default = m.group(1), m.group(2), m.group(3)
            out.append(
                f'${var} = if ($env:{env_var}) {{ $env:{env_var} }} else {{ "{default}" }}'
            )
            i += 1
            continue

        # if [ -f "$path" ]; then
        m = re.match(r'^if\s+\[\s+-f\s+"\$(\w+)"\s+\];\s*then', stripped)
        if m:
            out.append(f"if (Test-Path ${m.group(1)}) {{")
            i += 1
            continue

        # if [ -z "$VAR" ]; then
        m = re.match(r'^if\s+\[\s+-z\s+"\$(\w+)"\s+\];\s*then', stripped)
        if m:
            out.append(f"if (-not ${m.group(1)}) {{")
            i += 1
            continue

        if stripped == "fi":
            out.append("}")
            i += 1
            continue
        if stripped == "then":
            i += 1
            continue
        if stripped == "else":
            out.append("} else {")
            i += 1
            continue

        out.append(f"# TODO: manual conversion required — {stripped}")
        i += 1

    return "\n".join(out) + "\n"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Convert bash hooks to Windows-compatible formats."
    )
    parser.add_argument("input", help="Input bash file (use - for stdin)")
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--python",
        action="store_true",
        default=True,
        help="Convert to Python (default)",
    )
    group.add_argument("--mjs", action="store_true", help="Convert to Node.js/MJS")
    group.add_argument("--ps1", action="store_true", help="Convert to PowerShell")

    args = parser.parse_args()

    # Read input
    if args.input == "-":
        content = sys.stdin.read()
    else:
        with open(args.input, "r", encoding="utf-8") as f:
            content = f.read()

    lines = content.splitlines()

    # Convert
    if args.ps1:
        result = convert_to_ps1(lines)
    elif args.mjs:
        result = convert_to_mjs(lines)
    else:
        result = convert_to_python(lines)

    sys.stdout.write(result)


if __name__ == "__main__":
    main()
