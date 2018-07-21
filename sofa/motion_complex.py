"""a meta motion controller that combines several others"""
from motion import MotionController
from motion_normal import ForwardMC, ReverseMC
from motion_spin import SpinMC
from motion_crawl import CrawlMC
import status


def controller_selector(joystick):
    """
    determine which real motion controller to use based on
    the initial joystick position
    """
    angle = joystick.angle
    controller_class = None

    if joystick.button_c:
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


class ControllerStatus(status.Status):
    _attrs = ['mode', 'submode', 'motor_l', 'motor_r']
    _dashboard_fmt = ['{mode:8s}', '{submode:5s}', '{motor_l:3.0f}l',
                      '{motor_r:3.0f}r']


class ComplexMotionController(MotionController):
    _controller = None
    _online = False

    @property
    def name(self):
        if not self._online:
            return 'OFFLINE'

        if self._controller:
            return self._controller.name

        return 'IDLE'

    @property
    def status(self):
        motor_l, motor_r = self.motor_speeds
        return ControllerStatus(
            mode=self.name,
            submode=self.submode,
            motor_l=motor_l,
            motor_r=motor_r)

    @property
    def submode(self):
        if self._controller:
            return self._controller.submode
        return ""

    def _process_update(self):
        # if we haven't heard from the remote in a while, go offline
        if not self._joystick.valid:
            self._online = False
            self._controller = None
            return

        # only return online when the joystick is centered
        if not self._online and self._joystick.centered:
            self._online = True

        # if a controller isn't running, see if one should be:
        if self._online and not self._controller and not self._joystick.centered:
            self._controller = controller_selector(self._joystick)

        if not self._controller:
            return

        # if the existing controller is idle, kill it
        if not self._controller.active and self._joystick.centered:
            self._controller = None

        if self._controller:
            self._controller.update_joystick(self._joystick)

    @property
    def motor_speeds(self):
        if self._controller:
            return self._controller.motor_speeds

        return 0.0, 0.0
