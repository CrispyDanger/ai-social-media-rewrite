from rest_framework import status
from rest_framework.test import APITestCase

from apps.feed.tests.helpers import create_user
from apps.space.models import Invite, Membership, Space


class SpaceInviteApiTests(APITestCase):
    def setUp(self):
        self.creator = create_user('creator')
        self.invitee = create_user('invitee')
        self.outsider = create_user('outsider')
        self.space = Space.objects.create(
            name='Python',
            slug='python',
            created_by=self.creator,
        )
        self.client.force_authenticate(user=self.creator)

    def test_creator_can_invite_by_username(self):
        response = self._invite('invitee')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['invitee']['username'], 'invitee')
        self.assertEqual(response.data['status'], Invite.Status.PENDING)
        self.assertEqual(response.data['space']['slug'], 'python')

    def test_invite_is_case_insensitive_on_username(self):
        response = self._invite('Invitee')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['invitee']['username'], 'invitee')

    def test_unknown_username_is_rejected(self):
        response = self._invite('missing')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_invite_yourself(self):
        response = self._invite('creator')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_invite_existing_member(self):
        Membership.objects.create(space=self.space, user=self.invitee)
        response = self._invite('invitee')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_create_duplicate_pending_invite(self):
        self._invite('invitee')
        response = self._invite('invitee')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_member_cannot_invite(self):
        Membership.objects.create(space=self.space, user=self.invitee)
        self.client.force_authenticate(user=self.invitee)
        response = self._invite('outsider')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_non_member_cannot_invite(self):
        self.client.force_authenticate(user=self.outsider)
        response = self._invite('invitee')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_creator_lists_pending_invites(self):
        self._invite('invitee')
        response = self.client.get('/api/spaces/python/invites/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        usernames = [item['invitee']['username'] for item in response.data['results']]
        self.assertEqual(usernames, ['invitee'])

    def test_member_cannot_list_space_invites(self):
        Membership.objects.create(space=self.space, user=self.invitee)
        self.client.force_authenticate(user=self.invitee)
        response = self.client.get('/api/spaces/python/invites/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_invitee_lists_incoming_invites(self):
        self._invite('invitee')
        self.client.force_authenticate(user=self.invitee)
        response = self.client.get('/api/invites/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        slugs = [item['space']['slug'] for item in response.data['results']]
        self.assertEqual(slugs, ['python'])

    def test_outsider_incoming_list_is_empty(self):
        self._invite('invitee')
        self.client.force_authenticate(user=self.outsider)
        response = self.client.get('/api/invites/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'], [])

    def test_accept_invite_joins_space(self):
        invite_id = self._invite('invitee').data['id']
        self.client.force_authenticate(user=self.invitee)
        response = self.client.post(f'/api/invites/{invite_id}/accept/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], Invite.Status.ACCEPTED)
        self.assertTrue(
            Membership.objects.filter(space=self.space, user=self.invitee).exists()
        )
        space_response = self.client.get('/api/spaces/python/')
        self.assertEqual(space_response.status_code, status.HTTP_200_OK)

    def test_decline_invite_does_not_join_space(self):
        invite_id = self._invite('invitee').data['id']
        self.client.force_authenticate(user=self.invitee)
        response = self.client.post(f'/api/invites/{invite_id}/decline/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], Invite.Status.DECLINED)
        self.assertFalse(
            Membership.objects.filter(space=self.space, user=self.invitee).exists()
        )
        space_response = self.client.get('/api/spaces/python/')
        self.assertEqual(space_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_can_reinvite_after_decline(self):
        invite_id = self._invite('invitee').data['id']
        self.client.force_authenticate(user=self.invitee)
        self.client.post(f'/api/invites/{invite_id}/decline/')
        self.client.force_authenticate(user=self.creator)
        response = self._invite('invitee')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_cannot_accept_someone_elses_invite(self):
        invite_id = self._invite('invitee').data['id']
        self.client.force_authenticate(user=self.outsider)
        response = self.client.post(f'/api/invites/{invite_id}/accept/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_invite_is_unauthorized(self):
        self.client.force_authenticate(user=None)
        response = self._invite('invitee')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def _invite(self, username):
        return self.client.post(
            '/api/spaces/python/invites/',
            {'username': username},
            format='json',
        )
