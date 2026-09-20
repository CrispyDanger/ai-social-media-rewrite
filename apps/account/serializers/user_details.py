from rest_framework import serializers

from apps.account.models import User


class UserDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('pk', 'username', 'email', 'display_name')
        read_only_fields = ('pk', 'email')
