from __future__ import print_function

import os.path
import pickle
import time
import logging

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config.settings import GOOGLE_SHEETS_SPREADSHEET_ID

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GoogleSheet:
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

    def __init__(self):
        creds = None
        self.sheets_api_client = None
        token_path = os.path.join('apps', 'pars_settings', 'google_sheets', 'token.pickle')
        credentials_path = os.path.join('apps', 'pars_settings', 'google_sheets', 'credentials.json')

        if os.path.exists(token_path):
            with open(token_path, 'rb') as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_path, self.SCOPES)
                creds = flow.run_local_server(port=0)
            with open(token_path, 'wb') as token:
                pickle.dump(creds, token)

        self.sheets_api_client = build('sheets', 'v4', credentials=creds)

    def create_new_sheet(self, sheet_title):
        requests = [{
            'addSheet': {
                'properties': {
                    'title': sheet_title,
                }
            }
        }]
        body = {
            'requests': requests
        }

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
                logger.error(f"Произошла ошибка: {error}")
                if error.resp.status in [500, 502, 503, 504]:
                    time.sleep(2 ** attempt)
                else:
                    break
        return None

    def get_range_values(self, range):
        result = self.sheets_api_client.spreadsheets().values().get(spreadsheetId=GOOGLE_SHEETS_SPREADSHEET_ID, range=range).execute()
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
        result = self.sheets_api_client.spreadsheets().values().batchUpdate(spreadsheetId=GOOGLE_SHEETS_SPREADSHEET_ID,
                                                                  body=body).execute()

    def get_last_sheet_number(self):
        spreadsheet = self.sheets_api_client.spreadsheets().get(spreadsheetId=GOOGLE_SHEETS_SPREADSHEET_ID).execute()
        sheet_list = spreadsheet.get('sheets')
        sheet_id = int(sheet_list[-1]['properties']['title'][4:])
        return sheet_id

    def header_of_sheet(self, list_num):
        header_value = [
            [
                'Магазин', 'Запрос', 'Артикул', 'Текущая страница', 'Текущая позиция', 'Дата'
            ],
        ]
        header_range = f'List{list_num}!A1:M1'
        self.update_range_values(header_range, header_value)

    def google_sheet_export(self, data):
        sheet_title_number = self.get_last_sheet_number()
        default_range = f'List{sheet_title_number}!A1:M2000'
        values = self.get_range_values(default_range)

        if len(values) == 0:
            self.header_of_sheet(sheet_title_number)
            time.sleep(2)
            test_range = f'List{sheet_title_number}!A{len(values) + 2}:M2000'
        else:
            test_range = f'List{sheet_title_number}!A{len(values) + 1}:M2000'

        self.update_range_values(test_range, data)
        time.sleep(2)

        if len(values) >= 600:
            self.create_new_sheet(f'List{sheet_title_number + 1}')
