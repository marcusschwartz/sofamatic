"""Packet History"""
import collections


class PacketHistory(collections.deque):
    _MAX_LENGTH = 50
    _interval = 0

    def __init__(self, interval):
        super(PacketHistory, self).__init__()
        self._interval = interval

    def add(self, now, cycle_time, received_packets):
        self.append(tuple((now, cycle_time, received_packets)))
        while len(self) > self._MAX_LENGTH + 1:
            self.popleft()

    @property
    def summary(self):
        if len(self) < 2:
            return 0, 0, 0, 0

        cycle_time_total = 0
        cycle_time_max = 0
        jitter_total = 0
        interval_total = 0
        missing_total = 0.0
        extra_total = 0
        records = len(self) - 1

        record_iter = iter(self)
        last_timestamp, _, _ = record_iter.next()
        for [timestamp, cycle_time, received_packets] in record_iter:
            if cycle_time > cycle_time_max:
                cycle_time_max = cycle_time
            cycle_time_total += cycle_time
            if received_packets == 0:
                missing_total += 1
            elif received_packets > 1:
                extra_total += received_packets - 1
            interval_total += timestamp - last_timestamp
            last_timestamp = timestamp

        interval_avg = (interval_total / records)

        record_iter = iter(self)
        last_timestamp, _, _ = record_iter.next()
        for [timestamp, cycle_time, received_packets] in record_iter:
            jitter_total += abs((timestamp - last_timestamp) - interval_avg)
            last_timestamp = timestamp

        return int(100 * (cycle_time / records) / self._interval), int(1000 * interval_total / records), int(1000 * jitter_total / records), int(100 * missing_total / records)
