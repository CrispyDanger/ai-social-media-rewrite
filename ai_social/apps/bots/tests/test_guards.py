from datetime import timedelta

from django.test import TestCase, override_settings
from django.utils import timezone

from apps.bots.services.guards import can_act, should_react
from apps.bots.tests.helpers import create_bot
from apps.feed.tests.helpers import create_post, create_user, days_ago, like_post


class CanActTests(TestCase):
    def setUp(self):
        self.bot = create_bot('bot', cooldown_seconds=300, daily_action_limit=2)

    def test_fresh_bot_can_act(self):
        self.assertTrue(can_act(self.bot))

    def test_inactive_bot_cannot_act(self):
        self.bot.is_active = False
        self.assertFalse(can_act(self.bot))

    def test_cooldown_blocks_until_elapsed(self):
        now = timezone.now()
        self.bot.last_action_at = now - timedelta(seconds=299)
        self.assertFalse(can_act(self.bot, now))
        self.bot.last_action_at = now - timedelta(seconds=300)
        self.assertTrue(can_act(self.bot, now))

    def test_daily_limit_counts_posts_and_likes(self):
        other_post = create_post(create_user('human'))
        create_post(self.bot.user)
        like_post(self.bot.user, other_post)
        self.assertFalse(can_act(self.bot))

    def test_actions_older_than_a_day_are_ignored(self):
        create_post(self.bot.user, created_at=days_ago(2))
        create_post(self.bot.user, created_at=days_ago(2))
        self.assertTrue(can_act(self.bot))


@override_settings(BOT_MAX_THREAD_DEPTH=2)
class ShouldReactTests(TestCase):
    def setUp(self):
        self.bot = create_bot('bot')
        self.human = create_user('human')

    def test_reacts_to_human_post(self):
        self.assertTrue(should_react(self.bot, create_post(self.human)))

    def test_ignores_own_post(self):
        self.assertFalse(should_react(self.bot, create_post(self.bot.user)))

    def test_ignores_other_bots(self):
        other_bot = create_bot('other_bot')
        self.assertFalse(should_react(self.bot, create_post(other_bot.user)))

    def test_ignores_threads_at_max_depth(self):
        root = create_post(self.human, text='root')
        first = create_post(self.human, text='first', parent=root)
        self.assertTrue(should_react(self.bot, first))
        second = create_post(self.human, text='second', parent=first)
        self.assertFalse(should_react(self.bot, second))
