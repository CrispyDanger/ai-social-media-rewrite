from unittest.mock import call, patch

from django.test import TestCase

from apps.bots.tests.helpers import create_bot
from apps.feed.tests.helpers import create_post, create_user


@patch('apps.bots.signals.react_to_post.delay')
class ScheduleBotReactionsTests(TestCase):
    def setUp(self):
        self.bot = create_bot('Bot')
        self.human = create_user('human')

    def _create_post(self, **kwargs):
        with self.captureOnCommitCallbacks(execute=True):
            return create_post(**kwargs)

    def test_reply_to_bot_post_enqueues_reaction(self, delay):
        bot_post = create_post(self.bot.user, text='bot thoughts')
        reply = self._create_post(author=self.human, text='nice', parent=bot_post)
        delay.assert_called_once_with(self.bot.pk, reply.pk)

    def test_mention_is_case_insensitive(self, delay):
        post = self._create_post(author=self.human, text='hey @BOT what do you think?')
        delay.assert_called_once_with(self.bot.pk, post.pk)

    def test_multiple_bots_are_targeted(self, delay):
        other = create_bot('other')
        post = self._create_post(author=self.human, text='@bot @other hi')
        delay.assert_has_calls([call(self.bot.pk, post.pk), call(other.pk, post.pk)], any_order=True)

    def test_posts_by_bots_are_ignored(self, delay):
        create_bot('other')
        self._create_post(author=self.bot.user, text='hey @other')
        delay.assert_not_called()

    def test_inactive_bots_are_ignored(self, delay):
        self.bot.is_active = False
        self.bot.save()
        self._create_post(author=self.human, text='@bot hi')
        delay.assert_not_called()

    def test_plain_post_enqueues_nothing(self, delay):
        self._create_post(author=self.human, text='hello world')
        delay.assert_not_called()
