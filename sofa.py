"""
A Sofa has three major components:
  * nunchuk - a wireless joystick that returns a magnitude/angle vector
  * roboteq - a motor speed controller that takes left/right motor speeds
              as inputs
  * controller - a motion controller that translates the joystick vector
                 into left/right motor speeds

  It just runs in a loop, taking vectors from the joystick, translating them
  into motor speeds via the controller, and then passes the motor speeds to
  the roboteq.
"""
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

    def update_status_file(self, joystick):
        if self._status_path:
            status = open(self._status_path, "w")
            status.write(self._controller.status().string + "\n")
            status.write(joystick.status().string + "\n")
            status.write(self._roboteq.status().string + "\n")
            status.close()

    def status(self, joystick):
        return " ".join([self._controller.status().string,
                         joystick.status().string,
                         self._roboteq.status().string])

    def run(self):
        while True:
            joystick = self._nunchuk.get_joystick()
            self._controller.update_joystick(joystick)

            left_motor, right_motor = self._controller.motor_speeds()
            self._roboteq.set_speed(left_motor, right_motor)

            self.update_status_file(joystick)
            print self.status(joystick)

            time.sleep(0.1)
