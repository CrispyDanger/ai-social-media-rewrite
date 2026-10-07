from django.shortcuts import get_object_or_404
from rest_framework.generics import GenericAPIView, ListAPIView, ListCreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.space.models import Invite, Space
from apps.space.permissions import IsSpaceCreator
from apps.space.serializers import InviteSerializer
from apps.space.services import accept_invite, decline_invite
from apps.space.views.pagination import SpacePagination


class SpaceInviteListCreateView(ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsSpaceCreator]
    serializer_class = InviteSerializer
    pagination_class = SpacePagination

    def get_space(self):
        if not hasattr(self, '_space'):
            space = get_object_or_404(
                Space.objects.visible_to(self.request.user),
                slug=self.kwargs['slug'],
            )
            self.check_object_permissions(self.request, space)
            self._space = space
        return self._space

    def get_queryset(self):
        return (
            Invite.objects.filter(space=self.get_space(), status=Invite.Status.PENDING)
            .select_related('space', 'invitee', 'invited_by')
            .order_by('-created_at', '-id')
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['space'] = self.get_space()
        return context

    def perform_create(self, serializer):
        serializer.save(space=self.get_space(), invited_by=self.request.user)


class IncomingInviteListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = InviteSerializer
    pagination_class = SpacePagination

    def get_queryset(self):
        return (
            Invite.objects.filter(
                invitee=self.request.user,
                status=Invite.Status.PENDING,
            )
            .select_related('space', 'invitee', 'invited_by')
            .order_by('-created_at', '-id')
        )


class InviteResponseView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = InviteSerializer

    def get_queryset(self):
        return Invite.objects.filter(
            invitee=self.request.user,
            status=Invite.Status.PENDING,
        ).select_related('space', 'invitee', 'invited_by')

    def post(self, request, *args, **kwargs):
        invite = self.get_object()
        self.respond(invite)
        invite.refresh_from_db()
        return Response(self.get_serializer(invite).data)

    def respond(self, invite):
        raise NotImplementedError


class AcceptInviteView(InviteResponseView):
    def respond(self, invite):
        accept_invite(invite)


class DeclineInviteView(InviteResponseView):
    def respond(self, invite):
        decline_invite(invite)
