from django.conf import settings

import logging

from config.celery import BaseTask, app
from service.notify_service import NotifyService
from service.parsers import ProductPositionParser
from apps.pars_settings.models import Query
from apps.pars_settings.service import QueryUpdater, MessageType, bulk_create_positions
from apps.pars_settings.models import Shop
from service.utils import get_targets, get_clean_position
from apps.pars_settings.google_sheets.google_sheets_export import GoogleSheet, google_sheet_export
from datetime import datetime


from apps.pars_settings.models import Article


class StartParseSendMessageTask(BaseTask):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parse_results_service = NotifyService(token=settings.PARSE_RESULT_BOT_TOKEN)
        self.updates_service = NotifyService(token=settings.UPDATES_BOT_TOKEN)
        self.product_parser = ProductPositionParser()
        self.google_sheet = GoogleSheet()
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def _get_message(
            query: Query = None,
            updated_page: int = None,
            updated_position: int = None,
            message_type: MessageType = MessageType.DEFAULT,
    ) -> str:
        if message_type == MessageType.NOT_FOUND:
            return (
                f'<b>"{query.article.name}"</b> - <b>не найдено</b>\n'
            )
        else:
            return (
                f'<b>"{query.article.name}"</b> - '
                f'🅿️:<b>{updated_page}</b> ✅:<b>{updated_position}</b>\n'
            )

    def process(self):
        previous_query = ''
        new_positions = []

        default_info_message = '<strong>Информация по товарам 📊:</strong>\n\n'
        updated_info_message = '<strong>Обновление позиций товаров 📈:</strong>\n\n'

        for shop in Shop.objects.all():
            default_info_message += f'<strong>{shop.name}</strong>\n'
            updated_info_message += f'<strong>{shop.name}</strong>\n\n'

            for query in Query.objects.filter(article__shop=shop).order_by('query'):
                if query.query != previous_query:
                    default_info_message += f'\n<b>🔑:</b> {query.query}\n'

                for article in Article.objects.filter(queries=query, shop=shop):

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
                        date = datetime.now().strftime('%d-%m-%Y')
                        data = [
                            [shop.name, query.query, article.code, updated_page, updated_position, date]
                        ]
                        google_sheet_export(self.google_sheet, data)
                        if (get_clean_position(updated_page, updated_position) >
                                get_clean_position(query.target_page, query.target_position)):
                            updated_info_message += self._get_message(
                                query=query,
                                updated_page=updated_page,
                                updated_position=updated_position,
                                message_type=MessageType.UPDATED,
                            )

                previous_query = query.query

                if len(default_info_message) > 3750:
                    self.parse_results_service.send_message(default_info_message)
                    default_info_message = ''
                if len(updated_info_message) > 3750:
                    self.updates_service.send_message(updated_info_message)
                    updated_info_message = ''

                if len(new_positions) > 2500:
                    bulk_create_positions(new_positions)
                    new_positions = []

            if len(default_info_message) > 50:
                self.parse_results_service.send_message(default_info_message)
            if len(updated_info_message) > 50:
                self.updates_service.send_message(updated_info_message)

            default_info_message, updated_info_message = '', ''
            previous_query = ''

        if new_positions:
            bulk_create_positions(new_positions)


start_parse_send_message_task = app.register_task(StartParseSendMessageTask())
