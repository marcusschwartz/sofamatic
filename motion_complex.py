"""a meta motion controller that combines several others"""
from motion_normal import ForwardMC, ReverseMC
from motion_spin import SpinMC
from motion_crawl import CrawlMC


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
