# Wormhole Runner (web)

The whole single-player game in the browser: HTML5 canvas, CSS and vanilla JavaScript (ES modules).
No installs, no backend, no frameworks. Progress and settings are saved in this browser (localStorage).

## Run it
1. Unzip.
2. Start a static server in the folder (ES modules do not work from `file://`):
   `python -m http.server 8000`  (or VS Code Live Server)
3. Open http://localhost:8000

## What is in it
- **Modes:** Classic, Expedition (hazards, rock types, objectives, perks) and **Voyage** (star map of 11 zones with
  objectives and challenges, stations and planets, friendly ships, permanent upgrades, repairs, supplies).
- **13 ships** with abilities (cloak, hyperjump, hyperspace, deflect, repair, afterburner, nova, ram, time slip, launch drones),
  own weapons, passives, a Hangar and credits.
- **8 aliens** (drifter, chaser, sniper, swarm, seeker, teleporter, minelayer, mothership boss), 6 weapons + ship weapon (key 7),
  5 rock types, 4 hazards, all the Python numbers.
- **Game Editor** (main menu): every number, search box, live sprite preview, per-row reset, Save / Reset all.
- **Settings:** volume, mute, touch controls (auto / on / off), pause when the tab loses focus, remappable keys, fullscreen.

## Controls (change them in Settings)
Up/Down speed, Left/Right turn, Space fire, Shift ability, 1-9 weapons, P pause, Esc back/menu, Enter confirm.
On phones and tablets the on-screen buttons appear automatically.

## Files
- `index.html`, `css/styles.css`
- `js/config.js` (all data + settings store), `game.js` (simulation), `features.js` (credits, hazards, objectives, abilities, perks),
  `voyage.js` (allies, zones, upgrades), `render.js` (canvas + HUD), `ui.js` (menus, shops, star map), `editor.js`, `input.js`,
  `audio.js`, `assets.js`, `profile.js`, `utils.js`, `zones.js`, `entities/` (ship, weapons, rock, alien, ally, misc, hazards, perks, sprite)
- `assets/images/` - 48 PNG sprite sheets (rows of animation frames)
- `tools/make_assets.py` - redraws the PNGs (`pip install pillow`)

## Your own art
Replace any PNG with your own of the same name and tile size, or change tile size / count / fps / file name in the editor
(Images section). A missing file falls back to a built-in shape, so the game always runs.
Sounds are synthesized in the browser, so there are no audio files; use the editor to change their volumes.

## Differences from the Python game
- Single-player only (no LAN multiplayer).
- Sound and music are generated with the Web Audio API instead of WAV files.
- The editor cannot pick sound files (there are none) and cannot browse folders: type an image file name instead.
- Settings and the profile live in localStorage; there is no `config.json` / `profile.json` file.
