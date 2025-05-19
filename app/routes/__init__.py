# app/routes/__init__.py

"""
Routes package initialization.
"""

from app.routes.views_new import views_bp
from app.routes.api import api_bp

__all__ = ['views_bp', 'api_bp']