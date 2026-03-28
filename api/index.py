import os
import sys
from pathlib import Path

# Add the project root to sys.path so 'backend.app' can be found
_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent

if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# Direct import for Vercel's scanner
from backend.app import app

# Ensure 'app' is definitely at the top level
application = app
