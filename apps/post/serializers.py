from rest_framework import serializers

from apps.account.models import User
from apps.post.models import Post


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'display_name')


class PostSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    like_count = serializers.IntegerField(read_only=True)
    repost_count = serializers.IntegerField(read_only=True)
    reply_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Post
        fields = (
            'id',
            'text',
            'created_at',
            'author',
            'like_count',
            'repost_count',
            'reply_count',
        )
