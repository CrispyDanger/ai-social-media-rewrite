"""
Shared Django settings for all environments.
"""
import sys
from pathlib import Path

from datetime import timedelta

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

sys.path.append(str(BASE_DIR / 'ai_social'))

env = environ.Env(
    DEBUG=(bool, False),
    EMAIL_PORT=(int, 587),
    EMAIL_USE_TLS=(bool, True),
    EMAIL_HOST_USER=(str, ''),
    EMAIL_HOST_PASSWORD=(str, ''),
    DEFAULT_FROM_EMAIL=(str, 'webmaster@localhost'),
    GOOGLE_OAUTH_CALLBACK_URL=(str, 'http://localhost:3000/auth/google/callback'),
    GOOGLE_CLIENT_ID=(str, ''),
    GOOGLE_CLIENT_SECRET=(str, ''),
)

environ.Env.read_env(BASE_DIR / '.env')


# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
]

LOCAL_APPS = [
    'apps.core',
    'apps.account',
    'apps.post',
    'apps.space',
    'apps.interaction',
    'apps.feed',
    'apps.llm',
    'apps.bots',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'dj_rest_auth',
    'dj_rest_auth.registration',
]

INSTALLED_APPS = DJANGO_APPS + LOCAL_APPS + THIRD_PARTY_APPS


MIDDLEWARE = [
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

ROOT_URLCONF = 'ai_social.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'ai_social.wsgi.application'


# Database
# https://docs.djangoproject.com/en/6.1/ref/settings/#databases

DATABASES = {
    'default': env.db(
        'DATABASE_URL',
        default='postgres://postgres:postgres@localhost:5432/ai_twitter',
    ),
}


# Password validation
# https://docs.djangoproject.com/en/6.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/6.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

CELERY_BROKER_URL = env('REDIS_URL', default='redis://127.0.0.1:6379/0')
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULE = {
    'bots-schedule-posts': {
        'task': 'apps.bots.tasks.schedule_bot_posts',
        'schedule': env.int('BOT_POST_INTERVAL_SECONDS', default=60 * 30),
    },
}

OPENROUTER_API_KEY = env('OPENROUTER_API_KEY', default='')
BOT_LLM_MODEL = env('BOT_LLM_MODEL', default='nvidia/nemotron-3-super-120b-a12b:free')
BOT_LLM_JUDGE = env('BOT_LLM_JUDGE', default='typesafe/jev-1.13')
BOT_LLM_JUDGE_API_URL = env('BOT_LLM_JUDGE_API_URL', default='https://openrouter.ai/api/alpha/decisions')
BOT_JUDGE_MIN_CONFIDENCE = env.float('BOT_JUDGE_MIN_CONFIDENCE', default=0.2)
BOT_MAX_THREAD_DEPTH = env.int('BOT_MAX_THREAD_DEPTH', default=6)


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.1/ref/settings/#static-files

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

GOOGLE_OAUTH_CALLBACK_URL = env('GOOGLE_OAUTH_CALLBACK_URL')

from .auth import *  # noqa: E402, F403

SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'] = timedelta(  # noqa: F405
    minutes=env.int('JWT_ACCESS_TOKEN_LIFETIME_MINUTES', default=15),
)
SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'] = timedelta(  # noqa: F405
    days=env.int('JWT_REFRESH_TOKEN_LIFETIME_DAYS', default=7),
)
ACCOUNT_EMAIL_VERIFICATION = env('ACCOUNT_EMAIL_VERIFICATION', default='optional')  # noqa: F405

if env('GOOGLE_CLIENT_ID') and env('GOOGLE_CLIENT_SECRET'):
    SOCIALACCOUNT_PROVIDERS['google'] = {  # noqa: F405
        'APP': {
            'client_id': env('GOOGLE_CLIENT_ID'),
            'secret': env('GOOGLE_CLIENT_SECRET'),
            'key': '',
        },
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
    }
