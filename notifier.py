from plyer import notification
import time

class Notifier:
    def __init__(self):
        self.last_20_20_20_time = time.time()

    def send_notification(self, title, message):
        notification.notify(
            title=title,
            message=message,
            timeout=5
        )

    def check_20_20_20(self):
        if time.time() - self.last_20_20_20_time > 20*60:  # every 20 minutes
            self.send_notification("20-20-20 Rule", "Look at something 20 ft away for 20 seconds!")
            self.last_20_20_20_time = time.time()