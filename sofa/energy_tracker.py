'''A roboteq RS232 motor controller with accel/deccel enforcement'''
import time

import status


class EnergyTrackerStatus(status.Status):
    _attrs = ['volts', 'amps_l', 'amps_r', 'watt_hours', 'regen_watt_hours']
    _dashboard_fmt = ['{volts:4.2f}v', '{amps_l:3.1f}al', '{amps_r:3.1f}ar',
                      '{0.watts:4.1f}w', '{watt_hours:5.2f}wh',
                      '{regen_watt_hours:-6.3f}wh']

    @property
    def watts(self):
        return self[1] * (self[2] + self[3])


class EnergyTracker(object):
    _volts = 0
    _amps_l = 0
    _amps_r = 0
    _watt_hours = 0
    _regen_watt_hours = 0
    _last_update_ts = 0

    def update(self, volts, amps_l, amps_r):
        now = time.time()

        self._volts = volts
        self._amps_l = amps_l

        self._amps_r = amps_r
        watts = volts * (amps_l + amps_r)
        duration = self._last_update_ts - now
        current_watt_hours = watts * (duration / 3600)
        if current_watt_hours > 0:
            self._watt_hours += current_watt_hours
        else:
            self._regen_watt_hours += current_watt_hours

    @property
    def status(self):
        return EnergyTrackerStatus(
            volts=self._volts,
            amps_l=self._amps_l,
            amps_r=self._amps_r,
            watt_hours=self._watt_hours,
            regen_watt_hours=self._regen_watt_hours)
