from django.contrib import admin

from apps.interaction.models import Like


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'created_at')
    search_fields = ('user__username', 'post__text')
    autocomplete_fields = ('user', 'post')
    readonly_fields = ('created_at',)
