from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from apps.post.models import Post
from apps.post.permissions import IsAuthorOrReadOnly
from apps.post.serializers import PostSerializer


class PostPagination(PageNumberPagination):
    page_size = 20


class PostViewSet(ModelViewSet):
    serializer_class = PostSerializer
    pagination_class = PostPagination
    permission_classes = [IsAuthenticated, IsAuthorOrReadOnly]

    def get_queryset(self):
        queryset = (
            Post.objects.select_related('author')
            .with_engagement_counts()
            .order_by('-created_at', '-id')
        )
        if self.action == 'list':
            return self._apply_filters(queryset)
        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer(self, *args, **kwargs):
        serializer = super().get_serializer(*args, **kwargs)
        self._lock_relations_on_update(serializer)
        return serializer

    def _apply_filters(self, queryset):
        queryset = self._filter_by_id(queryset, 'author', 'author_id')
        return self._filter_by_id(queryset, 'parent', 'parent_id')

    def _filter_by_id(self, queryset, param, field):
        value = self.request.query_params.get(param)
        if value is None:
            return queryset
        if not str(value).isdigit():
            return queryset.none()
        return queryset.filter(**{field: value})

    def _lock_relations_on_update(self, serializer):
        if getattr(self, 'action', None) not in ('update', 'partial_update'):
            return
        serializer.fields['parent'].read_only = True
        serializer.fields['quoted_post'].read_only = True
