from django.db import models


class Article(models.Model):
    """Модель артикула."""

    code = models.CharField(
        max_length=255,
        unique=True,
        verbose_name='Код'
    )

    class Meta:
        verbose_name = 'Артикул'
        verbose_name_plural = 'Артикулы'

    def __str__(self):
        return self.code


class Query(models.Model):
    """Модель запроса."""

    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name='queries',
        verbose_name='Артикул'
    )
    query = models.CharField(
        max_length=255,
        verbose_name='Запрос'
    )

    class Meta:
        verbose_name = 'Запрос'
        verbose_name_plural = 'Запросы'
        unique_together = ('article', 'query')

    def __str__(self):
        return f'{self.query} ({self.article})'


class Position(models.Model):
    """Модель для позиций."""

    query = models.ForeignKey(
        Query,
        on_delete=models.CASCADE,
        related_name='positions',
        verbose_name='Запрос'
    )
    current_position = models.PositiveSmallIntegerField(
        verbose_name='Текущая позиция'
    )
    target_position = models.PositiveSmallIntegerField(
        verbose_name='Целевая позиция'
    )
    check_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата проверки'
    )

    class Meta:
        verbose_name = 'Позиция'
        verbose_name_plural = 'Позиции'

    def __str__(self):
        return f'{self.query} - {self.current_position}'

