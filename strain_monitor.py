import time

class StrainMonitor:
    def __init__(self):
        self.start_time = None  # Will be set when tracking actually starts
        self.blink_timestamps = []
        
        # At ~15 FPS, 15 frames is roughly 1 second.
        # If eye closed >= 1 second, it's considered fatigue
        self.long_closure_threshold_frames = 15
        
        self.screen_time_threshold_minutes = 60
        self.current_strain = "Low"
        self.blink_rate = 0
        self.screen_time = 0

    def update(self, blink_detected, eye_closed_frames):
        """Update monitor metrics based on blink data."""
        current_time = time.time()
        
        # Initialize start time if not set
        if self.start_time is None:
            self.start_time = current_time
            
        if blink_detected:
            self.blink_timestamps.append(current_time)
            
        # Keep blinks that occurred within the last 60 seconds
        self.blink_timestamps = [t for t in self.blink_timestamps if current_time - t <= 60]
        
        # Screen time in minutes
        time_elapsed = current_time - self.start_time
        self.screen_time = time_elapsed / 60.0
        
        # Extrapolate blink rate if we haven't been tracking for a full minute
        if time_elapsed > 0:
            if time_elapsed < 60:
                self.blink_rate = int(len(self.blink_timestamps) * (60.0 / time_elapsed))
            else:
                self.blink_rate = len(self.blink_timestamps)
        else:
            self.blink_rate = 0

        long_closure = eye_closed_frames >= self.long_closure_threshold_frames
        
        # Strain Logic:
        # High: blink_rate < 8 OR eye closed too long OR screen_time > threshold
        # Medium: 8 <= blink_rate <= 15
        # Low: blink_rate > 15
        if time_elapsed > 10 and self.blink_rate < 8 or long_closure or self.screen_time > self.screen_time_threshold_minutes:
            self.current_strain = "High"
        elif time_elapsed > 10 and 8 <= self.blink_rate <= 15:
            self.current_strain = "Medium"
        elif time_elapsed <= 10 and not long_closure:
            self.current_strain = "Low" # Give grace period before flagging low blink rate
        else:
            self.current_strain = "Low"
            
        return self.current_strain