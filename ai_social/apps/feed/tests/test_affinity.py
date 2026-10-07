from django.test import TestCase
from django.utils import timezone

from apps.feed.services.ranking import author_ids_user_interacts_often_with
from apps.feed.tests.helpers import (
    create_post,
    create_user,
    days_ago,
    like_post,
    repost_post,
)


class AffinityTests(TestCase):
    def setUp(self):
        self.now = timezone.now()
        self.viewer = create_user('viewer')
        self.author = create_user('author')

    def test_below_threshold_is_not_affinity(self):
        self._like_author_posts(count=2)
        self.assertNotIn(self.author.id, self._affinity_ids())

    def test_at_threshold_is_affinity(self):
        self._like_author_posts(count=3)
        self.assertIn(self.author.id, self._affinity_ids())

    def test_likes_reposts_and_replies_combine(self):
        post = create_post(self.author, text='one')
        like_post(self.viewer, post)
        other = create_post(self.author, text='two')
        repost_post(self.viewer, other)
        parent = create_post(self.author, text='parent')
        create_post(self.viewer, text='reply', parent=parent)
        self.assertIn(self.author.id, self._affinity_ids())

    def test_interactions_older_than_window_do_not_count(self):
        for index in range(3):
            post = create_post(self.author, text=f'old-{index}')
            like_post(self.viewer, post, created_at=days_ago(31, self.now))
        self.assertNotIn(self.author.id, self._affinity_ids())

    def test_self_replies_are_ignored(self):
        own_post = create_post(self.viewer, text='own')
        create_post(self.viewer, text='self-reply', parent=own_post)
        create_post(self.viewer, text='self-reply-2', parent=own_post)
        create_post(self.viewer, text='self-reply-3', parent=own_post)
        self.assertNotIn(self.viewer.id, self._affinity_ids())

    def _like_author_posts(self, count):
        for index in range(count):
            post = create_post(self.author, text=f'post-{index}')
            like_post(self.viewer, post)

    def _affinity_ids(self):
        return author_ids_user_interacts_often_with(self.viewer, now=self.now)
