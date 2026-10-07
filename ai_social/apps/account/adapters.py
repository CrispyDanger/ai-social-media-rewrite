from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model
from django.utils.text import slugify


class AccountAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form, commit=True):
        user = super().save_user(request, user, form, commit=False)
        display_name = self._display_name_from(form, user.username)
        if display_name:
            user.display_name = display_name[:50]
        if commit:
            user.save()
        return user

    def _display_name_from(self, form, username):
        cleaned = getattr(form, 'cleaned_data', None) or {}
        name = (cleaned.get('display_name') or '').strip()
        return name or username


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_open_for_signup(self, request, sociallogin):
        return True

    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        if not user.username:
            user.username = self._unique_handle(data)
        if not getattr(user, 'display_name', ''):
            user.display_name = self._display_name_from(data, user.username)
        return user

    def _display_name_from(self, data, username):
        name = (data.get('name') or '').strip()
        if name:
            return name[:50]
        full = self._full_name(data)
        return (full or username)[:50]

    def _full_name(self, data):
        first = (data.get('first_name') or '').strip()
        last = (data.get('last_name') or '').strip()
        return f'{first} {last}'.strip()

    def _unique_handle(self, data):
        email = data.get('email') or ''
        local_part = email.split('@')[0] if email else ''
        base = self._sanitize_handle(local_part) or 'user'
        return self._allocate_handle(base)

    def _sanitize_handle(self, value):
        slug = slugify(value).replace('-', '_')
        cleaned = ''.join(ch for ch in slug if ch.isalnum() or ch == '_')
        return cleaned[:15]

    def _allocate_handle(self, base):
        user_model = get_user_model()
        candidate = base[:15]
        suffix = 1
        while user_model.objects.filter(username__iexact=candidate).exists():
            suffix_text = str(suffix)
            candidate = f'{base[:15 - len(suffix_text)]}{suffix_text}'
            suffix += 1
        return candidate
