import cherrypy


__all__ = ['PingoutCmsApp']


class PingoutCmsApp(object):
    @cherrypy.expose
    @cherrypy.tools.render(template='auth.html')
    def index(self):
        return None

    @cherrypy.expose
    @cherrypy.tools.render(template='error.html')
    def error(self, code):
        return {"code": code}

    @cherrypy.expose
    @cherrypy.tools.render(template='mappa.html')
    @cherrypy.tools.authentication()
    def mappa(self):
        return {
            "token": cherrypy.session.get("token", None),
            "user_id": cherrypy.session.get("user_id", None)
        }
