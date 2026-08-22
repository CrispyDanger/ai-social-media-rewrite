"""
Local development settings.
"""

from .base import *  # noqa: F403
from .base import env

SECRET_KEY = env(
    'SECRET_KEY',
    default='django-insecure-qtxtzf-46ffnqpz7gjh_09da$!)o$8h1^a#d_1movjs_l3rivf',
)

DEBUG = env.bool('DEBUG', default=True)

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])

WHITENOISE_USE_FINDERS = True

# Email
# https://docs.djangoproject.com/en/6.1/topics/email/#topic-email-configuration

MAILERS = {
    'default': {
        'BACKEND': 'django.core.mail.backends.console.EmailBackend',
    },
}
