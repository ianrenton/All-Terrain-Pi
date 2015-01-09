# All-Terrain Pi control code
# By Ian Renton
# http://robots.ianrenton.com/atp

# This is the main control code. It runs a web server to serve the control web page, then
# listens for websocket connections. The data received over the websockets is used to
# drive the motors.

import os.path
import cherrypy
import PicoBorgRev
from time import sleep
from cherrypy.lib.static import serve_file
from ws4py.server.cherrypyserver import WebSocketPlugin, WebSocketTool
from ws4py.websocket import WebSocket

# Make sure we can serve static files out of current dir
current_dir = os.path.dirname(os.path.abspath(__file__))

# Set up and run the server
cherrypy.server.socket_host = '0.0.0.0'
cherrypy.server.socket_port = 9000
cherrypy.engine.timeout_monitor.unsubscribe()
WebSocketPlugin(cherrypy.engine).subscribe()
cherrypy.tools.websocket = WebSocketTool()

# Setup the PicoBorg Reverse
PBR = PicoBorgRev.PicoBorgRev()
PBR.Init()
PBR.ResetEpo()

# Main class
class Root(object):

  # When the root URL is visited, open interface.html
  @cherrypy.expose
  def index(self): 
    return serve_file(current_dir + '/interface.html')

  # When the websocket URL is visited, run the handler
  @cherrypy.expose
  def ws(self):
    handler = cherrypy.request.ws_handler

# Class that handles the websocket requests and acts on the data supplied
class CommandWebSocket(WebSocket):
  def received_message(self, message):
    # Convert message to motor demand
    command = message.data[:1] # 's': speed (motor 1), 't': turn (motor 2)
    value = float(message.data[1:]) # -100 to 100
    if (command == 's'):
      PBR.SetMotor1(value / 100.0)
    elif (command == 't'):
      PBR.SetMotor2(value / 100.0)
    # Print some debug
    print(message.data)
    print(command + ' ' + str(value))
    # Respond with something so the client knows we're listening
    self.send('')

# Quick fire of motors to show that we're up and running
PBR.SetMotor2(100)
sleep(0.05)
PBR.SetMotor2(0)

# Run CherryPy
cherrypy.quickstart(Root(), '/', config={'/ws': {'tools.websocket.on': True, 'tools.websocket.handler_cls': CommandWebSocket}, '/gyro.js': {'tools.staticfile.on': True, 'tools.staticfile.filename': current_dir + '/gyro.js'}})
