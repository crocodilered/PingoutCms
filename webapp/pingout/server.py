import json
import struct
import socket
import ssl
import crcmod.predefined
import requests
from requests.adapters import HTTPAdapter
from urllib3 import PoolManager


__all__ = ['Server']


SERVER_PORT_SOCKET = 8091
SERVER_PORT_HTTPS = 443
SERVER_HOST = '82.146.41.247'
SERVER_CERT = '../cert/cert_dev.dat'

# server_host = '188.120.251.22'  # server
# server_cert = '/var/radar/cert/cert.dat'
# server_host = '82.146.41.18'  # master
# server_cert = '/var/radar/cert/cert_master.dat'


class Server:

    def __init__(self, server_host, server_port, server_https_port, server_cert):

        self._server_host = server_host
        self._server_port = server_port
        self._server_https_port = server_https_port
        self._server_cert = server_cert

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connection = ssl.wrap_socket(self.socket,
                                          ssl_version=ssl.PROTOCOL_TLSv1_2,
                                          ca_certs=self._server_cert,
                                          cert_reqs=ssl.CERT_REQUIRED)
        self.connection.connect((self._server_host, self._server_port))

    def _read_socket(self):
        packet_header = self.connection.recv(8)
        request_header = self.connection.recv(5)
        body_size, crc, type, code = struct.unpack('<LLBL', packet_header + request_header)
        r = b''
        while len(r) < body_size:
            chunk = self.connection.recv(body_size - len(r))
            if chunk == '':
                break
            r += chunk
        if crcmod.predefined.mkCrcFun('crc-32c')(request_header + r) != crc:
            return 1, None
        return code, json.loads(r.decode('utf-8'))

    def _write_socket(self, data):
        try:
            data_json = json.dumps(data).encode('utf-8')
            request_header = struct.pack('<BL', 1, 2)
            packet_header = struct.pack('<LL',
                                        len(data_json),
                                        crcmod.predefined.mkCrcFun('crc-32c')(request_header + data_json))
            self.connection.sendall(packet_header + request_header + data_json)
            while True:
                code, r = self._read_socket()
                if code == 0:
                    pass  # got_server_msg
                elif code == 2:
                    return r
                else:
                    raise RuntimeError()
        except:
            raise
            pass

    #  PUBLIC  #########################################################################################################

    def action(self, cmd, token='', args=None):
        data = [cmd]
        if cmd not in ['send_otp', 'validate_otp']:
            data += [token]
        print(data + [args])
        resp = self._write_socket(data + [args])
        return resp

    def upload_file(self, token, file_data):
        session = requests.Session()
        session.mount('https://', Tls12HttpAdapter())
        file_name = None
        files = {
            'file': ('file', file_data, 'image/jpeg'),
            'json': ('file', json.dumps(['upload', token]), 'application/json')
        }
        r = session.post("https://%s:%s/" % (self._server_host, self._server_https_port),
                         files=files, verify=self._server_cert)
        if r.status_code == 200:
            response = json.loads(r.text)
            if response["code"] == 0:
                file_name = response["file_name"]
        return file_name


class Tls12HttpAdapter(HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = PoolManager(num_pools=connections, maxsize=maxsize, block=block,
                                       ssl_version=ssl.PROTOCOL_TLSv1_2, assert_hostname=False)


if __name__ == "__main__":
    sess = Server(SERVER_HOST, SERVER_PORT, SERVER_HTTPS_PORT, SERVER_CERT)

    # send_otp = sess.action('send_otp', args={'phone_number': '+79163140864'})
    validate_otp = sess.action('validate_otp', args={
        'phone_number': '+79163140864',
        'one_time_password': 4499, #  send_otp['one_time_password'],
        'install_id': "webapp",
        'os_id': 0,
        'device_name': "webapp"
    })
    token = validate_otp['token']
    user_id = int(validate_otp['user_id'])

    print('Server is alive (%s - %s).' % (user_id, token) if user_id else 'server is dead.')
