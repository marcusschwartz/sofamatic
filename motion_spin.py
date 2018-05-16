"""spinner"""

from motion import MotionController, linear_map, process_accel


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
