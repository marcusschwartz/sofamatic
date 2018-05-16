"""a sofa"""
import time

import nunchuk
import roboteq
import motion_complex


class Sofa(object):
    def __init__(self, roboteq_path, status_path, listen):
        self._status_path = status_path
        (addr, port) = listen.split(':')
        self._nunchuk = nunchuk.Nunchuk(addr=addr, port=int(port))
        self._roboteq = roboteq.Roboteq(path=roboteq_path)
        self._controller = motion_complex.ComplexMotionController()

    def status(self, joystick):
        return " ".join([self._controller.status(),
                         joystick.status(),
                         self._roboteq.status()])

    def run(self):
        while True:
            joystick = self._nunchuk.get_joystick()
            self._controller.update_joystick(joystick)

            left_motor, right_motor = self._controller.motor_speeds()
            self._roboteq.set_speed(left_motor, right_motor)

            print self.status(joystick)

            time.sleep(0.1)
