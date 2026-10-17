from pydantic_ai import Agent, RunContext

from apps.bots.models import BotPersona
from apps.bots.services.generation import schemas

BASE_INSTRUCTIONS = (
    'You are a user of a short-form social network similar to Twitter. '
    'Stay in character, write casually like a real person, and never mention being an AI. '
    f'Every post or reply must be at most {schemas.POST_MAX_LENGTH} characters.'
)

post_agent = Agent(
    name='bot_post',
    deps_type=BotPersona,
    output_type=schemas.NewPost,
    instructions=BASE_INSTRUCTIONS,
)

reply_agent = Agent(
    name='bot_reply',
    deps_type=BotPersona,
    output_type=schemas.Reply,
    instructions=BASE_INSTRUCTIONS,
)


def persona_instructions(ctx: RunContext[BotPersona]) -> str:
    return f'Your persona:\n{ctx.deps.persona_prompt}'


post_agent.instructions(persona_instructions)
reply_agent.instructions(persona_instructions)
