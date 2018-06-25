"""
Script to upload today-content to Pingout from Yandex.Locals project (YL).
We'll load data from YL, transform then, and upload to Pingout (do not forget to check for doubles.

Run me once in hour!
"""

import time
from scripts.upload.yandex_local.districts import DISTRICTS
from scripts.upload.base_uploader import BaseUploader


class Uploader(BaseUploader):

    LOAD_URL_TEMPLATE = 'https://yandex.ru/local/api/feed?district=%s&type=district'

    def load_new_pings(self, district_id):
        """
        Get data from source.
        Result is list of dicts with {lat, lon, text, image, tags} properties.
        """
        r = None
        self.logger.info('Loading data for district #%s from Yandex.Locals...' % district_id)
        url = self.LOAD_URL_TEMPLATE % district_id
        response = self.requests_session.get(url)
        if response.status_code == 200 and 'json' in response.headers['Content-Type']:
            data = response.json()
            r = []
            for event_id in data['state']['events']:
                # Filter uploaded data, coz of we dun need all of them
                event = data['state']['events'][event_id]
                rec = {
                    'lat': event['point']['lat'],
                    'lon': event['point']['lon'],
                    'text': event['text']
                }
                if 'images' in event and event['images']:
                    rec['image'] = event['images'][0]['url']
                if 'tags' in event and event['tags']:
                    rec['tags'] = []
                    for i in event['tags']:
                        rec['tags'].append(i['name'])
                r.append(rec)
        else:
            self.logger.error('Got HTTP-error: ' % response.status_code)
        self.logger.info('got %s records' % len(r))
        return r

    def run(self):
        """ Upload all the pings in stash """
        self.load_existing_pings()
        self.logger.info('Start to upload pings.')
        for i in DISTRICTS:
            new_pings = self.load_new_pings(i['id'])
            for data in new_pings:
                self.create_ping(data)
                time.sleep(.5)
