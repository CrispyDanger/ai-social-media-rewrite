from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.bots.models import BotPersona
from apps.feed.tests.helpers import create_user
from apps.space.models import Membership, Space

User = get_user_model()


class BotPersonaApiTests(APITestCase):
    def setUp(self):
        self.creator = create_user('creator')
        self.member = create_user('member')
        self.outsider = create_user('outsider')
        self.space = Space.objects.create(
            name='Python',
            slug='python',
            created_by=self.creator,
        )
        Membership.objects.create(space=self.space, user=self.member)
        self.client.force_authenticate(user=self.creator)

    def test_unauthenticated_list_is_unauthorized(self):
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/spaces/python/bots/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_creator_creates_bot_with_name_and_prompt(self):
        response = self._create('Ada Lovelace', 'Talks about computing.')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Ada Lovelace')
        self.assertEqual(response.data['username'], 'ada_lovelace')
        self.assertEqual(response.data['persona_prompt'], 'Talks about computing.')
        persona = BotPersona.objects.get(pk=response.data['id'])
        self.assertEqual(persona.owner, self.creator)
        self.assertEqual(persona.space, self.space)
        self.assertEqual(persona.user.display_name, 'Ada Lovelace')
        self.assertFalse(persona.user.has_usable_password())
        self.assertTrue(
            Membership.objects.filter(space=self.space, user=persona.user).exists()
        )

    def test_create_strips_name_and_prompt(self):
        response = self._create('  Ada  ', '  Curious.  ')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Ada')
        self.assertEqual(response.data['persona_prompt'], 'Curious.')

    def test_create_rejects_blank_name(self):
        response = self._create('   ', 'Curious.')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_rejects_blank_prompt(self):
        response = self._create('Ada', '   ')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_names_get_distinct_handles(self):
        first = self._create('Ada', 'First.')
        second = self._create('Ada', 'Second.')
        self.assertEqual(first.data['username'], 'ada')
        self.assertEqual(second.data['username'], 'ada1')

    def test_sixth_bot_in_a_space_is_rejected(self):
        for index in range(BotPersona.MAX_PER_SPACE):
            response = self._create(f'Bot {index}', 'Prompt.')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self._create('Extra', 'One too many.')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('5', response.data['non_field_errors'][0])
        self.assertEqual(BotPersona.objects.filter(space=self.space).count(), 5)

    def test_list_returns_newest_first(self):
        older = self._create('Ada', 'First.')
        newer = self._create('Grace', 'Second.')
        response = self.client.get('/api/spaces/python/bots/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [item['id'] for item in response.data['results']]
        self.assertEqual(ids, [newer.data['id'], older.data['id']])

    def test_member_cannot_list_or_create(self):
        self.client.force_authenticate(user=self.member)
        listed = self.client.get('/api/spaces/python/bots/')
        created = self._create('Ada', 'Prompt.')
        self.assertEqual(listed.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(created.status_code, status.HTTP_403_FORBIDDEN)

    def test_outsider_cannot_list_or_create(self):
        self.client.force_authenticate(user=self.outsider)
        listed = self.client.get('/api/spaces/python/bots/')
        created = self._create('Ada', 'Prompt.')
        self.assertEqual(listed.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(created.status_code, status.HTTP_404_NOT_FOUND)

    def test_creator_updates_name_and_prompt(self):
        created = self._create('Ada', 'First draft.')
        response = self.client.patch(
            f'/api/spaces/python/bots/{created.data["id"]}/',
            {'name': 'Ada Lovelace', 'persona_prompt': 'Revised.'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Ada Lovelace')
        self.assertEqual(response.data['persona_prompt'], 'Revised.')
        self.assertEqual(response.data['username'], 'ada')
        persona = BotPersona.objects.get(pk=created.data['id'])
        self.assertEqual(persona.user.display_name, 'Ada Lovelace')

    def test_member_cannot_update_or_delete(self):
        created = self._create('Ada', 'Prompt.')
        url = f'/api/spaces/python/bots/{created.data["id"]}/'
        self.client.force_authenticate(user=self.member)
        updated = self.client.patch(url, {'name': 'Stolen'}, format='json')
        deleted = self.client.delete(url)
        self.assertEqual(updated.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(deleted.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(BotPersona.objects.filter(pk=created.data['id']).exists())

    def test_delete_removes_bot_account(self):
        created = self._create('Ada', 'Prompt.')
        persona = BotPersona.objects.get(pk=created.data['id'])
        user_id = persona.user_id
        response = self.client.delete(f'/api/spaces/python/bots/{persona.pk}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(BotPersona.objects.filter(pk=persona.pk).exists())
        self.assertFalse(User.objects.filter(pk=user_id).exists())
        self.assertFalse(Membership.objects.filter(user_id=user_id).exists())

    def test_deleting_space_removes_bot_accounts(self):
        created = self._create('Ada', 'Prompt.')
        user_id = BotPersona.objects.get(pk=created.data['id']).user_id
        self.space.delete()
        self.assertFalse(User.objects.filter(pk=user_id).exists())

    def _create(self, name, persona_prompt):
        return self.client.post(
            '/api/spaces/python/bots/',
            {'name': name, 'persona_prompt': persona_prompt},
            format='json',
        )
