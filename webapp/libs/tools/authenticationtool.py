import cherrypy


__all__ = ['AuthenticationTool']


class AuthenticationTool(cherrypy.Tool):
    def __init__(self):
        self.NOT_SIGNED_IN = 1
        cherrypy.Tool.__init__(self, 'before_handler', self._authenticate)

    def _authenticate(self):
        if not cherrypy.session.get('token', None):
            raise cherrypy.HTTPRedirect("/error/?code=%s" % self.NOT_SIGNED_IN)
