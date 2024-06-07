from __future__ import print_function
import os.path
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import time
from googleapiclient.discovery import build
from config.settings import GOOGLE_SHEETS_SCOPES, GOOGLE_SHEETS_SPREADSHEET_ID


class GoogleSheet:
    SPREADSHEET_ID = GOOGLE_SHEETS_SPREADSHEET_ID
    SCOPES = GOOGLE_SHEETS_SCOPES
    service = None

    def __init__(self):
        creds = None
        if os.path.exists('apps/pars_settings/google_sheets/token.pickle'):
            with open('apps/pars_settings/google_sheets/token.pickle', 'rb') as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'apps/pars_settings/google_sheets/credentials.json', self.SCOPES)

                creds = flow.run_local_server(port=0)
            with open('apps/pars_settings/google_sheets/token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        self.service = build('sheets', 'v4', credentials=creds)

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
        response = self.service.spreadsheets().batchUpdate(
            spreadsheetId=self.SPREADSHEET_ID,
            body=body
        ).execute()
        return response

    def getRangeValues(self, range):
        result = self.service.spreadsheets().values().get(spreadsheetId=self.SPREADSHEET_ID, range=range).execute()
        values = result.get('values', [])
        return values

    def updateRangeValues(self, range, values):
        data = [{
            'range': range,
            'values': values
        }]
        body = {
            'valueInputOption': 'USER_ENTERED',
            'data': data
        }
        result = self.service.spreadsheets().values().batchUpdate(spreadsheetId=self.SPREADSHEET_ID,
                                                                  body=body).execute()

    def get_last_sheet_number(self):
        spreadsheet = self.service.spreadsheets().get(spreadsheetId=self.SPREADSHEET_ID).execute()
        sheet_list = spreadsheet.get('sheets')
        sheet_id = int(sheet_list[-1]['properties']['title'][4:])
        return sheet_id


def header_of_sheet(list_num, google_sheet):
    header_value = [
        [
            'Магазин', 'Запрос', 'Артикул', 'Текущая страница', 'Текущая позиция', 'Дата'
        ],
    ]
    header_range = f'List{list_num}!A1:M1'
    google_sheet.updateRangeValues(header_range, header_value)


def google_sheet_export(google_sheet, data):
    sheet_title_number = google_sheet.get_last_sheet_number()
    default_range = f'List{sheet_title_number}!A1:M2000'
    values = google_sheet.getRangeValues(default_range)

    if len(values) == 0:
        header_of_sheet(sheet_title_number, google_sheet)
        time.sleep(2)
        test_range = f'List{sheet_title_number}!A{len(values) + 2}:M2000'
    else:
        test_range = f'List{sheet_title_number}!A{len(values) + 1}:M2000'

    google_sheet.updateRangeValues(test_range, data)
    time.sleep(2)

    if len(values) >= 600:
        google_sheet.create_new_sheet(f'List{sheet_title_number + 1}')
