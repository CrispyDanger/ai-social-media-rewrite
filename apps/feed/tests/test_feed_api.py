from rest_framework import status
from rest_framework.test import APITestCase

from apps.feed.tests.helpers import (
    create_post,
    create_user,
    days_ago,
    follow,
    hours_ago,
    like_post,
)


class FeedApiTests(APITestCase):
    def setUp(self):
        self.viewer = create_user('viewer')
        self.followed = create_user('followed')
        self.stranger = create_user('stranger')
        follow(self.viewer, self.followed)
        self.client.force_authenticate(user=self.viewer)

    def test_unauthenticated_for_you_is_unauthorized(self):
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/feed/for-you/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_following_is_unauthorized(self):
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/feed/following/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_following_includes_followed_and_own_newest_first(self):
        older = create_post(self.followed, text='older', created_at=hours_ago(3))
        own = create_post(self.viewer, text='own', created_at=hours_ago(2))
        newer = create_post(self.followed, text='newer', created_at=hours_ago(1))
        create_post(self.stranger, text='hidden')

        ids = self._ids('/api/feed/following/')
        self.assertEqual(ids, [newer.id, own.id, older.id])

    def test_following_omits_replies(self):
        parent = create_post(self.followed, text='parent')
        create_post(self.viewer, text='reply', parent=parent)
        ids = self._ids('/api/feed/following/')
        self.assertEqual(ids, [parent.id])

    def test_for_you_omits_viewer_own_posts(self):
        own = create_post(self.viewer, text='own')
        other = create_post(self.stranger, text='other')
        ids = self._ids('/api/feed/for-you/')
        self.assertIn(other.id, ids)
        self.assertNotIn(own.id, ids)

    def test_for_you_ranks_recent_engagement_above_stale(self):
        stale = create_post(self.stranger, text='stale', created_at=hours_ago(48))
        recent = create_post(self.followed, text='recent', created_at=hours_ago(1))
        helper = create_user('helper')
        like_post(helper, stale)
        like_post(helper, recent)
        ids = self._ids('/api/feed/for-you/')
        self.assertLess(ids.index(recent.id), ids.index(stale.id))

    def test_for_you_boosts_affinity_author(self):
        affinity_author = create_user('close')
        stranger = create_user('other')
        now_offset = days_ago(10)
        for index in range(3):
            old_post = create_post(
                affinity_author,
                text=f'old-{index}',
                created_at=now_offset,
            )
            like_post(self.viewer, old_post, created_at=now_offset)

        affinity_post = create_post(affinity_author, text='close-now')
        stranger_post = create_post(stranger, text='stranger-now')
        helper = create_user('liker')
        like_post(helper, affinity_post)
        like_post(helper, stranger_post)

        ids = self._ids('/api/feed/for-you/')
        self.assertLess(ids.index(affinity_post.id), ids.index(stranger_post.id))

    def test_for_you_serializes_counts_and_author(self):
        post = create_post(self.stranger, text='counted')
        like_post(self.viewer, post)
        create_post(self.viewer, text='reply', parent=post)

        payload = self._results('/api/feed/for-you/')[0]
        self.assertEqual(payload['id'], post.id)
        self.assertEqual(payload['text'], 'counted')
        self.assertEqual(payload['author']['username'], 'stranger')
        self.assertEqual(payload['like_count'], 1)
        self.assertEqual(payload['reply_count'], 1)
        self.assertEqual(payload['repost_count'], 0)
        self.assertNotIn('score', payload)

    def _results(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response.data['results']

    def _ids(self, url):
        return [item['id'] for item in self._results(url)]
