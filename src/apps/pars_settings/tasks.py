from django.conf import settings

from config.celery import BaseTask, app
from service.notify_service import NotifyService
from service.parsers import ProductPositionParser
from apps.pars_settings.models import Position, Query
from apps.pars_settings.service import QueryUpdater, MessageType, bulk_create_positions
from apps.pars_settings.models import Shop
from service.utils import get_targets, get_clean_position


class StartParseSendMessageTask(BaseTask):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parse_results_service = NotifyService(token=settings.PARSE_RESULT_BOT_TOKEN)
        self.updates_service = NotifyService(token=settings.UPDATES_BOT_TOKEN)

        self.product_parser = ProductPositionParser()

    @staticmethod
    def _get_message(
            query: Query = None,
            updated_page: int = None,
            updated_position: int = None,
            message_type: MessageType = MessageType.DEFAULT,
    ) -> str:
        if message_type == MessageType.UPDATED:
            return (
                f'Товар <b>"{query.article.name}"</b> сместился с '
                f'<b>{query.target_page}</b> '
                f'страницы <b>{query.target_position}</b> позиции на '
                f' <b>{updated_page}</b> страницу '
                f'<b>{updated_position}</b>(ю) позицию\n\n'
                f'<b>Целевая позиция</b>:'
                f' {updated_page} страница {query.target_position} позиция\n'
                f'<b>Текущая позиция</b>: '
                f'{updated_page} страница {updated_position} позиция\n\n'
            )
        elif message_type == MessageType.NOT_FOUND:
            return (
                f'<b>Ключевой запрос:</b> {query.query}\n'
                f'<b>Артикул:</b> {query.article.code} - <b>не найдено</b>\n\n'
            )
        else:
            return (
                f'<b>Ключевой запрос:</b> {query.query}\n'
                f'<b>Артикул:</b> {query.article.code} - '
                f'<b>{updated_page}</b> страница <b>{updated_position}</b> позиция\n\n'
            )

    def process(self):
        new_positions = []

        shops = list(Shop.objects.all())
        default_info_message = '<strong>Информация по товарам 📊:</strong>\n\n'
        updated_info_message = '<strong>Обновление позиций товаров 📈:</strong>\n\n'

        for shop in shops:

            default_info_message += f'<strong>{shop.name}</strong>\n\n'
            updated_info_message += f'<strong>{shop.name}</strong>\n\n'
            for article in shop.articles.all():
                for query in article.queries.all():
                    parsed_position = self.product_parser.parse_position(
                        query=query.query,
                        article=int(article.code)
                    )
                    updated_page, updated_position = get_targets(parsed_position)
                    position = QueryUpdater.update_position(
                        query, updated_page, updated_position
                    )
                    new_positions.append(position)

                    if not updated_position:
                        default_info_message += self._get_message(
                            query=query,
                            message_type=MessageType.NOT_FOUND
                        )
                    else:
                        default_info_message += self._get_message(
                            query=query,
                            updated_page=updated_page,
                            updated_position=updated_position,
                            message_type=MessageType.DEFAULT,
                        )
                        if (get_clean_position(updated_page, updated_position) >
                                get_clean_position(query.target_page, query.target_position)):

                            updated_info_message += self._get_message(
                                query=query,
                                updated_page=updated_page,
                                updated_position=updated_position,
                                message_type=MessageType.UPDATED,
                            )

                if len(default_info_message) > 3750:
                    self.parse_results_service.send_message(default_info_message)
                if len(updated_info_message) > 3750:
                    self.updates_service.send_message(updated_info_message)

                if len(new_positions) > 2500:
                    bulk_create_positions(new_positions)
                    new_positions = []
            if len(default_info_message) > 50:
                self.parse_results_service.send_message(default_info_message)
            if len(updated_info_message) > 50:
                self.updates_service.send_message(updated_info_message)

            default_info_message, updated_info_message = '', ''

        if new_positions:
            bulk_create_positions(new_positions)


start_parse_send_message_task = app.register_task(StartParseSendMessageTask())
