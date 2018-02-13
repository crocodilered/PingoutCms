import cherrypy
from binascii import a2b_base64
from webapp.pingout.server import Server
from webapp.pingout.point import Point
from webapp.libs.users_lookup import UsersLookup
from webapp.libs.pings_lookup import PingsLookup


__all__ = ["PingoutCmsProxy"]


class PingoutCmsProxy(object):
    def __init__(self):
        self._server = None

    def _get_server(self):
        if not self._server:
            app = cherrypy.tree.apps[""]
            self._server = Server(app.config["PingOut"]["server.host"],
                                  app.config["PingOut"]["server.port_socket"],
                                  app.config["PingOut"]["server.port_https"],
                                  app.config["PingOut"]["server.cert"])
        return self._server

    @staticmethod
    def _get_identity():
        return cherrypy.session.get("token", None), cherrypy.session.get("user_id", None)

    @staticmethod
    def _set_identity(token=None, user_id=None):
        cherrypy.session["token"] = token
        cherrypy.session["user_id"] = user_id

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
        response = server.action("validate_otp", args={
            "phone_number": phone,
            "one_time_password": int(code),
            "install_id": "webapp%s" % phone,
            "os_id": 0,
            "device_name": "webapp%s" % phone
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
            response = server.action("sign_out", token)
            if response["code"] == 0:
                cherrypy.session["token"] = None
                cherrypy.session["user_id"] = None
            r = {"code": response["code"]}
        else:
            # он блять и не залогинен нигде
            r = {"code": -1}
        return r

    @cherrypy.expose(["list-complaints"])
    @cherrypy.tools.json_out()
    def list_complaints(self):
        """
        Запрос списока жалоб на пинги/пользователей.

        :return:
        """
        cherrypy.log("Start of list_complaints handler.")
        token, user_id = self._get_identity()
        r = {"code": 0}
        if user_id:
            server = self._get_server()
            response = server.action("get_complaint_list", token, {"limit": 100})
            if response["code"] == 0:
                cherrypy.log("got %s complains." % len(response["complaints"]))
                complaints = response["complaints"]

                # Build two arrays if users and pings ids.
                ping_ids = user_ids = []

                for complaint in complaints:
                    if "to_ping_id" in complaint:
                        ping_ids.append(int(complaint["to_ping_id"]))
                    if "to_user_id" in complaint:
                        user_ids.append(int(complaint["to_user_id"]))
                    user_ids.append(int(complaint["user_id"]))
                # Now get data for listed pings and users

                pings = users = None

                if ping_ids:
                    response = server.action("get_ping_info", token, {"ping_ids": list(set(ping_ids))})
                    if response["code"] == 0:
                        pings = PingsLookup(response["pings"])
                        # Have to add authors of complained pings t user_ids
                        for ping in response["pings"]:
                            user_ids.append(int(ping["user_id"]))
                    else:
                        r["code"] = int(response["code"] + 10000)

                if user_ids:
                    response = server.action("get_user_info", token, {"user_ids": list(set(user_ids))})
                    if response["code"] == 0:
                        users = UsersLookup(response["users"])
                    else:
                        r["code"] = int(response["code"] + 10000)

                # Now build entire complaints array
                complaints_for_response = []
                for complaint in complaints:
                    rec = {
                        "complaint_id": complaint["complaint_id"],
                        "user_id": complaint["user_id"],
                        "user_name": users.get(complaint["user_id"])["name"],
                        "reason": complaint["reason"],
                        "ts": complaint["ts"]
                    }
                    if "description" in complaint:
                        rec["description"] = complaint["description"]
                    if "to_user_id" in complaint:
                        rec["to_user_id"] = complaint["to_user_id"]
                        rec["to_user_name"] = users.get(complaint["to_user_id"])["name"]
                    if "to_ping_id" in complaint:
                        rec["to_ping_id"] = complaint["to_ping_id"]
                        rec["to_ping_title"] = pings.get(complaint["to_ping_id"])["title"]
                        rec["to_ping_user_id"] = pings.get(complaint["to_ping_id"])["user_id"]
                        rec["to_ping_user_name"] = users.get(pings.get(complaint["to_ping_id"])["user_id"])["name"]
                    complaints_for_response.append(rec)
                r["complaints"] = complaints_for_response
            else:
                r["code"] = response["code"]
        else:
            r["code"] = -1
        return r

    @cherrypy.expose(["list-pings"])
    @cherrypy.tools.json_out()
    def list_pings(self, ping_ids=None):
        """
        Запрос списка собственных пингов.
        Список дополняется расширенным набором данных из get_ping_info

        :param ping_ids: Список ID пингов, информацию о которых необходимо вернуть.
                    Если не передан, возвращается список всех пингов текущего пользователя.
                    Массив передается в виде строки с | в качестве разделителя.
        :return: Массив с пингами. Каждый элемент -- это объект.
        """
        token, user_id = self._get_identity()
        r = {"code": 0}
        if user_id:
            server = self._get_server()
            ping_ids_list = []
            if ping_ids:
                for ping_id in (int(i) for i in ping_ids.split("|")):
                    ping_ids_list.append(ping_id)
            else:
                response = server.action("get_news_feed", token, {"limit": 100, "user_id": user_id})
                if response["code"] == 0:
                    for p in (int(obj["ping_id"]) for obj in response["news_feed"] if "ping_id" in obj):
                        ping_ids_list.append(p)
                else:
                    r["code"] = response["code"]
            if ping_ids_list:
                response = server.action("get_ping_info", token, {"ping_ids": ping_ids_list})
                if response["code"] == 0:
                    r["pings"] = self.append_extra(response["pings"])
                else:
                    r["code"] = int(response["code"] + 10000)
        else:
            r["code"] = -1
        return r

    @cherrypy.expose(["delete-ping"])
    @cherrypy.tools.json_out()
    def delete_ping(self, ping_id):
        """
        Удаление собственного пинга

        :param ping_id: Пинг, который необходимо удалить
        :return: Ответ от сервера
        """
        r = {"code": 0}
        token, user_id = self._get_identity()
        if token:
            server = self._get_server()
            response = server.action("delete_ping", token, {"ping_id": int(ping_id)})
            r["code"] = response["code"]
        else:
            r["code"] = -1
        return r

    @cherrypy.expose(["update-ping"])
    @cherrypy.tools.json_out()
    def update_ping(self, ping_id, title, description, timestamp, color, file_data, **kwargs):
        """
        Обновление информации о пинге.

        :param ping_id:
        :param title:
        :param description:
        :param timestamp:
        :param color:
        :param tags: -- передается в kwargs
        :param file_data:
        :return:
        """
        r = {"code": 0}

        # Это гребаный костыль, потому что CherryPy не дружит с массивами, передаваемыми JQuery
        tags = kwargs.pop('tags[]', [])

        token, user_id = self._get_identity()
        if token:
            server = self._get_server()
            if ping_id:
                args = {
                    "ping_id": int(ping_id),
                    "title": title,
                    "description": description,
                    "color": int(color)
                }

                if tags:
                    args["tags"] = tags

                if file_data:
                    args["file_name"] = self.get_file_name(file_data)
                    r["file_name"] = server.get_file_url(args["file_name"])

                if timestamp:
                    args["fire_ts"] = int(timestamp)
                    args["event_type"] = 1  # установил от балды

                response = server.action("update_ping", token, args)
                r["code"] = response["code"]
            else:
                r["code"] = -2
        else:
            r["code"] = -1
        return r

    @cherrypy.expose(["create-ping"])
    @cherrypy.tools.json_out()
    def create_ping(self, lon, lat, title, description, timestamp, color, file_data, **kwargs):
        """
        Создание пинга.

        :param lon:
        :param lat:
        :param title:
        :param description:
        :param timestamp:
        :param color:
        :param tags: -- передается в kwargs
        :param file_data:
        :return:
        """
        r = {"code": 0}

        # Это гребаный костыль, потому что CherryPy не дружит с массивами, передаваемыми JQuery
        tags = kwargs.pop('tags[]', [])

        token, user_id = self._get_identity()
        if token:
            server = self._get_server()

            p = Point(0, 0)
            p.from_location(float(lon), float(lat))

            args = {
                "x": p.x,
                "y": p.y,
                "title": title,
                "description": description,
                "color": int(color)
            }

            if tags:
                args["tags"] = tags

            if file_data:
                args["file_name"] = self.get_file_name(file_data)
                r["file_name"] = self._get_server().get_file_url(args["file_name"])

            if timestamp:
                args["fire_ts"] = int(timestamp)
                args["event_type"] = 1  # установил от балды

            if lon and lat:
                response = server.action("create_ping", token, args)
                r["code"] = response["code"]
                if "ping_id" in response:
                    r["ping_id"] = response["ping_id"]
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

    def append_extra(self, pings):
        """
        К каждой записи переданного списка добавляет дополнительную информацию.

        :param pings:
        :return:
        """
        for ping in pings:
            # добавим гео-координаты
            if "x" in ping and "y" in ping:
                p = Point(ping["x"], ping["y"])
                ping["lng"], ping["lat"] = p.get_location()
            # Добавим адрес сервера к file_name
            if "file" in ping and "file_name" in ping["file"]:
                ping["file"]["file_name"] = self._get_server().get_file_url(ping["file"]["file_name"], 120)
        return pings
