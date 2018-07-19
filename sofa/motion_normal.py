"""a motion controller that behaves sort of like a normal steered vehicle"""
import math

from motion import MotionController, linear_map, gamma, process_accel

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

MAX_FWD_SPEED = 0.55
MAX_TURN_FWD_SPEED = 0.60

TURBO_MAX_FWD_SPEED = 1.0
TURBO_MAX_TURN_FWD_SPEED = 1.0

MAX_REV_SPEED = 0.2
MAX_TURN_REV_SPEED = 0.2

MOTOR_MULTIPLIER = 900


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
        if self._speed > 0 and (self._l_speed != 0 or self._r_speed != 0):
            return True

        return False

    def decode_turn(self):
        magnitude = self._joystick.magnitude
        angle = self._joystick.angle

        if magnitude > 10 and self._name == 'FWD':
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

        if self._joystick.centered or not self._joystick.valid:
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

        m1_speed = linear_map(turn_angle, start_angle, end_angle,
                              start_m1_speed, end_m1_speed)
        m2_speed = linear_map(turn_angle, start_angle, end_angle,
                              start_m2_speed, end_m2_speed)

        return submode, m1_speed, m2_speed, accel_profile

    def max_speed(self, turn_angle):
        if self._name == 'FWD':
            if self._joystick.button_z:
                max_speed = ((TURBO_MAX_FWD_SPEED - TURBO_MAX_TURN_FWD_SPEED) *
                             ((135.0 - float(turn_angle)) / 135.0)) + TURBO_MAX_TURN_FWD_SPEED
            else:
                max_speed = ((MAX_FWD_SPEED - MAX_TURN_FWD_SPEED) *
                             ((135.0 - float(turn_angle)) / 135.0)) + MAX_TURN_FWD_SPEED

        elif self._name == 'REV':
            max_speed = ((MAX_REV_SPEED - MAX_TURN_REV_SPEED) *
                         ((135.0 - float(turn_angle)) / 135.0)) + MAX_TURN_FWD_SPEED

        return max_speed

    def process_update(self):
        turn_direction, turn_angle = self.decode_turn()

        self._submode, m1_speed, m2_speed, accel_profile = self.decode_submode(turn_angle)

        max_speed = self.max_speed(turn_angle)

        if self._submode != 'COAST':
            speed = gamma(self._joystick.magnitude) / 100.0
        else:
            speed = 0.0

        if accel_profile == 'NORMAL' and self._joystick.button_z:
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

        left_motor *= 0.95

        if self._name == 'REV':
            left_motor *= -1.0
            right_motor *= -1.0

        left_motor *= MOTOR_MULTIPLIER
        right_motor *= MOTOR_MULTIPLIER

        return left_motor, right_motor


class ForwardMC(NormalMC):
    _name = "FWD"


class ReverseMC(NormalMC):
    _name = "REV"
