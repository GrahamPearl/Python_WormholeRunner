"""Audio manager: maps event names to files listed in the settings.

To add a sound: drop a file in assets/sounds/, add an entry under audio.events
(in the editor or config.json) and call ``audio.play("my_event")``.
A missing or unreadable file is silently ignored.
"""
import arcade

from .config import settings
from .constants import SOUNDS_DIR


class AudioManager:
    def __init__(self):
        self._cache = {}
        self._music_player = None

    def _entry(self, event):
        entry = settings.get(f"audio.events.{event}")
        return entry if isinstance(entry, dict) else None

    def _sound(self, event):
        entry = self._entry(event)
        if not entry or not entry.get("file"):
            return None
        path = SOUNDS_DIR / entry["file"]
        if path not in self._cache:
            try:
                self._cache[path] = arcade.load_sound(path)
            except Exception:
                self._cache[path] = None
        return self._cache[path]

    def play(self, event):
        sound = self._sound(event)
        if sound is None:
            return
        volume = settings.get("audio.sfx_volume", 0.7) * self._entry(event).get("volume", 1.0)
        try:
            arcade.play_sound(sound, volume=volume)
        except Exception:
            pass

    def play_music(self):
        self.stop_music()
        sound = self._sound("music")
        if sound is None:
            return
        volume = settings.get("audio.music_volume", 0.5) * self._entry("music").get("volume", 1.0)
        try:
            self._music_player = arcade.play_sound(sound, volume=volume, loop=True)
        except Exception:
            self._music_player = None

    def stop_music(self):
        if self._music_player is not None:
            try:
                arcade.stop_sound(self._music_player)
            except Exception:
                pass
            self._music_player = None

    @property
    def music_playing(self):
        return self._music_player is not None
