from dj_rest_auth.registration.serializers import RegisterSerializer as BaseRegisterSerializer
from rest_framework import serializers


class RegisterSerializer(BaseRegisterSerializer):
    display_name = serializers.CharField(max_length=50)

    def get_cleaned_data(self):
        data = super().get_cleaned_data()
        data['display_name'] = self.validated_data.get('display_name', '')
        return data

    def custom_signup(self, request, user):
        user.display_name = self.cleaned_data['display_name'].strip()
        user.save(update_fields=['display_name'])
