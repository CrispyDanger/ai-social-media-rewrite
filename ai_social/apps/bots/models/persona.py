from django.conf import settings
from django.db import models


class BotPersona(models.Model):
    MAX_PER_SPACE = 5

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bot_persona',
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_bot_personas',
    )
    space = models.ForeignKey(
        'space.Space',
        on_delete=models.CASCADE,
        related_name='bot_personas',
    )
    name = models.CharField(max_length=50)
    persona_prompt = models.TextField()
    is_active = models.BooleanField(default=True)
    daily_action_limit = models.PositiveIntegerField(default=20)
    cooldown_seconds = models.PositiveIntegerField(default=300)
    last_action_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['space', 'owner'], name='bots_space_owner_idx'),
        ]

    def __str__(self):
        return self.name
