import json
import struct
import socket
import ssl
import crcmod.predefined
import requests
from requests.adapters import HTTPAdapter
from urllib3 import PoolManager
import logging


__all__ = ["Server"]


class Server:
    """
    Реализуется связь с сервером Pingout.
    Иван говорит, что нужно делать для каждого Pingout-пользователя отдельное соединение,
    Потому:
    """

    # TODO: Это Plugin в чистом виде, так его и необходимо реализовать.

    # TODO: вынести все HTTP-дела, связанные с upload_file, в отдельный класс

    # TODO: Класс Server убить, вместо него реализовать класс Connection со свойством token
    #       Объекты Connection складывать в какой-нть менеджер. Публиковать в bus событие 'get-connection', к примеру.

    def __init__(self, server_host, server_port, server_https_port, server_cert):

        self._logger = logging.getLogger('PingoutServer')

        self._server_host = server_host
        self._server_port = server_port
        self._server_https_port = server_https_port
        self._server_cert = server_cert
        self._connection = self._connect()

    def _connect(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn = ssl.wrap_socket(sock, ssl_version=ssl.PROTOCOL_TLSv1_2, ca_certs=self._server_cert, cert_reqs=ssl.CERT_REQUIRED)
        conn.connect((self._server_host, self._server_port))
        return conn

    def _read_socket(self):
        packet_header = self._connection.recv(8)
        request_header = self._connection.recv(5)
        body_size, crc, type, code = struct.unpack("<LLBL", packet_header + request_header)
        r = b""
        while len(r) < body_size:
            chunk = self._connection.recv(body_size - len(r))
            if chunk == "":
                break
            r += chunk
        if crcmod.predefined.mkCrcFun("crc-32c")(request_header + r) != crc:
            return 1, None
        return code, json.loads(r.decode("utf-8"))

    def _write_socket(self, data):

        data_json = json.dumps(data).encode("utf-8")
        request_header = struct.pack("<BL", 1, 2)
        packet_header = struct.pack("<LL",
                                    len(data_json),
                                    crcmod.predefined.mkCrcFun("crc-32c")(request_header + data_json))

        while True:
            try:
                self._connection.sendall(packet_header + request_header + data_json)
                break
            except socket.error:
                self._logger.error("Socket closed, trying to reconnect.")
                self._connection = self._connect()

        while True:
            code, r = self._read_socket()
            if code == 0:
                pass  # got_server_msg
            elif code == 2:
                return r
            else:
                raise RuntimeError()

    #  PUBLIC  #########################################################################################################

    def action(self, cmd, token="", args=None):
        data = [cmd]
        if cmd not in ["send_otp", "validate_otp"]:
            data += [token]
        # print(data + [args])
        response = self._write_socket(data + [args])
        if response["code"] != 0:
            self._logger.warning("Pingout server response has non-zero error code! Cmd: %s, args: %s, response: %s"
                                 % (cmd, args, response))
        return response

    def upload_file(self, token, file_data):
        """
        Загружает файл на сервер, возвращает новое имя файла, выданное сервером
        :param token: токен для соединения
        :param file_data: файл
        :return:
        """
        r = None
        session = requests.Session()
        session.mount("https://", Tls12HttpAdapter())
        response = session.post(
            "https://%s:%s/api?action=upload&token=%s" % (self._server_host, self._server_https_port, token),
            headers={"Content-Type": "image/jpeg"},
            data=file_data,
            verify=self._server_cert
        )
        self._logger.debug(response)
        if response.status_code == 200:
            response_json = json.loads(response.text)
            if response_json["code"] == 0 and response_json["file"]:
                r = response_json["file"]["file_name"]
        return r

    def get_file_url(self, filename, image_size=None):
        if image_size:
            return "http://%s/%s_%s" % (self._server_host, filename, image_size)
        else:
            return "http://%s/%s" % (self._server_host, filename)


class Tls12HttpAdapter(HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = PoolManager(num_pools=connections, maxsize=maxsize, block=block,
                                       ssl_version=ssl.PROTOCOL_TLSv1_2, assert_hostname=False)
