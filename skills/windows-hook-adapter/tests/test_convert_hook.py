"""Tests for convert-hook.py — bash to Python/MJS/PS1 converter."""

import os
import subprocess
import sys

import pytest

from conftest import CONVERT_SCRIPT, SAMPLE_BASH, EXPECTED_PYTHON, EXPECTED_MJS


def run_converter(args, input_text=None):
    """Run convert-hook.py with given args and optional stdin."""
    result = subprocess.run(
        [sys.executable, CONVERT_SCRIPT] + args,
        capture_output=True,
        text=True,
        input=input_text,
    )
    return result


def has_pattern(output, pattern):
    """Check if a pattern (substring) is present in the output."""
    return pattern in output


class TestPythonConversion:
    """Test --python conversion target."""

    def test_convert_to_python_basic(self, sample_bash, expected_python):
        """Sample hook converts to Python with key structural elements."""
        result = run_converter(["--python", sample_bash])
        assert result.returncode == 0
        output = result.stdout
        # Check key structural patterns from expected output
        assert "import json" in output
        assert "import sys" in output
        assert "import os" in output
        assert "json.load(sys.stdin)" in output or "json.loads(" in output
        assert "sys.exit(0)" in output
        assert "sys.exit(2)" in output
        assert "file=sys.stderr" in output

    def test_utf8_boilerplate_added(self, sample_bash):
        """Python output includes the UTF-8 stdin wrapper."""
        result = run_converter(["--python", sample_bash])
        assert result.returncode == 0
        assert "io.TextIOWrapper" in result.stdout
        assert "encoding" in result.stdout

    def test_shebang_converted(self, sample_bash):
        """Bash shebang is converted to python3 shebang."""
        result = run_converter(["--python", sample_bash])
        assert result.returncode == 0
        lines = result.stdout.strip().splitlines()
        assert lines[0] == "#!/usr/bin/env python3"

    def test_exit_code_preserved(self):
        """exit N in bash becomes sys.exit(N) in Python."""
        bash = "#!/usr/bin/env bash\nexit 2\n"
        result = run_converter(["--python", "-"], input_text=bash)
        assert result.returncode == 0
        assert "sys.exit(2)" in result.stdout

    def test_stderr_preserved(self):
        """echo ... >&2 becomes print(..., file=sys.stderr)."""
        bash = '#!/usr/bin/env bash\necho "error msg" >&2\n'
        result = run_converter(["--python", "-"], input_text=bash)
        assert result.returncode == 0
        assert "file=sys.stderr" in result.stdout
        assert "error msg" in result.stdout

    def test_env_var_converted(self):
        """$VAR and ${VAR:-default} convert to os.environ.get()."""
        bash = '#!/usr/bin/env bash\nMY_DIR="${MY_DIR:-/tmp}"\n'
        result = run_converter(["--python", "-"], input_text=bash)
        assert result.returncode == 0
        assert "os.environ.get" in result.stdout
        assert "MY_DIR" in result.stdout

    def test_file_check_converted(self):
        """[ -f "$path" ] converts to os.path.isfile()."""
        bash = '#!/usr/bin/env bash\nif [ -f "$CONFIG" ]; then\n  echo "found"\nfi\n'
        result = run_converter(["--python", "-"], input_text=bash)
        assert result.returncode == 0
        assert "os.path.isfile" in result.stdout

    def test_jq_pattern_detected(self):
        """jq '.field' converts to json dict access."""
        bash = "#!/usr/bin/env bash\nNAME=$(echo \"$INPUT\" | jq -r '.name')\n"
        result = run_converter(["--python", "-"], input_text=bash)
        assert result.returncode == 0
        out = result.stdout
        # Should use json/dict access, not jq
        assert "jq" not in out
        assert "name" in out


class TestMjsConversion:
    """Test --mjs conversion target."""

    def test_convert_to_mjs_basic(self, sample_bash, expected_mjs):
        """Sample hook converts to MJS with key structural elements."""
        result = run_converter(["--mjs", sample_bash])
        assert result.returncode == 0
        output = result.stdout
        assert "JSON.parse" in output
        assert "process.exit(0)" in output
        assert "process.exit(2)" in output
        assert "console.error" in output


class TestUnsupportedPatterns:
    """Test that unsupported patterns generate TODO comments."""

    def test_complex_pattern_generates_todo(self):
        """Heredoc generates a TODO comment instead of wrong code."""
        bash = "#!/usr/bin/env bash\ncat <<EOF\nhello world\nEOF\n"
        result = run_converter(["--python", "-"], input_text=bash)
        assert result.returncode == 0
        assert "TODO" in result.stdout
        assert "manual conversion" in result.stdout.lower()
