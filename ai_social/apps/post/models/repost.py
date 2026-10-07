from django.conf import settings
from django.db import models

from .post import Post


class Repost(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reposts',
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='reposts',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'post'],
                name='unique_author_post_repost',
            ),
        ]

    def __str__(self):
        return f'{self.author} reposted {self.post}'
