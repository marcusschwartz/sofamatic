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
    INTERVAL = 0.1  # seconds
    GRACE = 0.2  # percent of INTERVAL, 0.0-1.0

    def __init__(self, roboteq_path, status_path, listen):
        self._status_path = status_path
        (addr, port) = listen.split(':')
        self._nunchuk = nunchuk.Nunchuk(addr=addr, port=int(port))
        self._roboteq = roboteq.Roboteq(path=roboteq_path)
        self._controller = motion_complex.ComplexMotionController()
        self._udp_status_delay = 0
        self._packet_history = collections.deque()
        self._watt_hours = 0
        self._regen_watt_hours = 0

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
        watt_hours = status["watt_hours"] + status["regen_watt_hours"]
        energy = "%3.1fwh" % watt_hours
        voltage = "%4.1fv" % roboteq_status.details["volts_12"]
        brake = roboteq_status.details["brake"]
        pl = "%3d%%" % (100 - status["packet_loss"])
        packet = " ".join((energy, voltage, pl))
        if False and brake:
            packet += "~**PARKING BRAKE**"
        elif controller_status.details["mode"] != "IDLE":
            watts = roboteq_status.details["watts"]
            packet += "~%s:%s %4dw" % (controller_status.details["mode"],
                                       controller_status.details["submode"],
                                       watts)
        else:
            if status["watt_hours"]:
                regen_pct = 100 * abs(status["regen_watt_hours"]) / status["watt_hours"]
            else:
                regen_pct = 0
            packet += "~%1d%% regen" % regen_pct
        sock.sendto(packet, addr)
        self._udp_status_delay = 10

    def tally_energy(self, watts, duration):
        watt_hours = (duration / 3600) * watts
        if watt_hours > 0:
            self._watt_hours += watt_hours
        else:
            self._regen_watt_hours += watt_hours

        return {
            "watt_hours": self._watt_hours,
            "regen_watt_hours": self._regen_watt_hours,
        }

    def _add_packet_history(self, joystick):
        duty_cycle = int(100 * self._cycle_time / self.INTERVAL)
        interval = self._packet_interval
        self._packet_history.append(tuple((duty_cycle, interval, joystick)))
        if len(self._packet_history) > 10:
            self._packet_history.popleft()

    def _analyze_packet_history(self):
        loop_util_total = 0
        jitter_total = 0
        interval_total = 0
        missing_total = 0
        records = len(self._packet_history)
        for [old_loop_util, old_interval, old_joystick] in self._packet_history:
            interval_total += old_interval
        interval = interval_total / records
        for [old_loop_util, old_interval, old_joystick] in self._packet_history:
            loop_util_total += old_loop_util
            jitter_total += abs(interval - old_interval)
            if not old_joystick.valid():
                missing_total += 1


        stats = {
            "duty_cycle": loop_util_total / records,
            "jitter": jitter_total / records,
            "interval": interval_total / records,
            "packet_loss": int(100 * missing_total / records),
        }

        return stats

    def loop_status_string(self, status):
        return "%5.1fwh %-5.2fwh %3d%% %4dms %4dms %2dms %3d%%" % (
            self._watt_hours, self._regen_watt_hours, status["duty_cycle"],
            int(1000 * self._packet_interval), int(1000 * status["interval"]), 
            int(1000 * status["jitter"]), status["packet_loss"])

    def run(self):
        last_rcv = time.time()
        timeout = 0
        while True:
            now = time.time()
            self._cycle_time = now - last_rcv
            timeout = (self.INTERVAL + (self.INTERVAL * self.GRACE)) - self._cycle_time
            joystick = self._nunchuk.get_joystick(timeout)
            now = time.time()
            self._packet_interval = now - last_rcv
            last_rcv = now

            self._controller.update_joystick(joystick)

            left_motor, right_motor = self._controller.motor_speeds()
            self._roboteq.set_speed(left_motor, right_motor)

            #
            # loop status 
            #

            self._add_packet_history(joystick)

            loop_status = self._analyze_packet_history()
            joystick_status = joystick.status()
            roboteq_status = self._roboteq.status()
            controller_status = self._controller.status()

            loop_status.update(self.tally_energy(
                roboteq_status.details["watts"], self._packet_interval))
        
            loop_status_string = self.loop_status_string(loop_status)

            self.update_status_file(joystick_status, roboteq_status, controller_status, loop_status)
            self.send_status_packet(joystick.addr(), joystick_status, roboteq_status, controller_status, loop_status)
            print self.status_string(joystick_status, roboteq_status, controller_status, loop_status_string)
