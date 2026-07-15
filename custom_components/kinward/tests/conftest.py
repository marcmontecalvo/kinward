"""Load api.py/const.py without executing __init__.py.

__init__.py imports homeassistant.*, which this lightweight devtools venv
intentionally does not install (see custom_components/kinward/README.md).
The pure response-classification logic in api.py has no homeassistant
dependency, so it's loaded directly as a synthetic 'kinward' package instead
of going through the real package __init__.
"""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, filename: str) -> types.ModuleType:
    spec = importlib.util.spec_from_file_location(name, PACKAGE_ROOT / filename)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    module.__package__ = "kinward"
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


if "kinward" not in sys.modules:
    fake_package = types.ModuleType("kinward")
    fake_package.__path__ = [str(PACKAGE_ROOT)]  # type: ignore[attr-defined]
    sys.modules["kinward"] = fake_package
    _load("kinward.const", "const.py")
    _load("kinward.api", "api.py")
