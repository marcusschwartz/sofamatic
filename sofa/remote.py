"""get magnitude/angle vectors from a remote wii nunchuck"""

import time

import status


class RemoteControlStatus(status.Status):
    _attrs = ['joystick', 'updated', 'avg_duty_cycle', 'max_duty_cycle']
    _dashboard_fmt = ['{avg_duty_cycle:3d}%', '{max_duty_cycle:3d}%max']

    @property
    def update_age(self):
        return time.time() - self[1]


class RemoteControl(object):
    def __init__(self, addr, sock, _status):
        self._addr = addr
        self._sock = sock
        self._status = _status
        self._last_status_update = 0

    @property
    def addr(self):
        return self._addr

    @property
    def joystick(self):
        return self._status.joystick

    @property
    def status(self):
        return self._status

    def update_status(self, status_update):
        if not self._addr:
            return
        if self._status.update_age and status_update == self._last_status_update:
            return
        self._last_status_update = status_update
        
        self._sock.sendto(status_update, self._addr)

#    """
#        if not self._addr:
#            return
#        send_now = False
#        brake_mode = ''
#        if status.roboteq.brake:
#            brake_mode = 'BRAKE'
#        mode = ":".join([controller_status.details["mode"],
#                         controller_status.details["submode"],
#                         brake_mode])
#        if mode != self._last_mode:
#            self._last_mode = mode
#            send_now = True
#        self._udp_status_delay -= 1
#        remote_status_age = joystick_status.details["status_age"]
#        if not send_now and (self._udp_status_delay > 0 and remote_status_age > 1000):
#            return
#
#        # sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
#        watt_hours = status["watt_hours"] + status["regen_watt_hours"]
#        energy = "%3.1fwh" % watt_hours
#        voltage = "%4.1fv" % roboteq_status.details["volts_12"]
#        pl = "%3d%%" % (100 - status["packet_loss"])
#        packet = " ".join((energy, voltage, pl))
#        if brake_mode == 'BRAKE' and controller_status.details["mode"] != "IDLE":
#            packet = "&PARKING~BRAKE"
#        elif brake_mode == 'BRAKE':
#            packet += "~**PARKING BRAKE**"
#        elif controller_status.details["mode"] != "IDLE":
#            watts = roboteq_status.details["watts"]
#            avg_motor_pct = (abs(controller_status.details["motor_l"]) +
#                             abs(controller_status.details["motor_r"])) / 20
#            packet = "&%s:%s~%d%% %dw" % (controller_status.details["mode"],
#                                          controller_status.details["submode"],
#                                          avg_motor_pct,
#                                          watts)
#        else:
#            if status["watt_hours"]:
#                regen_pct = 100 * abs(status["regen_watt_hours"]) / status["watt_hours"]
#            else:
#                regen_pct = 0
#            packet += "~%1d%% regen" % regen_pct
#        self._udp_status_delay = 10
#    """
