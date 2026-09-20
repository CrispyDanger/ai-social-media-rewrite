from rest_framework import serializers

from apps.post.models import Post
from apps.space.models import Membership, Space

from .author import AuthorSerializer


class PostSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    like_count = serializers.IntegerField(read_only=True, default=0)
    repost_count = serializers.IntegerField(read_only=True, default=0)
    reply_count = serializers.IntegerField(read_only=True, default=0)
    space = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Space.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Post
        fields = (
            'id',
            'text',
            'created_at',
            'author',
            'parent',
            'quoted_post',
            'space',
            'like_count',
            'repost_count',
            'reply_count',
        )
        extra_kwargs = {
            'parent': {'required': False, 'allow_null': True},
            'quoted_post': {'required': False, 'allow_null': True},
        }

    def validate_text(self, value):
        text = value.strip()
        if not text:
            raise serializers.ValidationError('This field may not be blank.')
        return text

    def validate_space(self, space):
        if space is None:
            return space
        user = self.context['request'].user
        if not Membership.objects.filter(space=space, user=user).exists():
            raise serializers.ValidationError('You are not a member of this space.')
        return space

    def create(self, validated_data):
        parent = validated_data.get('parent')
        if parent and not validated_data.get('space'):
            validated_data['space'] = parent.space
        return super().create(validated_data)
