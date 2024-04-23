import json
import requests

from django.conf import settings


class NotifyService:
    def __init__(self, token):
        self.token = token

    def send_message(self, message):
        api_url = settings.TELEGRAM_API_URL.format(self.token)
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
