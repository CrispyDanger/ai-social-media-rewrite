from typing import Literal, cast

from django.conf import settings

from apps.bots.models import BotPersona
from apps.bots.services.context.context import render_section, render_situation
from apps.llm.services import judge
from apps.post.models import Post

ReactionAction = Literal['reply', 'like', 'repost']

TARGET = 'the post marked with >>> in the thread'

REACTION_QUESTIONS: dict[str, judge.NoulQuestion] = {
    'reply': judge.NoulQuestion(
        instructions=f'Given the persona, should this user reply to {TARGET}?',
        criteria=judge.NoulCriteria(
            true='The post asks them something or they have something in character to add.',
            false='They have nothing worth saying about it.',
        ),
    ),
    'like': judge.NoulQuestion(
        instructions=f'Given the persona, would this user like {TARGET}?',
        criteria=judge.NoulCriteria(
            true='They would enjoy or agree with the post.',
            false='They are indifferent to or disagree with the post.',
        ),
    ),
    'repost': judge.NoulQuestion(
        instructions=f'Given the persona, would this user share {TARGET} with their followers?',
        criteria=judge.NoulCriteria(
            true='The post is worth showing to their audience.',
            false='The post is not worth sharing.',
        ),
    ),
}


def choose_reactions(persona: BotPersona, post: Post) -> set[ReactionAction]:
    situation = (
        'You are deciding what a social media user does next.\n\n'
        f'{render_section(f"Who they are (@{persona.user.username})", persona.persona_prompt)}\n\n'
        f'{render_situation(persona, post)}'
    )
    answers = judge.decide({'situation': situation}, REACTION_QUESTIONS)
    threshold = settings.BOT_JUDGE_MIN_CONFIDENCE
    return {
        cast(ReactionAction, action)
        for action, answer in answers.items()
        if answer.noul >= threshold
    }
