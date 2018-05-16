"""
  A Sofa has three major components:
    * nunchuk - a wireless joystick that returns a magnitude/angle vector
    * roboteq - a motor speed controller that takes left/right motor speeds
                as inputs
    * controller - a motion controller that translates the joystick vector
                   into left/right motor speeds

  It runs in a loop, taking vectors from the joystick, translating them into
  motor speeds via the controller, and then passes the motor speeds to the
  roboteq.
"""
import json
import time

import motion_complex
import nunchuk
import roboteq
import util


class Sofa(object):
    def __init__(self, roboteq_path, status_path, listen):
        self._status_path = status_path
        (addr, port) = listen.split(':')
        self._nunchuk = nunchuk.Nunchuk(addr=addr, port=int(port))
        self._roboteq = roboteq.Roboteq(path=roboteq_path)
        self._controller = motion_complex.ComplexMotionController()

    def update_status_file(self, joystick):
        if not self._status_path:
            return
        details = util.merge_status_details({
            "j": joystick.status().details,
            "m": self._roboteq.status().details,
            "c": self._controller.status().details,
        })
        details["ts"] = int(time.time())
        json.dump(details, open(self._status_path, "w"))

    def status_string(self, joystick):
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
            print self.status_string(joystick)

            time.sleep(0.1)
