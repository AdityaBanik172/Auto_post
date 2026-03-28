import os
import sys
from pathlib import Path

# Add the 'backend' folder to the Python path
# This allows imports like 'from linkedin.create_post import LinkedIn' to work
_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
_BACKEND = _ROOT / "backend"

if str(_BACKEND) not in sys.path:
    sys.path.append(str(_BACKEND))

# Import the 'app' object from 'backend/app.py'
try:
    from app import app as app_instance
    # Vercel looks for a variable named 'app' or 'application'
    app = app_instance
except ImportError as e:
    print(f"Error importing app: {e}")
    # Fallback to try relative import if needed
    from backend.app import app as app_instance
    app = app_instance
