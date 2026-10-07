from rest_framework import serializers

from apps.account.models import UserSettings


class UserSettingsSerializer(serializers.ModelSerializer):
    openrouter_api_key = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        max_length=256,
        trim_whitespace=True,
        style={'input_type': 'password'},
    )
    has_openrouter_api_key = serializers.BooleanField(read_only=True)

    class Meta:
        model = UserSettings
        fields = (
            'openrouter_api_key',
            'has_openrouter_api_key',
        )
        read_only_fields = ('has_openrouter_api_key',)

    def validate_openrouter_api_key(self, value):
        return _validated_openrouter_key(value)

    def update(self, instance, validated_data):
        if 'openrouter_api_key' in validated_data:
            instance.set_openrouter_api_key(validated_data.pop('openrouter_api_key'))
        return super().update(instance, validated_data)


def _validated_openrouter_key(value):
    if not value:
        return ''
    if not value.startswith('sk-or-') or len(value) < 20:
        raise serializers.ValidationError(
            'Enter a valid OpenRouter API key (starts with sk-or-).'
        )
    return value
