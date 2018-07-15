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
import collections
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

    def update_status_file(self, joystick_status, roboteq_status, controller_status, status):
        if not self._status_path:
            return
        details = util.merge_status_details({
            "j": joystick_status.details,
            "m": roboteq_status.details,
            "c": controller_status.details,
            "l": status,
        })
        details["ts"] = int(time.time())
        json.dump(details, open(self._status_path, "w"))

    def status_string(self, joystick_status, roboteq_status, controller_status, status_string):
        return " ".join([controller_status.string,
                         joystick_status.string,
                         roboteq_status.string,
                         status_string])

    def send_status_packet(self, addr, joystick_status, roboteq_status, controller_status, status):
        self._udp_status_delay -= 1
        if not addr or self._udp_status_delay > 0:
            return
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        clock = time.strftime("%I:%M:%S").lstrip("0")
        voltage = "%4.1fv" % roboteq_status.details["volts_12"]
        brake = roboteq_status.details["brake"]
        pl = "%3d%%" % (100 - status["packet_loss"])
        packet = " ".join((clock, voltage, pl))
        if brake:
            packet += "~**PARKING BRAKE**"
        sock.sendto(packet, addr)
        self._udp_status_delay = 10

    def run(self):
        last_rcv = time.time()
        timeout = 0
        INTERVAL = 0.1  # seconds
        GRACE = 0.2  # percent of INTERVAL, 0.0-1.0
        packet_history = collections.deque()
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

            packet_history.append(tuple((int(100 * cycle_time / INTERVAL),
                                            packet_interval, joystick)))
            if len(packet_history) > 10:
                packet_history.popleft()

            loop_util_total = 0
            jitter_total = 0
            interval_total = 0
            missing_total = 0
            for [old_loop_util, old_interval, old_joystick] in packet_history:
                loop_util_total += old_loop_util
                interval_total += old_interval
                jitter_total += abs(100 - old_interval)
                if not old_joystick.valid():
                    missing_total += 1

            loop_util_avg = loop_util_total / len(packet_history)
            jitter_avg = jitter_total / len(packet_history)
            interval_avg = interval_total / len(packet_history)
            packet_loss_pct = int(100 * missing_total / len(packet_history))

            stats["packet_loss"] = packet_loss_pct

            status_string = "%3d%% %4dms %4dms %2dms %3d%%" % (100 * cycle_time / INTERVAL,
                                             packet_interval, interval_avg, jitter_avg, packet_loss_pct)

            self._controller.update_joystick(joystick)

            left_motor, right_motor = self._controller.motor_speeds()
            self._roboteq.set_speed(left_motor, right_motor)

            joystick_status = joystick.status()
            roboteq_status = self._roboteq.status()
            controller_status = self._controller.status()

            self.update_status_file(joystick_status, roboteq_status, controller_status, stats)
            self.send_status_packet(joystick.addr(), joystick_status, roboteq_status, controller_status, stats)
            print self.status_string(joystick_status, roboteq_status, controller_status, status_string)
