from rest_framework import serializers

from apps.account.models import User
from apps.post.models import Post


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'display_name')


class PostSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    like_count = serializers.IntegerField(read_only=True, default=0)
    repost_count = serializers.IntegerField(read_only=True, default=0)
    reply_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Post
        fields = (
            'id',
            'text',
            'created_at',
            'author',
            'parent',
            'quoted_post',
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
