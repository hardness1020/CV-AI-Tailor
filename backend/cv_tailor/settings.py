"""
Django settings for cv_tailor project.
"""

import os
from pathlib import Path
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Security settings
SECRET_KEY = config('SECRET_KEY', default='django-insecure-placeholder-key-for-development')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=lambda v: [s.strip() for s in v.split(',')])

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    # 'django_ratelimit',
    'django_extensions',
    # Django-allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    # Project apps
    'accounts',
    'artifacts',
    'generation',
    'export',
    # Enhanced LLM services
    'llm_services',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'cv_tailor.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'cv_tailor.wsgi.application'

# Database Configuration
DB_ENGINE = config('DB_ENGINE', default='sqlite')

if DB_ENGINE == 'postgresql':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME', default='cv_tailor'),
            'USER': config('DB_USER', default='cv_tailor_user'),
            'PASSWORD': config('DB_PASSWORD', default='cv_tailor_dev_password'),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='5432', cast=int),
            'OPTIONS': {
                'connect_timeout': 10,
            },
        }
    }
else:
    # Default SQLite configuration for backward compatibility
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom user model
AUTH_USER_MODEL = 'accounts.User'

# REST Framework configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FileUploadParser',
    ]
}

# JWT Configuration
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

# CORS Configuration
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
]

# Cache Configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Celery Configuration
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

# File Upload Settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB

# Enhanced AI/LLM Settings (2025)
OPENAI_API_KEY = config('OPENAI_API_KEY', default='')
ANTHROPIC_API_KEY = config('ANTHROPIC_API_KEY', default='')

# Model Selection Strategy
MODEL_SELECTION_STRATEGY = config('MODEL_SELECTION_STRATEGY', default='balanced')
TRACK_MODEL_PERFORMANCE = config('TRACK_MODEL_PERFORMANCE', default=True, cast=bool)
OPTIMIZE_FOR_COST = config('OPTIMIZE_FOR_COST', default=False, cast=bool)
OPTIMIZE_FOR_QUALITY = config('OPTIMIZE_FOR_QUALITY', default=False, cast=bool)

# Model Strategy Configurations
MODEL_STRATEGIES = {
    'cost_optimized': {
        'job_parsing_model': 'gpt-4o-mini',
        'cv_generation_model': 'gpt-4o',
        'embedding_model': 'text-embedding-3-small',
        'embedding_dimensions': 1536,
        'max_cost_per_generation': 0.05,  # $0.05 per CV
        'fallback_model': 'gpt-4o-mini'
    },
    'balanced': {
        'job_parsing_model': 'gpt-4o',
        'cv_generation_model': 'gpt-4o',
        'embedding_model': 'text-embedding-3-small',
        'embedding_dimensions': 1536,
        'max_cost_per_generation': 0.15,  # $0.15 per CV
        'fallback_model': 'claude-sonnet-4-20250514'
    },
    'quality_optimized': {
        'job_parsing_model': 'claude-sonnet-4-20250514',
        'cv_generation_model': 'claude-opus-4-1-20250805',
        'embedding_model': 'text-embedding-3-large',
        'embedding_dimensions': 3072,
        'max_cost_per_generation': 0.50,  # $0.50 per CV
        'fallback_model': 'claude-sonnet-4-20250514'
    },
    'experimental': {
        'job_parsing_model': 'claude-opus-4-1-20250805',
        'cv_generation_model': 'claude-opus-4-1-20250805',
        'embedding_model': 'text-embedding-3-large',
        'embedding_dimensions': 3072,
        'max_cost_per_generation': 1.00,  # $1.00 per CV
        'fallback_model': 'gpt-4o'
    }
}

# Model Performance & Cost Budgets
MODEL_BUDGETS = {
    'daily_budget_usd': config('DAILY_LLM_BUDGET', default=50.0, cast=float),
    'monthly_budget_usd': config('MONTHLY_LLM_BUDGET', default=1000.0, cast=float),
    'max_cost_per_user_daily': config('MAX_USER_DAILY_COST', default=5.0, cast=float),
    'cost_alert_threshold': 0.8  # Alert at 80% of budget
}

# LangChain Document Processing
LANGCHAIN_SETTINGS = {
    'chunk_size': config('LANGCHAIN_CHUNK_SIZE', default=1000, cast=int),
    'chunk_overlap': config('LANGCHAIN_CHUNK_OVERLAP', default=200, cast=int),
    'max_chunks_per_document': config('MAX_CHUNKS_PER_DOCUMENT', default=50, cast=int),
    'semantic_chunking_threshold': config('SEMANTIC_CHUNKING_THRESHOLD', default=0.8, cast=float)
}

# Circuit Breaker Settings
CIRCUIT_BREAKER_SETTINGS = {
    'failure_threshold': 5,
    'timeout_duration': 30,  # seconds
    'retry_attempts': 3
}

# GitHub API Settings
GITHUB_TOKEN = config('GITHUB_TOKEN', default='')

# Django-allauth configuration
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'OAUTH_PKCE_ENABLED': True,
        'FETCH_USERINFO': True,
    }
}

SOCIALACCOUNT_ADAPTER = 'accounts.adapters.CustomSocialAccountAdapter'
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_VERIFICATION = 'optional'
SOCIALACCOUNT_STORE_TOKENS = False

# Google OAuth credentials
GOOGLE_CLIENT_ID = config('GOOGLE_CLIENT_ID', default='')
GOOGLE_CLIENT_SECRET = config('GOOGLE_CLIENT_SECRET', default='')

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'cv_tailor.log',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'google_auth': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}