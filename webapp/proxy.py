import cherrypy
from webapp.pingout.server import Server
from webapp.pingout.point import Point
from datetime import datetime
from binascii import a2b_base64


__all__ = ['PingoutCmsProxy']


class PingoutCmsProxy(object):

    def __init__(self):
        self._server = None

    def _get_server(self):
        if not self._server:
            app = cherrypy.tree.apps['']
            self._server = Server(app.config['PingOut']['server.host'],
                                  app.config['PingOut']['server.port_socket'],
                                  app.config['PingOut']['server.port_https'],
                                  app.config['PingOut']['server.cert'])
        return self._server

    def _get_identity(self):
        return cherrypy.session.get("token", None), cherrypy.session.get("user_id", None)

    def _set_identity(self, token=None, user_id=None):
        cherrypy.session['token'] = token
        cherrypy.session['user_id'] = user_id

    @cherrypy.expose(["get-code"])
    @cherrypy.tools.json_out()
    def get_code(self, phone):
        server = self._get_server()
        response = server.action("send_otp", args={"phone_number": phone})
        r = {"code": response["code"]}
        return r

    @cherrypy.expose(["sign-in"])
    @cherrypy.tools.json_out()
    def sign_in(self, phone, code):
        server = self._get_server()
        response = server.action('validate_otp', args={
            'phone_number': phone,
            'one_time_password': int(code),
            'install_id': "webapp%s" % phone,
            'os_id': 0,
            'device_name': "webapp%s" % phone
        })
        r = {"code": response["code"]}
        if response["code"] == 0:
            self._set_identity(response["token"], response["user_id"])
        return r

    @cherrypy.expose(["sign-out"])
    @cherrypy.tools.json_out()
    def sign_out(self):
        token, user_id = self._get_identity()
        if token and user_id:
            server = self._get_server()
            response = server.action('sign_out', token)
            if response["code"] == 0:
                cherrypy.session['token'] = None
                cherrypy.session['user_id'] = None
            r = {"code": response["code"]}
        else:
            #  он блять и не залогинен нигде
            r = {"code": -1}
        return r

    @cherrypy.expose(['list-pings'])
    @cherrypy.tools.json_out()
    def list_pings(self):
        token, user_id = self._get_identity()
        r = {"code": 0}
        if user_id:
            server = self._get_server()
            response = server.action('get_news_feed', token, {"limit": 100, "user_id": user_id})
            if response["code"] == 0:
                # тут нужно насобирать id-шники, превратить их в посты и отдать пользователю уже готовый список
                post_ids = event_ids = []
                for obj in response["news_feed"]:
                    if "event_id" in obj:
                        event_ids.append(obj['event_id'])
                    elif "post_id" in obj:
                        post_ids.append(obj['post_id'])
                # теперь у нас есть два массива, так сделаем два запроса, мазафака!
                if event_ids:
                    response = server.action("get_event_info", token, {"event_ids": event_ids})
                    if response["code"] == 0:
                        r['events'] = self.append_extra(response["events"])
                    else:
                        r["code"] = int(response["code"] + 10000)
                if post_ids:
                    response = server.action("get_post_info", token, {"post_ids": post_ids})
                    if response["code"] == 0:
                        r['posts'] = self.append_extra(response["posts"])
                    else:
                        r["code"] = int(response["code"] + 10000)
            else:
                r["code"] = response["code"]
        else:
            r["code"] = -1
        return r

    @cherrypy.expose(['delete-ping'])
    @cherrypy.tools.json_out()
    def delete_ping(self, ping_id, ping_type):
        """
        Удалить пинг
        """
        r = {"code": 0}
        token, user_id = self._get_identity()
        if token:
            server = self._get_server()
            ping_id_param_name = 'post_id' if ping_type == 'post' else 'event_id'
            response = server.action('delete_entity', token, {ping_id_param_name: int(ping_id)})
            r["code"] = response["code"]
        else:
            r["code"] = -1
        return r

    @cherrypy.expose(["update-ping"])
    @cherrypy.tools.json_out()
    def update_ping(self, ping_id, ping_type, ping_title, ping_description, ping_datetime, ping_color, ping_tags,
                    ping_file_data):
        """
        Обновить пинг
        """
        r = {"code": 0}

        token, user_id = self._get_identity()
        if token:
            server = self._get_server()
            if ping_type and ping_id:

                args = {
                    "%s_id" % ping_type: int(ping_id),
                    "title": ping_title,
                    "description": ping_description,
                    "color": int(ping_color),
                    "tags": ping_tags,
                }

                if ping_file_data:
                    args["file_name"] = r["file_name"] = self.get_file_name(ping_file_data)

                if ping_type == 'event':
                    args["fire_ts"] = self.str_to_timestamp(ping_datetime)
                    args["event_type"] = 1  # установил от балды
                response = server.action("update_%s" % ping_type, token, args)

                r["code"] = response["code"]
            else:
                r["code"] = -2
        else:
            r["code"] = -1
        return r

    @cherrypy.expose(["create-ping"])
    @cherrypy.tools.json_out()
    def create_ping(self, ping_lon, ping_lat, ping_title, ping_description, ping_datetime, ping_color, ping_tags,
                    ping_file_data):
        """
        Создать пинг
        """
        r = {"code": 0}
        token, user_id = self._get_identity()
        if token:
            server = self._get_server()

            p = Point(0, 0)
            p.from_location(float(ping_lon), float(ping_lat))

            args = {
                'x': p.x,
                'y': p.y,
                "title": ping_title,
                "description": ping_description,
                "color": int(ping_color),
                "tags": ping_tags
            }

            if ping_file_data:
                args["file_name"] = r["file_name"] = self.get_file_name(ping_file_data)

            ping_type = "post"

            if ping_datetime:
                ping_type = "event"
                args["fire_ts"] = self.str_to_timestamp(ping_datetime)
                args["event_type"] = 1  # установил от балды

            if ping_type and ping_lon and ping_lat:
                response = server.action('create_%s' % ping_type, token, args)
                r["code"] = response["code"]
                if "event_id" in response:
                    r["ping_id"] = response["event_id"]
                    r["ping_type"] = "event"
                if "post_id" in response:
                    r["ping_id"] = response["post_id"]
                    r["ping_type"] = "post"
            else:
                r["code"] = -2
        else:
            r["code"] = -2
        return r

    def get_file_name(self, ping_file_data):
        r = None
        if ping_file_data:
            # загрузим файл на сервер
            server = self._get_server()
            token, user_id = self._get_identity()
            ping_file_name = server.upload_file(token, a2b_base64(ping_file_data.split(",")[1]))
            if ping_file_name:
                r = ping_file_name
            return r

    @staticmethod
    def append_extra(l):
        for i in l:
            # добавим гео-координаты
            if "x" in i and "y" in i:
                p = Point(i['x'], i['y'])
                i['lng'], i['lat'] = p.get_location()
            # Добавим timestamp
            if "fire_ts" in i:
                i['fire_ts_str'] = PingoutCmsProxy.timestamp_to_str(i['fire_ts'])
        return l

    @staticmethod
    def str_to_timestamp(str):
        # str has format: dd.mm.yyyy hh:ii
        if len(str) != 16:
            raise ValueError
        dt = datetime(int(str[6:10]), int(str[3:5]), int(str[0:2]), int(str[11:13]), int(str[14:16]))
        return int(dt.timestamp())

    @staticmethod
    def timestamp_to_str(timestamp):
        # str has format: dd.mm.yyyy hh:ii
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%d.%m.%Y %H:%M")
