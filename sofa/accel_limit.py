'''A roboteq RS232 motor controller with accel/deccel enforcement'''

ACCEL_LIMIT = [
    [0, 99, 200],
    [100, 1000, 400],
]


def gen_accel_table(table_def):
    """generate an acceleration table"""
    table = []
    for i in range(1001):
        table.append(0)
    for limit_def in table_def:
        range_start, range_end, limit = limit_def
        for i in range(range_start, range_end + 1):
            table[i] = limit

    return table


class AccelerationLimiter(object):
    _ACCEL_TABLE = gen_accel_table(ACCEL_LIMIT)
    _DECEL_TABLE = gen_accel_table(ACCEL_LIMIT)

    def limit(self, target, current, delay):
        '''foo'''

        target = int(target)

        # never reverse speed in a single pass
        if (target > 0 and current < 0) or (target < 0 and current > 0):
            target = 0

        change = abs(target) - abs(current)

        if change > 0:
            limit = int(self._ACCEL_TABLE[abs(int(current))] * delay)
            if limit < change:
                # print "LIMIT ACCEL {} -> {}".format(change, limit)
                change = limit
            if target < current:
                change *= -1
        elif change < 0:
            limit = int(self._DECEL_TABLE[abs(int(current))] * delay)
            if limit < abs(change):
                # print "LIMIT DECEL {} -> {}".format(abs(change), limit)
                change = -1 * limit
            if target > current:
                change *= -1

        current += change

        return current

    def tables(self):
        return self._ACCEL_TABLE, self._DECEL_TABLE
