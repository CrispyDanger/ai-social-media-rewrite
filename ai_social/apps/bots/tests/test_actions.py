from django.test import TestCase

from apps.bots.services.generation import schemas
from apps.bots.services.generation.actions import execute_decisions, publish_post
from apps.bots.tests.helpers import create_bot
from apps.feed.tests.helpers import create_post, create_space, create_user
from apps.interaction.models import Like
from apps.post.models import Post, Repost


class ExecuteDecisionsTests(TestCase):
    def setUp(self):
        self.bot = create_bot('bot')
        self.post = create_post(create_user('human'), text='hello bots')

    def test_reply_creates_child_post(self):
        execute_decisions(self.bot, self.post, [schemas.Reply(text='hi human')])
        reply = Post.objects.get(parent=self.post)
        self.assertEqual((reply.author_id, reply.text), (self.bot.user_id, 'hi human'))
        self.assertIsNotNone(self.bot.last_action_at)

    def test_reply_inherits_space(self):
        space = create_space(self.post.author)
        self.post.space = space
        self.post.save()
        execute_decisions(self.bot, self.post, [schemas.Reply(text='hi')])
        self.assertEqual(Post.objects.get(parent=self.post).space_id, space.id)

    def test_like_is_idempotent(self):
        execute_decisions(self.bot, self.post, [schemas.Like()])
        execute_decisions(self.bot, self.post, [schemas.Like()])
        self.assertEqual(Like.objects.filter(user=self.bot.user, post=self.post).count(), 1)

    def test_repost_is_idempotent(self):
        execute_decisions(self.bot, self.post, [schemas.Repost()])
        execute_decisions(self.bot, self.post, [schemas.Repost()])
        self.assertEqual(Repost.objects.filter(author=self.bot.user, post=self.post).count(), 1)

    def test_applies_every_decision(self):
        execute_decisions(self.bot, self.post, [schemas.Like(), schemas.Reply(text='agreed')])
        self.assertTrue(Like.objects.filter(user=self.bot.user, post=self.post).exists())
        self.assertTrue(Post.objects.filter(parent=self.post, author=self.bot.user).exists())

    def test_empty_decisions_do_nothing(self):
        execute_decisions(self.bot, self.post, [])
        self.assertFalse(Post.objects.filter(parent=self.post).exists())
        self.assertIsNone(self.bot.last_action_at)


class PublishPostTests(TestCase):
    def test_creates_post_and_marks_action(self):
        bot = create_bot('bot')
        post = publish_post(bot, 'fresh take')
        self.assertEqual((post.author_id, post.parent_id), (bot.user_id, None))
        self.assertIsNotNone(bot.last_action_at)
