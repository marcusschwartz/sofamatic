"""
a motion controller to spin in place, where the left and right motors
move in exactly oposite speeds
"""
from motion import MotionController, linear_map, process_accel


JOY_DEADZONE = 10
MAX_SPEED = 150.0


class SpinMC(MotionController):
    _name = "SPIN"
    _direction = "NONE"
    _turn_speed = 0

    @property
    def active(self):
        if self._turn_speed > 0:
            return True
        return False

    @property
    def submode(self):
        return self._direction

    def _process_update(self):
        direction = None
        turn_speed = 0

        angle = self._joystick.angle

        if angle < JOY_DEADZONE or angle > 360 - JOY_DEADZONE:
            direction = 'NONE'
            turn_speed = 0
        elif angle > 180 - JOY_DEADZONE and angle < 180 + JOY_DEADZONE:
            direction = 'NONE'
            turn_speed = 0
        elif angle <= 90:
            direction = 'RIGHT'
            turn_speed = linear_map(angle, JOY_DEADZONE, 90, 0.0, 1.0)
        elif angle <= 180 - JOY_DEADZONE:
            direction = 'RIGHT'
            turn_speed = linear_map(angle, 90, 180 - JOY_DEADZONE, 1.0, 0.0)
        elif angle <= 270:
            direction = 'LEFT'
            turn_speed = linear_map(angle, 180 + JOY_DEADZONE, 270, 0.0, 1.0)
        else:
            direction = 'LEFT'
            turn_speed = linear_map(angle, 270, 360 - JOY_DEADZONE, 1.0, 0.0)

        self._direction = direction
        self._turn_speed = process_accel(turn_speed, self._turn_speed, 'SPIN')

    @property
    def motor_speeds(self):
        turn_speed = self._turn_speed

        # TODO doesn't switch directions with accel properly
        if self._direction == 'LEFT':
            return turn_speed * -1.0 * MAX_SPEED, turn_speed * MAX_SPEED
        if self._direction == 'RIGHT':
            return turn_speed * MAX_SPEED, turn_speed * -1.0 * MAX_SPEED

        return 0, 0
