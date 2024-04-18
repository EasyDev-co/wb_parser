import json
import requests

from django.conf import settings


class NotifyService:
    def __init__(self, bot_token):
        self.bot_token = bot_token

    def send_message(self, message):
        api_url = settings.TELEGRAM_API_URL.format(self.bot_token)
        payload = {
            "chat_id": settings.CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }
        headers = {
            "Content-Type": "application/json"
        }
        response = requests.post(api_url, data=json.dumps(payload), headers=headers)
        return response.json()
