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
        self._motors = roboteq.Roboteq(path=roboteq_path)
        self._controller = motion_complex.ComplexMotionController()

    def dump_status(self, joystick):
        volts = self._motors.volts()
        amps_l, amps_r = self._motors.amps()

        volts = "{:4.1f} ({:5.2f})".format(volts, volts / 3)
        amps = "{:4.1f} {:4.1f}".format(amps_l, amps_r)

        left_motor, right_motor = self._controller.motor_speeds()

        print("{:10s} {:10s} {:3d} {:3d} {:4f} {:4f} {:s} {:s}".format(
            self._controller.name(), self._controller.submode(), joystick.magnitude(),
            joystick.angle(), left_motor, right_motor, volts, amps))

    def control_loop(self):
        while True:
            joystick = self._nunchuk.get_joystick()
            self._controller.update_joystick(joystick)

            left_motor, right_motor = self._controller.motor_speeds()
            self._motors.speed(left_motor, right_motor)

            self.dump_status(joystick)

            time.sleep(0.1)
