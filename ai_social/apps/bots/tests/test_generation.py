from unittest.mock import patch

from django.test import TestCase
from pydantic_ai.messages import ModelResponse, ToolCallPart
from pydantic_ai.models.function import AgentInfo, FunctionModel
from pydantic_ai.models.test import TestModel

from apps.bots.services.generation import schemas
from apps.bots.services.generation.generation import generate_post, react_to_post
from apps.bots.tests.helpers import create_bot
from apps.feed.tests.helpers import create_post, create_user
from apps.interaction.models import Like
from apps.post.models import Post

BUILD_MODEL = 'apps.bots.services.generation.generation.build_model'
CHOOSE_REACTIONS = 'apps.bots.services.generation.generation.choose_reactions'


class GeneratePostTests(TestCase):
    def setUp(self):
        self.bot = create_bot('bot')

    def test_publishes_generated_text(self):
        model = TestModel(custom_output_args={'text': 'hello world'})
        with patch(BUILD_MODEL, return_value=model):
            post = generate_post(self.bot)
        self.assertEqual((post.author_id, post.text), (self.bot.user_id, 'hello world'))

    def test_skips_when_guard_blocks(self):
        self.bot.is_active = False
        with patch(BUILD_MODEL) as build_model:
            self.assertIsNone(generate_post(self.bot))
        build_model.assert_not_called()
        self.assertFalse(Post.objects.filter(author=self.bot.user).exists())


class ReactToPostTests(TestCase):
    def setUp(self):
        self.bot = create_bot('bot')
        self.post = create_post(create_user('human'), text='@bot thoughts?')

    def test_reply_creates_generated_reply(self):
        model = TestModel(custom_output_args={'text': 'sure'})
        with patch(CHOOSE_REACTIONS, return_value={'reply'}), patch(BUILD_MODEL, return_value=model):
            decisions = react_to_post(self.bot, self.post)
        self.assertEqual(decisions, [schemas.Reply(text='sure')])
        self.assertTrue(Post.objects.filter(parent=self.post, author=self.bot.user).exists())

    def test_like_creates_like_without_llm(self):
        with patch(CHOOSE_REACTIONS, return_value={'like'}), patch(BUILD_MODEL) as build_model:
            react_to_post(self.bot, self.post)
        build_model.assert_not_called()
        self.assertTrue(Like.objects.filter(user=self.bot.user, post=self.post).exists())

    def test_like_and_reply_together(self):
        model = TestModel(custom_output_args={'text': 'so true'})
        with patch(CHOOSE_REACTIONS, return_value={'like', 'reply'}), \
                patch(BUILD_MODEL, return_value=model):
            decisions = react_to_post(self.bot, self.post)
        self.assertEqual(decisions, [schemas.Like(), schemas.Reply(text='so true')])
        self.assertTrue(Like.objects.filter(user=self.bot.user, post=self.post).exists())
        self.assertTrue(Post.objects.filter(parent=self.post, author=self.bot.user).exists())

    def test_no_actions_does_nothing(self):
        with patch(CHOOSE_REACTIONS, return_value=set()):
            self.assertEqual(react_to_post(self.bot, self.post), [])
        self.assertFalse(Post.objects.filter(parent=self.post).exists())
        self.assertFalse(Like.objects.filter(post=self.post).exists())

    def test_judge_not_called_when_guard_blocks(self):
        self.bot.is_active = False
        with patch(CHOOSE_REACTIONS) as choose_reactions:
            self.assertIsNone(react_to_post(self.bot, self.post))
        choose_reactions.assert_not_called()

    def test_persona_prompt_is_sent_as_reply_instructions(self):
        captured = {}

        def respond(messages, info: AgentInfo) -> ModelResponse:
            captured['instructions'] = info.instructions
            tool_name = info.output_tools[0].name
            return ModelResponse(parts=[ToolCallPart(tool_name, {'text': 'hi'})])

        with patch(CHOOSE_REACTIONS, return_value={'reply'}), \
                patch(BUILD_MODEL, return_value=FunctionModel(respond)):
            react_to_post(self.bot, self.post)
        self.assertIn(self.bot.persona_prompt, captured['instructions'])
