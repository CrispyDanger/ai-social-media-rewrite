from django.urls import path

from apps.space.views import (
    AcceptInviteView,
    DeclineInviteView,
    IncomingInviteListView,
    SpaceInviteListCreateView,
    SpaceViewSet,
)

urlpatterns = [
    path(
        'spaces/',
        SpaceViewSet.as_view({'get': 'list', 'post': 'create'}),
        name='space-list',
    ),
    path(
        'spaces/<slug:slug>/invites/',
        SpaceInviteListCreateView.as_view(),
        name='space-invite-list',
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
    path('invites/', IncomingInviteListView.as_view(), name='invite-list'),
    path('invites/<int:pk>/accept/', AcceptInviteView.as_view(), name='invite-accept'),
    path('invites/<int:pk>/decline/', DeclineInviteView.as_view(), name='invite-decline'),
]
