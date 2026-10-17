from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated

from apps.bots.models import BotPersona
from apps.bots.serializers import BotPersonaSerializer
from apps.bots.services.personas.personas import delete_persona
from apps.space.models import Space
from apps.space.views.pagination import SpacePagination


class SpaceBotAccess:
    permission_classes = [IsAuthenticated]
    serializer_class = BotPersonaSerializer
    pagination_class = SpacePagination

    def get_space(self):
        if hasattr(self, '_space'):
            return self._space
        space = get_object_or_404(
            Space.objects.visible_to(self.request.user),
            slug=self.kwargs['slug'],
        )
        if space.created_by_id != self.request.user.id:
            raise PermissionDenied
        self._space = space
        return space

    def get_queryset(self):
        return (
            BotPersona.objects.filter(space=self.get_space(), owner=self.request.user)
            .select_related('user')
            .order_by('-created_at', '-id')
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['space'] = self.get_space()
        return context


class SpaceBotListCreateView(SpaceBotAccess, ListCreateAPIView):
    pass


class SpaceBotDetailView(SpaceBotAccess, RetrieveUpdateDestroyAPIView):
    def perform_destroy(self, instance):
        delete_persona(instance)
