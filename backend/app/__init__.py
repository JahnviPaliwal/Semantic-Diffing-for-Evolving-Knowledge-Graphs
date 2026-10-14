"""Backend application package."""
import sys
from pathlib import Path

# Ensure repository root is on sys.path so 'src' can always be imported regardless of cwd
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

__version__ = "2.0.0"
