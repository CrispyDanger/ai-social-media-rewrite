from django.urls import path

from apps.space.views import SpaceViewSet

urlpatterns = [
    path(
        'spaces/',
        SpaceViewSet.as_view({'get': 'list', 'post': 'create'}),
        name='space-list',
    ),
    path(
        'spaces/<slug:slug>/',
        SpaceViewSet.as_view({
            'get': 'retrieve',
            'put': 'update',
            'patch': 'partial_update',
            'delete': 'destroy',
        }),
        name='space-detail',
    ),
]
