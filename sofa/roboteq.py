'''A roboteq RS232 motor controller with accel/deccel enforcement'''
import time
import serial

import util

ACCEL_LIMIT = [
    [0, 99, 200],
    [100, 1000, 400],
]


def gen_accel_table(table_def):
    """generate an acceleration table"""
    table = []
    for i in range(1001):
        table.append(0)
    for limit_def in table_def:
        range_start, range_end, limit = limit_def
        for i in range(range_start, range_end + 1):
            table[i] = limit

    return table


class Roboteq(object):
    '''A roboteq RS232 motor controller with accel/deccel enforcement'''

    def __init__(self, path="/dev/ttyACM0", speed=115200):
        if path:
            self._roboteq = serial.Serial(path, speed, timeout=1)
        else:
            self._roboteq = None
        self._m1_current = 0
        self._m2_current = 0
        self._last_speed_ts = time.time()

        self._accel_table = gen_accel_table(ACCEL_LIMIT)
        self._decel_table = gen_accel_table(ACCEL_LIMIT)

    def status(self):
        amps_l, amps_r = self.amps()
        volts = self.volts()
        watts = volts * (amps_l + amps_r)
        brake_active = self.brake_active()
        if brake_active:
            brake = 'BRAKE'
        else:
            brake = ''

        status = util.Status()
        status_fmt = "{:5s} {:4.1f}v ({:5.2f}v)  {:4.1f}a {:4.1f}a {:4d}w {:4d}l {:4d}r"
        status.string = status_fmt.format(brake, volts, volts / 3, amps_l, amps_r, int(watts),
                                          self._m1_current, self._m2_current)
        status.details = {
            "volts": volts,
            "volts_12": volts / 3,
            "amps_l": amps_l,
            "amps_r": amps_r,
            "watts": watts,
            "brake": brake_active,
        }

        return status

    def process_accel(self, target, current, delay):
        '''foo'''

        target = int(target)

        # never reverse speed in a single pass
        if (target > 0 and current < 0) or (target < 0 and current > 0):
            target = 0

        change = abs(target) - abs(current)

        if change > 0:
            limit = int(self._accel_table[abs(int(current))] * delay)
            if limit < change:
                # print "LIMIT ACCEL {} -> {}".format(change, limit)
                change = limit
            if target < current:
                change *= -1
        elif change < 0:
            limit = int(self._decel_table[abs(int(current))] * delay)
            if limit < abs(change):
                # print "LIMIT DECEL {} -> {}".format(abs(change), limit)
                change = -1 * limit
            if target > current:
                change *= -1

        current += change

        return current

    def set_speed(self, m1_target, m2_target):
        '''set the speed of both motors'''

        now = time.time()
        delay = now - self._last_speed_ts
        self._last_speed_ts = now

        self._m1_current = self.process_accel(m1_target,
                                              self._m1_current,
                                              delay)
        self._m2_current = self.process_accel(m2_target,
                                              self._m2_current,
                                              delay)

        if self._roboteq is None:
            return

        self.roboteq_exec("!G 1 {}".format(-1 * int(self._m1_current)))
        self.roboteq_exec("!G 2 {}".format(int(self._m2_current)))

    def volts(self):
        '''return the current battery voltage'''
        if self._roboteq is None:
            return 0
        volts = self.roboteq_exec("?V")[2:]
        volts = float(volts.split(':')[1]) / 10
        return volts

    def amps(self):
        '''return the two motor amperages'''
        if self._roboteq is None:
            return 0, 0 
        amps = self.roboteq_exec("?BA")[3:]
        m1_amps = float(amps.split(':')[1]) / 10
        m2_amps = float(amps.split(':')[0]) / 10
        return m1_amps, m2_amps

    def brake_active(self):
        '''return true if the emergency brake is active.'''
        if self._roboteq is None:
            return False
        brake = int(self.roboteq_exec("?DI 6")[3:])
        return brake == 1

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
