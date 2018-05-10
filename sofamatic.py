#!/usr/bin/python

import atexit
from optparse import OptionParser
import os

import sofa

STATUS_PATH = None


def shutdown():
    """remove any evidence of our running"""
    try:
        os.unlink(STATUS_PATH)
    except BaseException:
        pass


def main():
    parser = OptionParser()
    parser.set_defaults(dryrun=False)

    parser.add_option('-n', '--dry-run', dest="dryrun", default=False,
                      action="store_true",
                      help="don't use the motors")
    parser.add_option('-s', '--status_path', dest="status_path",
                      default="/var/run/sofa_status",
                      help="path to runtime status file")
    parser.add_option('-l', '--listen', dest='listen',
                      default="0.0.0.0:31337",
                      help="ip:port to listen on for joystick data")

    (options, args) = parser.parse_args()
    global STATUS_PATH
    STATUS_PATH = options.status_path

    atexit.register(shutdown)

    use_motors = True
    if options.dryrun:
        use_motors = False
    sofamatic = sofa.sofa(use_motors=use_motors, status_path=STATUS_PATH,
                          listen=options.listen)
    sofamatic.control_loop()


main()
