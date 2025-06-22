"""
Spotlight Optimizer - Dynamic timing and detection for macOS Spotlight
Optimizes Spotlight opening performance by detecting when it actually opens
and adapting timing based on system responsiveness.
"""

import time
import pyautogui
import subprocess
from PIL import ImageGrab
import config


class SpotlightOptimizer:
    def __init__(self):
        self.system_speed = 1.0  # Multiplier based on detected system speed
        self.last_spotlight_time = None  # Track how long Spotlight took last time
        
    def detect_spotlight_open(self):
        """
        Detect if Spotlight is currently open using system commands
        Returns True if Spotlight is visible, False otherwise
        """
        try:
            # Use AppleScript to check if Spotlight is visible
            applescript = '''
            tell application "System Events"
                try
                    if exists window "Spotlight" of application process "Spotlight" then
                        return true
                    else
                        return false
                    end if
                on error
                    return false
                end try
            end tell
            '''
            
            result = subprocess.run(
                ['osascript', '-e', applescript], 
                capture_output=True, 
                text=True, 
                timeout=0.5
            )
            
            return result.stdout.strip().lower() == 'true'
            
        except Exception:
            # Fallback: use screenshot analysis
            return self._detect_spotlight_via_screenshot()
    
    def _detect_spotlight_via_screenshot(self):
        """
        Fallback method: detect Spotlight by analyzing screenshot
        Returns True if Spotlight appears to be open
        """
        try:
            # Take a quick screenshot of the center area where Spotlight appears
            screenshot = ImageGrab.grab()
            
            # Spotlight typically appears in the center-top area
            # Look for the characteristic dark search box
            width, height = screenshot.size
            center_x = width // 2
            top_y = height // 4
            
            # Sample a small area around where Spotlight should be
            search_area = screenshot.crop((
                center_x - 200, top_y - 50,
                center_x + 200, top_y + 100
            ))
            
            # Convert to grayscale and check for dark regions (Spotlight's search box)
            gray = search_area.convert('L')
            pixels = list(gray.getdata())
            
            # Count dark pixels (likely Spotlight background)
            dark_pixels = sum(1 for p in pixels if p < 100)
            dark_ratio = dark_pixels / len(pixels)
            
            # If more than 30% of the area is dark, Spotlight is likely open
            return dark_ratio > 0.3
            
        except Exception:
            return False
    
    def open_spotlight_optimized(self):
        """
        Open Spotlight with optimized timing and detection
        Returns tuple: (success: bool, time_taken: float)
        """
        start_time = time.time()
        
        # Check if Spotlight is already open
        if self.detect_spotlight_open():
            print("🔍 Spotlight already open")
            return True, 0.0
        
        print("🔍 Opening Spotlight with optimized sequence...")
        
        # Use the most reliable key sequence for macOS
        try:
            # Method 1: Reliable key sequence
            pyautogui.keyDown('command')
            time.sleep(0.02)  # Tiny pause to ensure keyDown registers
            pyautogui.press('space')
            time.sleep(0.02)
            pyautogui.keyUp('command')
            
            # Initial quick wait
            time.sleep(config.SPOTLIGHT_INITIAL_WAIT)
            
            # Dynamic detection loop
            max_wait_time = config.SPOTLIGHT_MAX_WAIT
            check_interval = config.SPOTLIGHT_CHECK_INTERVAL
            elapsed = config.SPOTLIGHT_INITIAL_WAIT
            
            while elapsed < max_wait_time:
                if self.detect_spotlight_open():
                    time_taken = time.time() - start_time
                    print(f"✅ Spotlight opened in {time_taken:.3f}s")
                    
                    # Update system speed estimate
                    self._update_system_speed(time_taken)
                    return True, time_taken
                
                time.sleep(check_interval)
                elapsed += check_interval
            
            # If detection failed, try one more time with different method
            print("🔄 First attempt timed out, trying alternative method...")
            return self._fallback_spotlight_open(start_time)
            
        except Exception as e:
            print(f"❌ Error in optimized Spotlight opening: {e}")
            return self._fallback_spotlight_open(start_time)
    
    def _fallback_spotlight_open(self, start_time):
        """
        Fallback method using traditional approach
        """
        try:
            # Try the traditional hotkey method
            pyautogui.hotkey('command', 'space')
            time.sleep(config.SPOTLIGHT_FALLBACK_WAIT)
            
            # Check if it worked
            if self.detect_spotlight_open():
                time_taken = time.time() - start_time
                print(f"✅ Spotlight opened (fallback) in {time_taken:.3f}s")
                return True, time_taken
            else:
                print("❌ Spotlight failed to open even with fallback method")
                return False, time.time() - start_time
                
        except Exception as e:
            print(f"❌ Fallback Spotlight opening failed: {e}")
            return False, time.time() - start_time
    
    def _update_system_speed(self, time_taken):
        """
        Update system speed estimate based on how quickly Spotlight opened
        """
        self.last_spotlight_time = time_taken
        
        if time_taken < config.FAST_SYSTEM_THRESHOLD:
            # System is fast, reduce future wait times
            self.system_speed = min(2.0, self.system_speed * 1.1)
            print(f"📈 System speed increased to {self.system_speed:.2f}x")
        elif time_taken > config.FAST_SYSTEM_THRESHOLD * 2:
            # System is slow, increase future wait times
            self.system_speed = max(0.5, self.system_speed * 0.9)
            print(f"📉 System speed decreased to {self.system_speed:.2f}x")
    
    def get_optimized_wait_time(self, base_time):
        """
        Get an optimized wait time based on system speed
        """
        return base_time / self.system_speed
    
    def clear_spotlight_if_open(self):
        """
        Clear Spotlight search if it's already open
        """
        if self.detect_spotlight_open():
            print("🧹 Clearing existing Spotlight content...")
            pyautogui.hotkey('command', 'a')  # Select all
            time.sleep(0.05)
            pyautogui.press('delete')  # Clear
            time.sleep(0.05)
            return True
        return False


# Global instance for reuse
spotlight_optimizer = SpotlightOptimizer() 