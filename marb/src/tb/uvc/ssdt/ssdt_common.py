from enum import IntEnum


class DriverType(IntEnum):
    """ Type of driver: PRODUCER or CONSUMER """
    PRODUCER = 0
    CONSUMER = 1
