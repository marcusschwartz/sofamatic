"""a simple motion controller and some helper routines"""

E = 2.7182

ACCEL_PROFILES = {
    'NORMAL': [0.03, 0.05],
    'TURBO': [0.1, 0.05],
    'BRAKE': [0.1, 0.2],
    'SPIN': [0.15, 0.15],
}


def gamma(orig):
    """make smaller values appear larger"""
    output = orig / 10
    gam = (E**(output / 4.1)) - 1
    return gam * 10


def linear_map(i, i_min, i_max, o_min, o_max):
    """mapping function"""
    if o_max > o_min:
        out = (float((i - i_min)) / float(i_max - i_min)) * \
            float(o_max - o_min) + o_min
    else:
        out = (1.0 - (float(i - i_min) / float(i_max - i_min))) * \
            float(o_min - o_max) + o_max
    return out


def process_accel(target_speed, current_speed, accel_profile):
    """do the accel/decel thing"""

    if target_speed > current_speed:
        # accelerate
        accel_rate = ACCEL_PROFILES[accel_profile][0]
        current_speed += accel_rate
        if current_speed > target_speed:
            current_speed = target_speed

    elif target_speed < current_speed:
        # deccelerate
        decel_rate = ACCEL_PROFILES[accel_profile][1]
        current_speed -= decel_rate
        if current_speed < target_speed:
            current_speed = target_speed

    return current_speed


def cuberoot(scalar):
    '''return the cuberoot of a real number'''
    return scalar ** (1.0 / 3)


class MotionController(object):
    _name = ""
    _joystick = None

    def name(self):
        return self._name

    def process_update(self):
        pass

    def update_joystick(self, new_joystick):
        self._joystick = new_joystick
        self.process_update()

    def status(self):
        return self.name()

    def active(self):
        return not self._joystick.centered()

    def motor_speeds(self):
        if self._joystick.centered():
            return 0.0, 0.0
        return self._joystick.magnitude(), self._joystick.magnitude()
