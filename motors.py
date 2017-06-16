#!/usr/bin/python

import serial


class roboteq:
    def __init__(self, path="/dev/ttyACM0", speed=115200):
        self._roboteq = serial.Serial(path, speed, timeout=1)

    def speed(self, left_motor, right_motor):
        self.roboteq_exec("!G 2 {}".format(-1 * int(left_motor)))
        self.roboteq_exec("!G 1 {}".format(int(right_motor)))

    def volts(self):
        volts = self.roboteq_exec("?V")[2:]
        volts = float(volts.split(':')[1]) / 10
        return volts

    def amps(self):
        amps = self.roboteq_exec("?BA")[3:]
        amps_l = float(amps.split(':')[0]) / 10
        amps_r = float(amps.split(':')[1]) / 10
        return amps_l, amps_r

    def roboteq_exec(self, cmd):
        """run a motor controller command and return the results"""
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
