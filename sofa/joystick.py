"""get magnitude/angle vectors from a remote wii nunchuck"""

import time

import status


class Joystick(status.Status):
    _attrs = ['magnitude', 'angle', 'button_z', 'button_c', 'recv_time']
    _dashboard_fmt = ['{magnitude:3d}m', '{angle:3d}a', '{0.z_text}{0.c_text}']

    @property
    def z_text(self):
        if self[2]:
            return 'Z'
        return 'z'

    @property
    def c_text(self):
        if self[3]:
            return 'C'
        return 'c'

    @property
    def valid(self):
        if self.age > 0.3:
            return False
        return True

    @property
    def magnitude(self):
        if self.age > 0.1:
            return 0
        return self[0]

    @property
    def age(self):
        return time.time() - self[4]

    @property
    def status(self):
        return self

    @property
    def centered(self):
        if self.magnitude <= 10:
            return True
        return False

    @property
    def active(self):
        return self.magnitude > 0


def new_centered(last_joystick=None):
    if last_joystick:
        recv_time = last_joystick.recv_time
    else:
        # by default return one that is already expired
        recv_time = time.time() - 10.0

    return Joystick(
        magnitude=0,
        angle=0,
        button_z=False,
        button_c=False,
        recv_time=recv_time)
