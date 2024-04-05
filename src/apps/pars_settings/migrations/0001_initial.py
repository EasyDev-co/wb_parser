# Generated by Django 5.0.2 on 2024-04-05 11:23

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Article',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=255, unique=True, verbose_name='Код')),
            ],
            options={
                'verbose_name': 'Артикул',
                'verbose_name_plural': 'Артикулы',
            },
        ),
        migrations.CreateModel(
            name='Query',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('query', models.CharField(max_length=255, verbose_name='Запрос')),
                ('target_position', models.PositiveSmallIntegerField(verbose_name='Целевая позиция')),
                ('article', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='queries', to='pars_settings.article', verbose_name='Артикул')),
            ],
            options={
                'verbose_name': 'Запрос',
                'verbose_name_plural': 'Запросы',
                'unique_together': {('article', 'query')},
            },
        ),
        migrations.CreateModel(
            name='Position',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('current_position', models.PositiveSmallIntegerField(verbose_name='Текущая позиция')),
                ('target_position', models.PositiveSmallIntegerField(verbose_name='Целевая позиция')),
                ('check_date', models.DateTimeField(auto_now_add=True, verbose_name='Дата проверки')),
                ('query', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='positions', to='pars_settings.query', verbose_name='Запрос')),
            ],
            options={
                'verbose_name': 'Позиция',
                'verbose_name_plural': 'Позиции',
            },
        ),
    ]
