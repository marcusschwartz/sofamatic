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

import motion_complex
import receiver
import roboteq
import status


class SofaStatus(status.Status):
    _attrs = ['receiver', 'roboteq', 'controller']
    _dashboard_fmt = ['{controller} |',
                      '{0.receiver.remote.joystick.dashboard} |',
                      '{roboteq} |', '{receiver}']
    _remote_parked_fmt = ['{0.roboteq.energy.watt_hours:3.1f}wh {0.roboteq.energy.volts:4.1f}v {0.receiver.signal_strength:3d}%~**PARKING BRAKE**']
    _remote_idle_fmt = ['{0.roboteq.energy.watt_hours:3.1f}wh {0.roboteq.energy.volts:4.1f}v {0.receiver.signal_strength:3d}%~']


class Sofa(object):

    def __init__(self, roboteq_path, status_path, listen):
        self._status_path = status_path
        (addr, port) = listen.split(':')
        self._receiver = receiver.RemoteControlReceiver(addr=addr, port=int(port))
        self._roboteq = roboteq.Roboteq(path=roboteq_path)
        self._controller = motion_complex.ComplexMotionController()

    @property
    def status(self):
        return SofaStatus(
            receiver=self._receiver.status,
            roboteq=self._roboteq.status,
            controller=self._controller.status,
        )

    def _update_status(self):
        _status = self.status
        self._update_status_file(_status)
        if self._roboteq.brake_active:
            remote_status = _status.remote_parked
        else:
            remote_status = _status.remote_idle
        self._receiver.remote.update_status(remote_status)
        print _status.dashboard

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
