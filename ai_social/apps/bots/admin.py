from django.contrib import admin

from apps.bots.models import BotPersona


@admin.register(BotPersona)
class BotPersonaAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'user',
        'owner',
        'space',
        'is_active',
        'daily_action_limit',
        'last_action_at',
    )
    list_filter = ('is_active',)
    search_fields = ('name', 'user__username', 'owner__username')
    raw_id_fields = ('user', 'owner', 'space')
    readonly_fields = ('last_action_at', 'created_at', 'updated_at')
