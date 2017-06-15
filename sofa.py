#!/usr/bin/python

import atexit
import math
import os
import socket
import tempfile
import time

import serial

# oem
# JOY_LEFT=30
# JOY_CENTER=135
# JOY_RIGHT=230
# JOY_TOP=231
# JOY_MIDDLE=130
# JOY_BOTTOM=31
# JOY_DEADZONE=5

# wireless
JOY_LEFT = 0
JOY_CENTER = 127
JOY_RIGHT = 255
JOY_TOP = 255
JOY_MIDDLE = 127
JOY_BOTTOM = 0
JOY_DEADZONE = 10

JOY_MODES = [
    # name, start_angle, m1_speed, m2_speed, accel_profile
    ["STRT", 0, 1.0, 1.0, 'NORMAL'],
    ["TURN", 10, 1.0, 1.0, 'NORMAL'],
    ["TURN", 90, 1.2, 0.8, 'NORMAL'],
    ["CRWL", 135, 1.0, 0.0, 'NORMAL'],
    ["STOP", 165, 0.0, 0.0, 'NORMAL'],
    ["BRAKE", 170, 0.0, 0.0, 'BRAKE'],
    ["", 180, 0.0, 0.0, "BRAKE"],
]

MAX_FWD_SPEED = 3.0
MAX_TURN_FWD_SPEED = 3.0

TURBO_MAX_FWD_SPEED = 9.0
TURBO_MAX_TURN_FWD_SPEED = 4.0

MAX_REV_SPEED = 2.0
MAX_TURN_REV_SPEED = 2.0

PI = 3.14159
E = 2.7182

SOCK = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
SOCK.bind(("192.168.3.1", 31337))
SOCK.setblocking(0)


def shutdown():
    """remove any evidence of our running"""
#    try:
    os.unlink("/var/run/sofa_status")
#    except:
#        pass


def gamma(orig):
    """make smaller values appear larger"""
    output = orig/10
    gam = (E**(output/4.1))-1
    return gam * 10


def correct_raw_joystick(raw_x, raw_y):
    """turn an i2c joystick x/y value into a -100:100 x/y value"""
    out_x = 0
    if raw_x >= JOY_RIGHT:
        out_x = 100
    elif raw_x <= JOY_LEFT:
        out_x = -100
    elif raw_x > JOY_CENTER + JOY_DEADZONE:
        j_min = JOY_CENTER + JOY_DEADZONE
        j_max = JOY_RIGHT
        out_x = int(100 * (raw_x - j_min) / (j_max - j_min))
    elif raw_x < JOY_CENTER - JOY_DEADZONE:
        y_min = JOY_LEFT
        y_max = JOY_CENTER - JOY_DEADZONE
        out_x = int(100 * (raw_x - j_min) / (j_max - j_min)) - 100

    out_y = 0
    if raw_y >= JOY_TOP:
        out_y = 100
    elif raw_y <= JOY_BOTTOM:
        out_y = -100
    elif raw_y > JOY_MIDDLE + JOY_DEADZONE:
        y_min = JOY_MIDDLE + JOY_DEADZONE
        y_max = JOY_TOP
        out_y = int(100 * (raw_y - y_min) / (y_max - y_min))
    elif raw_y < JOY_MIDDLE - JOY_DEADZONE:
        y_min = JOY_BOTTOM
        y_max = JOY_MIDDLE - JOY_DEADZONE
        out_y = int(100 * (raw_y - y_min) / (y_max - y_min)) - 100

    return out_x, out_y


def get_joystick_vector(joy_x, joy_y):
    """turn an x,y into a magnitude,angle"""
    magnitude = int(math.sqrt(joy_x * joy_x + joy_y * joy_y))
    if magnitude > 100:
        magnitude = 100
    angle = 0.0
    if joy_y > 0:
        angle = math.atan(abs(1.0 * joy_x)/abs(1.0 * joy_y))
        if joy_x < 0:
            angle = PI * 2 - angle
    elif joy_y < 0:
        angle = math.atan(abs(1.0 * joy_x)/abs(1.0 * joy_y))
        if joy_x > 0:
            angle = PI - angle
        elif joy_x < 0:
            angle = PI + angle
        else:
            angle = PI
    else:
        if joy_x > 0:
            angle = PI * 0.5
        elif joy_x < 0:
            angle = PI * 1.5

    angle = int(angle / (2 * PI) * 360)

    return magnitude, angle


def get_joystick():
    """get a joystick value"""
    got_packet = True
    data = False
    while got_packet:
        try:
            data, addr = SOCK.recvfrom(1024)
        except socket.error:
            got_packet = False

    if not data:
        return -1, -1, False, False

    raw_x_s, raw_y_s, raw_z, raw_c = data.split(':')
    joy_x, joy_y = correct_raw_joystick(int(raw_x_s), int(raw_y_s))
    button_z = False
    if raw_z == '1':
        button_z = True
    button_c = False
    if raw_c == '1':
        button_c = True

    magnitude, angle = get_joystick_vector(joy_x, joy_y)

    return magnitude, angle, button_c, button_z


def robotec_exec(ser, cmd):
    """run a motor controller command and return the results"""
    ser.write(cmd + "\r")
    ser.read(len(cmd) + 1)
    newline = False
    resp = ''
    while not newline:
        char = ser.read(1)
        if char == "\r":
            newline = True
        else:
            resp = resp + char

    return resp


def dump_status(mode, submode, magnitude, angle, left_motor, right_motor,
                volts, amps):
    """output interesting metrics to stdout and a status file"""
    print("{:8s} {:8s} {:3d}% {:3d}o {:5.0f},{:5.0f} {} {}".format(
        mode, submode, magnitude, angle, left_motor, right_motor, volts, amps))
    status = tempfile.NamedTemporaryFile(dir="/var/run", delete=False)
    status_temp_file = status.name
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    status.write("{}\n".format(now))
    status.write("MODE        {:8s}\n".format(mode))
    status.write("NUNCHUK {:3d}% {:3d}o\n".format(magnitude, angle))
    status.write("MOTOR     {:4.1f} {:4.1f}\n".format(left_motor, right_motor))
    status.write("VOLTS     {}\n".format(volts))
    status.write("AMPS        {}\n".format(amps))
    status.close()
    os.rename(status_temp_file, "/var/run/sofa_status")


def linear_map(i, i_min, i_max, o_min, o_max):
    """mapping function"""
    if o_max > o_min:
        out = (float((i - i_min)) / float(i_max - i_min)) * \
          float(o_max - o_min) + o_min
    else:
        out = (1.0 - (float(i - i_min) / float(i_max - i_min))) * \
          float(o_min - o_max) + o_max
    return out
