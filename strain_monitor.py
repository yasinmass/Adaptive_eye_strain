import time

class StrainMonitor:
    def __init__(self):
        self.start_time = time.time()
        self.blinks = 0

    def update(self, new_blinks):
        self.blinks = new_blinks

    def get_screen_time(self):
        return int(time.time() - self.start_time)  # seconds

    def get_blink_rate(self):
        minutes = self.get_screen_time() / 60
        return self.blinks / minutes if minutes > 0 else 0

    def get_strain_level(self):
        blink_rate = self.get_blink_rate()
        screen_time = self.get_screen_time() / 60  # minutes

        if blink_rate < 10 or screen_time > 60:
            return "High"
        elif blink_rate < 15:
            return "Medium"
        else:
            return "Low"