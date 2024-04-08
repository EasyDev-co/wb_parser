from config.celery import BaseTask, app
from service.notify_service import NotifyService
from service.parsers import ProductPositionParser
from apps.pars_settings.models import Position, Query
from apps.pars_settings.service import QueryUpdater, bulk_create_positions


class StartParseSendMessageTask(BaseTask):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.notify_service = NotifyService()
        self.product_parser = ProductPositionParser()

    def _send_position_notification(self, query: Query, position: Position):
        last_current_position = query.positions.last().current_position \
            if query.positions.last() \
            else query.target_position
        self.notify_service.send_message(
            message=(
                f'Товар с артиклом <b>{query.article.code}</b> сместился с '
                f'<b>{last_current_position}</b> позиции на '
                f'<b>{position.current_position}</b>(ю)\n\n'
                f'<b>Целевая позиция</b>={query.target_position}'

            )
        )

    def _send_error_notification(self, query: Query):
        self.notify_service.send_message(
            message=(
                f'Товар с артиклом <b>{query.article.code}</b> не найден'
            )
        )

    def process(self):
        queries = Query.objects.select_related('article')
        new_positions = []
        for query in queries:
            updated_position = self.product_parser.parse_position(
                query=query.query,
                article=query.article.code
            )
            position = QueryUpdater.update_position(query, updated_position)
            new_positions.append(position)
            if updated_position == 0:
                self._send_error_notification(query)
                continue
            if updated_position < query.target_position:
                self._send_position_notification(query, position)

            if len(new_positions) > 2500:
                bulk_create_positions(new_positions)
                new_positions = []

        if new_positions:
            bulk_create_positions(new_positions)


start_parse_send_message_task = app.register_task(StartParseSendMessageTask())
