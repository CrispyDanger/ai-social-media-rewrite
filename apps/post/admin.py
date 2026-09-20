from django.contrib import admin

from apps.post.models import Media, Post, Repost


class MediaInline(admin.TabularInline):
    model = Media
    extra = 0


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('author', 'text', 'parent', 'quoted_post', 'created_at')
    search_fields = ('author__username', 'text')
    autocomplete_fields = ('author', 'parent', 'quoted_post')
    readonly_fields = ('created_at',)
    list_filter = ('created_at',)
    inlines = [MediaInline]


@admin.register(Repost)
class RepostAdmin(admin.ModelAdmin):
    list_display = ('author', 'post', 'created_at')
    search_fields = ('author__username', 'post__text')
    autocomplete_fields = ('author', 'post')
    readonly_fields = ('created_at',)


@admin.register(Media)
class MediaAdmin(admin.ModelAdmin):
    list_display = ('post', 'media_type', 'file', 'created_at')
    list_filter = ('media_type',)
    search_fields = ('post__text', 'post__author__username')
    autocomplete_fields = ('post',)
    readonly_fields = ('created_at',)
