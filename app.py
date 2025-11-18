"""
Minimal entrypoint compatibility file for Render/Procfile.
Some deployment platforms expect the app module to be named `app` and run `gunicorn app:app`.
This file simply re-exports the FastAPI app from `main.py`.
"""

from main import app

# Expose name for WSGI/ASGI servers
__all__ = ["app"]
