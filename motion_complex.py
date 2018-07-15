"""a meta motion controller that combines several others"""
from motion_normal import ForwardMC, ReverseMC
from motion_spin import SpinMC
from motion_crawl import CrawlMC

import util


def controller_selector(joystick):
    """
    determine which real motion controller to use based on
    the initial joystick position
    """
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


class ComplexMotionController(object):
    _controller = None
    _online = False
    _missed_data = 0

    def name(self):
        if not self._online:
            return 'OFFLINE'

        if self._controller:
            return self._controller.name()

        return 'IDLE'

    def status(self):
        motor_l, motor_r = self.motor_speeds()
        status = util.Status()
        status.string = "{:10s} {:8s} {:6.1f}L {:6.1f}R".format(
            self.name(), self.submode(), motor_l, motor_r)
        status.details = {
            'mode': self.name(),
            'submode': self.submode(),
            'motor_l': motor_l,
            'motor_r': motor_r,
        }

        return status

    def submode(self):
        if self._controller:
            return self._controller.submode()
        return ""

    def update_joystick(self, joystick):
        if joystick.valid():
            self._missed_data = 0

            # only return online when the joystick is idle
            if not self._online and joystick.centered():
                self._online = True

            # if a controller isn't running, see if one should be:
            if self._online and not self._controller \
               and not joystick.centered():
                self._controller = controller_selector(joystick)
        else:
            # we don't have a valid joystick, prepare to go offline
            self._missed_data += 1
            if self._missed_data > 3:
                self._online = False
                self._controller = None

        if self._controller:
            self._controller.update_joystick(joystick)

            # if the existing controller is idle, kill it
            if not self._controller.active() and joystick.centered():
                self._controller = None

    def motor_speeds(self):
        if self._controller:
            return self._controller.motor_speeds()

        return 0.0, 0.0
