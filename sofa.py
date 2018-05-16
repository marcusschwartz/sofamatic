"""a sofa"""
import math
import time

import nunchuk
import roboteq

ACCEL_PROFILES = {
    'NORMAL': [0.03, 0.05],
    'TURBO': [0.1, 0.05],
    'BRAKE': [0.1, 0.2],
    'SPIN': [0.05, 0.05],
}

JOY_MODES = [
    # name, start_angle, m1_speed, m2_speed, accel_profile
    ["STRT", 0, 1.0, 1.0, 'NORMAL'],
    ["TURN", 10, 1.0, 1.0, 'NORMAL'],
    ["TURN", 90, 1.2, 0.4, 'NORMAL'],
    ["CRAWL", 135, 1.0, 0.0, 'NORMAL'],
    ["STOP", 165, 0.0, 0.0, 'NORMAL'],
    ["BRAKE", 170, 0.0, 0.0, 'BRAKE'],
    ["", 180, 0.0, 0.0, "BRAKE"],
]

MAX_FWD_SPEED = 0.25
MAX_TURN_FWD_SPEED = 0.25

TURBO_MAX_FWD_SPEED = 0.6
TURBO_MAX_TURN_FWD_SPEED = 0.6

MAX_REV_SPEED = 0.2
MAX_TURN_REV_SPEED = 0.2

MOTOR_MULTIPLIER = 900

PI = 3.14159
E = 2.7182


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
        # print "ACCEL {} {} {}".format(accel_profile, current_speed, accel_rate)
        current_speed += accel_rate
        if current_speed > target_speed:
            current_speed = target_speed

    elif target_speed < current_speed:
        # deccelerate
        decel_rate = ACCEL_PROFILES[accel_profile][1]
        # print "DECEL {} {} {}".format(accel_profile, current_speed, decel_rate)
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

    def active(self):
        return False

    def motor_speeds(self):
        return 0.0, 0.0


class CrawlMC(MotionController):
    _name = "CRAWL"


class SpinMC(MotionController):
    _name = "SPIN"
    _direction = "NONE"
    _turn_speed = 0

    def active(self):
        if self._joystick.magnitude() > 10:
            return True

        if self._turn_speed > 0:
            return True

        return False

    def submode(self):
        return self._direction

    def process_update(self):
        direction = None
        turn_speed = 0

        angle = self._joystick.angle()

        if angle in set([0, 180, 360]):
            direction = 'NONE'
            turn_speed = 0
        elif angle <= 90:
            direction = 'RIGHT'
            turn_speed = linear_map(angle, 0, 90, 0.0, 1.0)
        elif angle < 180:
            direction = 'RIGHT'
            turn_speed = linear_map(angle, 90, 180, 1.0, 0.0)
        elif angle <= 270:
            direction = 'LEFT'
            turn_speed = linear_map(angle, 180, 270, 0.0, 1.0)
        else:
            direction = 'LEFT'
            turn_speed = linear_map(angle, 270, 360, 1.0, 0.0)

        self._direction = direction
        self._turn_speed = process_accel(turn_speed, self._turn_speed, 'SPIN')

    def motor_speeds(self):
        turn_speed = self._turn_speed

        # XXX doesn't switch directions with accel properly
        if self._direction == 'LEFT':
            return turn_speed * -1.0, turn_speed
        if self._direction == 'RIGHT':
            return turn_speed, turn_speed * -1.0

        return 0, 0


class NormalMC(MotionController):
    _name = "NORMAL"
    _submode = ""

    _l_speed = 0.0
    _r_speed = 0.0
    _max_speed = 0.0
    _speed = 0.0

    def submode(self):
        return self._submode

    def active(self):
        if self._joystick.magnitude() > 10:
            return True

        if self._speed > 0 and (self._l_speed != 0 or self._r_speed != 0):
            return True

        return False

    def decode_turn(self):
        magnitude = self._joystick.magnitude()
        angle = self._joystick.angle()

        if magnitude > 10 and self._name == 'FORWARD':
            if angle <= 180:
                turn_direction = 'RIGHT'
                turn_angle = angle
            else:
                turn_direction = 'LEFT'
                turn_angle = 360 - angle
        elif magnitude > 10:
            if angle <= 180:
                turn_direction = 'RIGHT'
                turn_angle = 180 - angle
            else:
                turn_direction = 'LEFT'
                turn_angle = 180 - (360 - angle)
        else:
            turn_direction = 'NONE'
            turn_angle = 0

        return turn_direction, turn_angle

    def decode_submode(self, turn_angle):
        submode = 'NONE'
        start_angle = 0
        end_angle = 0
        start_m1_speed = 0
        end_m1_speed = 0
        start_m2_speed = 0
        end_m2_speed = 0
        accel_profile = None

        if self._joystick.magnitude() <= 10:
            return "COAST", 0.0, 0.0, "NORMAL"

        for i in range(0, len(JOY_MODES) - 1):
            submode, start_angle, start_m1_speed, start_m2_speed, \
                accel_profile = JOY_MODES[i]
            next_submode, end_angle, end_m1_speed, end_m2_speed, \
                next_accel_profile = JOY_MODES[i + 1]
            if turn_angle >= start_angle and turn_angle < end_angle:
                del next_submode
                del next_accel_profile
                break

        m1_speed = linear_map(turn_angle, start_angle, end_angle, start_m1_speed, end_m1_speed)
        m2_speed = linear_map(turn_angle, start_angle, end_angle, start_m2_speed, end_m2_speed)

        return submode, m1_speed, m2_speed, accel_profile

    def max_speed(self, turn_angle):
        if self._name == 'FORWARD':
            if self._joystick.button_z():
                max_speed = ((TURBO_MAX_FWD_SPEED - TURBO_MAX_TURN_FWD_SPEED) *
                             ((135.0 - float(turn_angle)) / 135.0)) + TURBO_MAX_TURN_FWD_SPEED
            else:
                max_speed = ((MAX_FWD_SPEED - MAX_TURN_FWD_SPEED) *
                             ((135.0 - float(turn_angle)) / 135.0)) + MAX_TURN_FWD_SPEED

        elif self._name == 'REVERSE':
            max_speed = ((MAX_REV_SPEED - MAX_TURN_REV_SPEED) *
                         ((135.0 - float(turn_angle)) / 135.0)) + MAX_TURN_FWD_SPEED

        return max_speed

    def process_update(self):
        turn_direction, turn_angle = self.decode_turn()

        self._submode, m1_speed, m2_speed, accel_profile = self.decode_submode(turn_angle)

        max_speed = self.max_speed(turn_angle)

        if self._submode != 'COAST':
            speed = gamma(self._joystick.magnitude()) / 100.0
        else:
            speed = 0.0

        if accel_profile == 'NORMAL' and self._joystick.button_z():
            accel_profile = 'TURBO'

        self._speed = process_accel(speed, self._speed, accel_profile)
        self._max_speed = process_accel(max_speed, self._max_speed, accel_profile)

        if turn_direction == 'LEFT':
            self._l_speed = process_accel(m2_speed, self._l_speed, accel_profile)
            self._r_speed = process_accel(m1_speed, self._r_speed, accel_profile)
        elif turn_direction == 'RIGHT':
            self._l_speed = process_accel(m1_speed, self._l_speed, accel_profile)
            self._r_speed = process_accel(m2_speed, self._r_speed, accel_profile)
        else:
            self._l_speed = process_accel(speed, self._l_speed, accel_profile)
            self._r_speed = process_accel(speed, self._r_speed, accel_profile)

    def motor_speeds(self):
        left_motor = math.sqrt(self._l_speed * self._speed) * self._max_speed
        right_motor = math.sqrt(self._r_speed * self._speed) * self._max_speed

# left_motor *= 0.96

        if self._name == 'REVERSE':
            left_motor *= -1.0
            right_motor *= -1.0

        left_motor *= MOTOR_MULTIPLIER
        right_motor *= MOTOR_MULTIPLIER

        return left_motor, right_motor


class ForwardMC(NormalMC):
    _name = "FORWARD"


class ReverseMC(NormalMC):
    _name = "REVERSE"


class ComplexMotionController(object):
    _controller = None
    _missed_data = 3

    def name(self):
        if self._controller:
            return self._controller.name()

        if self._missed_data >= 3:
            return 'OFFLINE'

        return 'IDLE'

    def submode(self):
        if self._controller:
            return self._controller.submode()
        return ""

    def controller_selector(self, joystick):
        if joystick.magnitude() < 10:
            return None

        angle = joystick.angle()
        controller_class = None

        if joystick.button_c():
            if angle <= 45 or angle >= 315:
                controller_class = SpinMC
            elif angle > 45 and angle < 135:
                controller_class = CrawlMC
            elif angle >= 135 and angle <= 225:
                controller_class = SpinMC
            elif angle > 225 and angle < 315:
                controller_class = CrawlMC
        elif (angle <= 45) or (angle >= 315):
            controller_class = ForwardMC
        elif (angle >= 135) and (angle <= 225):
            controller_class = ReverseMC

        if controller_class:
            return controller_class()

        return None

    def update_joystick(self, joystick):
        if joystick.valid():
            self._missed_data = 0

            # if a controller isn't running, see if one should be:
            if not self._controller:
                self._controller = self.controller_selector(joystick)
        else:
            self._missed_data += 1
            if self._missed_data > 3:
                self._controller = None

        if self._controller:
            self._controller.update_joystick(joystick)

            # if the existing controller is idle, kill it
            if not self._controller.active():
                self._controller = None

    def motor_speeds(self):
        if self._controller:
            return self._controller.motor_speeds()

        return 0.0, 0.0


class Sofa(object):
    '''A skid-steered couch'''
    _motors = None
    _nunchuk = None
    _status_path = None

    def __init__(self, roboteq_path, status_path, listen):
        self._status_path = status_path
        (addr, port) = listen.split(':')
        self._nunchuk = nunchuk.Nunchuk(addr=addr, port=int(port))
        self._motors = roboteq.Roboteq(path=roboteq_path)

    def dump_status(self, joystick, controller):
        volts = self._motors.volts()
        amps_l, amps_r = self._motors.amps()

        volts = "{:4.1f} ({:5.2f})".format(volts, volts / 3)
        amps = "{:4.1f} {:4.1f}".format(amps_l, amps_r)

        left_motor, right_motor = controller.motor_speeds()

        print("{:10s} {:10s} {:3d} {:3d} {:4f} {:4f} {:s} {:s}".format(
            controller.name(), controller.submode(), joystick.magnitude(),
            joystick.angle(), left_motor, right_motor, volts, amps))

    def control_loop(self):
        """the main logic"""

        controller = ComplexMotionController()

        while True:
            joystick = self._nunchuk.get_joystick()
            controller.update_joystick(joystick)

            left_motor, right_motor = controller.motor_speeds()
            self._motors.speed(left_motor, right_motor)

            self.dump_status(joystick, controller)

            time.sleep(0.1)
