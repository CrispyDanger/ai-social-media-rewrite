import json
import logging
from typing import Any, Literal

import httpx
from django.conf import settings
from pydantic import BaseModel

logger = logging.getLogger(__name__)

JUDGE_TIMEOUT_SECONDS = 30


class NoulCriteria(BaseModel):
    true: str
    false: str


class NoulQuestion(BaseModel):
    type: Literal['noul'] = 'noul'
    instructions: str
    criteria: NoulCriteria


class NoulAnswer(BaseModel):
    type: Literal['noul']
    noul: float


class DecisionResponse(BaseModel):
    answers: dict[str, NoulAnswer]


def decide(state: dict[str, Any], questions: dict[str, NoulQuestion]) -> dict[str, NoulAnswer]:
    payload = {
        'model': settings.BOT_LLM_JUDGE,
        'state': state,
        'questions': {key: question.model_dump() for key, question in questions.items()},
    }
    logger.debug('Judge prompt:\n%s', json.dumps(payload, indent=2))
    response = httpx.post(
        settings.BOT_LLM_JUDGE_API_URL,
        headers={'Authorization': f'Bearer {settings.OPENROUTER_API_KEY}'},
        json=payload,
        timeout=JUDGE_TIMEOUT_SECONDS,
    )
    logger.debug('Judge response:\n%s', response.text)
    response.raise_for_status()
    return DecisionResponse.model_validate(response.json()).answers
