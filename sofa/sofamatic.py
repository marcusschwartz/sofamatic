#!/usr/bin/python
"""fooo"""

import atexit
from optparse import OptionParser
import os

from sofa import Sofa


def shutdown(status_path):
    try:
        os.unlink(status_path)
    except BaseException:
        pass


def main():
    '''start the sofa'''
    parser = OptionParser()

    parser.add_option('-r', '--roboteq_path', dest='roboteq_path',
                      default="/dev/ttyACM0",
                      help="path to roboteq controller")
    parser.add_option('-s', '--status_path', dest="status_path",
                      default="/var/run/sofa_status",
                      help="path to runtime status file")
    parser.add_option('-l', '--listen', dest='listen',
                      default="0.0.0.0:31337",
                      help="ip:port to listen on for joystick data")

    (options, _) = parser.parse_args()

    atexit.register(lambda: shutdown(options.status_path))

    sofa = Sofa(roboteq_path=options.roboteq_path,
                status_path=options.status_path,
                listen=options.listen)
    sofa.run()


main()
