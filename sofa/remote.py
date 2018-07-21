"""get magnitude/angle vectors from a remote wii nunchuck"""

import time

import status


class RemoteControlStatus(status.Status):
    _attrs = ['joystick', 'updated']

    @property
    def update_age(self):
        return time.time() - self.updated


class RemoteControl(object):
    def __init__(self, addr, joystick, status_update_age):
        self._joystick = joystick
        self._addr = addr
        self._last_status_update = time.time() - float(int(status_update_age) / 1000)

    @property
    def addr(self):
        return self._addr

    @property
    def joystick(self):
        return self._joystick

    @property
    def status(self):
        return RemoteControlStatus(
            updated=self._last_status_update,
            joystick=self._joystick)

    def update_status(self, _status):
        pass
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
#        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
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
#        sock.sendto(packet, addr)
#        self._udp_status_delay = 10
#    """
