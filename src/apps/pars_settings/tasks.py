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

    def _send_updated_position_notification(self, query: Query, position: Position):
        self.notify_service.send_message(
            message=(
                f'Товар с артиклом <b>{query.article.code}</b> сместился с '
                f'<b>{query.target_position}</b> позиции на '
                f'<b>{position.current_position}</b>(ю)\n\n'
                f'<b>Целевая позиция</b>={query.target_position}'

            )
        )

    def _send_error_notification(self, query: Query):
        self.notify_service.send_message(
            message=(
                f'Товар с артикком <b>{query.article.code}</b> не найден'
            )
        )

    def _send_default_notification(self, query: Query, position: Position):
        self.notify_service.send_message(
            message=(
                '<strong>Информация о товаре:</strong>\n\n'
                f'<b>Артикул:</b> {query.article.code}\n\n'
                f'<b>Запрос:</b> {query.query}\n\n'
                f'<b>Текущая позиция:</b> {position.current_position}'
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
            position = QueryUpdater.update_position(query, updated_position)
            new_positions.append(position)
            if not updated_position:
                self._send_error_notification(query)
            else:
                self._send_default_notification(query, position)
                if updated_position > query.target_position:
                    self._send_updated_position_notification(query, position)

            if len(new_positions) > 2500:
                bulk_create_positions(new_positions)
                new_positions = []

        if new_positions:
            bulk_create_positions(new_positions)


start_parse_send_message_task = app.register_task(StartParseSendMessageTask())
