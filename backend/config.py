import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration for Computer Use Claude Agent
# API key is loaded from environment variable for security
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY environment variable is required. Please check your .env file.")

# Display settings - can be overridden by environment variables
DISPLAY_WIDTH = int(os.getenv("DISPLAY_WIDTH", 3024))
DISPLAY_HEIGHT = int(os.getenv("DISPLAY_HEIGHT", 1964))

PYAUTOGUI_PAUSE = 0.01
BETWEEN_ITERATIONS_SLEEP = 0.02
USER_WARNING_DELAY = 0.3
LOCK_RELEASE_DELAY = 0.1

# Dynamic Spotlight timing configuration
SPOTLIGHT_INITIAL_WAIT = 0.2
SPOTLIGHT_CHECK_INTERVAL = 0.1
SPOTLIGHT_MAX_WAIT = 2.0
SPOTLIGHT_FALLBACK_WAIT = 0.8

# System responsiveness calibration
FAST_SYSTEM_THRESHOLD = 0.5
SYSTEM_SPEED_MULTIPLIER = 1.0
