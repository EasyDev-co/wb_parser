from django.contrib import admin

from apps.pars_settings.models import Article, Query, Position


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    """Админ-панель для управления артикулами."""
    list_display = ('code',)
    search_fields = ('code',)


@admin.register(Query)
class QueryAdmin(admin.ModelAdmin):
    """Админ-панель для управления запросами."""
    list_display = ('query', 'article')
    list_filter = ('article',)
    search_fields = ('query', 'article__code')


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    """Админ-панель для управления позициями по запросам."""
    list_display = (
        'query',
        'current_position',
        'target_position',
        'check_date'
    )
    list_filter = ('query', 'query__article')
    search_fields = ('query__query', 'query__article__code')
    date_hierarchy = 'check_date'
