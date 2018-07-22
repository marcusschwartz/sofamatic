"""
  A Sofa has three major components:
    * receiver - a wireless joystick that returns a magnitude/angle vector
    * roboteq - a motor speed controller that takes left/right motor speeds
                as inputs
    * controller - a motion controller that translates the joystick vector
                   into left/right motor speeds

  It runs in a loop, taking vectors from the joystick, translating them into
  motor speeds via the controller, and then passes the motor speeds to the
  roboteq.
"""
import json
import time

import motion_complex
import receiver
import roboteq
import status


class SofaStatus(status.Status):
    _attrs = ['receiver', 'roboteq', 'controller', 'timestamp', 'runtime']
    _dashboard_fmt = ['{controller} |',
                      '{0.receiver.remote.joystick.dashboard} |',
                      '{roboteq} |', '{receiver} |',
                      '{0.receiver.remote.dashboard}']
    _remote_parked_fmt = ['{0.roboteq.energy.watt_hours:3.1f}wh',
                          '{0.roboteq.energy.volts:4.1f}v',
                          '{0.receiver.signal_strength:3d}%'
                          '~**PARKING BRAKE**']
    _remote_idle_fmt = ['{0.roboteq.energy.watt_hours:3.1f}wh',
                        '{0.roboteq.energy.volts:4.1f}v',
                        '{0.receiver.signal_strength:3d}%~'
			'{0.roboteq.min_temp:d-{0.roboteq.max_temp:d}F',
			'{0.roboteq.energy.regen_watt_hours:-6.2f}whr']
    _remote_active_fmt = ['&{0.controller.mode}:{0.controller.submode}'
                          '~{0.controller.throttle_pct:3d}%',
                          '{0.roboteq.energy.watts:3.0f}w']

class Sofa(object):

    def __init__(self, roboteq_path, status_path, listen):
        self._status_path = status_path
        (addr, port) = listen.split(':')
        self._receiver = receiver.RemoteControlReceiver(addr=addr, port=int(port))
        self._roboteq = roboteq.Roboteq(path=roboteq_path)
        self._controller = motion_complex.ComplexMotionController()
        self._start_ts = time.time()

    @property
    def status(self):
        now = time.time()
        return SofaStatus(
            receiver=self._receiver.status,
            roboteq=self._roboteq.status,
            controller=self._controller.status,
            timestamp=now,
            runtime=now - self._start_ts,
        )

    def _update_status(self):
        _status = self.status
        self._update_status_file(_status)
        self._receiver.remote.update_status(self._remote_status_string(_status))
        print _status.dashboard

    def _remote_status_string(self, _status):
        if self._roboteq.brake_active and self._receiver.remote.joystick.active:
            remote_status = '&PARKING~BRAKE'
        elif self._roboteq.brake_active:
            remote_status = _status.remote_parked
        elif self._controller.active:
            remote_status = _status.remote_active
        else:
	    if self._receiver.remote.joystick.button_z and self._receiver.remote.joystick.button_c:
	        remote_status = '&WOAH!!'
	    elif self._receiver.remote.joystick.button_z:
	        remote_status = '&TURBO'
	    elif self._receiver.remote.joystick.button_c:
	        remote_status = '&SPIN/~CRAWL'
	    else:
                remote_status = _status.remote_idle
        return remote_status

    def _update_status_file(self, _status):
        if not self._status_path:
            return
        json.dump(_status.as_dict, open(self._status_path, "w"),
                  sort_keys=True, indent=4, separators=(',', ': '))

    def run(self):
        while True:
            self._receiver.wait_for_update()
            self._controller.update_joystick(self._receiver.remote.joystick)
            left_motor, right_motor = self._controller.motor_speeds
            self._roboteq.set_speed(left_motor, right_motor)
            self._update_status()
