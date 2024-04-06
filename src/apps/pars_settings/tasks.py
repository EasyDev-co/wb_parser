from typing import List

from apps.pars_settings.models import Query
from config.celery import BaseTask, app
from django.db import transaction
from service.notify_service import NotifyService
from service.parsers import ProductPositionParser

from apps.pars_settings.models import Position


class QueryUpdater:
    @staticmethod
    def update_position(query: Query, updated_position: int) -> Position | None:
        if updated_position and updated_position != query.target_position:
            query.target_position = updated_position

            position = Position(
                query=query,
                current_position=updated_position,
                target_position=query.target_position,
            )

            return position


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

    def process(self):
        queries = Query.objects.select_related('article')
        new_positions = []
        for query in queries:
            updated_position = self.product_parser.parse_position(
                query=query.query,
                article=int(query.article.code)
            )
            position = QueryUpdater.update_position(query, updated_position)
            if position:
                new_positions.append(position)

            self.notify_service.send_message(
                message=(
                    f'Товар с артиклом <b>{query.article.code}</b> упал с '
                    f'<b>{position.target_position}</b> позиции на <b>{updated_position}(ю)</b>'
                )
            )

            if len(new_positions) > 2500:
                with transaction.atomic():
                    self._bulk_create_positions(new_positions)
                    new_positions = []

        if new_positions:
            self._bulk_create_positions(new_positions)


start_parse_send_message_task = app.register_task(StartParseSendMessageTask())
