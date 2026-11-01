from datetime import timedelta
from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone

from ai_social.celery import app as celery_app
from apps.bots.services.scheduling import COUNTDOWN_MAX_SECONDS, enqueue_due_turns, turn_lock_key
from apps.bots.services.turns import run_scheduled_turn
from apps.bots.tasks import run_bot_turn
from apps.bots.tests.helpers import create_bot
from apps.feed.tests.helpers import create_post, create_user, follow
from apps.interaction.models import Like

CHOOSE_REACTIONS = 'apps.bots.services.generation.generation.choose_reactions'
WRITE_POST = 'apps.bots.services.turns.write_post'
APPLY_ASYNC = 'apps.bots.tasks.run_bot_turn.apply_async'
RANDINT = 'apps.bots.services.scheduling.random.randint'


class ScheduleBotTurnsTests(TestCase):
    def setUp(self):
        cache.clear()
        self.now = timezone.now()
        self.bot = create_bot('bot')

    def test_beat_runs_every_minute(self):
        entry = celery_app.conf.beat_schedule['bots-schedule-turns']
        self.assertEqual(entry['task'], 'apps.bots.tasks.schedule_bot_turns')
        self.assertEqual(entry['schedule'], 60.0)

    @patch(RANDINT, return_value=50)
    @patch(APPLY_ASYNC)
    def test_enqueues_due_bot_with_countdown_and_locks_it(self, apply_async, randint):
        with patch('apps.bots.services.scheduling.cache.add', wraps=cache.add) as add:
            enqueue_due_turns(self.now)
        apply_async.assert_called_once_with((self.bot.pk,), countdown=50)
        randint.assert_called_once_with(0, COUNTDOWN_MAX_SECONDS)
        add.assert_called_once_with(turn_lock_key(self.bot.pk), 1, COUNTDOWN_MAX_SECONDS)
        self.assertEqual(cache.get(turn_lock_key(self.bot.pk)), 1)

    @patch(RANDINT, return_value=0)
    @patch(APPLY_ASYNC)
    def test_countdown_can_be_zero(self, apply_async, randint):
        enqueue_due_turns(self.now)
        apply_async.assert_called_once_with((self.bot.pk,), countdown=0)

    @patch(APPLY_ASYNC)
    def test_skips_bot_reserved_for_a_countdown(self, apply_async):
        cache.add(turn_lock_key(self.bot.pk), 1, COUNTDOWN_MAX_SECONDS)
        enqueue_due_turns(self.now)
        apply_async.assert_not_called()

    @patch(RANDINT, return_value=10)
    @patch(APPLY_ASYNC)
    def test_queues_again_when_the_lock_is_gone(self, apply_async, randint):
        cache.add(turn_lock_key(self.bot.pk), 1, COUNTDOWN_MAX_SECONDS)
        cache.delete(turn_lock_key(self.bot.pk))
        enqueue_due_turns(self.now)
        apply_async.assert_called_once_with((self.bot.pk,), countdown=10)

    @patch(APPLY_ASYNC)
    def test_skips_bot_on_cooldown_or_over_the_daily_limit(self, apply_async):
        self.bot.last_action_at = self.now
        self.bot.save(update_fields=['last_action_at'])
        enqueue_due_turns(self.now)
        self.bot.last_action_at = None
        self.bot.daily_action_limit = 1
        self.bot.save(update_fields=['last_action_at', 'daily_action_limit'])
        create_post(self.bot.user)
        enqueue_due_turns(self.now)
        apply_async.assert_not_called()


class RunBotTurnTests(TestCase):
    def setUp(self):
        cache.clear()
        self.bot = create_bot('bot')
        self.human = create_user('human')

    def test_missing_persona_is_ignored(self):
        run_bot_turn(0)

    @patch(WRITE_POST)
    def test_blocked_bot_releases_reservation_without_acting(self, write_post):
        self.bot.is_active = False
        self.bot.save(update_fields=['is_active'])
        cache.add(turn_lock_key(self.bot.pk), 1, COUNTDOWN_MAX_SECONDS)
        run_scheduled_turn(self.bot)
        write_post.assert_not_called()
        self.assertIsNone(cache.get(turn_lock_key(self.bot.pk)))
        self.bot.refresh_from_db()
        self.assertIsNone(self.bot.last_action_at)

    @patch(WRITE_POST)
    def test_writes_original_post_when_nobody_addressed_the_bot(self, write_post):
        run_scheduled_turn(self.bot)
        write_post.assert_called_once_with(self.bot)
        self.bot.refresh_from_db()
        self.assertIsNotNone(self.bot.last_action_at)

    @patch(CHOOSE_REACTIONS)
    @patch(WRITE_POST)
    def test_timeline_posts_do_not_replace_an_original_post(self, write_post, choose_reactions):
        follow(self.bot.user, self.human)
        create_post(self.human, text='just chatting', space=self.bot.space)
        run_scheduled_turn(self.bot)
        write_post.assert_called_once_with(self.bot)
        choose_reactions.assert_not_called()

    @patch(CHOOSE_REACTIONS, return_value=set())
    @patch(WRITE_POST)
    def test_mention_starts_cooldown_even_when_nothing_is_published(self, write_post, choose_reactions):
        cache.add(turn_lock_key(self.bot.pk), 1, COUNTDOWN_MAX_SECONDS)
        create_post(self.human, text='hey @BOT')
        run_scheduled_turn(self.bot)
        write_post.assert_not_called()
        choose_reactions.assert_called_once()
        self.bot.refresh_from_db()
        self.assertIsNotNone(self.bot.last_action_at)
        self.assertIsNone(cache.get(turn_lock_key(self.bot.pk)))
        self.assertFalse(Like.objects.filter(user=self.bot.user).exists())

    @patch(CHOOSE_REACTIONS, return_value={'like'})
    @patch(WRITE_POST)
    def test_reply_and_mention_are_judged_case_insensitively(self, write_post, choose_reactions):
        bot_post = create_post(self.bot.user, text='thoughts')
        reply = create_post(self.human, text='nice', parent=bot_post)
        mention = create_post(self.human, text='hey @BOT')
        run_scheduled_turn(self.bot)
        write_post.assert_not_called()
        judged = {call.args[1].pk for call in choose_reactions.call_args_list}
        self.assertEqual(judged, {reply.pk, mention.pk})
        self.assertEqual(Like.objects.filter(user=self.bot.user).count(), 2)

    @patch(CHOOSE_REACTIONS, return_value={'like'})
    @patch(WRITE_POST)
    def test_reaction_turn_includes_human_timeline_once(self, write_post, choose_reactions):
        other = create_user('other')
        other_bot = create_bot('other_bot')
        follow(self.bot.user, self.human)
        follow(self.bot.user, other)
        follow(self.bot.user, other_bot.user)
        mention = create_post(self.human, text='@bot hey', space=self.bot.space)
        timeline = create_post(other, text='practice was good', space=self.bot.space)
        create_post(other_bot.user, text='bot chatter', space=self.bot.space)
        run_scheduled_turn(self.bot)
        write_post.assert_not_called()
        judged = [call.args[1].pk for call in choose_reactions.call_args_list]
        self.assertEqual(sorted(judged), sorted({mention.pk, timeline.pk}))

    @patch(CHOOSE_REACTIONS, return_value={'like'})
    def test_finishes_reactions_past_the_daily_limit(self, choose_reactions):
        self.bot.daily_action_limit = 1
        self.bot.save(update_fields=['daily_action_limit'])
        create_post(self.human, text='@bot one')
        create_post(self.human, text='@bot two')
        run_scheduled_turn(self.bot)
        self.assertEqual(Like.objects.filter(user=self.bot.user).count(), 2)

    @patch(CHOOSE_REACTIONS, return_value={'like'})
    @patch(WRITE_POST)
    def test_ignores_emails_and_handles_that_only_share_a_prefix(self, write_post, choose_reactions):
        create_post(self.human, text='mail me@bot.com and @bot_extra')
        run_scheduled_turn(self.bot)
        choose_reactions.assert_not_called()
        write_post.assert_called_once_with(self.bot)

    @patch(CHOOSE_REACTIONS, return_value={'like'})
    @patch(WRITE_POST)
    def test_ignores_bots_and_posts_from_before_the_last_action(self, write_post, choose_reactions):
        now = timezone.now()
        other_bot = create_bot('other_bot')
        create_post(other_bot.user, text='@bot from a bot')
        create_post(self.human, text='@bot too old', created_at=now - timedelta(hours=2))
        self.bot.last_action_at = now - timedelta(seconds=self.bot.cooldown_seconds)
        self.bot.save(update_fields=['last_action_at'])
        run_scheduled_turn(self.bot)
        choose_reactions.assert_not_called()
        write_post.assert_called_once_with(self.bot)


class PostSaveDoesNotQueueBotsTests(TestCase):
    @patch(APPLY_ASYNC)
    def test_creating_a_post_does_not_queue_a_bot_turn(self, apply_async):
        bot = create_bot('bot')
        human = create_user('human')
        bot_post = create_post(bot.user, text='thoughts')
        create_post(human, text='@bot hey', parent=bot_post)
        apply_async.assert_not_called()
