from rest_framework import serializers

from apps.space.models import Space


class SpacePreviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Space
        fields = ('id', 'name', 'slug')
