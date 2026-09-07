# settings/production.py
# Konfigurasi untuk VPS produksi (ami.unisan-g.id)
# AKTIFKAN dengan: export DJANGO_SETTINGS_MODULE=ami_project.settings.production

from .base import *
from decouple import config

DEBUG = False

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='').split(',')

# nginx menerima HTTPS lalu meneruskan ke gunicorn via HTTP biasa (proxy_pass
# http://127.0.0.1:PORT) sambil mengirim header X-Forwarded-Proto. Tanpa baris
# ini, Django tidak tahu request aslinya HTTPS -> is_secure() selalu False ->
# SECURE_SSL_REDIRECT bikin redirect loop tak berhingga ke URL yang sama.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Database production akan dikonfigurasi via .env
# Static & Media handling untuk production akan dikonfigurasi nanti
