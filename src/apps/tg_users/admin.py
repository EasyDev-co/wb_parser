from django.contrib import admin
from apps.tg_users.models import TelegramUser


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = ('name', 'telegram_id', )
    list_editable = ('telegram_id', )

    fields = ('telegram_id', 'name', )
    search_fields = ('name__iregex', 'telegram_id__iregex', )

