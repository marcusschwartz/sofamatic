'''A roboteq RS232 motor controller with accel/deccel enforcement'''
import time
import serial

import accel_limit
import energy_tracker
import status


class RoboteqStatus(status.Status):
    _attrs = ['energy', 'brake', 'speed_l', 'speed_r', 'temps']
    _dashboard_fmt = ['{energy:20s}', '{0.brake_text:5s}', '{speed_l:4.0f}l',
                      '{speed_r:4.0f}r', '{0.max_temp:3d}F']

    @property
    def brake_text(self):
        if self.brake:
            return 'BRAKE'
        return ''

    @property
    def max_temp(self):
        return max(self.temps)


class Roboteq(object):
    '''A roboteq RS232 motor controller with accel/deccel enforcement'''
    _speed_l = 0
    _speed_r = 0
    _energy = energy_tracker.EnergyTracker()
    _accel_limit = accel_limit.AccelerationLimiter()

    def __init__(self, path="/dev/ttyACM0", speed=115200):
        if path:
            self._roboteq = serial.Serial(path, speed, timeout=1)
        else:
            self._roboteq = None
        self._last_speed_ts = time.time()

        self._poll_energy()

    @property
    def status(self):
        self._poll_energy()

        return RoboteqStatus(
            brake=self.brake_active,
            energy=self._energy.status,
            temps=self.temps,
            speed_l=self._speed_l,
            speed_r=self._speed_r)

    def _poll_energy(self):
        if self._roboteq is None:
            return
        volts = self.roboteq_exec("?V")[2:]
        amps = self.roboteq_exec("?BA")[3:]

        volts = float(volts.split(':')[1]) / 10
        amps_l = float(amps.split(':')[1]) / 10
        amps_r = float(amps.split(':')[0]) / 10

        self._energy.update(volts, amps_l, amps_r)

    def set_speed(self, speed_l, speed_r):
        '''set the speed of both motors'''

        now = time.time()
        delay = now - self._last_speed_ts
        self._last_speed_ts = now

        self._speed_l = self._accel_limit.limit(speed_l, self._speed_l, delay)
        self._speed_r = self._accel_limit.limit(speed_r, self._speed_r, delay)

        if self._roboteq is None:
            return

        self.roboteq_exec("!G 1 {}".format(-1 * int(self._speed_l)))
        self.roboteq_exec("!G 2 {}".format(int(self._speed_r)))

    @property
    def brake_active(self):
        '''return true if the emergency brake is active.'''
        if self._roboteq is None:
            return False
        brake = int(self.roboteq_exec("?DI 6")[3:])
        return brake == 1

    @property
    def temps(self):
        if self._roboteq is None:
            return 0, 0, 0
        temps = self.roboteq_exec("?T")[2:]
        return [int((float(x) * 1.8) + 32.0) for x in temps.split(':')]

    def roboteq_exec(self, cmd):
        '''run a single serial command against the controller'''
        if self._roboteq is None:
            return None
        self._roboteq.write(cmd + "\r")
        self._roboteq.read(len(cmd) + 1)
        newline = False
        resp = ''
        while not newline:
            char = self._roboteq.read(1)
            if char == "\r":
                newline = True
            else:
                resp = resp + char

        return resp
