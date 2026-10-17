from unittest.mock import patch

from django.test import TestCase, override_settings

from apps.bots.services.judge.reaction_judge import REACTION_QUESTIONS, choose_reactions
from apps.bots.tests.helpers import create_bot
from apps.feed.tests.helpers import create_post, create_user
from apps.llm.services.judge import NoulAnswer

DECIDE = 'apps.bots.services.judge.reaction_judge.judge.decide'


def judged(reply=0.0, like=0.0, repost=0.0):
    return {
        'reply': NoulAnswer(type='noul', noul=reply),
        'like': NoulAnswer(type='noul', noul=like),
        'repost': NoulAnswer(type='noul', noul=repost),
    }


@override_settings(BOT_JUDGE_MIN_CONFIDENCE=0.5)
class ChooseReactionsTests(TestCase):
    def setUp(self):
        self.bot = create_bot('bot')
        self.post = create_post(create_user('human'), text='@bot thoughts?')

    def test_returns_every_action_above_threshold(self):
        with patch(DECIDE, return_value=judged(reply=0.9, like=0.7, repost=0.2)):
            self.assertEqual(choose_reactions(self.bot, self.post), {'reply', 'like'})

    def test_returns_nothing_when_all_below_threshold(self):
        with patch(DECIDE, return_value=judged(reply=0.4, like=0.3, repost=0.1)):
            self.assertEqual(choose_reactions(self.bot, self.post), set())

    def test_asks_all_questions_with_persona_and_thread(self):
        with patch(DECIDE, return_value=judged()) as decide:
            choose_reactions(self.bot, self.post)
        state, questions = decide.call_args.args
        self.assertEqual(questions, REACTION_QUESTIONS)
        self.assertIn('Who they are (@bot):\n' + self.bot.persona_prompt, state['situation'])
        self.assertIn('>>> @human: @bot thoughts?', state['situation'])
