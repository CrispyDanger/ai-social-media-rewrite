from django.contrib import admin

from apps.space.models import Membership, Space


class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 0
    autocomplete_fields = ('user',)
    readonly_fields = ('created_at',)


@admin.register(Space)
class SpaceAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_by', 'created_at')
    search_fields = ('name', 'slug', 'description')
    autocomplete_fields = ('created_by',)
    readonly_fields = ('created_at',)
    prepopulated_fields = {'slug': ('name',)}
    inlines = [MembershipInline]


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'space', 'created_at')
    search_fields = ('user__username', 'space__name', 'space__slug')
    autocomplete_fields = ('user', 'space')
    readonly_fields = ('created_at',)
