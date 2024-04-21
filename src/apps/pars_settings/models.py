from django.core.validators import MaxValueValidator
from django.db import models


class Shop(models.Model):
    """Модель магазина."""
    name = models.CharField(
        max_length=255,
        verbose_name='Название магазина'
    )

    class Meta:
        verbose_name = 'Магазина'
        verbose_name_plural = 'Магазины'

    def __str__(self):
        return self.name


class Article(models.Model):
    """Модель артикула."""
    name = models.CharField(
        max_length=255,
        verbose_name='Название товара'
    )
    code = models.PositiveIntegerField(
        unique=True,
        verbose_name='Код'
    )
    shop = models.ForeignKey(
        Shop,
        on_delete=models.CASCADE,
        related_name='articles',
        verbose_name='Магазин'
    )

    class Meta:
        verbose_name = 'Артикул'
        verbose_name_plural = 'Артикулы'

    def __str__(self):
        return f'{self.name} ({self.code})'


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
    target_page = models.PositiveSmallIntegerField(
        verbose_name='Целевой номер страницы',
        default=1,
    )
    target_position = models.PositiveSmallIntegerField(
        verbose_name='Целевая позиция',
        validators=[
            MaxValueValidator(limit_value=100),
        ]
    )

    class Meta:
        verbose_name = 'Запрос'
        verbose_name_plural = 'Запросы'
        unique_together = ('article', 'query')

    def __str__(self):
        return f'Товар: {self.article}, позиция: {self.target_position}'


class Position(models.Model):
    """Модель для позиций."""

    query = models.ForeignKey(
        Query,
        on_delete=models.CASCADE,
        related_name='positions',
        verbose_name='Запрос'
    )
    current_page = models.PositiveSmallIntegerField(
        verbose_name='Текущий номер страницы',
        default=1,
    )
    current_position = models.PositiveSmallIntegerField(
        verbose_name='Текущая позиция'
    )
    target_page = models.PositiveSmallIntegerField(
        verbose_name='Целевой номер страницы',
        default=1,
    )
    target_position = models.PositiveSmallIntegerField(
        verbose_name='Целевая позиция',
        validators=[MaxValueValidator(limit_value=100), ]
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

    @staticmethod
    def get_targets(position: int) -> tuple[int, int]:
        """Метод для получения страницы и позиции"""
        if position > 100:
            return (position // 100) + 1, position % 100

        return 1, position
