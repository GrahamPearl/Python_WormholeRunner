"""Multiplayer menus: choose Host / Join (LAN browser) / Join by IP address."""
import arcade

from . import net
from .config import settings
from .profile import profile
from .constants import BACKGROUND_COLOR, SCREEN_HEIGHT as H, SCREEN_WIDTH as W
from .sprites import Background
from .ui import CYAN, GOLD, GREEN, GREY, RED, WHITE, TextCache


class MultiplayerMenu(arcade.View):
    ITEMS = ("Host a game", "Join a game on my network", "Join by IP address", "Back")

    def __init__(self):
        super().__init__()
        self.sel = 0
        self.background = Background(W, H)
        self.text = TextCache()
        self.ips = net.lan_ipv4_addresses()

    def on_show_view(self):
        self.window.background_color = BACKGROUND_COLOR

    def on_update(self, dt):
        self.background.update(dt)

    def _y(self, i):
        return H // 2 + 30 - i * 60

    def on_draw(self):
        self.clear()
        self.background.draw()
        t = self.text
        t.draw("title", "MULTIPLAYER", W / 2, H - 150, GOLD, 48, "center", bold=True)
        t.draw("sub", "Two players, one map, the same rocks and aliens", W / 2, H - 195, GREY, 16, "center")
        for i, item in enumerate(self.ITEMS):
            on = i == self.sel
            t.draw(f"i{i}", f"> {item} <" if on else item, W / 2, self._y(i),
                   GOLD if on else WHITE, 28, "center", "center")
        port = settings.get("net.port")
        addr = ", ".join(self.ips) if self.ips else "(no network address found)"
        t.draw("a1", f"Your address: {addr}    port {port}", W / 2, 90, CYAN, 14, "center")
        t.draw("a2", f"Playing as '{settings.get('net.player_name')}' - change name/port in the Game Editor",
               W / 2, 66, GREY, 12, "center")

    def _hit(self, x, y):
        for i in range(len(self.ITEMS)):
            if abs(y - self._y(i)) < 28 and abs(x - W / 2) < 260:
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
        k = arcade.key
        if symbol == k.UP:
            self.sel = (self.sel - 1) % len(self.ITEMS)
        elif symbol == k.DOWN:
            self.sel = (self.sel + 1) % len(self.ITEMS)
        elif symbol in (k.ENTER, k.NUM_ENTER):
            self._activate()
        elif symbol == k.ESCAPE:
            self._back()

    def _back(self):
        from .menu_view import MenuView
        self.window.show_view(MenuView())

    def _activate(self):
        if self.sel == 0:
            from .game_view import GameView
            self.window.show_view(GameView(host=True))
        elif self.sel == 1:
            self.window.show_view(JoinView("browse"))
        elif self.sel == 2:
            self.window.show_view(JoinView("ip"))
        else:
            self._back()


class JoinView(arcade.View):
    """mode 'browse': hosts found on the LAN.  mode 'ip': type an address."""

    def __init__(self, mode="browse"):
        super().__init__()
        self.mode = mode
        self.text = TextCache()
        self.background = Background(W, H)
        self.scanner = net.LanScanner(settings.get("net.port"))
        self.scan_timer = 0.0
        self.sel = 0
        self.address = str(settings.get("net.last_ip"))
        self.status, self.status_color = "", GREY
        self.connector = None

    def on_show_view(self):
        self.window.background_color = BACKGROUND_COLOR

    # ------------------------------------------------------------ connecting
    def _connect(self, ip, port):
        if self.connector:
            return
        self.status, self.status_color = f"Connecting to {ip}:{port} ...", GOLD
        self.connector = net.Connector(ip, port, settings.get("net.player_name") or "Pilot",
                                       profile.selected)

    def on_update(self, dt):
        self.background.update(dt)
        if self.mode == "browse" and not self.connector:
            self.scan_timer -= dt
            if self.scan_timer <= 0:
                self.scan_timer = 3.0
                self.scanner.scan()
        c = self.connector
        if c and c.done:
            self.connector = None
            if c.result:
                conn, welcome = c.result
                settings.set("net.last_ip", c.ip)
                try:
                    settings.save()
                except OSError:
                    pass
                from .client_view import ClientView
                self.window.show_view(ClientView(conn, welcome))
            else:
                self.status, self.status_color = c.error or "Could not connect", RED

    # ------------------------------------------------------------ drawing
    def on_draw(self):
        self.clear()
        self.background.draw()
        t = self.text
        if self.mode == "browse":
            t.draw("title", "FIND A GAME", W / 2, H - 120, GOLD, 44, "center", bold=True)
            hosts = self.scanner.results()
            self.sel = min(self.sel, max(0, len(hosts) - 1))
            if not hosts:
                msg = "Searching the network..." if self.scanner.scanning else \
                      "No games found yet. Ask your friend to choose 'Host a game'."
                t.draw("none", msg, W / 2, H / 2 + 40, GREY, 18, "center")
            for i in range(8):
                if i < len(hosts):
                    h = hosts[i]
                    on = i == self.sel
                    label = (f"{h.get('name', '?')}   {h['ip']}:{h.get('port', '?')}   "
                             f"level {h.get('level', '?')}   {h.get('players', '?')}/{h.get('max', 2)} players")
                    t.draw(f"h{i}", label, W / 2, H / 2 + 60 - i * 40, GOLD if on else WHITE,
                           20, "center", "center", on)
                else:
                    t.draw(f"h{i}", "", W / 2, 0)
            t.draw("help", "UP/DOWN choose   ENTER join   R search again   TAB type an IP address   ESC back",
                   W / 2, 70, GREY, 14, "center")
        else:
            t.draw("title", "JOIN BY IP ADDRESS", W / 2, H - 120, GOLD, 44, "center", bold=True)
            t.draw("lab", "Host's IPv4 address (add :port if it isn't the default)", W / 2, H / 2 + 70,
                   GREY, 16, "center")
            t.draw("addr", self.address + "_", W / 2, H / 2 + 10, WHITE, 36, "center", "center")
            t.draw("help", "Type the address   ENTER connect   TAB find on network   ESC back",
                   W / 2, 70, GREY, 14, "center")
        t.draw("status", self.status, W / 2, 130, self.status_color, 18, "center")

    # ------------------------------------------------------------ input
    def on_text(self, text):
        if self.mode == "ip" and not self.connector:
            for ch in text:
                if (ch.isdigit() or ch in ".:") and len(self.address) < 21:
                    self.address += ch

    def on_key_press(self, symbol, modifiers):
        k = arcade.key
        if symbol == k.ESCAPE:
            if self.connector:
                return
            self.window.show_view(MultiplayerMenu())
        elif symbol == k.TAB:
            self.mode = "ip" if self.mode == "browse" else "browse"
            self.scan_timer = 0.0
            self.status = ""
        elif self.mode == "ip":
            if symbol == k.BACKSPACE:
                self.address = self.address[:-1]
            elif symbol in (k.ENTER, k.NUM_ENTER):
                try:
                    ip, port = net.parse_address(self.address, settings.get("net.port"))
                except ValueError as exc:
                    self.status, self.status_color = str(exc), RED
                    return
                self._connect(ip, port)
        else:
            hosts = self.scanner.results()
            if symbol == k.UP and hosts:
                self.sel = (self.sel - 1) % len(hosts)
            elif symbol == k.DOWN and hosts:
                self.sel = (self.sel + 1) % len(hosts)
            elif symbol == k.R:
                self.scan_timer = 0.0
            elif symbol in (k.ENTER, k.NUM_ENTER) and hosts:
                h = hosts[self.sel]
                self._connect(h["ip"], int(h.get("port", settings.get("net.port"))))
