import os.path
import cherrypy
from webapp.libs.tools.makotool import MakoTool
from webapp.libs.plugins.makoplugin import MakoTemplatePlugin

cur_dir = os.path.abspath(os.path.dirname(__file__))
template_dir = os.path.join(cur_dir, 'templates')
template_cache_dir = os.path.join(cur_dir, 'templates', '.cache')
conf_dir = os.path.join(cur_dir, 'conf')
conf_path = os.path.join(cur_dir, 'conf', 'server.conf')

cherrypy.tools.render = MakoTool()

from webapp.app import PingoutCmsApp
from webapp.proxy import PingoutCmsProxy
app = PingoutCmsApp()
app.proxy = PingoutCmsProxy()
cherrypy.tree.mount(app, '/', conf_path)

MakoTemplatePlugin(cherrypy.engine, template_dir, template_cache_dir).subscribe()

if os.environ['PINGOUTCMS_DEBUG'] == '1':
    cherrypy.engine.start()
