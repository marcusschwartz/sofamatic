#!/usr/bin/python

import socket
import math
import serial
import time
import tempfile
import os
import atexit

#oem
#JOY_LEFT=30
#JOY_CENTER=135
#JOY_RIGHT=230
#JOY_TOP=231
#JOY_MIDDLE=130
#JOY_BOTTOM=31
#JOY_DEADZONE=5

#wireless
JOY_LEFT=0
JOY_CENTER=127
JOY_RIGHT=255
JOY_TOP=255
JOY_MIDDLE=127
JOY_BOTTOM=0
JOY_DEADZONE=10

JOY_MODES  = [
  # name, start_angle, m1_speed, m2_speed, accel_profile
  ["STRT",          0,      1.0,      1.0, 'NORMAL'],
  ["TURN",         10,      1.0,      1.0, 'NORMAL'],
  ["TURN",         90,      1.2,      0.8, 'NORMAL'],
  ["CRWL",        135,      1.0,      0.0, 'NORMAL'],
  ["STOP",        165,      0.0,      0.0, 'NORMAL'],
  ["BRAKE",       170,      0.0,      0.0, 'BRAKE'],
  ["",            180,      0.0,      0.0, "BRAKE"],
]

MAX_FWD_SPEED=3.0
MAX_TURN_FWD_SPEED=3.0

TURBO_MAX_FWD_SPEED=9.0
TURBO_MAX_TURN_FWD_SPEED=4.0

MAX_REV_SPEED=3.0
MAX_TURN_REV_SPEED=2.0

PI=3.14159
E=2.7182

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("192.168.3.1", 31337))
sock.setblocking(0)

def shutdown():
  try:
    os.unlink("/var/run/sofa_status")
  except:
    pass

def gamma(x):
  x = x/10
  g = (E**(x/4.1))-1
  return g * 10

def correctRawJoystick(raw_x, raw_y):
  x = 0
  if (raw_x >= JOY_RIGHT):
    x = 100
  elif (raw_x <= JOY_LEFT):
    x = -100
  elif (raw_x > JOY_CENTER + JOY_DEADZONE):
    min = JOY_CENTER + JOY_DEADZONE
    max = JOY_RIGHT
    x = int(100 * (raw_x - min) / (max - min))
  elif (raw_x < JOY_CENTER - JOY_DEADZONE):
    min = JOY_LEFT
    max = JOY_CENTER - JOY_DEADZONE
    x = int(100 * (raw_x - min) / (max - min)) - 100

  y = 0
  if (raw_y >= JOY_TOP):
    y = 100
  elif (raw_y <= JOY_BOTTOM):
    y = -100
  elif (raw_y > JOY_MIDDLE + JOY_DEADZONE):
    min = JOY_MIDDLE + JOY_DEADZONE
    max = JOY_TOP
    y = int(100 * (raw_y - min) / (max - min))
  elif (raw_y < JOY_MIDDLE - JOY_DEADZONE):
    min = JOY_BOTTOM
    max = JOY_MIDDLE - JOY_DEADZONE
    y = int(100 * (raw_y - min) / (max - min)) - 100
  
  return x, y

def getJoystickVector(x, y):
  magnitude = int(math.sqrt(x * x + y * y))
  if (magnitude > 100):
    magnitude = 100
  angle = 0.0
  if (y > 0):
    angle = math.atan(abs(1.0 * x)/abs(1.0 * y))
    if (x < 0):
      angle = PI * 2 - angle
  elif (y < 0):
    angle = math.atan(abs(1.0 * x)/abs(1.0 * y))
    if (x > 0):
      angle = PI - angle
    elif (x < 0):
      angle = PI + angle
    else:
      angle = PI
  else:
    if (x > 0):
      angle = PI * 0.5
    elif (x < 0):
      angle = PI * 1.5

  angle = int(angle / (2 * PI) * 360)

  return magnitude, angle

def getJoystick():
  got_packet = True
  data = False
  while got_packet:
    try:
      data, addr = sock.recvfrom(1024)
    except socket.error:
      got_packet = False

  if not data:
    print("NO DATA")
    return -1, -1, False, False

  raw_x_s, raw_y_s, raw_z, raw_c = data.split(':')
  x, y = correctRawJoystick(int(raw_x_s), int(raw_y_s))
  z = False
  z_str = ' '
  if raw_z == '1':
    z = True
    z_str = 'Z'
  c = False
  c_str = ' '
  if raw_c == '1':
    c = True
    c_str = 'C'

  magnitude, angle = getJoystickVector(x, y)

  return magnitude, angle, c, z

def roboteqExec(ser, cmd):
	ser.write(cmd + "\r")
	r = ser.read(len(cmd) + 1)
	newline = False
	resp = ''
	while not newline:
		r = ser.read(1)
		if r == "\r":
			newline = True
		else:
			resp = resp + r
          
	return resp

def dump_status(magnitude, angle, left_motor, target_right_motor, volts, amps):
  print("{:8s} {:8s} {:3d}% {:3d}o {:5.0f},{:5.0f} {} {}".format(mode, submode, magnitude, angle, left_motor, right_motor, volts, amps))
  start=time.time()
  status = tempfile.NamedTemporaryFile(dir="/var/run", delete=False)
  status_temp_file = status.name
  i = 0
  now = time.strftime("%Y-%m-%d %H:%M:%S")
  status.write("{}\n".format(now))
  status.write("MODE    {:8s}\n".format(mode))
  status.write("NUNCHUK {:3d}% {:3d}o\n".format(magnitude, angle))
  status.write("MOTOR   {:4.1f} {:4.1f}\n".format(left_motor, right_motor))
  status.write("VOLTS   {}\n".format(volts))
  status.write("AMPS    {}\n".format(amps))
  status.close()
  os.rename(status_temp_file, "/var/run/sofa_status")
  end = time.time()

def linear_map(i, i_min, i_max, o_min, o_max):
  if o_max > o_min:
    o = (float((i - i_min)) / float(i_max - i_min)) * float(o_max - o_min) + o_min
  else:
    o = (1.0 - (float(i - i_min) / float(i_max - i_min))) * float(o_min - o_max) + o_max
#  print("{} [{}:{}] -> {} [{}:{}]".format(i, i_min, i_max, o, o_min, o_max))
  return o

atexit.register(shutdown)

mode = 'IDLE'
submode = ''

ser = serial.Serial("/dev/ttyACM0", 115200, timeout=1)

missed_data = 0

target_speed = 0.0
current_speed = 0.0

m1_speed = 0.0
m2_speed = 0.0

while True:
  magnitude, angle, c, z = getJoystick()

  left_motor = 0.0
  right_motor = 0.0

  if (magnitude < 0):
    missed_data += 1
    if missed_data > 3:
      mode = 'OFFLINE'
      left_motor = 0.0
      right_motor = 0.0

  else:
    missed_data = 0

    if mode == 'OFFLINE':
      mode = 'IDLE'
      
    if mode == 'IDLE':
      if (magnitude > 10):
        if ( (angle <= 45) or (angle >= 315) ):
          mode = 'FORWARD'
	elif ( (angle >= 135) and (angle <= 225) ):
	  mode = 'REVERSE'

    elif mode == 'FORWARD' or mode == 'REVERSE':
      turn_direction = 'NONE'
      turn_angle = 0
      submode = ""
      accel_profile = ""
      start_angle = 0
      end_angle = 0
      start_m1_speed = 0.0
      end_m1_speed = 0.0
      start_m2_speed = 0.0
      end_m2_speed = 0.0

      if magnitude == 0 and current_speed == 0:
        mode = 'IDLE'
	continue

      if magnitude > 10 and mode == 'FORWARD':
        if angle <= 180:
          turn_direction = 'RIGHT'
  	  turn_angle = angle
#          print("TURN RIGHT {}".format(turn_angle))
        else:
          turn_direction = 'LEFT'
	  turn_angle = 360 - angle
#          print("TURN LEFT {}".format(turn_angle))
      elif magnitude > 10:
        if angle <= 180:
          turn_direction = 'RIGHT'
  	  turn_angle = 180 - angle
#          print("TURN RIGHT {}".format(turn_angle))
        else:
          turn_direction = 'LEFT'
	  turn_angle = 180 - (360 - angle)
#          print("TURN LEFT {}".format(turn_angle))


      if magnitude > 10:
        for i in range(0, len(JOY_MODES) - 1):
          submode, start_angle, start_m1_speed, start_m2_speed, accel_profile = JOY_MODES[i]
          next_submode, end_angle, end_m1_speed, end_m2_speed, next_accel_profile = JOY_MODES[i+1]
  	  if turn_angle >= start_angle and turn_angle < end_angle:
            break

        m1_speed = linear_map(turn_angle, start_angle, end_angle, start_m1_speed, end_m1_speed)
        m2_speed = linear_map(turn_angle, start_angle, end_angle, start_m2_speed, end_m2_speed)
      else:
        submode = "COAST"
      
#      print("SUBMODE {:6s} {:4.2f} {:4.2f} {} {}".format(submode, m1_speed, m2_speed, start_angle, end_angle))

      if mode == 'FORWARD':
	if z:
          max_speed = ((TURBO_MAX_FWD_SPEED - TURBO_MAX_TURN_FWD_SPEED) * ( (135.0 - float(turn_angle)) / 135.0)) + TURBO_MAX_TURN_FWD_SPEED
	else:
          max_speed = ((MAX_FWD_SPEED - MAX_TURN_FWD_SPEED) * ( (135.0 - float(turn_angle)) / 135.0)) + MAX_TURN_FWD_SPEED

      elif mode == 'REVERSE':
        max_speed = ((MAX_REV_SPEED - MAX_TURN_REV_SPEED) * ( (135.0 - float(turn_angle)) / 135.0)) + MAX_TURN_FWD_SPEED

      if submode != 'COAST':
        target_speed = gamma(magnitude) * max_speed
      else:
        target_speed = 0

      print("TARGET {} {} {}".format(target_speed, m1_speed, m2_speed))
      print("CURRENT {} {} {}".format(current_speed, m1_speed, m2_speed))

      if target_speed > current_speed:
        # accelerate
        if z:
          accel_rate = target_speed / 10.0
        else: 
          accel_rate = target_speed / 20.0
	print("ACCEL {} {}".format(current_speed, accel_rate))
        current_speed += accel_rate
        if current_speed > target_speed:
          current_speed = target_speed
      elif target_speed < current_speed:
        # deccelerate
	decel_rate = current_speed / 20.0
        if accel_profile == 'BRAKE':
          decel_rate *= 3
        if decel_rate < 35:
          decel_rate = 35 
	print("DECEL {} {}".format(current_speed, decel_rate))
        current_speed -= decel_rate 
        if current_speed < target_speed:
          current_speed = target_speed

      if turn_direction == 'LEFT':
        left_motor = m2_speed * current_speed
        right_motor = m1_speed * current_speed
      elif turn_direction == 'RIGHT':
        left_motor = m1_speed * current_speed
        right_motor = m2_speed * current_speed
      else:
        left_motor = current_speed
        right_motor = current_speed

      left_motor *= 0.96

      if mode == 'REVERSE':
        left_motor *= -1.0
	right_motor *= -1.0
      
  roboteqExec(ser, "!G 2 {}".format(-1 * int(left_motor)))
  roboteqExec(ser, "!G 1 {}".format(int(right_motor)))

  volts = roboteqExec(ser, "?V")[2:]
  volts = float(volts.split(':')[1]) / 10
  volts = "{:4.1f} ({:5.2f})".format(volts, volts / 3)
  amps = roboteqExec(ser, "?BA")[3:]
  amps_l = float(amps.split(':')[0]) / 10
  amps_r = float(amps.split(':')[1]) / 10
  amps = "{:4.1f} {:4.1f}".format(amps_l, amps_r)

  dump_status(magnitude, angle, int(left_motor), int(right_motor), volts, amps)
  time.sleep(0.1)

