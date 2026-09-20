from django.urls import include, path
from dj_rest_auth.registration.views import VerifyEmailView

from apps.account import views

urlpatterns = [
    path('', include('dj_rest_auth.urls')),
    path('registration/', include('dj_rest_auth.registration.urls')),
    path(
        'registration/account-confirm-email/',
        VerifyEmailView.as_view(),
        name='account_email_verification_sent',
    ),
    path('google/', views.GoogleLogin.as_view(), name='google_login'),
    path('settings/', views.UserSettingsView.as_view(), name='user-settings'),
]
