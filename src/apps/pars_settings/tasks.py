from typing import List

from apps.pars_settings.models import Query
from config.celery import BaseTask, app
from django.db import transaction

from service.notify_service import NotifyService
from service.parsers import ProductPositionParser
from apps.pars_settings.models import Position


class QueryUpdater:
    @staticmethod
    def update_position(query: Query, updated_position: int)\
            -> tuple[Position | None, bool]:
        """Создаем новую позицию и проверяем упал ли товар"""
        if updated_position and updated_position != query.target_position:
            last_position, created = Position.objects.get_or_create(
                id=query.positions.last().id,
                defaults={
                    'query': query,
                    'current_position': updated_position,
                    'target_position': query.target_position
                }
            )
            position = Position(
                query=query,
                current_position=updated_position,
                target_position=query.target_position
            )

            is_changed = position.current_position < last_position.current_position

            return position, is_changed


class StartParseSendMessageTask(BaseTask):
    auto_retry_for = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.notify_service = NotifyService()
        self.product_parser = ProductPositionParser()

    @staticmethod
    def _bulk_create_positions(positions: List[Position]):
        with transaction.atomic():
            Position.objects.bulk_create(positions)

    def _send_position_notification(self, query: Query, position: Position):
        last_position = query.positions.last()
        self.notify_service.send_message(
            message=(
                f'Товар с артиклом <b>{query.article.code}</b> упал с '
                f'<b>{last_position.current_position}</b> позиции на '
                f'<b>{position.current_position}</b>(ю)'
            )
        )

    def process(self):
        queries = Query.objects.select_related('article')
        new_positions = []
        for query in queries:
            updated_position = self.product_parser.parse_position(
                query=query.query,
                article=int(query.article.code)
            )
            position, is_changed = QueryUpdater.update_position(query, updated_position)
            if not position:
                continue
            new_positions.append(position)
            if is_changed:
                self._send_position_notification(query, position)

            if len(new_positions) > 2500:
                self._bulk_create_positions(new_positions)
                new_positions = []

        if new_positions:
            self._bulk_create_positions(new_positions)


start_parse_send_message_task = app.register_task(StartParseSendMessageTask())
