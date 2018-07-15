"""incomplete"""

from motion import MotionController


class CrawlMC(MotionController):
    _name = "CRAWL"

    def submode(self):
        return "NONE"

    def motor_speeds(self):
        return 0.0, 0.0
