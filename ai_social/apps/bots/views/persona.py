from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView

from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from apps.bots.models import BotPersona
from apps.bots.serializers import BotPersonaSerializer
from apps.space.models import Space
from apps.space.views.pagination import SpacePagination
from apps.bots.services.personas.personas import delete_persona


def get_space(request, slug):
    space = get_object_or_404(
        Space.objects.visible_to(request.user),
        slug=slug,
    )
    if space.created_by_id != request.user.id:
        raise PermissionDenied
    return space


class SpaceBotListCreateView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BotPersonaSerializer
    pagination_class = SpacePagination

    def get_queryset(self):
        return (
            BotPersona.objects.filter(space=get_space(self.request,
                                                      self.kwargs['slug']),
                                      owner=self.request.user)
            .select_related('user')
            .order_by('-created_at', '-id')
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['space'] = get_space(self.request, self.kwargs['slug'])
        return context


class SpaceBotDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BotPersonaSerializer
    pagination_class = SpacePagination

    def get_queryset(self):
        return (
            BotPersona.objects.filter(space=get_space(self.request,
                                                      self.kwargs['slug']),
                                      owner=self.request.user)
            .select_related('user')
            .order_by('-created_at', '-id')
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['space'] = get_space(self.request, self.kwargs['slug'])
        return context

    def perform_destroy(self, instance):
        delete_persona(instance)
