"""Research runners and compatibility imports for the flat code/ implementation."""
from pathlib import Path
import sys

_package_root = str(Path(__file__).resolve().parents[1])
if _package_root not in sys.path:
    sys.path.insert(0, _package_root)
