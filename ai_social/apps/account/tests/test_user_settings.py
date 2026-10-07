from django.db import connection
from rest_framework import status
from rest_framework.test import APITestCase

from apps.account.models import User, UserSettings
from apps.account.services import get_openrouter_api_key

VALID_OPENROUTER_KEY = 'sk-or-v1-' + 'a' * 64
SETTINGS_URL = '/api/auth/settings/'


class UserSettingsApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='ada@example.com',
            username='ada',
            password='correcthorse1',
            display_name='Ada Lovelace',
        )
        self.client.force_authenticate(user=self.user)

    def test_new_user_gets_empty_settings(self):
        self.assertTrue(UserSettings.objects.filter(user=self.user).exists())
        response = self.client.get(SETTINGS_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['has_openrouter_api_key'])
        self.assertNotIn('openrouter_api_key', response.data)

    def test_unauthenticated_get_is_unauthorized(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(SETTINGS_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_save_key_returns_flag_not_secret(self):
        response = self.client.patch(
            SETTINGS_URL,
            {'openrouter_api_key': VALID_OPENROUTER_KEY},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['has_openrouter_api_key'])
        self.assertNotIn('openrouter_api_key', response.data)

    def test_key_is_encrypted_in_the_database(self):
        self.client.patch(
            SETTINGS_URL,
            {'openrouter_api_key': VALID_OPENROUTER_KEY},
            format='json',
        )
        stored = _raw_openrouter_key(self.user.settings)
        self.assertNotEqual(stored, VALID_OPENROUTER_KEY)
        self.assertNotIn(VALID_OPENROUTER_KEY, stored)
        self.assertEqual(get_openrouter_api_key(self.user), VALID_OPENROUTER_KEY)

    def test_invalid_key_is_rejected(self):
        response = self.client.patch(
            SETTINGS_URL,
            {'openrouter_api_key': 'not-a-real-key'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(self.user.settings.has_openrouter_api_key)

    def test_blank_key_clears_stored_secret(self):
        self.client.patch(
            SETTINGS_URL,
            {'openrouter_api_key': VALID_OPENROUTER_KEY},
            format='json',
        )
        response = self.client.patch(
            SETTINGS_URL,
            {'openrouter_api_key': ''},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['has_openrouter_api_key'])
        self.assertIsNone(get_openrouter_api_key(self.user))


def _raw_openrouter_key(settings_row):
    table = UserSettings._meta.db_table
    column = UserSettings._meta.get_field('openrouter_api_key').column
    with connection.cursor() as cursor:
        cursor.execute(
            f'SELECT {column} FROM {table} WHERE id = %s',
            [settings_row.pk],
        )
        return cursor.fetchone()[0]
