from __future__ import print_function

import os
import pickle
import time
import logging

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config.settings import GOOGLE_SHEETS_SPREADSHEET_ID, GOOGLE_SHEETS_SCOPES

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GoogleSheet:
    def __init__(self):
        credentials_path = os.path.join('apps', 'pars_settings', 'google_sheets', 'credentials.json')

        try:
            creds = Credentials.from_service_account_file(credentials_path, scopes=GOOGLE_SHEETS_SCOPES)
            self.sheets_api_client = build('sheets', 'v4', credentials=creds)
            logger.info("Google Sheets API клиент успешно инициализирован.")
        except Exception as e:
            logger.error(f"Ошибка инициализации Google Sheets API клиента: {e}")
            raise

    def create_new_sheet(self, sheet_title):
        requests = [{
            'addSheet': {
                'properties': {
                    'title': sheet_title,
                }
            }
        }]
        body = {'requests': requests}
        retries = 3
        for attempt in range(retries):
            try:
                response = self.sheets_api_client.spreadsheets().batchUpdate(
                    spreadsheetId=GOOGLE_SHEETS_SPREADSHEET_ID,
                    body=body
                ).execute()
                logger.info(f"Таблица '{sheet_title}' успешно создана.")
                return response
            except HttpError as error:
                logger.error(f"Произошла ошибка при создании листа {sheet_title}: {error}")
                if error.resp.status in [500, 502, 503, 504]:
                    time.sleep(2 ** attempt)
                else:
                    break
        return None

    def clear_sheet(self, sheet_title):
        try:
            request = self.sheets_api_client.spreadsheets().values().clear(
                spreadsheetId=GOOGLE_SHEETS_SPREADSHEET_ID,
                range=sheet_title
            )
            response = request.execute()
            logger.info(f"Лист '{sheet_title}' успешно очищен.")
            return response
        except HttpError as error:
            logger.error(f"Произошла ошибка при очистке листа {sheet_title}: {error}")
            return None

    def get_range_values(self, range):
        result = self.sheets_api_client.spreadsheets().values().get(
            spreadsheetId=GOOGLE_SHEETS_SPREADSHEET_ID, range=range).execute()
        values = result.get('values', [])
        return values

    def update_range_values(self, range, values):
        data = [{
            'range': range,
            'values': values
        }]
        body = {
            'valueInputOption': 'USER_ENTERED',
            'data': data
        }
        result = self.sheets_api_client.spreadsheets().values().batchUpdate(
            spreadsheetId=GOOGLE_SHEETS_SPREADSHEET_ID, body=body).execute()

    def get_last_sheet_number(self):
        spreadsheet = self.sheets_api_client.spreadsheets().get(spreadsheetId=GOOGLE_SHEETS_SPREADSHEET_ID).execute()
        sheet_list = spreadsheet.get('sheets')
        sheet_id = int(sheet_list[-1]['properties']['title'][4:])
        return sheet_id

    def header_of_sheet(self, list_num):
        header_value = [
            [
                'Магазин', 'Запрос', 'Артикул', 'Текущая страница', 'Текущая позиция', 'Дата', 'Статус',
            ],
        ]
        header_range = f'List{list_num}!A1:M1'
        self.update_range_values(header_range, header_value)

    def google_sheet_export(self, data):
        self.clear_sheet('List1')
        self.header_of_sheet(1)
        time.sleep(2)
        sheet_range = f'List1!A2:M10000'
        self.update_range_values(sheet_range, data)
        time.sleep(2)
