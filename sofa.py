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

    def update_status_file(self, joystick, status):
        if not self._status_path:
            return
        details = util.merge_status_details({
            "j": joystick.status().details,
            "m": self._roboteq.status().details,
            "c": self._controller.status().details,
            "l": status,
        })
        details["ts"] = int(time.time())
        json.dump(details, open(self._status_path, "w"))

    def status_string(self, joystick, status_string):
        return " ".join([self._controller.status().string,
                         joystick.status().string,
                         self._roboteq.status().string,
                         status_string])

    def send_status_packet(self, joystick, status):
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
        last_rcv = time.time()
        timeout = 0
        INTERVAL = 0.1  # seconds
        GRACE = 0.2  # percent of INTERVAL, 0.0-1.0
        while True:
            now = time.time()
            cycle_time = now - last_rcv
            timeout = (INTERVAL + (INTERVAL * GRACE)) - cycle_time
            joystick = self._nunchuk.get_joystick(timeout)
            now = time.time()
            packet_interval = int(1000 * (now - last_rcv))
            last_rcv = now

            stats = {
                "loop_util": cycle_time / INTERVAL,
                "interval": packet_interval,
            }

            status_string = "%3d%% %4dms" % (100 * cycle_time / INTERVAL,
                                             packet_interval)

            self._controller.update_joystick(joystick)

            left_motor, right_motor = self._controller.motor_speeds()
            self._roboteq.set_speed(left_motor, right_motor)

            self.update_status_file(joystick, stats)
            self.send_status_packet(joystick, stats)
            print self.status_string(joystick, status_string)
