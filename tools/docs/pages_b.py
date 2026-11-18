"""Pages: inheritance, game loop, physics, levels and the world."""
import math

from lib import (box, build_page, diagram, intentions, quiz, snippet, snippet_between, symbol_link,
                 table, try_it)
from game.config import DEFAULTS as D


def inheritance():
    def node(x, y, w, text, fill="#e6f0ff", stroke="#17306b"):
        return (f'<rect x="{x}" y="{y}" width="{w}" height="34" rx="7" fill="{fill}" stroke="{stroke}" stroke-width="2"/>'
                f'<text x="{x + w / 2}" y="{y + 22}" text-anchor="middle" font-size="13">{text}</text>')

    def link(x1, y1, x2, y2):
        return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#0f7a8a" stroke-width="2"/>'

    kids = ["Ship", "Rock", "PowerUp", "Wormhole", "Freighter", "Bullet", "Alien"]
    parts = [node(290, 10, 160, "arcade.Sprite", "#ffe9b8", "#b86e00"), node(290, 70, 160, "AnimatedSprite")]
    parts.append(link(370, 44, 370, 70))
    for i, k in enumerate(kids):
        x = 10 + i * 100
        parts.append(link(370, 104, x + 45, 150))
        parts.append(node(x, 150, 90, k))
    aliens = ["Drifter", "Chaser", "Sniper", "Swarm", "Seeker", "Teleporter", "Minelayer", "Mothership"]
    for i, a in enumerate(aliens):
        x = 10 + i * 88
        parts.append(link(655, 184, x + 40, 240))
        parts.append(node(x, 240, 82, a, "#e6f8ec", "#2c9a52"))
    svg = f'<svg viewBox="0 0 720 290" xmlns="http://www.w3.org/2000/svg">{"".join(parts)}</svg>'

    body = f'''
{intentions(
    ["understand inheritance: a class that builds on another",
     "tell the difference between <em>is-a</em> and <em>has-a</em> relationships",
     "understand polymorphism: one method name, many behaviours",
     "read a class diagram"],
    ["draw a simple class diagram",
     "explain why <code>Chaser</code> and <code>Sniper</code> can both be used as an <code>Alien</code>",
     "explain what <code>super().__init__</code> does"])}

<h2>Inheritance: "is a"</h2>
<p>Many things in the game share the same jobs: they have a position, a picture and they play an animation. Rather than write that
code again and again, one class holds it and others <strong>inherit</strong> it. A <code>Ship</code> <em>is an</em> <code>AnimatedSprite</code>.
A <code>Chaser</code> <em>is an</em> <code>Alien</code>.</p>
{diagram(svg, "The family tree of the game's sprite classes. Arrows go from a parent class down to its children.", "Class diagram showing Sprite, AnimatedSprite and its subclasses")}
<p>The top class, <code>arcade.Sprite</code>, comes from the Arcade library. It already knows how to hold a picture and draw it.
<code>AnimatedSprite</code> adds one thing: it can flip through a sheet of pictures to make an animation.</p>
{snippet("game/sprites.py", "AnimatedSprite",
         note="<code>super().__init__(...)</code> runs the parent class's constructor first. Then this class adds its own attributes.")}
<p>Now a <code>Ship</code> only needs to say what makes it different. This is the start of its class line:</p>
{snippet_between("game/sprites.py", "class Ship(AnimatedSprite):", "super().__init__(", title="game/sprites.py")}

<h2>Polymorphism: same name, different behaviour</h2>
<p>Every alien has a method called <code>think</code>. Each kind of alien writes its own version. The game does not need to know which
kind it has. It just calls <code>think</code> and each alien behaves in its own way. The word <strong>polymorphism</strong> means "many forms".</p>
{snippet("game/aliens.py", "Alien", first=1, last=27, note="The base class sets up what every alien shares.")}
{snippet("game/aliens.py", "Alien.update_alien",
         note="<code>self.think(dt, ctx)</code> calls <em>this</em> alien's own version.")}
<p>Compare how two aliens fill in <code>think</code>. The Drifter wobbles along a wave. The Chaser turns toward you.</p>
{snippet("game/aliens.py", "Drifter")}
{snippet("game/aliens.py", "Chaser")}
<p>A dictionary can turn a name such as <code>"chaser"</code> into the right class. This makes it easy to create aliens from a list of names:</p>
{snippet_between("game/aliens.py", "ALIEN_CLASSES = {", '"mothership": Mothership}')}

<h2>Composition: "has a"</h2>
<p>A <code>Player</code> is <em>not</em> a ship. A player <em>has a</em> ship, <em>has</em> weapons and <em>has</em> a score. When a class holds other objects
as attributes, we call this <strong>composition</strong>. A good rule: use inheritance for <em>is-a</em>, composition for <em>has-a</em>.</p>
{snippet("game/player.py", "Player.reset")}

<h2>Mixins: sharing a set of methods</h2>
<p>The main game class got very big. To keep it tidy, the extra systems (credits, hazards, objectives, abilities and perks) live in a separate class called
<code>FeaturesMixin</code>. The game class lists it as a parent so it can use all those methods:</p>
{snippet_between("game/game_view.py", "class GameView(", "def __init__")}
<p>The class has <em>two</em> parents. This is called <strong>multiple inheritance</strong>. A mixin is a parent that is never used alone.</p>

<h2>Encapsulation: keeping things tidy</h2>
<p>A class keeps its own data and the methods that change it together. Other code should ask the object to do things rather than
reach in and change everything. In the game, a ship's ability timers are changed by ship methods, and the game asks <code>ship.cloaked</code> instead of
checking the timers itself. A name that starts with an underscore, like <code>_break_rock</code>, is a hint: <em>"this is for the class's own use"</em>.</p>

{try_it("draw it", "<p>Draw a class diagram for a new kind of alien called <code>Bomber</code> that drops bombs. Which class does it inherit from? "
        "Which method must it write? Which attributes will it need?</p>")}

{quiz([
    ("Is a <code>Player</code> a <code>Ship</code>? Which relationship is it?", "No. A player <em>has a</em> ship. That is composition, not inheritance."),
    ("What does <code>super().__init__()</code> do?", "It runs the parent class's constructor so the parent's setup is done."),
    ("What is polymorphism? Give an example from the game.", "Different classes with the same method name behaving differently, such as each alien's <code>think</code> method."),
    ("Why does <code>ALIEN_CLASSES</code> make the code simpler?", "It looks up the class from a name, so one line can create any alien without a long chain of <code>if</code> statements."),
    ("Name one benefit of putting shared code in a parent class.", "Less repeated code, and a fix in one place helps every child class."),
])}
'''
    build_page("inheritance", "4. Inheritance and design", body, "How classes build on each other.")


def game_loop():
    flow = """<svg viewBox="0 0 700 330" xmlns="http://www.w3.org/2000/svg">
<defs><marker id="ar" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto"><polygon points="0,0 10,4 0,8" fill="#0f7a8a"/></marker></defs>
<g stroke="#0f7a8a" stroke-width="3" fill="none" marker-end="url(#ar)">
<path d="M130 60 H190"/><path d="M350 60 H410"/><path d="M570 60 H600 V120"/><path d="M600 190 V240 H350"/><path d="M190 240 H100 V120 L100 60"/>
</g>
<rect x="20" y="30" width="110" height="60" rx="10" fill="#e6f0ff" stroke="#17306b" stroke-width="2"/><text x="75" y="58" text-anchor="middle" font-size="14">Start</text><text x="75" y="76" text-anchor="middle" font-size="12">open window</text>
<rect x="190" y="30" width="160" height="60" rx="10" fill="#e6f8ec" stroke="#2c9a52" stroke-width="2"/><text x="270" y="56" text-anchor="middle" font-size="14">Read input</text><text x="270" y="76" text-anchor="middle" font-size="12">keys, network</text>
<rect x="410" y="30" width="160" height="60" rx="10" fill="#fff6dd" stroke="#b86e00" stroke-width="2"/><text x="490" y="56" text-anchor="middle" font-size="14">on_update(dt)</text><text x="490" y="76" text-anchor="middle" font-size="12">move + rules</text>
<rect x="520" y="120" width="160" height="70" rx="10" fill="#f1e9ff" stroke="#7a4fd6" stroke-width="2"/><text x="600" y="150" text-anchor="middle" font-size="14">on_draw()</text><text x="600" y="170" text-anchor="middle" font-size="12">paint the picture</text>
<rect x="190" y="215" width="160" height="50" rx="10" fill="#ffe9e6" stroke="#d6452e" stroke-width="2"/><text x="270" y="245" text-anchor="middle" font-size="14">Wait for next frame</text>
<text x="360" y="305" text-anchor="middle" font-size="13">Repeats about 60 times every second</text></svg>"""
    body = f'''
{intentions(
    ["understand that a game is one big loop",
     "explain what <code>on_update</code>, <code>on_draw</code> and <code>dt</code> are for",
     "see how input events reach the code",
     "understand why the order of drawing matters"],
    ["describe the game loop in my own words",
     "explain why movement is multiplied by <code>dt</code>",
     "say what happens to a sprite drawn last"])}

<h2>A game is a loop</h2>
<p>A film is many still pictures shown quickly. A game is the same. About 60 times every second the game does three things:
<strong>(1)</strong> check what the player pressed, <strong>(2)</strong> update the world, <strong>(3)</strong> draw a new picture.
Each round is called a <strong>frame</strong>.</p>
{diagram(flow, "The game loop. The library repeats these steps until you close the window.", "Flowchart of the game loop")}
<p>Our game uses the <strong>Arcade</strong> library. Arcade runs the loop for us and calls our methods at the right time:</p>
{table(["Method", "When it runs", "Its job"],
       [["<code>on_update(delta_time)</code>", "every frame", "Change the world: move, collide, apply rules"],
        ["<code>on_draw()</code>", "every frame, after update", "Paint everything on the screen"],
        ["<code>on_key_press(key, mods)</code>", "when a key goes down", "React to a key press"],
        ["<code>on_key_release(key, mods)</code>", "when a key comes up", "Stop reacting to a key"]])}
<p>The program starts in <code>main.py</code>. It makes a window, shows the menu and hands control to Arcade:</p>
{snippet("main.py", "main")}
<p>A <strong>View</strong> is one screen of the game: the menu, the Hangar, the editor, the game itself. <code>show_view</code> swaps which screen is active.</p>

<h2>Delta time: keeping speed fair</h2>
<p>Computers run at different speeds. If a ship moves 5 pixels per frame, a fast computer (120 frames a second) would make it twice as fast as a slow one.
The fix is to move by <em>speed &times; time</em>. Arcade tells us how long the last frame took. It is called <code>delta_time</code>, or <code>dt</code> for short.</p>
<pre class="inline"><code>x = x + speed * dt
# speed = 300 pixels per second, dt = 1/60 of a second
# so each frame the ship moves 300 * (1/60) = 5 pixels</code></pre>
<p>The game also limits <code>dt</code> so that a long pause (like dragging the window) does not cause a huge jump:</p>
{snippet_between("game/game_view.py", "dt = min(delta_time, 1 / 20)", "dt = min(delta_time, 1 / 20)")}

<h2>What happens inside one update</h2>
{snippet("game/game_view.py", "GameView.on_update", first=1, last=45,
         note="Read the method names. They tell the story: hazards act, each player moves and fires, rocks and aliens move, collisions are checked, and so on.")}
{box("tip", "Order matters",
     "<p>Hazards are updated <em>before</em> ships, because they change the ship's drift. Collisions are checked <em>after</em> everything has moved. "
     "Thinking about the order of steps is a big part of good program design.</p>")}

<h2>Drawing: the painter's algorithm</h2>
<p>Computers draw things one after another. Whatever is drawn <strong>last</strong> ends up on top, like layers of paint. So the game draws the background first and the ships last:</p>
{snippet("game/game_view.py", "GameView.on_draw", first=1, last=15)}
<p>There are two <strong>cameras</strong>. The <em>world camera</em> can zoom out so you can see the whole map. The <em>GUI camera</em> never moves, so the score and health bars stay put.</p>

<h2>Events: reacting to keys</h2>
<p>Pressing a key is an <strong>event</strong>. Arcade calls <code>on_key_press</code> and our code decides what it means. Held keys are kept in a set. The ship's steering code asks if a key is in the set each frame.</p>
{snippet("game/game_view.py", "GameView.on_key_press", first=1, last=23)}

<h2>Safe code: <code>try</code> and <code>except</code></h2>
<p>If a sound file is missing, the game should stay silent, not crash. The audio code wraps risky steps in <code>try</code>/<code>except</code>:</p>
{snippet("game/audio.py", "AudioManager.play")}

{try_it("slow motion", "<p>In <code>on_update</code>, change <code>dt = min(delta_time, 1 / 20)</code> to <code>dt = min(delta_time, 1 / 20) * 0.3</code>. "
        "Play the game. What happens? Why does everything slow down together?</p>")}

{quiz([
    ("About how many frames are drawn each second?", "About 60."),
    ("Why do we multiply by <code>dt</code> when moving?", "So the speed is the same on fast and slow computers."),
    ("The game draws the ship after the rocks. What is the result if a ship and a rock overlap?", "The ship appears on top, because it was drawn last."),
    ("What is the job of <code>on_draw</code>? Should it change the ship's health?", "It only paints the picture. The rules (like changing health) belong in <code>on_update</code>."),
    ("What is an event? Give an example.", "Something that happens that the program can react to, such as a key press."),
])}
'''
    build_page("game-loop", "5. The game loop", body, "How the game runs, frame after frame.")


def physics():
    # gravity curves from the game's own settings
    G = D["physics"]["gravity"]
    soft = D["physics"]["softening"]
    cap = D["physics"]["max_accel"]
    W, H, L, B = 640, 300, 60, 40
    def pt(d, a):
        x = L + d / 600 * (W - L - 20)
        y = H - B - a / 340 * (H - B - 20)
        return f"{x:.1f},{y:.1f}"
    curves = []
    for mass, color, label in ((2.56, "#d6452e", "big rock (mass 2.56)"), (1.0, "#b86e00", "medium rock (mass 1)"), (0.36, "#2c9a52", "small rock (mass 0.36)")):
        pts = " ".join(pt(d, min(G * mass / (d * d + soft * soft), cap)) for d in range(0, 601, 10))
        curves.append(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="3"/>')
    legend = "".join(f'<rect x="{360}" y="{30 + i * 22}" width="14" height="14" fill="{c}"/><text x="380" y="{42 + i * 22}" font-size="13">{t}</text>'
                     for i, (c, t) in enumerate((("#d6452e", "big rock (mass 2.56)"), ("#b86e00", "medium rock (mass 1)"), ("#2c9a52", "small rock (mass 0.36)"))))
    ticks = "".join(f'<text x="{L + d / 600 * (W - L - 20):.0f}" y="{H - 18}" text-anchor="middle" font-size="12">{d}</text>' for d in range(0, 601, 100))
    yticks = "".join(f'<text x="{L - 8}" y="{H - B - a / 340 * (H - B - 20) + 4:.0f}" text-anchor="end" font-size="12">{a}</text>' for a in (0, 100, 200, 300))
    gsvg = (f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">'
            f'<line x1="{L}" y1="{H - B}" x2="{W - 10}" y2="{H - B}" stroke="#55607a" stroke-width="2"/><line x1="{L}" y1="{H - B}" x2="{L}" y2="10" stroke="#55607a" stroke-width="2"/>'
            f'{ticks}{yticks}{"".join(curves)}{legend}'
            f'<text x="{(L + W) / 2}" y="{H - 2}" text-anchor="middle" font-size="13">distance from the rock (pixels)</text>'
            f'<text x="14" y="{H / 2}" font-size="13" transform="rotate(-90 14 {H / 2})" text-anchor="middle">pull (pixels/second&#178;)</text></svg>')

    bearing = """<svg viewBox="0 0 520 260" xmlns="http://www.w3.org/2000/svg">
<defs><marker id="ar2" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto"><polygon points="0,0 10,4 0,8" fill="#d6452e"/></marker></defs>
<line x1="60" y1="220" x2="60" y2="20" stroke="#55607a" stroke-width="2"/><text x="68" y="30" font-size="13">up (0&#176;)</text>
<line x1="60" y1="220" x2="300" y2="220" stroke="#55607a" stroke-width="2"/>
<line x1="60" y1="220" x2="200" y2="80" stroke="#d6452e" stroke-width="4" marker-end="url(#ar2)"/>
<line x1="200" y1="80" x2="200" y2="220" stroke="#0f7a8a" stroke-width="2" stroke-dasharray="6"/><line x1="60" y1="80" x2="200" y2="80" stroke="#0f7a8a" stroke-width="2" stroke-dasharray="6"/>
<path d="M60 160 A60 60 0 0 1 102 178" fill="none" stroke="#b86e00" stroke-width="3"/><text x="105" y="165" font-size="14">bearing</text>
<text x="120" y="240" font-size="14">dx = sin(bearing)</text><text x="208" y="155" font-size="14">dy = cos(bearing)</text>
<text x="310" y="90" font-size="14">The ship faces this way.</text><text x="310" y="112" font-size="14">Moving 1 step forward moves it</text><text x="310" y="132" font-size="14">dx across and dy up.</text></svg>"""

    wrap = """<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg">
<rect x="40" y="30" width="560" height="100" fill="#e6f0ff" stroke="#17306b" stroke-width="3"/>
<circle cx="585" cy="80" r="14" fill="#d6452e"/><text x="585" y="115" text-anchor="middle" font-size="12">ship at x = 1265</text>
<circle cx="62" cy="80" r="14" fill="#2c9a52"/><text x="62" y="115" text-anchor="middle" font-size="12">rock at x = 15</text>
<path d="M600 60 Q 640 20 20 20" fill="none" stroke="#0f7a8a" stroke-width="3" stroke-dasharray="7"/>
<text x="320" y="16" text-anchor="middle" font-size="13">shortest way: only 30 pixels, across the edge</text>
<text x="320" y="152" text-anchor="middle" font-size="13">the long way across the screen: 1250 pixels</text></svg>"""

    body = f'''
{intentions(
    ["use speed, time and direction to move things",
     "understand how gravity is calculated from mass and distance",
     "understand wrap-around using the modulo operator",
     "check for collisions using distance"],
    ["explain <code>x = x + v * dt</code>",
     "say what happens to gravity when the distance doubles",
     "explain why the game uses <code>%</code> for wrap-around",
     "describe how two circles are tested for a collision"])}

<h2>1. Movement: position, speed and time</h2>
<p>Speed tells us how far something moves in one second. In one frame it moves <code>speed &times; dt</code>. The new position is the old position plus that move.
This is the same idea as <em>distance = speed &times; time</em> from science class.</p>

<h2>2. Direction: sine and cosine</h2>
<p>The ship has a <strong>bearing</strong>: the direction it faces, in degrees clockwise from straight up (like a compass). To move forward we need how far to go
<em>across</em> (<code>dx</code>) and <em>up</em> (<code>dy</code>). Trigonometry gives us the answer:</p>
{diagram(bearing, "A bearing split into sideways and upward parts.", "Diagram of a bearing with sine and cosine")}
<p>Python's <code>math.sin</code> and <code>math.cos</code> want angles in <strong>radians</strong>, so the code first converts with <code>math.radians</code>. Here is the part of the ship's update
that does the maths:</p>
{snippet("game/sprites.py", "Ship.update_ship",
         note="Find <code>math.sin(rad)</code> and <code>math.cos(rad)</code>. Then find where the gravity drift is added, and where <code>world.wrap(self)</code> keeps the ship on the map.")}

<h2>3. Gravity</h2>
<p>Isaac Newton found that the pull between two objects gets stronger with <strong>mass</strong> and weaker with <strong>distance</strong>. It gets weaker very quickly, with the <em>square</em> of the distance:</p>
<p style="text-align:center;font-size:1.3rem"><strong>pull = G &times; mass &divide; distance&#178;</strong></p>
<p>Double the distance and the pull is four times weaker. In the game, <code>G</code> is the setting <code>gravity</code>. Two safety tricks stop the pull from becoming silly:
a <strong>softening</strong> number added to the distance (so a ship right on top of a rock is not pulled with infinite force) and a <strong>cap</strong> (a maximum).</p>
{snippet("game/physics.py", "gravity_accel")}
{diagram(gsvg, "Pull from the game's real settings. Bigger rocks pull harder, and every curve drops quickly as you move away.", "Graph of gravity pull against distance for three rock sizes")}
<p>The ship's pull is the <em>sum</em> of the pull from every rock. Remember the loop on the Python basics page? This is where it is used:</p>
{snippet("game/game_view.py", "GameView._gravity_on")}
<p>The result changes the ship's <strong>drift</strong>, an extra velocity added on top of its steering. To stop the drift growing forever, a little of it is removed each frame, like friction:</p>
{snippet_between("game/sprites.py", "# Gravity changes the drift velocity", "self.drift_y *= damp", note="Multiplying by a number just below 1 each frame makes a value fade away smoothly.")}

<h2>4. Wrap-around: the modulo operator</h2>
<p>The map has no walls. Fly off the right side and you appear on the left. The trick is the <strong>modulo</strong> operator <code>%</code>, which gives the <em>remainder</em> after division.
If the world is 1280 wide, then <code>1290 % 1280</code> is <code>10</code>. The position wraps back to the start.</p>
{snippet("game/world.py", "World.wrap")}
<p>Wrapping creates a new problem. A ship at the far right and a rock at the far left are <em>really</em> close together, even though their numbers are far apart.
The <code>delta</code> method finds the <strong>shortest</strong> way, even if it goes across the edge:</p>
{diagram(wrap, "On a wrapped map, the shortest path can cross the edge.", "Ship and rock on opposite edges that are really close")}
{snippet("game/world.py", "World.delta")}
<p>If the gap is more than half the world, going the other way is shorter, so it takes away one world width. Every collision, every pull and every alien chase uses <code>delta</code>.</p>

<h2>5. Collisions: circles and Pythagoras</h2>
<p>The game treats most things as circles. Two circles touch when the distance between their centres is less than the two radii added together. The distance comes from <strong>Pythagoras' theorem</strong>
(<code>math.hypot</code> does it in one go):</p>
{snippet("game/game_view.py", "GameView._overlap")}
<p>When two rocks collide and "split when rocks collide" is off, they bounce. The bounce uses <strong>mass</strong>: a heavy rock changes a light rock's direction more than the other way round.</p>
{snippet("game/game_view.py", "GameView._rock_rock_collisions", first=11, last=30,
         note="<code>(nx, ny)</code> is the direction from one rock to the other. <code>rel</code> says whether they are moving together. The last lines share the push according to mass.")}

<h2>6. Steering a missile</h2>
<p>The homing missile turns toward its target, but only a little each frame, so it curves. The clever line is the one that finds the <em>shortest turn</em> (left or right) between two angles:</p>
{snippet("game/weapons.py", "Bullet._steer", first=13, last=19)}
<p><code>(wanted - heading + &pi;) % (2&pi;) - &pi;</code> always gives an answer between &minus;180&deg; and +180&deg;. Positive means turn one way, negative the other.</p>

{try_it("test the physics", """<ol><li>In the Game Editor, set <em>Gravity strength</em> to 0. Fly close to a rock. What changes?</li>
<li>Set <em>Drift damping</em> to 0. What happens after you are pulled by a rock? Why?</li>
<li>Fly off the right edge. Where do you come out? Which function made that happen?</li></ol>""")}

{quiz([
    ("A ship moves at 300 pixels per second. How far does it move in one frame at 60 frames per second?", "300 &divide; 60 = 5 pixels."),
    ("A rock pulls with strength 80 at 100 pixels. How strong is the pull at 200 pixels?", "Double the distance gives one quarter of the pull: 20."),
    ("What is <code>1290 % 1280</code>?", "10."),
    ("Why is <code>World.delta</code> needed as well as <code>World.wrap</code>?", "Wrap moves things back onto the map. Delta works out the true shortest distance between two things, even across the edge."),
    ("Two circles have radii 20 and 30. The centres are 45 apart. Do they touch?", "Yes: 20 + 30 = 50, and 45 is less than 50."),
])}
'''
    build_page("physics", "6. Physics", body, "Movement, gravity, wrap-around and collisions, in real code.")


def levels_and_world():
    d = D
    ex = ("drifter", "chaser", "sniper", "swarm", "seeker", "teleporter", "minelayer")
    rows = []
    for L in range(1, 11):
        ws = min(d["world"]["max_scale"], 1 + d["world"]["growth_per_level"] * (L - 1))
        rocks = round((d["rocks"]["count"] + d["difficulty"]["extra_rocks_per_level"] * (L - 1)) * ws)
        speed = 1 + d["difficulty"]["speed_per_level"] * (L - 1)
        grav = 1 + d["difficulty"]["gravity_per_level"] * (L - 1)
        aliens = []
        for k in ex:
            c = d["aliens"][k]
            if L >= c["min_level"]:
                n = max(1, round((1 + (L - c["min_level"]) // 3) * ws))
                aliens.append(f"{k.title()} &times;{n}" + (f" (groups of {c['group_size']})" if k == "swarm" else ""))
        boss = L >= d["aliens"]["mothership"]["min_level"] and L % d["aliens"]["mothership"]["boss_every"] == 0
        if boss:
            aliens.append("<strong>Mothership</strong>")
        hz = [name for name, key in (("Nebula", "nebula_from"), ("Black hole", "blackhole_from"),
                                    ("Ion storm", "ion_from"), ("Solar flare", "flare_from")) if L >= d["hazards"][key]]
        obj = "Destroy the mothership" if boss else ("None" if L == 1 else
              ("Collect crystals", "Rescue pods", "Escort the freighter")[(L - 2) % 3])
        rows.append([f"<strong>{L}</strong>", f"&times;{ws:.2f}", rocks, f"&times;{speed:.2f}", f"&times;{grav:.1f}",
                     ", ".join(aliens), ", ".join(hz) or "None", obj])
    tbl = table(["Level", "Map size", "Rocks", "Rock speed", "Gravity", "Aliens", "Hazards", "Objective"], rows)

    zoom_snip = snippet_between("game/game_view.py", "self.zoom += (self.zoom_target", "world.zoom_speed")
    body = f'''
{intentions(
    ["see how a level is built from rules and numbers",
     "understand how the game gets harder as levels go up",
     "understand how a bigger map is created and how the camera zooms out",
     "read a formula in code"],
    ["explain how many rocks a level has",
     "explain the job of the wormhole",
     "predict the map size for any level"])}

<h2>The goal of a level</h2>
<p>In every level the aim is the same: <strong>survive, finish the objective, then fly into the wormhole</strong>. A wormhole appears at a random time and stays open for a few seconds.
In <em>Expedition</em> mode it will not open until the objective is done. On every fifth level, a boss ship called the Mothership must be destroyed first.</p>

<h2>Building a level</h2>
<p>When a level starts, one method builds everything. Read it from top to bottom. It is a long list of steps, which is a great example of <strong>sequence</strong>.</p>
{snippet("game/game_view.py", "GameView._start_level", first=1, last=39)}
<p>Notice how the level number appears in formulas. Here is the rule for the <strong>size of the map</strong>:</p>
<pre class="inline"><code>world_scale = min(max_scale, 1.0 + growth_per_level * (level - 1))</code></pre>
<p>With the default settings (growth 0.25, maximum 3.0), level 1 is 1.0, level 2 is 1.25, level 3 is 1.5, and so on, until it stops at 3.0 (level 9). <code>min</code> picks the smaller of the two numbers so the map never grows past the limit.</p>

<h2>Difficulty goes up with the level</h2>
<p>Three small numbers make later levels harder. For each level above 1, rocks are 8% faster and gravity is 10% stronger. There are more rocks, and later levels bring new aliens and hazards.</p>
{tbl}
<p>This table was <em>generated from the game's own settings</em> by a Python script, so it always matches the real rules.</p>

<h2>Zooming out: the camera</h2>
<p>A bigger map would not fit on your screen, so the camera <strong>zooms out</strong>. At map size 2.0, the zoom is 1 &divide; 2.0 = 0.5, so everything looks half as big. The change is smooth, not sudden. Each frame the zoom moves a small part of the way to the target:</p>
{zoom_snip}
<p>This is a classic trick called <strong>easing</strong>: <code>value += (target - value) * small_number</code>.</p>

<h2>Finishing a level</h2>
<p>When a ship touches an open wormhole, <em>both</em> players move on. The code adds points and credits, raises the level number, saves your credits and builds the next level:</p>
{snippet("game/game_view.py", "GameView._complete_level")}
{symbol_link("game/game_view.py", "GameView._spawn_aliens", "See _spawn_aliens in the full file")}

{try_it("design a level", """<p>Pick level 6 in the table. How many rocks are there? Which aliens appear? Now open <code>game/config.py</code> and find the numbers
<code>"growth_per_level"</code> and <code>"extra_rocks_per_level"</code>. Change them, run the game and see if you were right.</p>""")}

{quiz([
    ("What is the map size at level 5 with default settings?", "1.0 + 0.25 &times; 4 = 2.0 times the screen."),
    ("What does <code>min(3.0, 4.5)</code> return?", "3.0, the smaller value."),
    ("Why must the camera zoom out when the map gets bigger?", "The bigger map would not fit on the screen otherwise."),
    ("Which part of <code>_start_level</code> would you change to add more rocks per level?", "The lines that work out <code>target_rocks</code>, or the <code>extra_rocks_per_level</code> setting."),
    ("What must happen on boss levels before a wormhole opens?", "The Mothership must be destroyed."),
])}
'''
    build_page("levels-and-world", "7. Levels and the world", body, "How levels are built and how the game gets harder.")


def build():
    inheritance()
    game_loop()
    physics()
    levels_and_world()
