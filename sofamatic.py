#!/usr/bin/python

import atexit

import sofa


def shutdown():
    """remove any evidence of our running"""
    try:
        os.unlink("/var/run/sofa_status")
    except BaseException:
        pass


atexit.register(shutdown)
sofamatic = sofa.sofa()
sofamatic.control_loop()
