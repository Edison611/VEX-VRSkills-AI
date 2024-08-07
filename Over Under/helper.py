from PIL import ImageGrab
import time
import os


def focus_tab():
    applescript = """
        tell application "Google Chrome"
            activate
        end tell
        """
    os.system(f"osascript -e '{applescript}'")


def capture_screen_region(bbox, filename='screenshot_region.png'):
    """
    Captures a specific region of the screen and saves it to a file.

    Args:
    bbox (tuple): A tuple of (left, top, right, bottom) coordinates for the bounding box.
    filename (str): The name of the file to save the screenshot.
    """
    # Capture the specified region of the screen
    screenshot = ImageGrab.grab(bbox=bbox)

    # Save the screenshot to a file
    screenshot.save(filename, 'PNG')

    # Optionally show the screenshot
    screenshot.show()



time.sleep(3)

capture_screen_region((700, 320, 1280, 700))

