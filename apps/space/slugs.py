from django.utils.text import slugify

from apps.space.models import Space

SLUG_MAX_LENGTH = 50


def unique_slug_for(name):
    base = _slug_base(name)
    slug = base
    suffix = 2
    while Space.objects.filter(slug__iexact=slug).exists():
        slug = _suffixed_slug(base, suffix)
        suffix += 1
    return slug


def _slug_base(name):
    return (slugify(name) or 'space')[:SLUG_MAX_LENGTH]


def _suffixed_slug(base, suffix):
    suffix_text = f'-{suffix}'
    return f'{base[:SLUG_MAX_LENGTH - len(suffix_text)]}{suffix_text}'
