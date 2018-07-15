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
import socket
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
	self._udp_status_delay = 0

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

    def send_status_packet(self, joystick):
        self._udp_status_delay -= 1
        if not joystick.addr() or self._udp_status_delay > 0:
	    return
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
	clock = time.strftime("%I:%M:%S%p").lstrip("0")
	voltage = " %4.1fv" % self._roboteq.status().details["volts_12"]
	packet = " ".join((clock, voltage))
        sock.sendto(packet, joystick.addr())
	self._udp_status_delay = 10

    def run(self):
        _ts = time.time()
        while True:
	    start = time.time()
            joystick = self._nunchuk.get_joystick()
            self._controller.update_joystick(joystick)

            left_motor, right_motor = self._controller.motor_speeds()
            self._roboteq.set_speed(left_motor, right_motor)

            self.update_status_file(joystick)
	    self.send_status_packet(joystick)
            print self.status_string(joystick)
	    end = time.time()
	    cycle_time = end - _ts
            _ts = end

	    loop_time = end - start
	    if loop_time < 0.1:
	      delay = 0.1 - loop_time
              time.sleep(0.1 - delay)
