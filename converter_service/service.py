import json
import logging
import os
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

from converter_service.parser import CurrencyParser
from converter_service.settings import HOST, PORT, TEMPLATES_DIR

logging.basicConfig(
    format='#%(levelname)s [%(asctime)s]: %(message)s',
    level='INFO',
    handlers=[
        logging.StreamHandler()
    ],
    datefmt='%Y.%m.%d %H:%M:%S'
)


class Converter:
    def __init__(self):
        self.server = HTTPServer((HOST, PORT), ConverterHandler)

    def run(self):
        try:
            logging.info('Started httpserver on %s:%s' % (HOST, PORT))
            self.server.serve_forever()

        except KeyboardInterrupt:
            logging.info('^C received, shutting down the web server')
            self.server.server_close()


class ConverterHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        parse_path = urllib.parse.urlparse(self.path)
        path = parse_path.path.rstrip('/')
        params = urllib.parse.parse_qs(parse_path.query)

        if path == '':
            headers = {
                'Content-type': 'text/html; charset=utf-8'
            }

            self._set_response(status_code=200, headers=headers)
            self._send_template('index.html')

        elif path == '/get_currency':
            try:
                to_currency = params['to'][0]
                amount = float(params['amount'][0])

            except KeyError as error:
                logging.info('Invalud request for conversion')

                error = {'error': 'Missing parameter: "%s".' % (error.args[0])}
                return self._return_json(error, status_code=422)

            except ValueError:
                logging.info('Invalud request for conversion')

                error = {'error': 'Invalid data format. Amount data must be a number'}
                return self._return_json(error, status_code=422)

            if to_currency not in ['USD', 'RUB']:
                error = {'error': 'Invalid currency'}
                return self._return_json(error, status_code=422)

            parser = CurrencyParser()
            data = parser.get_currency()
            parser_error = data.get('error')

            if parser_error:
                logging.info('Error getting data from service')

                return self._return_json(parser_error, status_code=422)

            response = {
                'currency': data,
            }

            if to_currency == 'USD':
                logging.info('Request for conversion of %s RUB to USD' % amount)

                total = amount / data['rate']

                response['from'] = 'RUB'
                response['to'] = 'USD'
                response['amount'] = amount
                response['total'] = total

            elif to_currency == 'RUB':
                logging.info('Request for conversion of %s USD to RUB' % amount)

                total = amount * data['rate']

                response['from'] = 'USD'
                response['to'] = 'RUB'
                response['amount'] = amount
                response['total'] = total

            self._return_json(response, status_code=200)

        else:
            self._return_404()

    @staticmethod
    def _get_template_file(filename: str):
        template_path = os.path.join(TEMPLATES_DIR, filename)
        return open(template_path, mode='rb')

    def _set_response(self, status_code: int, headers: dict, message: str or None = None):
        self.send_response(status_code, message)

        for header, content in headers.items():
            self.send_header(header, content)

        self.end_headers()

    def _send_template(self, filename: str):
        with self._get_template_file(filename) as file:
            self.wfile.write(file.read())

    def _return_json(self, data: dict, status_code: int):
        headers = {
            'Content-type': 'application/json; charset=utf-8'
        }

        self._set_response(status_code=status_code, headers=headers)

        json_data = json.dumps(data, indent=2, ensure_ascii=False)
        self.wfile.write(json_data.encode())

    def _return_404(self):
        headers = {
            'Content-type': 'text/html; charset=utf-8'
        }

        self._set_response(status_code=404, message='Not Found', headers=headers)
        self._send_template('404.html')

    def log_message(self, format: str, *args):
        logging.info("%s - - %s" % (self.address_string(), format % args))
