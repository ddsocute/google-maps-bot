import os
import sys

# Add the parent directory to sys.path so we can import app.py from the root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

# Vercel expects a variable named 'app' (or 'handler') to be the entry point
# This file acts as the bridge between Vercel's serverless environment and our Flask app
