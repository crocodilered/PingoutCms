""" Base class for uploader workers """


import random
import requests
import logging
from webapp.libs.server import Server
from webapp.libs.point import Point
from scripts.libs.config_reader import ConfigReader


__all__ = ['BaseUploader']


class BaseUploader(object):

    def __init__(self, config_file_path):
        if config_file_path:
            self.config = ConfigReader(config_file_path)

            # User who will upload credentials
            self.USER_ID = int(self.config.get('Upload', 'upload.user_id'))
            self.TOKEN = self.config.get('Upload', 'upload.user_token')

            # Dict with tuples as key for fast finding
            self.existing_pings = {}

            # Pingout server config
            server_host = self.config.get('PingOut', 'server.host')
            server_port_socket = int(self.config.get('PingOut', 'server.port_socket'))
            server_port_https = int(self.config.get('PingOut', 'server.port_https'))
            server_cert = self.config.get('PingOut', 'server.cert')
            self.server = Server(server_host, server_port_socket, server_port_https, server_cert)

            # HTTP session to download data
            self.requests_session = requests.session()

            self.logger = logging.getLogger('uploader')
            logging.basicConfig(level=logging.WARN)
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

    def load_existing_pings(self):
        """ Load existing pings for doubles testing """
        self.logger.info('Loading existing pings...')

        ping_ids = []
        # Lets pretend YL got less than 1000 records by hour
        response = self.server.action('get_news_feed', self.TOKEN, {'limit': 100, 'user_id': self.USER_ID})
        if response['code'] == 0:
            for ping_id in (int(obj['ping_id']) for obj in response['news_feed'] if 'ping_id' in obj):
                ping_ids.append(ping_id)
        else:
            self.logger.error('Got response error when loading ids: %s' % response['code'])

        if ping_ids:
            response = self.server.action('get_ping_info', self.TOKEN, {'ping_ids': ping_ids})
            if response['code'] == 0:
                # We need location and title only, so filter!
                for ping in response['pings']:
                    # self.existing_pings[(ping['x'], ping['y'], ping['title'])] = True
                    self.existing_pings[ping['title']] = True
            else:
                self.logger.error('Got response error when loading pings: %s' % response['code'])

        self.logger.info('Got %s records' % len(self.existing_pings))

    def create_ping(self, data):
        """ Create one ping """
        point = Point(0, 0)
        point.from_location(float(data['lon']), float(data['lat']))
        x = int(point.x)
        y = int(point.y)
        title = self.gen_title_from_text(data['text'])
        log_str = 'Creating ' + title + ':'

        if title in self.existing_pings:
            # Ping is existing
            log_str += ' already in.'
        else:
            ping = {
                'x': x,
                'y': y,
                'title': title,
                'description': data['text'],
                'color': self.get_rand_color()
            }
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
            response = self.server.action("create_ping", self.TOKEN, ping)
            if response['code'] == 0:
                log_str += ' done.'
            else:
                log_str += ' error (%s).' % response['code']
        print(log_str)


class BaseUploaderNoCfgFileException(Exception):
    pass
