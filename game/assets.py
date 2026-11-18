"""Loads images (as tile sequences) into Arcade textures."""
from PIL import Image
import arcade

from .constants import IMAGES_DIR

_cache = {}


def list_files(folder, extensions):
    if not folder.exists():
        return []
    return sorted(p.name for p in folder.iterdir()
                  if p.suffix.lower() in extensions)


def _missing(width, height):
    img = Image.new("RGBA", (width, height), (255, 0, 255, 255))
    return [arcade.Texture(img)]


def load_frames(spec):
    """Return a list of textures cut from spec['file'] using the frame size/count."""
    fw = max(1, int(spec["frame_w"]))
    fh = max(1, int(spec["frame_h"]))
    count = max(1, int(spec["frames"]))
    key = (spec["file"], fw, fh, count)
    if key in _cache:
        return _cache[key]
    try:
        sheet = Image.open(IMAGES_DIR / spec["file"]).convert("RGBA")
    except (OSError, ValueError):
        frames = _missing(fw, fh)
    else:
        cols = max(1, sheet.width // fw)
        rows = max(1, sheet.height // fh)
        frames = []
        for i in range(min(count, cols * rows)):
            col, row = i % cols, i // cols
            box = (col * fw, row * fh, (col + 1) * fw, (row + 1) * fh)
            frames.append(arcade.Texture(sheet.crop(box)))
    _cache[key] = frames
    return frames
