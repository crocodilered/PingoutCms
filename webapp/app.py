import cherrypy


__all__ = ['PingoutCmsApp']


class PingoutCmsApp(object):
    @cherrypy.expose
    @cherrypy.tools.render(template='index.html')
    def index(self):
        return {
            'shooters': None,
            'path': 'shooters'
        }

    @cherrypy.expose
    @cherrypy.tools.render(template='mappa.html')
    def mappa(self):
        return {
            'token': cherrypy.session['token'] if 'token' in cherrypy.session else None,
            'user_id': cherrypy.session['user_id'] if 'user_id' in cherrypy.session else None
        }
