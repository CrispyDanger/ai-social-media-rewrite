import logging

from apps.bots.models import BotPersona
from apps.bots.services.context.context import build_post_prompt, build_reply_prompt
from apps.bots.services.generation import schemas
from apps.bots.services.generation.actions import execute_decisions, publish_post
from apps.bots.services.generation.agents import post_agent, reply_agent
from apps.bots.services.guards import can_act, should_react
from apps.bots.services.judge.reaction_judge import ReactionAction, choose_reactions
from apps.llm.services.model import build_model
from apps.post.models import Post

logger = logging.getLogger(__name__)

SILENT_DECISIONS: dict[ReactionAction, schemas.Decision] = {
    'like': schemas.Like(),
    'repost': schemas.Repost(),
}


def generate_post(persona: BotPersona) -> Post | None:
    if not can_act(persona):
        return None
    result = post_agent.run_sync(build_post_prompt(persona), deps=persona, model=build_model())
    logger.info('Bot %s generated a post, usage=%s', persona.user_id, result.usage)
    return publish_post(persona, result.output.text)


def react_to_post(persona: BotPersona, post: Post) -> list[schemas.Decision] | None:
    if not (can_act(persona) and should_react(persona, post)):
        return None
    actions = choose_reactions(persona, post)
    decisions: list[schemas.Decision] = [
        decision for action, decision in SILENT_DECISIONS.items() if action in actions
    ]
    if 'reply' in actions:
        result = reply_agent.run_sync(build_reply_prompt(persona, post), deps=persona, model=build_model())
        logger.info('Bot %s wrote a reply to post %s, usage=%s', persona.user_id, post.pk, result.usage)
        decisions.append(result.output)
    logger.info('Bot %s reacted to post %s with %s', persona.user_id, post.pk,
                [type(decision).__name__ for decision in decisions] or 'nothing')
    execute_decisions(persona, post, decisions)
    return decisions
