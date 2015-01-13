# All-Terrain Pi control code
# By Ian Renton
# http://robots.ianrenton.com/atp

# This is the main control code. It runs a web server to serve the control web
# page, then listens for websocket connections. The data received over the
# websockets is used to drive the motors.

# This script runs the web server on port 80 and assumes it can exec
# 'shutdown -h now' so should be run as root. To run as non-root, change port
# to a high number and set up sudo appropriately if shutdown function is
# needed. (Port number also needs setting on 'ws://' URLs in interface.html.)

import os
import cherrypy
import PicoBorgRev
from time import time, sleep
from threading import Thread
from cherrypy.lib.static import serve_file
from ws4py.server.cherrypyserver import WebSocketPlugin, WebSocketTool
from ws4py.websocket import WebSocket

# Make sure we can serve static files out of current dir
current_dir = os.path.dirname(os.path.abspath(__file__))

# Set up and run the server
cherrypy.server.socket_host = '0.0.0.0'
cherrypy.server.socket_port = 80
cherrypy.engine.timeout_monitor.unsubscribe()
WebSocketPlugin(cherrypy.engine).subscribe()
cherrypy.tools.websocket = WebSocketTool()

# Setup the PicoBorg Reverse
PBR = PicoBorgRev.PicoBorgRev()
PBR.Init()
PBR.ResetEpo()

# Watchdog timer
stopWatchdog = False
lastRxTime = int(round(time() * 1000))

# CherryPy server main class
class CherryPy(object):

  # When the root URL is visited, open interface.html
  @cherrypy.expose
  def index(self): 
    return serve_file(current_dir + '/interface.html')

  # When the websocket URL is visited, run the handler
  @cherrypy.expose
  def ws(self):
    handler = cherrypy.request.ws_handler

  # When the "/s" URL is visited, shut down the computer. This isn't linked
  # anywhere on the web interface to avoid unintentional clicks, but can be
  # visited from the browser address bar. Allows a soft shutdown of the Pi
  # instead of pulling the power or SSHing in to run the shutdown command.
  @cherrypy.expose
  def s(self):
    os.system('shutdown -h now')
    return 'Shutting down.'

# Class that handles the websocket requests and acts on the data supplied
class CommandWebSocket(WebSocket):
  def received_message(self, message):
    global lastRxTime
    # Received a demand, so reset watchdog
    lastRxTime = int(round(time() * 1000))

    # Convert message to motor demand
    command = message.data[:1] # 's': speed (motor 1), 't': turn (motor 2)
    value = float(message.data[1:]) # -100 to 100
    if (command == 's'):
      PBR.SetMotor1(value / 100.0)
    elif (command == 't'):
      PBR.SetMotor2(value / 100.0)

    print('Received command: ' + message.data + ' at ' + str(lastRxTime))

    # Respond with something so the client knows we're listening
    self.send('')

# Watchdog function that will demand motors are zeroed if we lose comms
class Watchdog(Thread):
  def run(self):
    global stopWatchdog
    while not stopWatchdog:
      print('Watchdog check, now ' + str(int(round(time() * 1000))) + ' last Rx at ' + str(lastRxTime))
      if (int(round(time() * 1000)) > lastRxTime + 1000):
        print('No comms, zeroing motor output')
        PBR.SetMotor1(0)
        PBR.SetMotor2(0)
      sleep(1)

# Quick fire of motors to show that we're up and running
print('Starting up...')
PBR.SetMotor2(100)
sleep(0.05)
PBR.SetMotor2(0)

# Start watchdog timer
print('Starting watchdog timer...')
w = Watchdog()
w.daemon = True
w.start()

# Run CherryPy
print('Starting web server...')
cherrypy.quickstart(CherryPy(), '/', config={'/ws': {'tools.websocket.on': True, 'tools.websocket.handler_cls': CommandWebSocket}, '/gyro.js': {'tools.staticfile.on': True, 'tools.staticfile.filename': current_dir + '/gyro.js'}})

# Cancel watchdog
print('Shutting down...')
stopWatchdog = True
