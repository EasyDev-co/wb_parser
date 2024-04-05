import json
import requests

from django.conf import settings


class WBBot:
    @staticmethod
    def send_message(message):
        api_url = settings.TELEGRAM_API_URL.format(settings.BOT_TOKEN)
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
