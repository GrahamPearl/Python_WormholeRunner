# Wormhole Runner (Arcade 3.x) - Windows and Linux

## Run it
Needs Python 3.10+.

- **Windows:** double-click `run_windows.bat` (creates a `.venv`, installs the requirements, starts the game).
- **Linux:** `./run_linux.sh` (on Debian/Ubuntu first: `sudo apt install python3-venv`).
- Manually on either: `pip install -r requirements.txt` then `python main.py`.

First run creates placeholder art/sounds in `assets/` (existing files are never overwritten).
Linux audio needs OpenAL or PulseAudio (normally already present); sound is skipped quietly if unavailable.



## Learning site (docs/)
`docs/` is a static website that teaches Python, classes, physics and web development using this game
(16 pages, written for Years 9-10). Open `docs/index.html` in a browser, or publish it with GitHub Pages
(Settings -> Pages -> branch `main`, folder `/docs`). Before publishing, edit `docs/site-config.js` with your GitHub
user and repository name so the "View on GitHub" links work. After changing the game's code, refresh the
snippets, line numbers and tables with `python tools/build_docs.py`.

## Ships, credits and modes
- **Hangar** (main menu): spend credits on ships and pick the one you fly. Credits exist only in the game; you earn
  them from kills, rocks (gold ore pays extra), power-ups, crystals, rescued pods, objectives and clearing levels.
  Your credits, owned ships and best level are saved in `profile.json` (per machine). Delete it to start over.
- **Ability key: SHIFT** (cooldown shown bottom right). **Key 7** fires the ship's own weapon.

| Ship | Price | Ability (SHIFT) | Own weapon (key 7) |
|---|---|---|---|
| Scout | free | none (balanced) | - |
| Phantom | 600 | Cloak: aliens lose you (firing or being hit breaks it) | Silent Bolt: strong, keeps the cloak |
| Skipper | 800 | Hyperjump to a random safe spot | Jump-blast: instant area burst |
| Specter | 1000 | Hyperspace: 3s immune to rocks, aliens, bullets (no firing/pickups) | Phase Lance: pierces 8 targets |
| Bulwark | 1200 | Deflect: reflects alien bullets; plus a rechargeable shield bar | Flak Cannon: 7-pellet shotgun |
| Medic | 900 | Repair Burst: heals you and a nearby ally; plus slow self-repair | Repair Dart: heals an ally, hurts aliens |

- **Mode** (main menu, ENTER toggles; also in the editor): *Classic* is the original game. *Expedition* adds:
  - smarter aliens: **Seeker** (finds cloaked ships), **Teleporter** (blinks next to you), **Minelayer**;
  - hazards: **nebulae** (hide ships from aliens), **black holes**, **ion storms** (abilities/shields stop recharging),
    **solar flares** (warning band, then a damaging burst);
  - rock types: **ice** (shatters into 3), **explosive**, **gold ore** (pays credits), **metal** (3 hits);
  - objectives that must be done before the wormhole opens: collect crystals, rescue pods, escort a freighter
    (boss levels: destroy the mothership);
  - a choice of 1 of 3 **perks** after every level (press 1-3). In multiplayer the game waits for both players.
- In multiplayer the host's mode and rules apply; credits are banked on each player's own machine.

## Multiplayer (2 players on one LAN)
1. **Host:** Main menu -> *Multiplayer (LAN)* -> *Host a game*. You start playing immediately; the top of the
   screen shows your address (for example `192.168.1.20:5555`). The second player can join at any time.
2. **Join:** *Multiplayer (LAN)* -> *Join a game on my network* (hosts appear automatically), or
   *Join by IP address* and type the host's IPv4 address (`192.168.1.20` or `192.168.1.20:6000`).
3. Both players fly on the same map against the same rocks and aliens (co-op, no friendly fire). Either player
   entering a wormhole takes both to the next level. A downed player returns at the next level at half health;
   the game ends when both are down. Player 2's ship is tinted green. ESC leaves.
4. Set your name and the port in the *Game Editor* -> Multiplayer. Both machines must use the same port for
   automatic discovery (a typed `IP:port` works with any port). The host's gameplay settings (gravity, weapons,
   aliens, timing...) are sent to the joiner for the session; each PC keeps its own art and sounds.

### Firewall (the usual reason a game is not found)
Allow port **5555** (TCP and UDP) on the **host** PC, on a private network.
- Windows: accept the "Windows Defender Firewall" prompt for Python (tick *Private networks*), or in an admin
  prompt: `netsh advfirewall firewall add rule name="Wormhole Runner" dir=in action=allow protocol=TCP localport=5555`
  and the same with `protocol=UDP`.
- Linux (ufw): `sudo ufw allow 5555`. (firewalld: `sudo firewall-cmd --add-port=5555/tcp --add-port=5555/udp`.)

Discovery uses UDP broadcast on your /24 subnet. If hosts are not listed (guest Wi-Fi, VLANs, VPN), use
*Join by IP address*. Run `python lan_check.py` to see your addresses and test discovery, or
`python lan_check.py host` on one PC and `python lan_check.py connect <host-ip>` on the other.

### How it works
The host runs the whole simulation. The joiner sends its held keys (30/s) over TCP and draws the world
snapshots the host sends back (30/s, interpolated); its own ship is predicted locally so steering feels
instant. UDP is used only for discovery. Standard library only (`socket`, `threading`, `json`).


## Controls
UP/DOWN speed, LEFT/RIGHT rotate, SPACE fire (hold to keep firing), SHIFT ship ability, 1-9 select weapon, P pause, ESC menu.

## Layout
- `game/config.py` – all settings + defaults, saved to `config.json`
- `game/sprites.py` – `AnimatedSprite`, `Ship`, `Rock`, `PowerUp`, `Wormhole`, `Background`
- `game/weapons.py` – `Bullet` (bolt / homing / mine) and `WeaponSystem` (slots 1-9, ammo, cooldown)
- `game/aliens.py` – `Alien` base class + `Drifter`, `Chaser`, `Sniper`, `Swarm`, `Mothership` (one `think()` AI each)
- `game/world.py` – wrap-around play area (`delta()` gives the shortest vector across edges)
- `game/net.py`, `game/net_views.py` – connection, discovery, host/join screens
- `game/client_view.py` – the joiner's screen (interpolation + ship prediction); `game/hud.py` shared HUD
- `game/game_features.py` – credits, rock types, hazards, objectives, abilities, perks (mixed into GameView)
- `game/hazards.py`, `game/perks.py`, `game/profile.py`, `game/hangar_view.py`
- `game/player.py` – a player's ship, weapons, score
- `game/physics.py` – gravity (pull = G * rock_mass / distance^2) and rotation helper
- `game/audio.py` – `AudioManager`: event name -> file in `assets/sounds/`
- `game/game_view.py`, `menu_view.py`, `editor_view.py` – the views

## Your own art (tile sequences)
Put a PNG sheet in `assets/images/`, then in the editor choose the file and set tile
width/height, tile count and fps. Tiles are read left-to-right, top-to-bottom.

## Your own sounds
Drop a file in `assets/sounds/`, pick it in the editor (T tests it). To add a new
event, add `audio.events.<name>` in `config.json` and call `audio.play("<name>")`.
WAV works everywhere; MP3/OGG may need FFmpeg installed (a pyglet requirement).

## Weapons, aliens, world
- Weapons live under `weapons.w1`..`w9` in the settings. 7-9 ship disabled: enable and tune them in the editor
  (type: bolt, homing or mine). Each slot's bullet image is `graphics.bullet_wN`, its sound is the event named in `sound`.
- Alien types live under `aliens.<type>`; each has its own image (`graphics.alien_<type>`) and sound events
  `<type>_spawn`, `<type>_fire`, `<type>_die`. A mothership boss appears every `boss_every` levels and must be
  destroyed before a wormhole will open.
- The world grows by `world.growth_per_level` each level (capped by `world.max_scale`); the camera zooms out to show it all.
- To add an alien type: subclass `Alien` in `aliens.py`, implement `think()`, register it in `ALIEN_CLASSES`,
  and add `aliens.<type>` + `graphics.alien_<type>` entries.
