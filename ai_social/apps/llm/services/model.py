from functools import cache

from django.conf import settings
from pydantic_ai.models.openrouter import OpenRouterModel
from pydantic_ai.providers.openrouter import OpenRouterProvider


@cache
def build_model() -> OpenRouterModel:
    provider = OpenRouterProvider(api_key=settings.OPENROUTER_API_KEY or None)
    return OpenRouterModel(settings.BOT_LLM_MODEL, provider=provider)
