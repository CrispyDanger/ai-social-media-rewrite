from rest_framework import status
from rest_framework.test import APITestCase

from apps.feed.tests.helpers import create_user, hours_ago, set_created_at
from apps.space.models import Membership, Space


class SpaceApiTests(APITestCase):
    def setUp(self):
        self.creator = create_user('creator')
        self.other = create_user('other')
        self.client.force_authenticate(user=self.creator)

    def test_unauthenticated_list_is_unauthorized(self):
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/spaces/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_space_sets_creator_and_slug(self):
        response = self.client.post(
            '/api/spaces/',
            {'name': 'Machine Learning', 'description': 'ML talk'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Machine Learning')
        self.assertEqual(response.data['slug'], 'machine-learning')
        self.assertEqual(response.data['created_by']['username'], 'creator')
        self.assertEqual(response.data['member_count'], 1)

    def test_create_uses_unique_slug_when_taken(self):
        self._create_space(self.creator, name='News', slug='news')
        response = self.client.post('/api/spaces/', {'name': 'News'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['slug'], 'news-2')

    def test_create_rejects_duplicate_slug(self):
        self._create_space(self.creator, name='News', slug='news')
        response = self.client.post(
            '/api/spaces/',
            {'name': 'Daily News', 'slug': 'News'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_rejects_blank_name(self):
        response = self.client.post('/api/spaces/', {'name': '   '}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_returns_newest_first(self):
        older = self._create_space(self.creator, name='Older', slug='older')
        newer = self._create_space(self.creator, name='Newer', slug='newer')
        set_created_at(older, hours_ago(2))
        set_created_at(newer, hours_ago(1))
        ids = self._ids('/api/spaces/')
        self.assertEqual(ids, [newer.id, older.id])

    def test_list_omits_spaces_user_is_not_in(self):
        visible = self._create_space(self.creator, name='Mine', slug='mine')
        self._create_space(self.other, name='Theirs', slug='theirs')
        ids = self._ids('/api/spaces/')
        self.assertEqual(ids, [visible.id])

    def test_retrieve_member_space(self):
        space = self._create_space(self.other, name='Python', slug='python')
        Membership.objects.create(space=space, user=self.creator)
        response = self.client.get('/api/spaces/python/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], space.id)
        self.assertEqual(response.data['member_count'], 2)

    def test_retrieve_non_member_space_is_not_found(self):
        self._create_space(self.other, name='Python', slug='python')
        response = self.client.get('/api/spaces/python/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_own_space_name(self):
        space = self._create_space(self.creator, name='Draft', slug='draft')
        response = self.client.patch(
            '/api/spaces/draft/',
            {'name': 'Published', 'description': 'Updated'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Published')
        space.refresh_from_db()
        self.assertEqual(space.name, 'Published')
        self.assertEqual(space.slug, 'draft')

    def test_update_ignores_slug_change(self):
        self._create_space(self.creator, name='Draft', slug='draft')
        response = self.client.patch(
            '/api/spaces/draft/',
            {'name': 'Published', 'slug': 'published'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['slug'], 'draft')

    def test_update_non_member_space_is_not_found(self):
        self._create_space(self.other, name='Theirs', slug='theirs')
        response = self.client.patch(
            '/api/spaces/theirs/',
            {'name': 'Stolen'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_member_cannot_update_others_space(self):
        space = self._create_space(self.other, name='Theirs', slug='theirs')
        Membership.objects.create(space=space, user=self.creator)
        response = self.client.patch(
            '/api/spaces/theirs/',
            {'name': 'Stolen'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_own_space(self):
        self._create_space(self.creator, name='Gone', slug='gone')
        response = self.client.delete('/api/spaces/gone/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Space.objects.filter(slug='gone').exists())

    def test_delete_non_member_space_is_not_found(self):
        self._create_space(self.other, name='Theirs', slug='theirs')
        response = self.client.delete('/api/spaces/theirs/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Space.objects.filter(slug='theirs').exists())

    def _create_space(self, creator, name, slug):
        return Space.objects.create(name=name, slug=slug, created_by=creator)

    def _ids(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return [item['id'] for item in response.data['results']]
