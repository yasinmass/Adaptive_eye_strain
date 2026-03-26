import screen_brightness_control as sbc
import threading
import time

class BrightnessManager:
    def __init__(self):
        try:
            current = sbc.get_brightness()
            if isinstance(current, list):
                self.current_brightness = current[0]
            else:
                self.current_brightness = current
        except:
            self.current_brightness = 80
            
        self.target_brightness = self.current_brightness
        self.running = True
        
        self.thread = threading.Thread(target=self._adjust_loop, daemon=True)
        self.thread.start()

    def set_strain_level(self, strain_level):
        if strain_level == "High":
            self.target_brightness = 40
        elif strain_level == "Medium":
            self.target_brightness = 60
        else:
            self.target_brightness = 80

    def _adjust_loop(self):
        while self.running:
            if abs(self.target_brightness - self.current_brightness) > 1:
                # Gradual transition logic to avoid sudden jumps
                self.current_brightness += (self.target_brightness - self.current_brightness) * 0.1
                
                try:
                    sbc.set_brightness(int(self.current_brightness))
                except Exception:
                    pass
            time.sleep(0.1)

    def stop(self):
        self.running = False

brightness_manager = BrightnessManager()

def adjust_brightness(strain_level):
    """Adjusts the screen brightness based on the given strain level smoothly."""
    brightness_manager.set_strain_level(strain_level)