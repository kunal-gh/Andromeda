import sys
from pathlib import Path

# Add backend directory to sys.path so modules can be imported
sys.path.append(str(Path(__file__).parent.parent))

# Import the FastAPI app
from app.main import app