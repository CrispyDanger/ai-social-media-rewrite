from django.conf import settings
from django.db import models


class Membership(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='space_memberships',
    )
    space = models.ForeignKey(
        'space.Space',
        on_delete=models.CASCADE,
        related_name='memberships',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'space'],
                name='unique_user_space_membership',
            ),
        ]

    def __str__(self):
        return f'{self.user} in {self.space}'
