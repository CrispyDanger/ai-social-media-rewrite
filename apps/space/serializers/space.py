from rest_framework import serializers

from apps.space.models import Space
from apps.space.services import unique_slug_for

from .creator import CreatorSerializer


class SpaceSerializer(serializers.ModelSerializer):
    created_by = CreatorSerializer(read_only=True)
    member_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Space
        fields = (
            'id',
            'name',
            'slug',
            'description',
            'created_by',
            'created_at',
            'member_count',
        )
        extra_kwargs = {
            'slug': {'required': False},
            'description': {'required': False, 'allow_blank': True},
        }

    def validate_name(self, value):
        name = value.strip()
        if not name:
            raise serializers.ValidationError('This field may not be blank.')
        return name

    def validate_slug(self, value):
        slug = value.lower()
        queryset = Space.objects.filter(slug__iexact=slug)
        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError('A space with this slug already exists.')
        return slug

    def create(self, validated_data):
        if not validated_data.get('slug'):
            validated_data['slug'] = unique_slug_for(validated_data['name'])
        return super().create(validated_data)
