"""Research runners and compatibility imports for the local code/ package.

The production package name is buy_or_wait, never code (a Python stdlib module).
"""
from pathlib import Path
import sys

_package_root = str(Path(__file__).resolve().parents[1] / 'code')
if _package_root not in sys.path:
    sys.path.insert(0, _package_root)
