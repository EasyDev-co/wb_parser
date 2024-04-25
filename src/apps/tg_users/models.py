from django.db import models


class TelegramUser(models.Model):
    name = models.CharField(
        'Имя пользователя',
        max_length=255,
        blank=True,
        null=True,
        default=None,
    )
    telegram_id = models.PositiveIntegerField(
        'Телеграм id',
        unique=True,
        db_index=True,
    )

    class Meta:
        verbose_name = 'Telegram пользователь'
        verbose_name_plural = 'Telegram пользователи'

    def __str__(self):
        return f'{self.name}: {self.telegram_id}' if self.name\
            else str(self.telegram_id)
