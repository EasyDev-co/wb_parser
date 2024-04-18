from django.conf import settings

from config.celery import BaseTask, app
from service.notify_service import NotifyService
from service.parsers import ProductPositionParser
from apps.pars_settings.models import Position, Query
from apps.pars_settings.service import QueryUpdater, MessageType, bulk_create_positions


class StartParseSendMessageTask(BaseTask):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parse_results_service = NotifyService(bot_token=settings.PARSE_RESULT_BOT_TOKEN)
        self.updates_service = NotifyService(bot_token=settings.UPDATES_BOT_TOKEN)

        self.product_parser = ProductPositionParser()

    @staticmethod
    def _get_message(
            query: Query = None,
            updated_position: int = None,
            message_type: MessageType = MessageType.DEFAULT,
    ) -> str:
        if message_type == MessageType.UPDATED:
            return (
                    f'Товар по запросу <b>"{query.query}"</b> сместился с '
                    f'<b>{query.target_position}</b> позиции на '
                    f'<b>{updated_position}</b>(ю)\n\n'
                    f'<b>Целевая позиция</b>: {query.target_position}\n'
                    f'<b>Текущая позиция</b>: {updated_position}\n\n\n'
                    )
        elif message_type == MessageType.NOT_FOUND:
            return (
                    f'<b>Ключевой запрос:</b> {query.query}\n'
                    f'<b>Артикул:</b> {query.article.code} - <b>не найдено</b>\n\n\n'
                )
        else:
            return (
                    f'<b>Ключевой запрос:</b> {query.query}\n'
                    f'<b>Артикул:</b> {query.article.code} - {updated_position} <b>позиция</b>\n\n\n'
                )

    def process(self):
        queries = list(Query.objects.select_related('article'))
        new_positions = []
        default_info_message = '<strong>Информация по товарам 📊:</strong>\n\n'
        updated_info_message = '<strong>Обновление позиций товаров 📈:</strong>\n\n'

        for query in queries:
            updated_position = self.product_parser.parse_position(
                query=query.query,
                article=int(query.article.code)
            )
            position = QueryUpdater.update_position(query, updated_position)
            new_positions.append(position)
            if not updated_position:
                default_info_message += self._get_message(
                    query=query,
                    message_type=MessageType.NOT_FOUND
                )
            else:
                default_info_message += self._get_message(
                    query=query,
                    updated_position=updated_position,
                    message_type=MessageType.DEFAULT,
                )
                if updated_position > query.target_position:
                    updated_info_message += self._get_message(
                        query=query,
                        updated_position=updated_position,
                        message_type=MessageType.UPDATED,
                    )

            if len(new_positions) > 2500:
                bulk_create_positions(new_positions)
                new_positions = []

        if len(default_info_message) > 30:
            self.parse_results_service.send_message(default_info_message)
        if len(updated_info_message) > 30:
            self.updates_service.send_message(updated_info_message)
        if new_positions:
            bulk_create_positions(new_positions)


start_parse_send_message_task = app.register_task(StartParseSendMessageTask())
