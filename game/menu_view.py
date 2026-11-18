"""Main menu."""
import arcade

from .config import settings
from .constants import BACKGROUND_COLOR, SCREEN_HEIGHT as H, SCREEN_WIDTH as W
from .profile import profile
from .sprites import Background
from .ui import GOLD, GREY, WHITE, TextCache

MODE_TEXT = {
    "classic": "Classic: rocks, aliens, weapons and wormholes",
    "expedition": "Expedition: + smarter aliens, hazards, rock types, objectives and perks",
}


class MenuView(arcade.View):
    def __init__(self, message=""):
        super().__init__()
        self.message = message
        self.sel = 0
        self.background = Background(W, H)
        self.text = TextCache()

    def items(self):
        mode = settings.get("game.mode")
        return ("Play", "Multiplayer (LAN)", "Hangar (ships)", f"Mode: {mode.title()}",
                "Game Editor", "Quit")

    def on_show_view(self):
        self.window.background_color = BACKGROUND_COLOR

    def on_update(self, delta_time):
        self.background.update(delta_time)

    def _y(self, i):
        return H // 2 + 40 - i * 56

    def on_draw(self):
        self.clear()
        self.background.draw()
        t = self.text
        t.draw("title", "WORMHOLE RUNNER", W / 2, H - 150, GOLD, 56, "center", bold=True)
        t.draw("sub", "Dodge the rocks. Find the wormhole.", W / 2, H - 195, GREY, 18, "center")
        items = self.items()
        for i, item in enumerate(items):
            on = i == self.sel
            t.draw(f"item{i}", f"> {item} <" if on else item, W / 2, self._y(i),
                   GOLD if on else WHITE, 28, "center", "center")
        t.draw("modeinfo", MODE_TEXT[settings.get("game.mode")], W / 2, self._y(len(items)) + 6, GREY, 14, "center")
        ship = settings.get(f"ships.{profile.selected}.name", "Scout")
        t.draw("prof", f"Ship: {ship}    Credits: {profile.credits}    Best level: {profile.best_level}",
               W / 2, 80, GOLD, 15, "center")
        if self.message:
            t.draw("msg", self.message, W / 2, H - 250, (255, 120, 120, 255), 20, "center")
        t.draw("hint", "UP/DOWN + ENTER, or use the mouse", W / 2, 50, GREY, 14, "center")

    def _hit(self, x, y):
        for i in range(len(self.items())):
            if abs(y - self._y(i)) < 25 and abs(x - W / 2) < 220:
                return i
        return None

    def on_mouse_motion(self, x, y, dx, dy):
        i = self._hit(x, y)
        if i is not None:
            self.sel = i

    def on_mouse_press(self, x, y, button, modifiers):
        i = self._hit(x, y)
        if i is not None:
            self.sel = i
            self._activate()

    def on_key_press(self, symbol, modifiers):
        n = len(self.items())
        if symbol == arcade.key.UP:
            self.sel = (self.sel - 1) % n
        elif symbol == arcade.key.DOWN:
            self.sel = (self.sel + 1) % n
        elif symbol in (arcade.key.LEFT, arcade.key.RIGHT) and self.items()[self.sel].startswith("Mode"):
            self._toggle_mode()
        elif symbol in (arcade.key.ENTER, arcade.key.NUM_ENTER):
            self._activate()
        elif symbol == arcade.key.ESCAPE:
            arcade.exit()

    def _toggle_mode(self):
        settings.set("game.mode", "classic" if settings.get("game.mode") == "expedition" else "expedition")
        try:
            settings.save()
        except OSError:
            pass

    def _activate(self):
        item = self.items()[self.sel]
        if item == "Play":
            from .game_view import GameView
            self.window.show_view(GameView())
        elif item.startswith("Multiplayer"):
            from .net_views import MultiplayerMenu
            self.window.show_view(MultiplayerMenu())
        elif item.startswith("Hangar"):
            from .hangar_view import HangarView
            self.window.show_view(HangarView())
        elif item.startswith("Mode"):
            self._toggle_mode()
        elif item == "Game Editor":
            from .editor_view import EditorView
            self.window.show_view(EditorView())
        else:
            arcade.exit()
