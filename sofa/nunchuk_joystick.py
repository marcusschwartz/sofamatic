"""get magnitude/angle vectors from a remote wii nunchuck"""

import math

import joystick

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


def _scale_joystick_xy(raw_x, raw_y):
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


def _get_joystick_vector(joy_x, joy_y):
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


def from_remote_nunchuk(raw_x, raw_y, raw_z, raw_c, recv_time):
    joy_x, joy_y = _scale_joystick_xy(int(raw_x), int(raw_y))
    magnitude, angle = _get_joystick_vector(joy_x, joy_y)
    button_z = False
    if raw_z == '1':
        button_z = True
    button_c = False
    if raw_c == '1':
        button_c = True
    return joystick.Joystick(magnitude=magnitude,
                             angle=angle,
                             button_z=button_z,
                             button_c=button_c,
                             recv_time=recv_time)
