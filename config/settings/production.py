"""
Production settings. Requires environment variables for secrets and SMTP.
"""

from .base import *  # noqa: F403
from .base import env

SECRET_KEY = env('SECRET_KEY')

DEBUG = False
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')

# Email
# https://docs.djangoproject.com/en/6.1/topics/email/#topic-email-configuration

MAILERS = {
    'default': {
        'BACKEND': 'django.core.mail.backends.smtp.EmailBackend',
        'OPTIONS': {
            'host': env('EMAIL_HOST'),
            'port': env('EMAIL_PORT'),
            'username': env('EMAIL_HOST_USER'),
            'password': env('EMAIL_HOST_PASSWORD'),
            'use_tls': env('EMAIL_USE_TLS'),
        },
    },
}

DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL')
