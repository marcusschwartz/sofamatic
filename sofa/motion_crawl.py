"""incomplete"""

from motion import MotionController


class CrawlMC(MotionController):
    _name = "CRAWL"

    @property
    def submode(self):
        return "NONE"

    @property
    def motor_speeds(self):
        return 0, 0
