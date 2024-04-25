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
                f'🆔: <b>"{query.article.code}"</b>\n'
                f'🅿:<b>{query.target_page}</b> ✅:<b>{query.target_position}</b> -'
                f'🅿:<b>{updated_page}</b> ✅:<b>{updated_position}</b>\n'
            )
        elif message_type == MessageType.NOT_FOUND:
            return (
                f'<b>🆔:</b> <b>"{query.article.code}"</b> - <b>не найдено</b>\n'
            )
        else:
            return (
                f'<b>🆔:</b> <b>"{query.article.code}"</b>'
                f'🅿:<b>{updated_page}</b> ✅:<b>{updated_position}</b>\n'
            )

    def process(self):
        last_query = ''
        new_positions = []

        shops = list(Shop.objects.all())
        default_info_message = '<strong>Информация по товарам 📊:</strong>\n\n'
        updated_info_message = '<strong>Обновление позиций товаров 📈:</strong>\n\n'

        for shop in shops:
            default_info_message += f'<strong>{shop.name}</strong>\n\n'
            updated_info_message += f'<strong>{shop.name}</strong>\n\n'

            for article in shop.articles.all():
                if article.queries.last().query != last_query:
                    default_info_message += f'\n<b>🔑:</b> {article.queries.last().query}\n'

                for query in Query.objects.select_related('article').filter(article__code=article.code):
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

                last_query = article.queries.last().query

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
