from apps.pars_settings.models import Query
from config.celery import BaseTask, app
from service.notify_service import NotifyService
from service.parsers import ProductPositionParser


class StartParseSendMessageTask(BaseTask):
    auto_retry_for = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.notify_service = NotifyService()
        self.product_parser = ProductPositionParser()

    def procces(self):
        queries = Query.objects.select_related('article')
        for query in queries:
            updated_position = self.product_parser.parse_position(
                query=query.query,
                article=int(query.article.code)
            )
            if updated_position and updated_position != query.target_position:
                query.target_position = updated_position
                query.positions.update(current_position=updated_position)
                query.save()

                self.notify_service.send_message(
                    message=(
                        f'Товар с артиклом <b>{query.article.code}</b> упал с '
                        f'<b>{query.target_position}</b> позиции на <b>{updated_position}(ю)</b>'
                    )
                )


start_parse_send_message_task = app.register_task(StartParseSendMessageTask())



