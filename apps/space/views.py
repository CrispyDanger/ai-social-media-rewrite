from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from apps.space.models import Space
from apps.space.permissions import IsCreatorOrReadOnly
from apps.space.serializers import SpaceSerializer


class SpacePagination(PageNumberPagination):
    page_size = 20


class SpaceViewSet(ModelViewSet):
    serializer_class = SpaceSerializer
    pagination_class = SpacePagination
    permission_classes = [IsAuthenticated, IsCreatorOrReadOnly]
    lookup_field = 'slug'

    def get_queryset(self):
        return (
            Space.objects.visible_to(self.request.user)
            .select_related('created_by')
            .with_member_count()
            .order_by('-created_at', '-id')
        )

    def perform_create(self, serializer):
        space = serializer.save(created_by=self.request.user)
        serializer.instance = self.get_queryset().get(pk=space.pk)

    def get_serializer(self, *args, **kwargs):
        serializer = super().get_serializer(*args, **kwargs)
        self._lock_slug_on_update(serializer)
        return serializer

    def _lock_slug_on_update(self, serializer):
        if getattr(self, 'action', None) not in ('update', 'partial_update'):
            return
        serializer.fields['slug'].read_only = True
