import os.path
import cherrypy
from webapp.libs.tools.authenticationtool import AuthenticationTool
from webapp.libs.tools.makotool import MakoTool
from webapp.libs.plugins.makoplugin import MakoTemplatePlugin

cur_dir = os.path.abspath(os.path.dirname(__file__))
template_dir = os.path.join(cur_dir, 'templates')
template_cache_dir = os.path.join(cur_dir, 'templates', '.cache')
conf_dir = os.path.join(cur_dir, 'conf')
conf_path = os.path.join(cur_dir, 'conf', 'server.conf')

cherrypy.tools.render = MakoTool()
cherrypy.tools.authentication = AuthenticationTool()

from webapp.app import RootApp
from webapp.api import Api
app = RootApp()
cherrypy.tree.mount(app, '/', conf_path)
app.api = Api()

MakoTemplatePlugin(cherrypy.engine, template_dir, template_cache_dir).subscribe()

if __name__ == "__main__":
    cherrypy.engine.start()
