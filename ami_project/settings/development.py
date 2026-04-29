"""
settings/development.py
Konfigurasi untuk development di komputer lokal.
DEBUG dan database settings sudah diambil dari .env via base.py
"""

from .base import *

# Email backend: tampil di console PowerShell saat development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Django Debug Toolbar - hanya aktif di development
INTERNAL_IPS = [
    '127.0.0.1',
    'localhost',
]

# Logging untuk development - lebih verbose
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}