"""
Django settings for ami_project — SI-AMI UNISAN
Sistem Audit Mutu Internal Universitas Ichsan Gorontalo
Django 5.2 LTS + PostgreSQL 15

Reference: Catatan Teknis SI-AMI Bab 6
"""


from pathlib import Path
from decouple import config, Csv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
# Akan di-override via .env di STEP A8
SECRET_KEY = config('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
# Akan di-override di development.py dan production.py
DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())


# ============================================
# APPLICATION DEFINITION
# ============================================

INSTALLED_APPS = [
    # Django built-in
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party packages
    'rest_framework',
    'drf_spectacular',
    'corsheaders',
    'axes',
    'django_htmx',
    'django_filters',
    'django_tables2',
    'channels',
    'debug_toolbar',
    'django_extensions',
    
    # SI-AMI Apps (12 modul)
    'apps.ami_core',          # Core: User, SSO, base
    'apps.ami_master',        # Modul 1: Master data (Fakultas, Prodi)
    'apps.ami_assessment',    # Modul 2-3: Self-Assessment + Upload Bukti
    'apps.ami_de',            # Modul 4: Desk Evaluasi (KRITIS)
    'apps.ami_visitasi',      # Modul 5: Visitasi
    'apps.ami_temuan',        # Modul 6-7: Temuan + FVTB
    'apps.ami_rtm',           # Modul 8: Rapat Tinjauan Manajemen
    'apps.ami_dashboard',     # Modul 9: Dashboard Analytics
    'apps.ami_pelaporan',     # Modul 10: Bundle BAN-PT, Laporan
    'apps.ami_user',          # Modul 11: User Management
    'apps.ami_arsip',         # Modul 12: Arsip & Retensi
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_htmx.middleware.HtmxMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'axes.middleware.AxesMiddleware',  # Harus di urutan terakhir
]

ROOT_URLCONF = 'ami_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'ami_project.wsgi.application'
ASGI_APPLICATION = 'ami_project.asgi.application'  # Untuk WebSocket (Modul 8 RTM)


# ============================================
# DATABASE
# PostgreSQL dedicated per-app (container sendiri), mengikuti pola
# deployment Docker siobe/alumni — bukan schema bersama di unisan_db.
# ============================================

DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE', default='django.db.backends.postgresql'),
        'NAME': config('DB_NAME', default='siami'),
        'USER': config('DB_USER', default='siami'),
        'PASSWORD': config('DB_PASSWORD', default=''),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
        'CONN_MAX_AGE': 60,
    }
}


# ============================================
# AUTHENTICATION
# ============================================

AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',  # Harus di urutan pertama
    'django.contrib.auth.backends.ModelBackend',
]

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8},
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# ============================================
# DJANGO-AXES (Brute Force Protection)
# ============================================

AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 1  # 1 jam lockout
AXES_LOCKOUT_PARAMETERS = ['username', 'ip_address']
AXES_RESET_ON_SUCCESS = True


# ============================================
# REST FRAMEWORK & API DOCUMENTATION
# ============================================

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'SI-AMI UNISAN API',
    'DESCRIPTION': 'API REST untuk Sistem Audit Mutu Internal Universitas Ichsan Gorontalo',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'CONTACT': {
        'name': 'LP3M UNISAN',
        'email': 'lp3m@unisan-g.id',
    },
}


# ============================================
# INTERNATIONALIZATION
# Sesuai Catatan Teknis Bab 6.4
# ============================================

LANGUAGE_CODE = 'id'  # Bahasa Indonesia
TIME_ZONE = 'Asia/Makassar'  # WITA - Gorontalo
USE_I18N = True
USE_TZ = True


# ============================================
# STATIC FILES (CSS, JavaScript, Images)
# ============================================

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# WhiteNoise compression untuk production
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# ============================================
# MEDIA FILES (Upload dari user)
# ============================================

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# File upload limits
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5 MB (sesuai standar UNISAN)
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5 MB


# ============================================
# DEFAULT PRIMARY KEY
# ============================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ============================================
# SESSION & SECURITY
# ============================================

SESSION_COOKIE_AGE = 7200  # 2 jam (sesuai standar UNISAN Bab 6.2)
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_HTTPONLY = True


# ============================================
# CORS HEADERS (untuk API integration)
# ============================================

CORS_ALLOWED_ORIGINS = [
    'https://portal.unisan-g.id',
    'https://kinerja.unisan-g.id',
    'https://akreditasi.unisan-g.id',
]
CORS_ALLOW_CREDENTIALS = True


# ============================================
# CHANNELS (WebSocket untuk Modul 8 RTM)
# ============================================

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
        # Production akan pakai Redis
    },
}


# ============================================
# DEBUG TOOLBAR
# ============================================

INTERNAL_IPS = ['127.0.0.1']


# ============================================
# CUSTOM SI-AMI SETTINGS
# ============================================

# SSO Configuration (akan dikonfigurasi setelah Portal SSO siap)
SSO_BASE_URL = config('SSO_BASE_URL', default='https://portal.unisan-g.id')
SSO_TOKEN_VERIFY_ENDPOINT = '/api/v1/verify/'
SSO_LOGIN_ENDPOINT = '/login/'
SSO_LOGOUT_ENDPOINT = '/logout/'

# AMI Custom Settings
AMI_SIKLUS_AKTIF = 8  # Siklus AMI 2025/2026
AMI_VERSION = '1.0.0'

# ============================================
# EMAIL BACKEND (akan dikonfigurasi via .env)
# ============================================
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')