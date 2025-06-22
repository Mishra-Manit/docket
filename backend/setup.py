#!/usr/bin/env python3
"""
Setup script for Computer Use Claude Agent
"""

import subprocess
import sys
import os

def install_requirements():
    """Install required packages"""
    print("Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Requirements installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing requirements: {e}")
        return False

def check_chrome():
    """Check if Chrome is installed"""
    chrome_paths = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",  # macOS
        "/usr/bin/google-chrome",  # Linux
        "/usr/bin/chromium-browser",  # Linux alternative
    ]
    
    for path in chrome_paths:
        if os.path.exists(path):
            print(f"✅ Chrome found at: {path}")
            return True
    
    print("⚠️  Chrome not found in common locations. Please make sure Chrome is installed.")
    return False

def main():
    print("=== Computer Use Claude Agent Setup ===")
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher required")
        return
    
    print(f"✅ Python {sys.version.split()[0]} detected")
    
    # Install requirements
    if not install_requirements():
        return
    
    # Check Chrome installation
    check_chrome()
    
    print("\n=== Setup Complete ===")
    print("To run the computer use agent:")
    print("  python app.py")
    print("\nMake sure to:")
    print("1. Update config.py with your actual API key if needed")
    print("2. Adjust display settings in config.py if your screen resolution is different")
    print("3. Ensure Chrome is installed and accessible")

if __name__ == "__main__":
    main() 