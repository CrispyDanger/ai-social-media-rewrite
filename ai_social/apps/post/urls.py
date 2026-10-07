from rest_framework.routers import DefaultRouter

from apps.post.views import PostViewSet

router = DefaultRouter()
router.register(r'posts', PostViewSet, basename='post')

urlpatterns = router.urls
