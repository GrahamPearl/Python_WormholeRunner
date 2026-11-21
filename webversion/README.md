# Wormhole Runner (web)

Single-player browser port. No installs, no backend: just static files.

## Run it
1. Unzip this folder.
2. Start a static server in it (ES modules do not work from `file://`):
   `python -m http.server 8000`   (or VS Code Live Server)
3. Open http://localhost:8000

## Files
- `index.html`, `css/styles.css` - page and overlays
- `js/` - `main.js`, `game.js`, `config.js`, `input.js`, `assets.js`, `utils.js`, `entities/`
- `assets/images/` - 10 PNG sprites (ship, rock, drifter, chaser, bullet, wormhole, speed, health, shield, ammo)
- `tools/make_assets.py` - redraws those PNGs (needs `pip install pillow`)

## Your own art
Replace any PNG in `assets/images/` with your own of the same name (keep the sizes: ships, rocks and aliens
64x64, bullet 12x28, wormhole 128x128, power-ups 32x32). If a file is missing, the game draws a built-in
replacement, so it still runs. Sound effects are generated in the browser, so there are no audio files to install.
