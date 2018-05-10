'''A roboteq RS232 motor controller with accel/deccel enforcement'''

import serial


class Roboteq(object):
    '''A roboteq RS232 motor controller with accel/deccel enforcement'''
    def __init__(self, path="/dev/ttyACM0", speed=115200):
        if path:
            self._roboteq = serial.Serial(path, speed, timeout=1)
        else:
            self._roboteq = None

    def speed(self, m1_target, m2_target):
        '''set the speed of both motors'''
        if self._roboteq is None:
            print "SPEED {} {}".format(int(m1_target), int(m2_target))
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
