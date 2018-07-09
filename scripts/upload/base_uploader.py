""" Base class for uploader workers """


import random
import requests
import logging
import time
from webapp.libs.server import Server
from webapp.libs.point import Point
from scripts.libs.config_reader import ConfigReader


__all__ = ['BaseUploader']


class BaseUploader(object):
    PING_TITLE_MAX_LEN = int(255 / 2)
    PING_DESCRIPTION_MAX_LEN = int(4095 / 2)

    def __init__(self, config_file_path):
        if config_file_path:
            self.config = ConfigReader(config_file_path)

            # User who will upload credentials
            self.USER_ID = self.config.get_int('Upload', 'upload.user_id')
            self.TOKEN = self.config.get('Upload', 'upload.user_token')
            self.TIMEOUT = self.config.get_float('Upload', 'upload.timeout')

            # Dict with tuples as key for fast finding
            self.existing_pings = {}

            # Pingout server config
            server_host = self.config.get('PingOut', 'server.host')
            server_port_socket = self.config.get_int('PingOut', 'server.port_socket')
            server_port_https = self.config.get_int('PingOut', 'server.port_https')
            server_cert = self.config.get('PingOut', 'server.cert')
            self.server = Server(server_host, server_port_socket, server_port_https, server_cert)

            # HTTP session to download data
            self.requests_session = requests.session()

            # Logger
            self.logger = logging.getLogger('uploader')
            logging.basicConfig(level=logging.INFO)

            # Counters
            self.counter_pings_created = 0  # Number of created pings
            self.counter_errors = 0  # Number of errors while ping creation
        else:
            raise BaseUploaderNoCfgFileException

    @staticmethod
    def gen_title_from_text(text: str):
        """ Generate title from long string """
        text = text.replace('\n', ' ')
        text = text.replace('  ', ' ')
        if len(text) < 35:
            return text
        else:
            r = ''
            tokens = text.split(' ')
            while len(tokens) > 0 and len(r) < 35:
                r += tokens.pop(0) + ' '
            r = r.strip()
            if r[-1] in '.,:(-':
                r = r[:-1]
            hellip = '…' if len(r) < len(text) else ''
            return r + hellip

    @staticmethod
    def get_rand_color():
        """ Simply returns random color """
        return random.randrange(0, 12)

    def is_ping_exists(self, ping):
        """
        Test if there is such ping on the server.
        Approach: search ping with full title and if found... We got this sonofabitch!
        :param ping:
        :return:
        """
        response = self.server.action('search', self.TOKEN, {'text': ping['title']})
        if response and 'found' in response and len(response['found']) > 0 and 'ping_id' in response['found'][0]:
            return True
        else:
            return False

    def create_ping(self, data):
        """ Create one ping """
        point = Point(0, 0)
        point.from_location(float(data['lon']), float(data['lat']))
        ping = {
            'x': int(point.x),
            'y': int(point.y),
            'title': self.gen_title_from_text(data['text']),
            'description': data['text'][:self.PING_DESCRIPTION_MAX_LEN],
            'color': self.get_rand_color()
        }

        log_str = 'Creating ' + ping['title'] + ':'

        if self.is_ping_exists(ping):
            # Ping is existing
            log_str += ' already in.'
        else:
            # Populate tags they are here
            if 'tags' in data:
                log_str += ' got tags;'
                ping['tags'] = data['tags']
            # Populate image
            if 'image' in data:
                # download image
                log_str += ' got image info;'
                image_response = self.requests_session.get(data['image'], stream=True)
                if image_response.status_code == 200:
                    log_str += ' image downloaded;'
                    # upload image to server
                    file_name = self.server.upload_file(self.TOKEN, image_response.content)
                    if file_name:
                        log_str += ' image assigned;'
                        ping['file_name'] = file_name
                        ping['color'] = 0
                    else:
                        log_str += ' image NOT assigned (no filename came from server);'
                else:
                    log_str += ' got http error while downloading image (%s);' % image_response.status_code
            response = self.server.action('create_ping', self.TOKEN, ping)
            if response['code'] == 0:
                self.counter_pings_created += 1
                log_str += ' done.'
            else:
                self.counter_errors += 1
                log_str += ' error (%s).' % response['code']

        self.logger.info(log_str)

    def sleep(self):
        time.sleep(self.TIMEOUT)


class BaseUploaderNoCfgFileException(Exception):
    pass
