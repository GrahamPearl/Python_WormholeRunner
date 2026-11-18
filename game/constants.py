"""Global constants and file locations."""
from pathlib import Path

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
SCREEN_TITLE = "Wormhole Runner"

BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"
IMAGES_DIR = ASSETS_DIR / "images"
SOUNDS_DIR = ASSETS_DIR / "sounds"
CONFIG_PATH = BASE_DIR / "config.json"

# Arcade 3.x: Sprite.angle rotates clockwise, so a "bearing" (clockwise degrees
# from straight up) can be assigned directly. If the ship ever points the wrong
# way on another Arcade version, change this to -1.
ANGLE_SIGN = 1

BACKGROUND_COLOR = (6, 8, 22, 255)
