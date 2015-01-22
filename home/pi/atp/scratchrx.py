# Scratch "Remote Sensors Protocol" receiver for All-Terrain Pi
# Allows programmatic control of the robot from the Scratch
# programming environment.
# by Ian Renton
# http://robots.ianrenton.com/atp

import PicoBorgRev
import re
import socket
from time import sleep

# Setup the PicoBorg Reverse
PBR = PicoBorgRev.PicoBorgRev()
PBR.Init()
PBR.ResetEpo()

# Wait for Scratch to start
sleep(30)

# Connect to Scratch
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('127.0.0.1', 42001))

# Quick fire of motors to show that we're up and running
print('Starting up...')
PBR.SetMotor2(100)
sleep(0.05)
PBR.SetMotor2(0)

while True:
  # Receive a data packet - one arrives every time a var is changed
  data = s.recv(100)
  print data

  # Parse packet to get the command(s) out
  regex = re.compile('"(\w*)" ([\-\d]*)')
  allCommands = regex.findall(data)
  for command in allCommands:
    if command[0] == 'speed':
      print 'speed ' + command[1]
      PBR.SetMotor1(int(command[1]))
    elif command[0] == 'turn':
      print 'turn ' + str(int(command[1])*100)
      PBR.SetMotor2(int(command[1])*100)

s.close()
