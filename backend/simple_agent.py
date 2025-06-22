import time
import pyautogui


def open_chrome_and_go(url: str):
    """Open Google Chrome (via Spotlight) and navigate to the given URL."""
    # Disable failsafe so moving mouse to corner doesn't abort unexpectedly
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.5

    # Open Spotlight (⌘+Space), search for Chrome and launch it
    pyautogui.hotkey('command', 'space')
    pyautogui.typewrite('chrome')
    pyautogui.press('return')

    # Give Chrome a moment to launch
    time.sleep(2)

    # Open a new tab (⌘+T)
    pyautogui.hotkey('command', 't')

    # Type URL and press Enter
    pyautogui.typewrite(url)
    pyautogui.press('return')


if __name__ == "__main__":
    open_chrome_and_go('traderjoes.com') 