from rest_framework import status
from rest_framework.test import APITestCase

from apps.feed.tests.helpers import create_post, create_user, hours_ago, like_post


class PostApiTests(APITestCase):
    def setUp(self):
        self.author = create_user('author')
        self.other = create_user('other')
        self.client.force_authenticate(user=self.author)

    def test_unauthenticated_list_is_unauthorized(self):
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/posts/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_post_sets_author(self):
        response = self.client.post('/api/posts/', {'text': 'hello'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['text'], 'hello')
        self.assertEqual(response.data['author']['username'], 'author')
        self.assertIsNone(response.data['parent'])
        self.assertEqual(response.data['like_count'], 0)

    def test_create_rejects_blank_text(self):
        response = self.client.post('/api/posts/', {'text': '   '}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_reply_and_quote(self):
        parent = create_post(self.other, text='parent')
        quoted = create_post(self.other, text='quoted')
        response = self.client.post(
            '/api/posts/',
            {'text': 'reply', 'parent': parent.id, 'quoted_post': quoted.id},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['parent'], parent.id)
        self.assertEqual(response.data['quoted_post'], quoted.id)

    def test_list_returns_newest_first(self):
        older = create_post(self.author, text='older', created_at=hours_ago(2))
        newer = create_post(self.other, text='newer', created_at=hours_ago(1))
        ids = self._ids('/api/posts/')
        self.assertEqual(ids, [newer.id, older.id])

    def test_list_filters_by_author(self):
        own = create_post(self.author, text='own')
        create_post(self.other, text='hidden')
        ids = self._ids(f'/api/posts/?author={self.author.id}')
        self.assertEqual(ids, [own.id])

    def test_list_filters_by_parent(self):
        parent = create_post(self.other, text='parent')
        reply = create_post(self.author, text='reply', parent=parent)
        create_post(self.author, text='original')
        ids = self._ids(f'/api/posts/?parent={parent.id}')
        self.assertEqual(ids, [reply.id])

    def test_retrieve_includes_counts_and_author(self):
        post = create_post(self.other, text='counted')
        like_post(self.author, post)
        create_post(self.author, text='reply', parent=post)
        response = self.client.get(f'/api/posts/{post.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['text'], 'counted')
        self.assertEqual(response.data['author']['username'], 'other')
        self.assertEqual(response.data['like_count'], 1)
        self.assertEqual(response.data['reply_count'], 1)
        self.assertEqual(response.data['repost_count'], 0)

    def test_update_own_post_text(self):
        post = create_post(self.author, text='draft')
        response = self.client.patch(
            f'/api/posts/{post.id}/',
            {'text': 'edited'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['text'], 'edited')
        post.refresh_from_db()
        self.assertEqual(post.text, 'edited')

    def test_update_ignores_parent_change(self):
        parent = create_post(self.other, text='parent')
        other_parent = create_post(self.other, text='other-parent')
        post = create_post(self.author, text='reply', parent=parent)
        response = self.client.patch(
            f'/api/posts/{post.id}/',
            {'text': 'edited', 'parent': other_parent.id},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        post.refresh_from_db()
        self.assertEqual(post.text, 'edited')
        self.assertEqual(post.parent_id, parent.id)

    def test_update_others_post_is_forbidden(self):
        post = create_post(self.other, text='theirs')
        response = self.client.patch(
            f'/api/posts/{post.id}/',
            {'text': 'stolen'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_own_post(self):
        post = create_post(self.author, text='gone')
        response = self.client.delete(f'/api/posts/{post.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(self._exists(post.id))

    def test_delete_others_post_is_forbidden(self):
        post = create_post(self.other, text='theirs')
        response = self.client.delete(f'/api/posts/{post.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(self._exists(post.id))

    def _ids(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return [item['id'] for item in response.data['results']]

    def _exists(self, post_id):
        return self.client.get(f'/api/posts/{post_id}/').status_code == status.HTTP_200_OK
