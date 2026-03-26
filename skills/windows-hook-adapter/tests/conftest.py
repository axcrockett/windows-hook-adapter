import os
import pytest

REPO_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
FIXTURES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
CONVERT_SCRIPT = os.path.join(
    REPO_ROOT, "skills", "windows-hook-adapter", "scripts", "convert-hook.py"
)
SAMPLE_BASH = os.path.join(FIXTURES_DIR, "sample-bash-hook.sh")
EXPECTED_PYTHON = os.path.join(FIXTURES_DIR, "expected-python-hook.py")
EXPECTED_MJS = os.path.join(FIXTURES_DIR, "expected-mjs-hook.mjs")


@pytest.fixture
def convert_script():
    return CONVERT_SCRIPT


@pytest.fixture
def sample_bash():
    return SAMPLE_BASH


@pytest.fixture
def expected_python():
    return EXPECTED_PYTHON


@pytest.fixture
def expected_mjs():
    return EXPECTED_MJS
