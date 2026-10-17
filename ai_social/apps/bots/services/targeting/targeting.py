from functools import reduce
from operator import or_

from django.db.models import Q
from django.db.models.functions import Lower

from apps.bots.models import BotPersona
from apps.bots.services.targeting.mentions import extract_handles
from apps.post.models import Post


def resolve_target_bot_ids(post: Post) -> set[int]:
    filters = []
    handles = extract_handles(post.text)
    if handles:
        filters.append(Q(username_lower__in=handles))
    if post.parent_id:
        filters.append(Q(user_id=post.parent.author_id))
    if not filters:
        return set()
    personas = (
        BotPersona.objects.filter(is_active=True)
        .annotate(username_lower=Lower('user__username'))
        .filter(reduce(or_, filters))
        .exclude(user_id=post.author_id)
    )
    return set(personas.values_list('id', flat=True))
