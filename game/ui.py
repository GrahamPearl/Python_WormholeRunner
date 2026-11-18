"""Tiny UI helpers: cached text and bars."""
import arcade

WHITE = (255, 255, 255, 255)
GOLD = (255, 208, 64, 255)
GREY = (150, 160, 185, 255)
RED = (235, 70, 70, 255)
GREEN = (80, 220, 120, 255)
CYAN = (90, 220, 255, 255)
ORANGE = (255, 160, 50, 255)
BLUE = (60, 90, 170, 255)


class TextCache:
    """Keeps one arcade.Text per slot so text is not rebuilt every frame."""

    def __init__(self):
        self._items = {}

    def draw(self, slot, text, x, y, color=WHITE, size=16,
             anchor_x="left", anchor_y="baseline", bold=False):
        sig = (size, anchor_x, anchor_y, bold)
        item = self._items.get(slot)
        if item is None or item[1] != sig:
            label = arcade.Text(text, x, y, color, size, anchor_x=anchor_x,
                                anchor_y=anchor_y, bold=bold)
            self._items[slot] = (label, sig)
        else:
            label = item[0]
            if label.text != text:
                label.text = text
            if tuple(label.color) != tuple(color):
                label.color = color
            label.x, label.y = x, y
        self._items[slot][0].draw()


def draw_bar(x, y, width, height, fraction, color):
    fraction = max(0.0, min(1.0, fraction))
    arcade.draw_lbwh_rectangle_filled(x, y, width, height, (40, 44, 62, 255))
    if fraction > 0:
        arcade.draw_lbwh_rectangle_filled(x, y, width * fraction, height, color)
    arcade.draw_lbwh_rectangle_outline(x, y, width, height, WHITE, 2)
