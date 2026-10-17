from apps.bots.models import BotPersona
from apps.feed.tests.helpers import create_space, create_user


def create_bot(username, **persona_fields):
    persona_fields.setdefault('persona_prompt', f'{username} loves talking about Python.')
    persona_fields.setdefault('name', username)
    if 'owner' not in persona_fields:
        persona_fields['owner'] = create_user(f'o_{username}'[:15])
    if 'space' not in persona_fields:
        persona_fields['space'] = create_space(
            persona_fields['owner'],
            name=username,
            slug=username.lower(),
        )
    return BotPersona.objects.create(user=create_user(username), **persona_fields)
