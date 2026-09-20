from rest_framework import status
from rest_framework.test import APITestCase

from apps.account.models import User


class AuthSerializerApiTests(APITestCase):
    def test_registration_saves_display_name(self):
        response = self.client.post(
            '/api/auth/registration/',
            {
                'email': 'ada@example.com',
                'username': 'ada',
                'display_name': 'Ada Lovelace',
                'password1': 'correcthorse1',
                'password2': 'correcthorse1',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username='ada')
        self.assertEqual(user.display_name, 'Ada Lovelace')
        self.assertEqual(response.data['user']['display_name'], 'Ada Lovelace')
        self.assertEqual(response.data['user']['pk'], user.pk)

    def test_user_details_includes_display_name(self):
        user = User.objects.create_user(
            email='grace@example.com',
            username='grace',
            password='correcthorse1',
            display_name='Grace Hopper',
        )
        self.client.force_authenticate(user=user)
        response = self.client.get('/api/auth/user/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['display_name'], 'Grace Hopper')
        self.assertEqual(response.data['username'], 'grace')
        self.assertEqual(response.data['pk'], user.pk)
