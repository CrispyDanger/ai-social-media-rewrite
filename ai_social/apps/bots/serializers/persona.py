from rest_framework import serializers

from apps.bots.models import BotPersona
from apps.bots.services.personas.personas import (
    BotLimitReached,
    create_owned_persona,
    sync_bot_display_name,
)

PROMPT_MAX_LENGTH = 4000


class BotPersonaSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    persona_prompt = serializers.CharField(max_length=PROMPT_MAX_LENGTH)

    class Meta:
        model = BotPersona
        fields = (
            'id',
            'name',
            'username',
            'persona_prompt',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('created_at', 'updated_at')

    def create(self, validated_data):
        try:
            return create_owned_persona(
                owner=self.context['request'].user,
                space=self.context['space'],
                name=validated_data['name'],
                persona_prompt=validated_data['persona_prompt'],
            )
        except BotLimitReached:
            raise serializers.ValidationError(
                {'non_field_errors': [limit_message()]},
            ) from None

    def update(self, instance, validated_data):
        name = validated_data.get('name')
        if name is not None:
            sync_bot_display_name(instance.user, name)
        return super().update(instance, validated_data)


def limit_message() -> str:
    return f'You can create up to {BotPersona.MAX_PER_SPACE} bots in this space.'
