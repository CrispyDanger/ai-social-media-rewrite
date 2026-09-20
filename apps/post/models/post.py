from django.conf import settings
from django.db import models


class Post(models.Model):
    text = models.CharField(max_length=280)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='posts',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name='replies',
        null=True,
        blank=True,
    )
    quoted_post = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        related_name='quotes',
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['author', '-created_at']),
            models.Index(fields=['parent', '-created_at']),
        ]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(pk=models.F('parent')),
                name='prevent_self_reply',
            ),
            models.CheckConstraint(
                condition=~models.Q(pk=models.F('quoted_post')),
                name='prevent_self_quote',
            ),
        ]

    def __str__(self):
        return f'{self.author}: {self.text[:50]}'
