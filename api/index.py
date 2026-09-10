import sys
import os

# Ensure the root project directory is in the Python module search path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

# Vercel looks for the WSGI application callable
app = app
