from django.contrib import admin

from apps.pars_settings.models import Article, Query, Position, Shop


class ArticleInline(admin.TabularInline):
    """Инлайн для админ-панели магазина."""
    model = Article
    extra = 1


class QueryInline(admin.TabularInline):
    """Инлайн для админ-панели запроса."""
    model = Query
    extra = 1


class PositionInline(admin.TabularInline):
    """Инлайн для админ-панели позиции."""
    model = Position
    extra = 1


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    """Админ-панель для управления артикулами."""
    list_display = ('name',)
    search_fields = ('name__iregex',)
    inlines = (ArticleInline,)


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    """Админ-панель для управления артикулами."""
    list_display = ('name', 'code')
    list_filter = ('shop__name',)
    search_fields = ('name__iregex', 'code__iregex',  )
    autocomplete_fields = ('shop',)
    inlines = (QueryInline,)


@admin.register(Query)
class QueryAdmin(admin.ModelAdmin):
    """Админ-панель для управления запросами."""
    list_display = ('query', 'article')
    list_filter = ('article__shop__name',)
    search_fields = ('query__iregex', 'article__code__iregex')
    autocomplete_fields = ('article',)
    inlines = (PositionInline,)


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    """Админ-панель для управления позициями."""
    list_display = (
        'query',
        'current_page',
        'current_position',
        'target_page',
        'target_position',
        'check_date',
    )
    list_filter = ('query__article__shop__name', 'check_date', )

    search_fields = ('query__query__iregex', )
    date_hierarchy = 'check_date'
    autocomplete_fields = ('query', )
