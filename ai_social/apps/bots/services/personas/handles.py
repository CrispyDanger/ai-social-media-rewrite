import uuid

from django.contrib.auth import get_user_model
from django.utils.text import slugify

HANDLE_MAX_LENGTH = 15


def provision_bot_user(name: str):
    user_model = get_user_model()
    slug = slugify(name).replace('-', '_')
    base = (''.join(ch for ch in slug if ch.isalnum() or ch == '_') or 'bot')[:HANDLE_MAX_LENGTH]
    handle, suffix = base, 1
    while user_model.objects.filter(username__iexact=handle).exists():
        suffix_text = str(suffix)
        handle = f'{base[:HANDLE_MAX_LENGTH - len(suffix_text)]}{suffix_text}'
        suffix += 1
    user = user_model(
        email=f'bot-{uuid.uuid4().hex}@bots.invalid',
        username=handle,
        display_name=name.strip()[:50],
    )
    user.set_unusable_password()
    user.save()
    return user
