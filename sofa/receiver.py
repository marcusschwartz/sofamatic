"""get magnitude/angle vectors from a remote wii nunchuck"""
import select
import socket
import time

import joystick
import nunchuk_joystick
import packet_history
import remote
import status


class ReceiverStatus(status.Status):
    _attrs = ['avg_duty_cycle', 'max_duty_cycle', 'interval', 'jitter',
              'packet_loss', 'remote']
    _dashboard_fmt = ['{avg_duty_cycle:2d}%', '{max_duty_cycle:2d}%',
                      '{interval:3d}ms', '{jitter:2d}ms', '{packet_loss:3d}%']


class RemoteControlReceiver(object):
    """a calibrated magnitude/angle from a wii nunchuk"""
    INTERVAL = 0.1
    GRACE = 0.1

    _sock = None
    _last_recv = 0
    _cycle_time = 0

    _packet_history = packet_history.PacketHistory(INTERVAL)

    def __init__(self, addr="0.0.0.0", port=31337):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind((addr, port))
        self._sock.setblocking(0)
        self._remote = remote.RemoteControl(None, joystick.new_centered(), 1)

    @property
    def remote(self):
        return self._remote

    @property
    def status(self):
        (avg_duty_cycle, max_duty_cycle, interval,
         jitter, packet_loss) = self._packet_history.summary
        return ReceiverStatus(avg_duty_cycle=avg_duty_cycle,
                              max_duty_cycle=max_duty_cycle,
                              interval=interval,
                              jitter=jitter,
                              packet_loss=packet_loss,
                              remote=self._remote.status)

    def wait_for_update(self):
        now = time.time()
        cycle_time = now - self._last_recv
        timeout = (self.INTERVAL + (self.INTERVAL * self.GRACE)) - cycle_time
        if timeout < 0:
            timeout = 0

        data = None
        if select.select([self._sock], [], [], timeout):
            received_packets = 0
            while True:
                try:
                    data, addr = self._sock.recvfrom(1024)
                    received_packets += 1
                except socket.error:
                    break

        now = time.time()
        self._last_recv = now
        self._packet_history.add(now, cycle_time, received_packets)

        if data:
            raw_x, raw_y, raw_z, raw_c, status_age = data.split(':')
            _joystick = nunchuk_joystick.from_remote_nunchuk(
                raw_x, raw_y, raw_z, raw_c, now)
            self._remote = remote.RemoteControl(addr, _joystick, status_age)
