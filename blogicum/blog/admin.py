"""Настройки панели администратора для приложения blog."""

from django.contrib import admin

from .models import Category, Comment, Location, Post


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Настройки админ-зоны для модели Category."""

    list_display = (
        'title',
        'slug',
        'is_published',
        'created_at',
    )
    list_editable = ('is_published',)
    search_fields = ('title', 'description', 'slug')
    list_filter = ('is_published',)


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    """Настройки админ-зоны для модели Location."""

    list_display = (
        'name',
        'is_published',
        'created_at',
    )
    list_editable = ('is_published',)
    search_fields = ('name',)
    list_filter = ('is_published',)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """Настройки админ-зоны для модели Post."""

    list_display = (
        'title',
        'pub_date',
        'author',
        'category',
        'location',
        'is_published',
        'created_at',
    )
    list_editable = (
        'is_published',
        'category',
    )
    search_fields = ('title', 'text')
    list_filter = (
        'is_published',
        'category',
        'location',
    )
    list_display_links = ('title',)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Настройки админ-зоны для модели Comment."""

    list_display = (
        'text',
        'post',
        'author',
        'created_at',
    )
    search_fields = ('text',)
    list_filter = ('created_at',)
