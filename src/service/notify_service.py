import json
import requests

from django.conf import settings

from apps.tg_users.models import TelegramUser


class NotifyService:
    def __init__(self, token):
        self.token = token

    def send_message(self, message):
        api_url = settings.TELEGRAM_API_URL.format(self.token)

        headers = {
            "Content-Type": "application/json"
        }
        responses_data = []

        for user in TelegramUser.objects.values('telegram_id'):
            payload = {
                "chat_id": user.get('telegram_id'),
                "text": message,
                "parse_mode": "HTML"
            }
            response = requests.post(api_url, data=json.dumps(payload), headers=headers)
            responses_data.append(response.json())
        return responses_data
