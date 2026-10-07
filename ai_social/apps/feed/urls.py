from django.urls import path

from apps.feed.views import FollowingFeedView, ForYouFeedView

urlpatterns = [
    path('for-you/', ForYouFeedView.as_view(), name='feed-for-you'),
    path('following/', FollowingFeedView.as_view(), name='feed-following'),
]
