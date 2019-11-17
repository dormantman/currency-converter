import json
import traceback

import urllib3
from urllib3 import HTTPResponse


class CurrencyParser:
    def __init__(self):
        self.http = urllib3.PoolManager()

    def parse(self):
        url = 'https://www.cbr-xml-daily.ru/daily_json.js'

        try:
            response = self.http.request('GET', url)

        except ConnectionError:
            return {
                'error': 'Error getting data from service.'
            }

        try:
            return json.loads(response.data)

        except json.decoder.JSONDecodeError:
            return {
                'error': 'Failed to get data from the service. Service is unavailable'
            }

    def get_currency(self, currency: str = 'USD'):
        data = self.parse()

        parse_error = data.get('error')
        if parse_error:
            return data

        try:
            currencies = data['Valute']

            try:
                currency_data = currencies[currency.upper()]

            except KeyError:
                return {
                    'error': 'No currencies named "%s" found' % currency
                }

            return {
                'date': data['Date'],
                'code': {
                    'num': currency_data['NumCode'],
                    'label': currency_data['CharCode']
                },
                'name': currency_data['Name'],
                'rate': currency_data['Value'],
            }

        except KeyError:
            return {
                'error': 'Internal error. The format of the data to receive has been changed'
            }
