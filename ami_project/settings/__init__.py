# settings/__init__.py
# Auto-load development settings by default
# Production akan di-set via DJANGO_SETTINGS_MODULE environment variable

from .base import *

try:
    from .development import *
except ImportError:
    pass
