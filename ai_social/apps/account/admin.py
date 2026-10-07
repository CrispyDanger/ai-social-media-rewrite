from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from apps.account.models import Follow, Profile, User, UserSettings


class AccountUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('email', 'username', 'display_name')


class AccountUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    extra = 0


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    form = AccountUserChangeForm
    add_form = AccountUserCreationForm
    inlines = [ProfileInline]
    list_display = (
        'email',
        'username',
        'display_name',
        'is_verified',
        'is_staff',
        'is_active',
    )
    list_filter = ('is_verified', 'is_staff', 'is_active', 'is_superuser')
    search_fields = ('email', 'username', 'display_name')
    ordering = ('email',)
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        (
            'Profile',
            {'fields': ('display_name', 'is_verified', 'first_name', 'last_name')},
        ),
        (
            'Permissions',
            {
                'fields': (
                    'is_active',
                    'is_staff',
                    'is_superuser',
                    'groups',
                    'user_permissions',
                ),
            },
        ),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': (
                    'email',
                    'username',
                    'display_name',
                    'password1',
                    'password2',
                ),
            },
        ),
    )


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('follower', 'following', 'created_at')
    search_fields = ('follower__username', 'following__username')
    autocomplete_fields = ('follower', 'following')
    readonly_fields = ('created_at',)


@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'has_openrouter_api_key', 'updated_at')
    search_fields = ('user__username', 'user__email')
    autocomplete_fields = ('user',)
    readonly_fields = (
        'has_openrouter_api_key',
        'updated_at',
    )
    fields = (
        'user',
        'has_openrouter_api_key',
        'updated_at',
    )
