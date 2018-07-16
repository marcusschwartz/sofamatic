#!/usr/bin/python

import time
import atexit

from OmegaExpansion import oledExp


def shutdown():
    oledExp.clear()


empty = list()
for line in range(0, 8):
    empty.append("{:20s}".format(""))


def init():
    oledExp.driverInit()
    oledExp.clear()
    oledExp.setTextColumns()


atexit.register(shutdown)

count = 0

init()
current = list(empty)

while True:
    try:
        status = open("/var/run/sofa_status")
        lines = status.readlines()
        status.close()
        i = 0
        for line in lines:
            line = line.strip()
            line = "{:20s}".format(line)
            if current[i] != line:
                min_diff = 255
                max_diff = 0
                for x in range(0, len(current[i])):
                    if current[i][x] != line[x]:
                        if x < min_diff:
                            min_diff = x
                        if x > max_diff:
                            max_diff = x
                oledExp.setCursor(i, min_diff)
                for x in range(min_diff, max_diff + 1):
                    oledExp.writeChar(line[x])
                current[i] = line
            i += 1
        time.sleep(0.05)
        count += 1
        if count > 1200:
            # re-init every 60 seconds because sometimes
            # the display gets wonky
            init()
            current = list(empty)
            count = 0
    except BaseException as e:
        print("Exception %s" % e)
        init()
        current = list(empty)
        time.sleep(0.05)
