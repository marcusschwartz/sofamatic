"""get magnitude/angle vectors from a remote wii nunchuck"""
import math
import select
import socket
import struct

import util

PI = 3.14159

# oem
JOY_LEFT = 30
JOY_CENTER = 135
JOY_RIGHT = 230
JOY_TOP = 231
JOY_MIDDLE = 130
JOY_BOTTOM = 31
JOY_DEADZONE = 5

# wireless
# JOY_LEFT = 0
# JOY_CENTER = 127
# JOY_RIGHT = 255
# JOY_TOP = 255
# JOY_MIDDLE = 127
# JOY_BOTTOM = 0
# JOY_DEADZONE = 10


class Joystick(object):
    _magnitude = 0
    _angle = 0
    _button_z = 0
    _button_c = 0
    _addr = ''

    def __init__(self, magnitude, angle, button_c, button_z, addr):
        self._magnitude = magnitude
        self._angle = angle
        self._button_c = button_c
        self._button_z = button_z
        self._addr = addr

    def status(self):
        if self._magnitude >= 0:
            string = "{:3d}m {:3d}o".format(
                self._magnitude, self._angle)
        else:
            string = " XX   XX "
        status = util.Status()
        status.string = string
        status.details = {
            'magnitude': self._magnitude,
            'angle': self._angle,
        }

        return status

    def centered(self):
        if not self.valid():
            return False
        if self._magnitude <= 10:
            return True
        return False

    def valid(self):
        if self._magnitude >= 0:
            return True
        return False

    def magnitude(self):
        return self._magnitude

    def angle(self):
        return self._angle

    def button_c(self):
        return self._button_c

    def button_z(self):
        return self._button_z

    def addr(self):
        return self._addr


class Nunchuk(object):
    """a calibrated magnitude/angle from a wii nunchuk"""
    _sock = None

    def __init__(self, addr="224.0.0.250", port=31337):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind((addr, port))
        self._sock.setblocking(0)
        if addr.startswith("22"):
            mreq = struct.pack("4sl", socket.inet_aton(addr), socket.INADDR_ANY)
            self._sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    def correct_raw_joystick(self, raw_x, raw_y):
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
            j_min = JOY_LEFT
            j_max = JOY_CENTER - JOY_DEADZONE
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

    def get_joystick_vector(self, joy_x, joy_y):
        """turn an x,y into a magnitude,angle"""
        magnitude = int(math.sqrt(joy_x * joy_x + joy_y * joy_y))
        if magnitude > 100:
            magnitude = 100
        angle = 0.0
        if joy_y > 0:
            angle = math.atan(abs(1.0 * joy_x) / abs(1.0 * joy_y))
            if joy_x < 0:
                angle = PI * 2 - angle
        elif joy_y < 0:
            angle = math.atan(abs(1.0 * joy_x) / abs(1.0 * joy_y))
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

    def get_joystick(self, timeout):
        """get a joystick value"""
        data = None
        if timeout < 0:
            timeout = 0
        if select.select([self._sock], [], [], timeout):
            while True:
                try:
                    data, addr = self._sock.recvfrom(1024)
                except socket.error:
                    break
        if not data:
            return Joystick(-1, -1, False, False, None)

        raw_x_s, raw_y_s, raw_z, raw_c = data.split(':')
        joy_x, joy_y = self.correct_raw_joystick(int(raw_x_s), int(raw_y_s))
        button_z = False
        if raw_z == '1':
            button_z = True
        button_c = False
        if raw_c == '1':
            button_c = True

        magnitude, angle = self.get_joystick_vector(joy_x, joy_y)

        return Joystick(magnitude, angle, button_c, button_z, addr)
