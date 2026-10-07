from django.conf import settings
from django.db import models


class Invite(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        ACCEPTED = 'accepted', 'Accepted'
        DECLINED = 'declined', 'Declined'

    space = models.ForeignKey(
        'space.Space',
        on_delete=models.CASCADE,
        related_name='invites',
    )
    invitee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_space_invites',
    )
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_space_invites',
    )
    status = models.CharField(
        max_length=8,
        choices=Status,
        default=Status.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['space', 'invitee'],
                condition=models.Q(status='pending'),
                name='unique_pending_space_invitee',
            ),
            models.CheckConstraint(
                condition=~models.Q(invitee_id=models.F('invited_by_id')),
                name='prevent_self_invite',
            ),
        ]

    def __str__(self):
        return f'{self.invited_by} invited {self.invitee} to {self.space}'
