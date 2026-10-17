from django.urls import path

from apps.bots.views import SpaceBotDetailView, SpaceBotListCreateView

urlpatterns = [
    path(
        'spaces/<slug:slug>/bots/',
        SpaceBotListCreateView.as_view(),
        name='space-bot-list',
    ),
    path(
        'spaces/<slug:slug>/bots/<int:pk>/',
        SpaceBotDetailView.as_view(),
        name='space-bot-detail',
    ),
]
