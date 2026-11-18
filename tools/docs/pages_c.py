"""Pages: ships and credits, alien AI, rocks/hazards/rules, going further."""
from lib import (box, build_page, diagram, file_link, intentions, quiz, snippet, snippet_between,
                 symbol_link, table, try_it)
from game.config import DEFAULTS as D
from game.perks import PERKS
from game.sprites import ROCK_TINTS


def ships():
    rows = []
    for sid, c in D["ships"].items():
        ab = c["ability"]
        w = c["weapon"]
        rows.append([f"<strong>{c['name']}</strong>", c["price"] or "free", int(c["health"]),
                     f"&times;{c['speed_mult']:.2f} / &times;{c['accel_mult']:.2f} / &times;{c['turn_mult']:.2f}",
                     (f"<strong>{ab['name']}</strong>: {ab['desc']}" if ab else "none"),
                     (f"{w['name']} ({w['type']}, {w['damage']} damage)" if w else "none")])
    ship_tbl = table(["Ship", "Price", "Hull", "Speed / accel / turn", "Ability (SHIFT)", "Own weapon (key 7)"], rows)
    wrows = []
    for key, w in D["weapons"].items():
        if not w["enabled"]:
            continue
        ammo = "unlimited" if w["ammo"] < 0 else w["ammo"]
        wrows.append([key[1:], f"<strong>{w['name']}</strong>", w["type"], w["damage"], f"{w['cooldown']}s", ammo, w["unlock_level"]])
    weapon_tbl = table(["Key", "Weapon", "Type", "Damage", "Delay", "Ammo", "Unlocks at level"], wrows)
    crows = [[k.replace("_", " "), v] for k, v in D["credits"].items() if k != "start_credits"]
    credit_tbl = table(["Earn credits for&hellip;", "Amount"], crows)

    flow = """<svg viewBox="0 0 700 300" xmlns="http://www.w3.org/2000/svg">
<defs><marker id="ar3" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto"><polygon points="0,0 10,4 0,8" fill="#0f7a8a"/></marker></defs>
<g stroke="#0f7a8a" stroke-width="3" fill="none" marker-end="url(#ar3)">
<path d="M130 50 H170"/><path d="M290 50 H330"/><path d="M450 50 H490"/><path d="M610 50 H640 V90"/><path d="M230 80 V140"/><path d="M390 80 V140"/></g>
<rect x="10" y="25" width="120" height="50" rx="10" fill="#e6f0ff" stroke="#17306b" stroke-width="2"/><text x="70" y="55" text-anchor="middle" font-size="14">SHIFT pressed</text>
<rect x="170" y="25" width="120" height="50" rx="10" fill="#fff6dd" stroke="#b86e00" stroke-width="2"/><text x="230" y="48" text-anchor="middle" font-size="13">Has an ability?</text><text x="230" y="64" text-anchor="middle" font-size="12">Cooldown over?</text>
<rect x="330" y="25" width="120" height="50" rx="10" fill="#fff6dd" stroke="#b86e00" stroke-width="2"/><text x="390" y="48" text-anchor="middle" font-size="13">In an ion storm?</text><text x="390" y="64" text-anchor="middle" font-size="12">Phased out?</text>
<rect x="490" y="25" width="120" height="50" rx="10" fill="#fff6dd" stroke="#b86e00" stroke-width="2"/><text x="550" y="55" text-anchor="middle" font-size="13">Which type?</text>
<rect x="590" y="90" width="100" height="50" rx="10" fill="#e6f8ec" stroke="#2c9a52" stroke-width="2"/><text x="640" y="120" text-anchor="middle" font-size="13">Run it!</text>
<rect x="170" y="140" width="120" height="50" rx="10" fill="#ffe9e6" stroke="#d6452e" stroke-width="2"/><text x="230" y="170" text-anchor="middle" font-size="13">NO: do nothing</text>
<rect x="330" y="140" width="120" height="50" rx="10" fill="#ffe9e6" stroke="#d6452e" stroke-width="2"/><text x="390" y="162" text-anchor="middle" font-size="13">Yes: ability off</text><text x="390" y="178" text-anchor="middle" font-size="12">for now</text>
<text x="20" y="240" font-size="14">Cloak, Hyperspace, Deflect, Repair: switch on for a few seconds.</text>
<text x="20" y="264" font-size="14">Hyperjump: move the ship to a random safe place straight away.</text>
<text x="20" y="288" font-size="14">Then start the cooldown timer.</text></svg>"""

    body = f'''
{intentions(
    ["see how ships are described using data instead of lots of code",
     "understand each ship's ability and how it is checked in code",
     "understand shields, damage order and the credits economy",
     "see how weapons are built from a few simple types"],
    ["explain what makes a ship different from another",
     "describe the order the game checks before it damages a ship",
     "explain why credits are saved in a file",
     "add a new ship to the game by editing the settings"])}

<h2>Ships are data</h2>
<p>There is one <code>Ship</code> class, but six different ships. How? Each ship is described by a <strong>dictionary of settings</strong>: name, price, hull strength, speed numbers,
an ability, and its own weapon. The same class reads those numbers and behaves differently. This idea is called <strong>data-driven design</strong>.</p>
{snippet("game/config.py", "_ship", note="A small <em>helper function</em> that builds one ship's dictionary. Calling it six times makes six ships.")}
{ship_tbl}

<h2>The ability system</h2>
<p>Every ship has at most one special move, triggered with <strong>SHIFT</strong>. Before it can run, the game checks several conditions. This is a chain of
<code>if</code> decisions:</p>
{diagram(flow, "The decisions the game makes when SHIFT is pressed.", "Flowchart of the ability check")}
{snippet("game/game_features.py", "FeaturesMixin._try_ability",
         note="Notice the first <code>if</code> uses <code>or</code> to join four conditions. Any one of them being true stops the ability.")}
<p>Timed abilities such as the Cloak are stored as a countdown called <code>active</code>. The ship's properties check that countdown, so the rest of the game can simply ask
<code>ship.cloaked</code> or <code>ship.phased</code>:</p>
{snippet_between("game/sprites.py", "def _on(self, kind):", "healing = property")}
<h3>Hyperjump: searching for a safe place</h3>
<p>The Skipper jumps to a random spot. But landing inside a rock would be unfair. So the code <strong>tries a random place, tests it, and tries again</strong> (up to 60 times):</p>
{snippet("game/game_features.py", "FeaturesMixin._hyperjump",
         note="A <code>for</code> loop with an <code>ok</code> flag. <code>break</code> leaves the loop as soon as a good spot is found.")}

<h2>Taking damage: the order of checks</h2>
<p>When something hurts a ship, the game asks questions in a careful order. A Specter in hyperspace takes <em>no</em> damage. The Bulwark's shield soaks up damage <em>before</em> the hull does.</p>
{snippet("game/game_view.py", "GameView._damage_player")}
<ol>
<li>Is the ship dead, phased out, invincible (power-up) or in its short grace period? Then <strong>no damage</strong>. The function returns <code>False</code>.</li>
<li>If the ship has a shield with energy left, the shield absorbs the damage first.</li>
<li>Any damage left over reduces the hull. If the hull reaches 0, the ship is destroyed.</li>
</ol>

<h2>Weapons</h2>
<p>All the weapons come from four simple <em>types</em>. The <code>type</code> setting decides which code runs:</p>
<ul>
<li><strong>bolt</strong>: a shot that flies straight. (A shotgun is just several bolts at slightly different angles.)</li>
<li><strong>homing</strong>: a bolt that steers toward a target.</li>
<li><strong>mine</strong>: stays where it is and explodes after a fuse, or when something comes close.</li>
<li><strong>pulse</strong>: an instant explosion around the ship.</li>
</ul>
{weapon_tbl}
{snippet("game/weapons.py", "WeaponSystem.fire", note="A good example of <code>if</code> / <code>elif</code> choosing between weapon types, and a <code>for</code> loop creating several bullets for a spread.")}

<h2>Credits: the in-game money</h2>
<p>Credits exist <em>only inside the game</em>. They are not real money and you can never buy them. You earn them by playing. Then you spend them in the Hangar.</p>
{credit_tbl}
<p>Your credits and the ships you own are saved in a file called <code>profile.json</code>, so they are still there next time. Buying is a short function with a decision in it:</p>
{snippet("game/profile.py", "Profile.buy")}
<p>The earnings are added with <code>_earn</code>. Perks such as <em>Scavenger</em> multiply the amount:</p>
{snippet("game/game_features.py", "FeaturesMixin._earn")}

{try_it("make your own ship", """<p>Open <code>game/config.py</code> and find the <code>"medic"</code> entry inside <code>"ships"</code>. Copy the whole entry, paste it below, and change <code>"medic"</code> to
<code>"tinker"</code> and the <code>"Medic"</code> name to <code>"Tinker"</code>. Change the health, price and the ability numbers. Run the game and open the Hangar. Your new ship is there! Why did we not need to change any
other code?</p>""")}

{quiz([
    ("Why can one <code>Ship</code> class make six different ships?", "Each ship's numbers and abilities come from a settings dictionary, so the same code gives different results."),
    ("What does <code>or</code> do in an <code>if</code> condition?", "The whole condition is true if <em>any</em> part is true."),
    ("A Bulwark with 30 shield energy takes 40 damage. How much reaches the hull?", "10. The shield absorbs 30 first."),
    ("Why does the hyperjump code try up to 60 times?", "A random spot might be next to a rock or alien. It keeps trying until it finds a safe one."),
    ("Where are your credits saved, and why?", "In <code>profile.json</code>, so they are remembered after you close the game."),
])}
'''
    build_page("ships", "8. Ships and credits", body, "One class, many ships, and the money system.")


def aliens():
    info = {
        "drifter": ("Wanders along a wavy path. Never shoots.", "Easy points. Watch the wobble."),
        "chaser": ("Hunts you and tries to ram you. Turns slowly.", "Fly in a circle: it cannot turn fast enough."),
        "sniper": ("Keeps its distance and fires where you <em>will</em> be.", "Change direction often. It flickers before it fires."),
        "swarm": ("A group of four that orbit you and fire.", "Shoot them one at a time."),
        "seeker": ("Patrols until it spots you, even through a cloak.", "Stay far away and it loses you."),
        "teleporter": ("Blinks next to you and fires a burst.", "Move as it flickers: that is the warning."),
        "minelayer": ("Drops proximity mines as it patrols.", "Learn where the mines are. They glow red."),
        "mothership": ("Boss. Fires patterns and launches chasers.", "Keep moving. Use your strongest weapons."),
    }
    rows = []
    for k, c in D["aliens"].items():
        rows.append([f"<strong>{k.title()}</strong>", c["min_level"], c["health"], c["speed"], c["score"], info[k][0], info[k][1]])
    tbl = table(["Alien", "From level", "Health", "Speed", "Score", "Behaviour", "Tip"], rows)

    lead = """<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg">
<defs><marker id="ar4" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto"><polygon points="0,0 10,4 0,8" fill="#d6452e"/></marker></defs>
<circle cx="60" cy="170" r="16" fill="#9a4fd6"/><text x="60" y="205" text-anchor="middle" font-size="13">alien</text>
<circle cx="300" cy="60" r="16" fill="#2c9a52"/><text x="300" y="38" text-anchor="middle" font-size="13">your ship now</text>
<line x1="318" y1="60" x2="520" y2="60" stroke="#2c9a52" stroke-width="3" stroke-dasharray="6" marker-end="url(#ar4)"/>
<circle cx="540" cy="60" r="16" fill="none" stroke="#2c9a52" stroke-width="3" stroke-dasharray="4"/><text x="540" y="38" text-anchor="middle" font-size="13">where you will be</text>
<line x1="78" y1="165" x2="300" y2="75" stroke="#999" stroke-width="2" stroke-dasharray="3"/><text x="150" y="105" font-size="13" fill="#999">aim here: misses</text>
<line x1="78" y1="168" x2="525" y2="75" stroke="#d6452e" stroke-width="3" marker-end="url(#ar4)"/><text x="330" y="150" font-size="14" fill="#d6452e">aim here: hits (lead the target)</text></svg>"""

    state = """<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg">
<defs><marker id="ar5" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto"><polygon points="0,0 10,4 0,8" fill="#0f7a8a"/></marker></defs>
<g stroke="#0f7a8a" stroke-width="3" fill="none" marker-end="url(#ar5)"><path d="M190 60 H250"/><path d="M430 60 H490"/><path d="M590 90 V130 H340 V100"/></g>
<rect x="30" y="30" width="160" height="60" rx="10" fill="#e6f0ff" stroke="#17306b" stroke-width="2"/><text x="110" y="56" text-anchor="middle" font-size="14">1. Approach</text><text x="110" y="74" text-anchor="middle" font-size="12">drift toward you</text>
<rect x="250" y="30" width="180" height="60" rx="10" fill="#fff6dd" stroke="#b86e00" stroke-width="2"/><text x="340" y="56" text-anchor="middle" font-size="14">2. Charge</text><text x="340" y="74" text-anchor="middle" font-size="12">flickers for 0.6 s</text>
<rect x="490" y="30" width="190" height="60" rx="10" fill="#f1e9ff" stroke="#7a4fd6" stroke-width="2"/><text x="585" y="56" text-anchor="middle" font-size="14">3. Blink + fire</text><text x="585" y="74" text-anchor="middle" font-size="12">teleport, burst of 3</text>
<text x="350" y="158" text-anchor="middle" font-size="13">then the timer resets and it starts again</text></svg>"""

    body = f'''
{intentions(
    ["understand how an enemy can be programmed to make choices (AI)",
     "see how a finite state machine works",
     "understand how an alien decides what it can see",
     "compare different movement strategies"],
    ["describe how three different aliens behave",
     "explain what 'leading the target' means",
     "explain how a cloak hides you from an alien"])}

<h2>What is "AI" in a game?</h2>
<p>The aliens are not clever like a person. Each follows a small set of rules, and the rules together make it look as if it is thinking. Game programmers call this
<strong>AI</strong> (artificial intelligence). Your job as a programmer is to choose simple rules that feel interesting to play against.</p>
{tbl}

<h2>The shared brain</h2>
<p>Every alien class inherits the same <code>update_alien</code> method. It does the same three things each frame: find a target, decide what to do, then move.</p>
{snippet("game/aliens.py", "Alien.update_alien")}
{snippet("game/aliens.py", "Alien.wander", note="If an alien can see nobody, it drifts aimlessly. <code>random.uniform</code> gives a random number in a range.")}

<h2>What can an alien see?</h2>
<p>Before an alien thinks, the game asks: <em>which ship can this alien see?</em> A cloaked ship, or one inside a nebula, is invisible unless the alien is very close. The Seeker has special
long-range sensors.</p>
{snippet("game/game_view.py", "GameView.nearest_ship")}
{snippet("game/game_features.py", "FeaturesMixin._hidden_from")}
<p>This is a nice example of <strong>returning <code>None</code></strong>: "nothing". If every ship is hidden, <code>nearest_ship</code> gives back <code>None</code>, and the alien <code>wander</code>s.</p>

<h2>Strategy 1: simple pursuit (Chaser)</h2>
<p>The Chaser turns toward you, but only by a limited amount each second. That "turn limit" is why you can dodge it by circling.</p>
{snippet("game/aliens.py", "Chaser")}

<h2>Strategy 2: predicting the future (Sniper)</h2>
<p>If the Sniper aimed at where you <em>are</em>, its shot would miss when you keep moving. So it works out how long the bullet takes to arrive, then aims at where you <em>will be</em>.</p>
{diagram(lead, "Leading the target: aim ahead of a moving ship.", "Diagram of an alien aiming ahead of a moving ship")}
{snippet("game/aliens.py", "Sniper.think",
         note="<code>t = dist / bullet_speed</code> is the travel time. The ship's velocity multiplied by <code>t</code> tells us how far it will move.")}

<h2>Strategy 3: a timeline (Teleporter) and state machines</h2>
<p>Many AIs are <strong>state machines</strong>: the alien is always in one <em>state</em> and changes state when something happens. The Teleporter's states use timers:</p>
{diagram(state, "The Teleporter's cycle of states.", "State machine diagram of the Teleporter")}
{snippet("game/aliens.py", "Teleporter.think")}

<h2>Strategy 4: formations (Swarm)</h2>
<p>Each ship in a Swarm gets a slot number. Slot 0 orbits at one angle, slot 1 a quarter of the way round, and so on. Together they circle you like a ring:</p>
{snippet("game/aliens.py", "Swarm.think")}

<h2>Strategy 5: leaving traps (Minelayer)</h2>
{snippet("game/aliens.py", "Minelayer")}
<p>The Minelayer does not care about you. It just patrols and drops mines on a timer. The danger is the <em>mines</em>, which are rewarded by the game's collision code.</p>

{try_it("tune an alien", """<p>In the Game Editor, find <em>Alien: Chaser</em>. Raise its <em>Turn rate</em> to 360 and play level 2. Is it harder to dodge? Now try making the Sniper's
<em>Bullet speed</em> very slow. What happens to its aim?</p>""")}

{quiz([
    ("What does <code>nearest_ship</code> return when every ship is hidden?", "<code>None</code>."),
    ("Why does the Sniper aim ahead of your ship?", "The bullet takes time to arrive, and your ship moves in that time."),
    ("What is a state machine?", "A program that is in one state at a time and changes state when something happens."),
    ("Why can you dodge a Chaser by flying in a circle?", "It can only turn a limited amount each second."),
    ("Which alien ignores you completely?", "The Minelayer. It patrols and drops mines."),
])}
'''
    build_page("aliens", "9. Alien AI", body, "How seven enemies and a boss make their decisions.")


def rocks_hazards_rules():
    def swatch(c):
        return f'<span style="display:inline-block;width:1.1em;height:1.1em;border-radius:4px;background:rgb({c[0]},{c[1]},{c[2]});border:1px solid #555;vertical-align:middle"></span>'
    effects = {
        "ice": "Shatters into <strong>three</strong> pieces instead of two.",
        "explosive": "Blows up when destroyed. The blast hurts ships, aliens and other rocks, and can set off a chain.",
        "gold": "Pays extra credits when you destroy it.",
        "metal": "Armoured. It takes <strong>3 hits</strong> from bullets before it breaks.",
    }
    rrows = [["Normal", "1", "60", "plain grey-brown", "Splits into two smaller rocks."]]
    for k, c in D["rock_types"].items():
        rrows.append([f"{swatch(ROCK_TINTS[k])} {k.title()}", c["min_level"], c["weight"], k, effects[k]])
    rock_tbl = table(["Rock", "From level", "Chance weight", "What it does"], [r[:3] + r[4:] for r in rrows])

    hz = D["hazards"]
    hrows = [
        ["Nebula", hz["nebula_from"], "A cloud. Ships inside are hidden from aliens."],
        ["Black hole", hz["blackhole_from"], "Pulls ships and rocks toward it. Touching the centre hurts."],
        ["Ion storm", hz["ion_from"], "Abilities and shields stop recharging and the ship is jostled."],
        ["Solar flare", hz["flare_from"], f"A glowing warning band appears, then a burst hurts everything in the band ({hz['flare_damage']} damage to ships)."],
    ]
    hazard_tbl = table(["Hazard", "From level", "Effect"], hrows)
    objective_tbl = table(["Objective", "How it works"],
                          [["Collect crystals", f"Fly through the crystals ({D['objectives']['crystals_base']} + level &divide; 2 of them)."],
                           ["Rescue pods", f"Touch the drifting pods ({D['objectives']['pods_base']} + level &divide; 3 of them)."],
                           ["Escort the freighter", f"Keep a slow cargo ship alive for {int(D['objectives']['escort_seconds'])} seconds. If it is destroyed, the wormhole still opens, but with no bonus."],
                           ["Destroy the mothership", "On every fifth level."]])
    perk_tbl = table(["Perk", "Effect"], [[f"<strong>{n}</strong>", d] for n, d in PERKS.values()])

    body = f'''
{intentions(
    ["understand the five rock types and how a random choice is made",
     "understand the hazards and what each one does to a ship",
     "know the rules for objectives, perks, scoring and wormholes",
     "read a few more examples of conditionals and loops"],
    ["explain what 'chance weight' means",
     "describe three hazards",
     "list the order of events when a level is finished"])}

<h2>Rock types</h2>
<p>A rock has a <em>kind</em>. The kind changes its colour and what happens when it breaks. In Expedition mode, each new rock picks its kind at random, but some kinds are more likely than others. Each kind has a <strong>weight</strong>. A bigger weight means more likely.</p>
{rock_tbl}
{snippet("game/game_features.py", "FeaturesMixin._pick_rock_kind",
         note="<code>random.choices</code> picks one item using weights. A rock kind only goes into the pool once the level is high enough.")}
<p>When a rock breaks it splits into smaller rocks, so a big rock can become many small ones. The smallest rocks simply disappear. Here is the splitting code. Ice uses three directions, everything else uses two:</p>
{snippet("game/sprites.py", "Rock.split")}
{snippet("game/game_view.py", "GameView._break_rock", note="This is where gold pays credits and explosive rocks explode.")}

<h2>Hazards</h2>
{hazard_tbl}
<p>Hazards are small classes. The black hole is just a hazard with a "reach" and a core:</p>
{snippet("game/hazards.py", "BlackHole")}
<p>The game applies their effects every frame. Look at how a loop goes over every hazard and every ship, and uses <code>if</code>/<code>elif</code> on the hazard's kind:</p>
{snippet("game/game_features.py", "FeaturesMixin._update_hazards")}
{snippet("game/hazards.py", "SolarFlare", note="A flare has a timer. Phase 0 is the warning, phase 1 is the burst. The <code>covers</code> method tests whether something is inside the band.")}

<h2>Objectives</h2>
<p>In Expedition mode, the wormhole stays closed until the level's objective is done. This is a rule the game checks every frame.</p>
{objective_tbl}
{snippet("game/game_features.py", "FeaturesMixin._setup_objective")}

<h2>Perks</h2>
<p>After every level in Expedition mode you pick one of three random perks. In multiplayer the game waits until both players choose (or 20 seconds pass).</p>
{perk_tbl}
{snippet("game/perks.py", "apply_perk", note="A long <code>if</code> / <code>elif</code> chain: exactly one branch runs, depending on which perk was picked.")}

<h2>The rulebook</h2>
<ol>
<li>Rocks hurt ships. Each hit costs hull strength, then you get a short grace period.</li>
<li>Bullets break rocks and hurt aliens. Kills earn score and credits.</li>
<li>A level is finished when a ship enters an <em>open</em> wormhole. Then <strong>every</strong> player moves on.</li>
<li>The wormhole will not open until the objective is done, and (on boss levels) the Mothership is destroyed.</li>
<li>A destroyed ship comes back at the start of the next level with half its hull. The game is over when all ships are destroyed.</li>
<li>The map grows each level, and rocks, aliens and gravity get stronger.</li>
<li>In Classic mode there are no hazards, objectives, new aliens, rock types or perks.</li>
</ol>

{try_it("add a rock type", """<p>You can invent a rock kind using only the settings and one small code change:</p>
<ol><li>Add <code>"slow"</code> to <code>"rock_types"</code> in <code>game/config.py</code>.</li>
<li>Add a colour for it to <code>ROCK_TINTS</code> in <code>game/sprites.py</code>.</li>
<li>Add an <code>if rock.kind == "slow":</code> rule in <code>_break_rock</code> that gives the player a bonus.</li></ol>
<p>Which three files or places did you need to touch? Could this be made simpler?</p>""")}

{quiz([
    ("An ice rock of size 3 breaks. How many rocks does it become?", "Three smaller rocks of size 2 (if there is room under the maximum)."),
    ("If normal has weight 60 and gold has weight 8, which is more likely?", "Normal rocks."),
    ("Why does an ion storm stop shields from recharging?", "It is a rule: ships inside have <code>jammed</code> set to true, and the recharge code skips jammed ships."),
    ("What must happen before a wormhole opens on level 10?", "The objective must be finished and the Mothership destroyed."),
    ("Which statement runs in an <code>if</code> / <code>elif</code> chain: all matching branches, or just the first?", "Just the first one that is true."),
])}
'''
    build_page("rocks-hazards-rules", "10. Rocks, hazards and rules", body, "Everything that can hurt you, and the rules that tie it all together.")


def going_further():
    net = """<svg viewBox="0 0 700 240" xmlns="http://www.w3.org/2000/svg">
<defs><marker id="ar6" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto"><polygon points="0,0 10,4 0,8" fill="#0f7a8a"/></marker></defs>
<rect x="20" y="40" width="200" height="140" rx="12" fill="#e6f8ec" stroke="#2c9a52" stroke-width="2"/><text x="120" y="70" text-anchor="middle" font-size="16" font-weight="bold">HOST</text>
<text x="120" y="98" text-anchor="middle" font-size="13">runs the whole game:</text><text x="120" y="118" text-anchor="middle" font-size="13">rocks, aliens, rules</text><text x="120" y="150" text-anchor="middle" font-size="13">is the "truth"</text>
<rect x="480" y="40" width="200" height="140" rx="12" fill="#e6f0ff" stroke="#17306b" stroke-width="2"/><text x="580" y="70" text-anchor="middle" font-size="16" font-weight="bold">JOINER</text>
<text x="580" y="98" text-anchor="middle" font-size="13">sends key presses,</text><text x="580" y="118" text-anchor="middle" font-size="13">draws what the host</text><text x="580" y="138" text-anchor="middle" font-size="13">sends back</text>
<line x1="220" y1="85" x2="480" y2="85" stroke="#0f7a8a" stroke-width="3" marker-end="url(#ar6)"/><text x="350" y="75" text-anchor="middle" font-size="13">snapshots (30 per second)</text>
<line x1="480" y1="150" x2="220" y2="150" stroke="#0f7a8a" stroke-width="3" marker-end="url(#ar6)"/><text x="350" y="172" text-anchor="middle" font-size="13">keys pressed (30 per second)</text>
<text x="350" y="220" text-anchor="middle" font-size="14">Both messages travel as small pieces of text called JSON.</text></svg>"""
    body = f'''
{intentions(
    ["get a first idea of how two computers can play one game",
     "learn the words: network, client, server, protocol",
     "think about staying safe online",
     "find ideas to extend the game"],
    ["explain why one computer is the 'host'",
     "explain what a snapshot is",
     "list two rules for staying safe when playing online"])}

<h2>Two computers, one game</h2>
<p>When two people play together, both screens must show the <em>same</em> rocks and aliens. If each computer ran its own game, they would soon disagree. So one computer, the
<strong>host</strong>, runs the real game. The other computer, the <strong>joiner</strong>, sends what keys it is pressing and draws pictures of the world the host sends back.</p>
{diagram(net, "The host and the joiner talk by sending messages.", "Diagram of a host and a joiner exchanging messages")}
<h3>Finding a game</h3>
<p>A host shouts "I'm here!" to everyone on the local network when asked. This is called a <strong>broadcast</strong>. The joiner's search sends a short question and listens for answers:</p>
{snippet("game/net.py", "LanScanner.scan")}
<h3>Snapshots</h3>
<p>About 30 times a second the host builds a <strong>snapshot</strong>: a list of where everything is. It is a dictionary turned into text (JSON) and sent over the network:</p>
{snippet("game/game_view.py", "GameView._network_tick", first=1, last=30)}
<h3>Smooth movement</h3>
<p>Snapshots arrive in jumps, but we want smooth movement. The joiner <strong>interpolates</strong>: it slides things from their old position to their new one. For its own ship it <strong>predicts</strong>:
it moves the ship straight away using the same rules as the host, then gently corrects if the host disagrees.</p>
{snippet("game/client_view.py", "ClientView._predict", first=1, last=22)}
{box("tip", "Why TCP?",
     "<p>Computers send data in different ways. <strong>TCP</strong> guarantees everything arrives, in order. <strong>UDP</strong> is faster but may lose messages. The game uses TCP for play and UDP only for the 'who is hosting?' question.</p>")}

<h2>Staying safe</h2>
<ul>
<li>Only play with people you know, on a trusted network such as your school or home.</li>
<li>Never share your address, school or full name in a game.</li>
<li>Your teacher or caregiver should know who you are playing with.</li>
<li>If someone makes you uncomfortable, stop playing and tell a trusted adult.</li>
</ul>
<p>Programmers have a responsibility too: this game never asks for personal information, and your credits are saved only on your own computer.</p>

<h2>Ideas to extend the game</h2>
<ul>
<li>A new <strong>alien</strong> with its own <code>think</code> method (a Shielder that protects other aliens?).</li>
<li>A new <strong>ship</strong> with an ability that heals nearby ships or slows time.</li>
<li>A <strong>high-score table</strong> saved in a file.</li>
<li>Your own <strong>art and sound</strong>: replace the generated pictures in <code>assets/images</code>.</li>
<li>A <strong>level editor</strong> that places rocks by hand.</li>
<li>Show your credits and scores on a <strong>web page</strong> (see the next page).</li>
</ul>

<h2>Using an AI helper well</h2>
<p>An AI assistant can write code, but it is only a helper. You must <strong>read</strong> what it writes, <strong>test</strong> it, and be able to <strong>explain</strong> it. Good prompts are small, clear and ask for one thing at a time.
The tutorial page shows examples.</p>
{try_it("explain it", "<p>Pick any code box on this site. Write three sentences explaining it to a friend who has never programmed. Then ask a classmate to find anything you got wrong.</p>")}

{quiz([
    ("Why does one computer act as the host?", "So there is one true copy of the game, and both players see the same thing."),
    ("What is a snapshot?", "A list of where everything is at one moment, sent from host to joiner."),
    ("What does interpolation do?", "It slides things smoothly between the positions from two snapshots."),
    ("Give two safety rules for online games.", "For example: only play with people you know; do not share personal information."),
    ("Why must you test code an AI helper gives you?", "It can contain mistakes. You are responsible for checking it works and understanding it."),
])}
'''
    build_page("going-further", "11. Going further", body, "Multiplayer, safety and ideas to take the game further.")


def build():
    ships()
    aliens()
    rocks_hazards_rules()
    going_further()
