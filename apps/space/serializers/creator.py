from rest_framework import serializers

from apps.account.models import User


class CreatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'display_name')
