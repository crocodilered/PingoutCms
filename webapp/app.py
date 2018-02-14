import cherrypy


__all__ = ['PingoutCmsApp']


class PingoutCmsApp(object):
    def __compose_response(self, custom_data=None):
        q = 1
        common_data = {
            "token": cherrypy.session.get("token", None),
            "user_id": cherrypy.session.get("user_id", None),
            "uri": cherrypy.request.path_info
        }
        return {**common_data, **custom_data} if custom_data else common_data

    @cherrypy.expose
    @cherrypy.tools.render(template='auth.html')
    def index(self):
        return self.__compose_response()

    @cherrypy.expose
    @cherrypy.tools.render(template='error.html')
    def error(self, code):
        return self.__compose_response({"code": code})

    @cherrypy.expose
    @cherrypy.tools.render(template='mappa.html')
    @cherrypy.tools.authentication()
    def mappa(self):
        return self.__compose_response()

    @cherrypy.expose
    @cherrypy.tools.render(template='complaints.html')
    @cherrypy.tools.authentication()
    def complaints(self):
        return self.__compose_response()

    @cherrypy.expose
    def default(self, **kwargs):
        cherrypy.response.status = 404
        return b"<h1>404</h1>"
