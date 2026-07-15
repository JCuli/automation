import mss
import numpy as np
from numpy.typing import NDArray
import cv2
import pyautogui
from dataclasses import dataclass, field
from pathlib import Path
import time
import pyperclip
import sys


def resource_path(relative_path: str) -> Path:
    """Get path to resource, works for dev and for PyInstaller bundle."""
    if hasattr(sys, "_MEIPASS"):
        base_path = Path(sys._MEIPASS)
    else:
        base_path = Path(__file__).parent
    return base_path / relative_path


class Screen:

    def __init__(self, region):
        self.region = region

    def capture(self):
        with mss.MSS() as sct:
            shot = sct.grab(self.region)
            img = np.array(shot)
            return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

region = {
    "top": 0,
    "left": 0,
    "width": 800,
    "height": 600
}
screen = Screen(region)

@dataclass
class Detection:
    found: bool
    x: int = -1
    y: int = -1
    confidence: float = 0.0

@dataclass
class Template:
    image: NDArray[np.uint8]
    width: int
    height: int

@dataclass
class Detector:
    template_dir: Path
    threshold : float = 0.9
    templates: dict = field(init=False)
    def __post_init__(self):
        self.templates = {}
        for file in self.template_dir.glob("*.png"):
            image = cv2.imread(str(file), cv2.COLOR_BGRA2BGR)
            if image is None:
                raise ValueError(f"Could not load {file}")
            self.templates[file.stem] = Template(
                image=image,
                width=image.shape[1],
                height=image.shape[0],
            )

    def find(self, frame, name: str) -> Detection:
        if name not in self.templates:
            raise KeyError(f"Unknown template '{name}'")
        template = self.templates[name]
        result = cv2.matchTemplate(
            frame,
            template.image,
            cv2.TM_CCOEFF_NORMED
        )
        _, confidence, _, location = cv2.minMaxLoc(result)
        if confidence >= self.threshold:
            return Detection(
                found =True,
                x = location[0] + (template.width/2),
                y = location[1] + (template.height/2),
                confidence = confidence,
                )
        return Detection(found =False)

detector = Detector(resource_path("templates"))

def wait_for(temp_name: str, timeout: float = 5.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        img = screen.capture()
        button = detector.find(img, temp_name)
        if button.found:
            print(f"confidence: {button.confidence}")
            print(f"position: {button.x, button.y}")
            return button
    raise TimeoutError(f"Could not find '{temp_name}'")



button = wait_for("stocks")
pyautogui.click(button.x, button.y)
button = wait_for("item1")
pyautogui.click(button.x, button.y)
pyautogui.write("Df 1 duf sps1;sns-gal4", interval=0.05)
button = wait_for("8")
pyautogui.click(button.x, button.y)
button = wait_for("anadido")
pyautogui.moveTo(button.x+30, button.y)
pyautogui.dragRel(200, 0, duration=0.2)
# Clear the clipboard
pyperclip.copy("")
pyautogui.hotkey("ctrl", "c")  # Copy

# Give the application a moment to update the clipboard
time.sleep(0.2)

pyperclip.paste()
