from django.conf import settings

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

    def _send_notification(
            self,
            query: Query = None,
            position: Position = None,
            message_type=settings.DEFAULT,
    ):
        if message_type == settings.UPDATED:
            self.notify_service.send_message(
                message=(
                    f'Товар с артиклом <b>{query.article.code}</b> сместился с '
                    f'<b>{query.target_position}</b> позиции на '
                    f'<b>{position.current_position}</b>(ю)\n\n'
                    f'<b>Целевая позиция</b>={query.target_position}'
                )
            )
        elif message_type == settings.NOT_FOUND:
            self.notify_service.send_message(
                message=(
                    f'Товар с артикком <b>{query.article.code}</b> не найден'
                )
            )
        else:
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
                self._send_notification(
                    query=query,
                    message_type=settings.NOT_FOUND
                )
            else:
                self._send_notification(
                    query=query,
                    position=position,
                    message_type=settings.DEFAULT,
                )
                if updated_position > query.target_position:
                    self._send_notification(
                        query=query,
                        position=position,
                        message_type=settings.UPDATED
                    )

            if len(new_positions) > 2500:
                bulk_create_positions(new_positions)
                new_positions = []

        if new_positions:
            bulk_create_positions(new_positions)


start_parse_send_message_task = app.register_task(StartParseSendMessageTask())
