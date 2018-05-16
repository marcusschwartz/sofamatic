'''A roboteq RS232 motor controller with accel/deccel enforcement'''
import time
import serial

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
                print "LIMIT ACCEL {} -> {}".format(change, limit)
                change = limit
        elif change < 0:
            limit = int(self._decel_table[abs(int(current))] * delay)
            if limit < abs(change):
                print "LIMIT DECEL {} -> {}".format(abs(change), limit)
                change = -1 * limit

        current += change

        return current

    def speed(self, m1_target, m2_target):
        '''set the speed of both motors'''

        now = time.time()
        delay = now - self._last_speed_ts
        self._last_speed_ts = now

        self._m1_current = self.process_accel(m1_target, self._m1_current, delay)
        self._m2_current = self.process_accel(m2_target, self._m2_current, delay)

        if self._roboteq is None:
            print "SPEED {} {}".format(int(self._m1_current), int(self._m2_current))
            return
        self.roboteq_exec("!G 1 {}".format(-1 * int(m1_target)))
        self.roboteq_exec("!G 2 {}".format(int(m2_target)))

    def volts(self):
        '''return the current battery voltage'''
        if self._roboteq is None:
            return -1
        volts = self.roboteq_exec("?V")[2:]
        volts = float(volts.split(':')[1]) / 10
        return volts

    def amps(self):
        '''return the two motor amperages'''
        if self._roboteq is None:
            return -1, -1
        amps = self.roboteq_exec("?BA")[3:]
        m1_amps = float(amps.split(':')[1]) / 10
        m2_amps = float(amps.split(':')[0]) / 10
        return m1_amps, m2_amps

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
