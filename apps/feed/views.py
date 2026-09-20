from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination

from apps.feed.services.timeline import following_posts, for_you_posts
from apps.post.serializers import PostSerializer


class FeedPagination(PageNumberPagination):
    page_size = 20


class ForYouFeedView(ListAPIView):
    serializer_class = PostSerializer
    pagination_class = FeedPagination

    def get_queryset(self):
        return for_you_posts(self.request.user)


class FollowingFeedView(ListAPIView):
    serializer_class = PostSerializer
    pagination_class = FeedPagination

    def get_queryset(self):
        return following_posts(self.request.user)
