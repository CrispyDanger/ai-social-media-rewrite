from django.db.models import Count
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
        queryset = (
            Space.objects.select_related('created_by')
            .annotate(member_count=Count('memberships'))
            .order_by('-created_at', '-id')
        )
        if self.action == 'list':
            return self._apply_filters(queryset)
        return queryset

    def perform_create(self, serializer):
        space = serializer.save(created_by=self.request.user)
        serializer.instance = self.get_queryset().get(pk=space.pk)

    def get_serializer(self, *args, **kwargs):
        serializer = super().get_serializer(*args, **kwargs)
        self._lock_slug_on_update(serializer)
        return serializer

    def _apply_filters(self, queryset):
        return self._filter_by_id(queryset, 'member', 'members')

    def _filter_by_id(self, queryset, param, field):
        value = self.request.query_params.get(param)
        if value is None:
            return queryset
        if not str(value).isdigit():
            return queryset.none()
        return queryset.filter(**{field: value})

    def _lock_slug_on_update(self, serializer):
        if getattr(self, 'action', None) not in ('update', 'partial_update'):
            return
        serializer.fields['slug'].read_only = True
