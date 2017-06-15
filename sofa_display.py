#!/usr/bin/python

import time
import atexit

def shutdown():
  oledExp.clear()

atexit.register(shutdown)

from OmegaExpansion import oledExp

oledExp.driverInit()
oledExp.clear()
oledExp.setTextColumns()

current = list()
for line in range(0, 8):
  current.append("{:20s}".format(""))
empty = current

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
  except:
    current = empty
    oledExp.clear()
    time.sleep(0.05)
