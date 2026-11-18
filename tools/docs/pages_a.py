"""Pages: start here, Python basics, memory and data, classes and objects."""
from lib import (box, build_page, diagram, file_link, intentions, quiz, snippet, snippet_between,
                 symbol_link, table, try_it)


def index():
    cards = [
        ("python-basics", "1. Python basics", "Variables, if-statements and loops, using real game code."),
        ("memory-and-data", "2. Memory and data", "Lists, dictionaries and how Python stores things."),
        ("classes-and-objects", "3. Classes and objects", "Blueprints for ships, rocks and players."),
        ("inheritance", "4. Inheritance and design", "How one class builds on another."),
        ("game-loop", "5. The game loop", "How a game runs 60 times every second."),
        ("physics", "6. Physics", "Movement, gravity, wrap-around and collisions."),
        ("levels-and-world", "7. Levels and the world", "How the game gets harder."),
        ("ships", "8. Ships and credits", "Abilities, the shop and the rules behind them."),
        ("aliens", "9. Alien AI", "Seven kinds of enemy, each with its own brain."),
        ("rocks-hazards-rules", "10. Rocks, hazards, rules", "Everything that can hurt you, and how scoring works."),
        ("going-further", "11. Going further", "Multiplayer and ideas to extend the game."),
        ("web-development", "12. Web development", "How this website works, and a project to build your own."),
        ("tutorial-steps", "13. Rebuild it: prompts", "16 short prompts to build the game step by step."),
    ]
    cards_html = '<div class="cards">' + "".join(
        f'<div class="card"><h3><a href="{s}.html">{t}</a></h3><p>{d}</p></div>' for s, t, d in cards) + "</div>"
    body = f'''
<p>Nau mai, haere mai! This site teaches the basics of <strong>Python</strong> by taking apart a real
space game called <em>Wormhole Runner</em>. You fly a ship, dodge rocks that pull on you with gravity,
fight aliens, and escape through wormholes. Every idea on these pages is something you can find in the game's code.</p>
{intentions(
    ["see how a real program is built from small, simple parts",
     "learn selection (<code>if</code>), iteration (loops), variables and data structures",
     "learn how classes and objects are used to design a program",
     "link the code to ideas in maths and physics",
     "connect programming to web development: this site is itself a web project"],
    ["read a short piece of Python and explain what it does",
     "change a number in the game's settings and predict what will happen",
     "draw a class diagram for a part of the game",
     "write a prompt that asks an AI helper for one feature, then test the result"])}
<h2>How to use these pages</h2>
<ol>
<li><strong>Get the game running first.</strong> Follow the steps on the <a href="teachers.html">Teacher notes</a> page
(install Python, then run the launcher file for your computer).</li>
<li><strong>Read a page, then open the code.</strong> Each code box shows real code from the game. The
<em>View on GitHub</em> link opens the same lines in the full file.</li>
<li><strong>Try the "Try it" boxes.</strong> They ask you to change a setting or a line and see what happens.</li>
<li><strong>Check your understanding.</strong> Click each question to reveal the answer after you have had a go.</li>
</ol>
{box("tip", "Tip: how to read code",
     "<p>Do not try to understand every line at once. First read the <em>names</em> (like <code>health</code> or <code>speed</code>). "
     "Good programmers choose names that explain themselves. Then read the comments. Then work out the steps one at a time.</p>")}
<h2>Pages</h2>
{cards_html}
<h2>What you need</h2>
<ul>
<li>A computer with <strong>Python 3.10 or newer</strong> (Windows, Linux or Mac).</li>
<li>The game files. Use <code>run_windows.bat</code> or <code>run_linux.sh</code> to start it.</li>
<li>A text editor such as Visual Studio Code, Thonny or IDLE.</li>
</ul>
<p>Two players on the same network can fly together. Only play with people you know, on your school or home network.</p>
'''
    build_page("index", "Wormhole Runner: learn Python by exploring a game", body,
               "A guide for ākonga (learners) in Years 9 and 10.")


def python_basics():
    body = f'''
{intentions(
    ["understand variables and different kinds of data",
     "use <code>if</code>, <code>elif</code> and <code>else</code> to make decisions",
     "use <code>for</code> and <code>while</code> loops to repeat things",
     "write and use functions"],
    ["explain what a variable is using an example from the game",
     "read an <code>if</code> statement and say when each branch runs",
     "say how many times a <code>for</code> loop will run",
     "explain why a function is useful"])}

<h2>Programs are instructions</h2>
<p>A program is a list of instructions the computer follows <strong>in order</strong>. This is called <strong>sequence</strong>.
There are two other big ideas: <strong>selection</strong> (making a choice) and <strong>iteration</strong> (repeating).
Every program you will ever meet is built from these three ideas.</p>

<h2>Variables: labelled boxes</h2>
<p>A <strong>variable</strong> is a name that points to a value. In the game the ship has a health value.
When it is hit, the health goes down:</p>
<pre class="inline"><code>health = 100        # make a variable
health = health - 25   # use it, then store the new answer
</code></pre>
<p>Python has several kinds of data (called <strong>types</strong>):</p>
{table(["Type", "What it holds", "Example from the game"],
       [["<code>int</code>", "whole numbers", "<code>count = 6</code> (rocks at the start)"],
        ["<code>float</code>", "numbers with decimals", "<code>speed = 420.0</code>"],
        ["<code>str</code>", "text (a string)", "<code>name = \"Phantom\"</code>"],
        ["<code>bool</code>", "<code>True</code> or <code>False</code>", "<code>enabled = True</code>"]])}

<h2>Selection: <code>if</code>, <code>elif</code>, <code>else</code></h2>
<p>A <strong>conditional statement</strong> lets the program choose. The ship's steering code asks four yes/no questions:
"Is the left key down? Is the right key down?" and so on.</p>
{snippet("game/sprites.py", "control_step",
         note="Each <code>if</code> only runs its indented lines when the condition is <code>True</code>. The last two lines use "
              "<code>max</code> and <code>min</code> to keep the speed between 0 and the top speed.")}
<p>Look at this line: <code>boost = cfg("ship.boost_multiplier") if boosted else 1.0</code>. It is a short way to write
"if boosted is true, use the boost number, otherwise use 1.0". This is called a <strong>conditional expression</strong>.</p>
{box("tip", "Comparing values",
     "<p>Use <code>==</code> to ask <em>are these equal?</em>, <code>!=</code> for <em>not equal</em>, and <code>&lt;</code>, "
     "<code>&gt;</code>, <code>&lt;=</code>, <code>&gt;=</code> for sizes. Join conditions with <code>and</code>, <code>or</code> and "
     "<code>not</code>. A single <code>=</code> is different: it <em>stores</em> a value.</p>")}

<h3>Decisions inside decisions</h3>
<p>You can put an <code>if</code> inside another <code>if</code>. This is called <strong>nesting</strong>. Here the game replaces
rocks that have been destroyed, but only if there are too few rocks <em>and</em> the timer has run out:</p>
{snippet("game/game_view.py", "GameView._update_respawns")}

<h2>Iteration: loops</h2>
<h3>The <code>for</code> loop: repeat for each item</h3>
<p>Every rock pulls on your ship with gravity. The game adds up the pull from <em>each</em> rock using a <code>for</code> loop:</p>
{snippet("game/game_view.py", "GameView._gravity_on",
         note="The loop runs once for every rock in <code>self.rock_list</code>. With 12 rocks, the lines inside run 12 times.")}
<p>You can also loop a set number of times with <code>range</code>. <code>for _ in range(5):</code> repeats five times.
(The underscore <code>_</code> means "I don't need the counter".) Loops can be <strong>nested</strong> (a loop inside a loop).
The code that creates aliens does this: one loop for each kind of alien, and another loop for how many of that kind.</p>
{snippet("game/game_view.py", "GameView._spawn_aliens", first=1, last=19)}
<p><code>continue</code> means "skip the rest of this go and start the next one". <code>break</code> means "stop the loop now".</p>

<h3>The <code>while</code> loop: repeat until something changes</h3>
<p>A <code>while</code> loop keeps going as long as its condition is <code>True</code>. When two computers play together, a helper keeps
listening for messages for as long as the connection is alive:</p>
{snippet("game/net.py", "Connection._reader",
         note="<code>while self.alive:</code> repeats until the connection closes. <code>try</code>/<code>except</code> catches errors so the program does not crash.")}
{box("warn", "Careful: endless loops",
     "<p>If a <code>while</code> condition never becomes <code>False</code>, the loop never ends and your program freezes. "
     "Always make sure something inside the loop changes the condition.</p>")}

<h2>Functions: reusable recipes</h2>
<p>A <strong>function</strong> is a named block of code you can use again and again. It can take <strong>parameters</strong>
(inputs) and <strong>return</strong> a result. The gravity rule is a small function that works out how hard one rock pulls:</p>
{snippet("game/physics.py", "gravity_accel")}
<p>The names in the brackets are the inputs. The <code>return</code> line sends two answers back. Because it is a function,
the game can use the same rule for rocks, for black holes and for anything else that pulls.</p>

{try_it("change a number", "<p>Find <code>\"gravity\": 600000.0</code> in <code>game/config.py</code> (or use the in-game Game Editor). "
        "Make it much bigger, then play. What happens to your ship near a rock? Now make it 0. Why does the ship stop being pulled?</p>")}

{quiz([
    ("What are the three big ideas every program is built from?", "Sequence (steps in order), selection (choices with <code>if</code>) and iteration (repeating with loops)."),
    ("In <code>control_step</code>, what happens if <code>up</code> is <code>False</code>?", "The lines inside <code>if up:</code> are skipped, so the speed does not increase."),
    ("A <code>for</code> loop goes over 12 rocks. How many times do the lines inside it run?", "12 times, once per rock."),
    ("Why does <code>gravity_accel</code> use a function instead of copying the code each time?", "A function can be reused. If the rule needs fixing, you fix it in one place."),
    ("What is the difference between <code>=</code> and <code>==</code>?", "<code>=</code> stores a value in a variable. <code>==</code> asks whether two values are equal."),
])}
'''
    build_page("python-basics", "1. Python basics", body,
               "Variables, decisions and loops, using code from the real game.")


def memory_and_data():
    body = f'''
{intentions(
    ["see how Python stores values in memory",
     "use lists, dictionaries, tuples and sets",
     "understand that two names can point to the same object",
     "understand the difference between a copy and a reference"],
    ["choose the right data structure for a job",
     "draw a memory diagram for a list and a dictionary",
     "explain what happens when two variables share one list"])}

<h2>Memory is a giant set of boxes</h2>
<p>When a program runs, Python keeps its data in the computer's <strong>memory</strong> (RAM). Think of a variable as a
<em>name tag</em> attached to a box that holds the value. If you write <code>health = 100</code>, the name <code>health</code>
is attached to a box containing 100.</p>

{diagram("""<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg">
<rect x="20" y="40" width="130" height="50" rx="8" fill="#17306b"/><text class="lt" x="85" y="70" text-anchor="middle" font-size="18">health</text>
<line x1="150" y1="65" x2="240" y2="65" stroke="#0f7a8a" stroke-width="3"/><polygon points="240,65 228,58 228,72" fill="#0f7a8a"/>
<rect x="240" y="40" width="110" height="50" rx="8" fill="#ffd479" stroke="#b86e00" stroke-width="2"/><text x="295" y="72" text-anchor="middle" font-size="22">100</text>
<text x="20" y="130" font-size="15">name (variable)</text><text x="225" y="130" font-size="15">value in memory</text>
<rect x="420" y="40" width="130" height="50" rx="8" fill="#17306b"/><text class="lt" x="485" y="70" text-anchor="middle" font-size="18">speed</text>
<line x1="550" y1="65" x2="590" y2="65" stroke="#0f7a8a" stroke-width="3"/><polygon points="610,65 598,58 598,72" fill="#0f7a8a"/>
<rect x="580" y="110" width="0" height="0"/><text x="440" y="130" font-size="15">another name, another box</text></svg>""",
"A variable is a name that points to a value stored in memory.", "A variable name pointing to a value")}

<h2>Lists: an ordered row of boxes</h2>
<p>A <strong>list</strong> keeps many values in order. Items have a position number called an <strong>index</strong>, starting at 0.
The game keeps its players in a list:</p>
<pre class="inline"><code>players = ["Pilot", "Medi"]
print(players[0])      # Pilot  (index 0 is the first item)
players.append("Kai")  # add to the end
print(len(players))    # 3
</code></pre>
{snippet_between("game/game_view.py", "self.local = Player(1", "self.players = [self.local]",
                 note="A list holds the local player. When a friend joins, the game uses <code>self.players.append(...)</code> to add them.")}
<p>Arcade, the game library we use, gives us a special <code>SpriteList</code> that works like a list but is much faster to draw.
That is why the game has <code>rock_list</code>, <code>alien_list</code> and <code>bullet_list</code>.</p>

<h2>Dictionaries: look things up by name</h2>
<p>A <strong>dictionary</strong> stores <strong>key: value</strong> pairs. Instead of remembering that "gravity" is item number 4,
you just ask for <code>"gravity"</code>. All of the game's settings live in one big dictionary, with dictionaries inside it:</p>
{snippet_between("game/config.py", '"physics": {', '},')}
<p>A dictionary inside a dictionary is called <strong>nested</strong>. The class below finds a value using a dotted name such as
<code>"physics.gravity"</code>. It splits the name at the dots and steps down one level at a time:</p>
{snippet("game/config.py", "Config.get")}
{snippet("game/config.py", "Config._walk")}
{diagram("""<svg viewBox="0 0 680 210" xmlns="http://www.w3.org/2000/svg">
<rect x="10" y="10" width="190" height="190" rx="10" fill="#e6f0ff" stroke="#17306b" stroke-width="2"/>
<text x="105" y="34" text-anchor="middle" font-size="15" font-weight="bold">data (dictionary)</text>
<rect x="25" y="48" width="160" height="40" rx="6" fill="#fff" stroke="#17306b"/><text x="35" y="74" font-size="14">"physics"  &#8594;</text>
<rect x="25" y="98" width="160" height="40" rx="6" fill="#fff" stroke="#17306b"/><text x="35" y="124" font-size="14">"ship"  &#8594;</text>
<rect x="25" y="148" width="160" height="40" rx="6" fill="#fff" stroke="#17306b"/><text x="35" y="174" font-size="14">"rocks"  &#8594;</text>
<line x1="185" y1="68" x2="270" y2="68" stroke="#0f7a8a" stroke-width="3"/>
<rect x="270" y="30" width="250" height="110" rx="10" fill="#e6f8ec" stroke="#2c9a52" stroke-width="2"/>
<text x="395" y="52" text-anchor="middle" font-size="15" font-weight="bold">physics (dictionary)</text>
<text x="285" y="82" font-size="14">"gravity"  :  600000.0</text><text x="285" y="106" font-size="14">"max_accel"  :  320.0</text><text x="285" y="130" font-size="14">"softening"  :  50.0</text>
<text x="545" y="86" font-size="14">get("physics.gravity")</text><text x="545" y="106" font-size="14">&#8594; 600000.0</text></svg>""",
"A dictionary inside a dictionary. The dotted name steps into the inner dictionary.", "Nested dictionaries holding the physics settings")}
<p>Dictionaries are also how settings are saved to a file. The text format is called <strong>JSON</strong>, and Python can turn a dictionary into JSON and back again.</p>

<h2>Tuples and sets</h2>
<ul>
<li>A <strong>tuple</strong> is like a list that <em>cannot be changed</em> once made. It is written with round brackets. Colours are tuples:
red, green, blue, opacity.</li>
<li>A <strong>set</strong> holds unique items with no order and no repeats. It is perfect for "which keys are held down right now?"</li>
</ul>
{snippet_between("game/player.py", "TINTS =", "TINTS =", note="A dictionary whose values are tuples (or <code>None</code>). Player 2's ship is tinted green.")}

<h2>Mutable or not?</h2>
<p>Some things can be changed after they are made (<strong>mutable</strong>): lists, dictionaries, sets. Others cannot
(<strong>immutable</strong>): numbers, strings, tuples. When you "change" a number, Python really makes a new one and moves the name tag.</p>

<h2>Two names, one object: references</h2>
<p>This idea catches out many programmers. If you write <code>b = a</code> for a list, you do <strong>not</strong> get a second list.
You get a second <em>name tag on the same box</em>. Change the list through one name and the other name sees the change.</p>
{diagram("""<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg">
<rect x="20" y="30" width="120" height="44" rx="8" fill="#17306b"/><text class="lt" x="80" y="58" text-anchor="middle" font-size="16">a</text>
<rect x="20" y="110" width="120" height="44" rx="8" fill="#17306b"/><text class="lt" x="80" y="138" text-anchor="middle" font-size="16">b</text>
<line x1="140" y1="52" x2="300" y2="85" stroke="#0f7a8a" stroke-width="3"/><line x1="140" y1="132" x2="300" y2="100" stroke="#0f7a8a" stroke-width="3"/>
<rect x="300" y="55" width="300" height="70" rx="10" fill="#ffd479" stroke="#b86e00" stroke-width="2"/>
<text x="450" y="82" text-anchor="middle" font-size="15" font-weight="bold">one list</text><text x="450" y="108" text-anchor="middle" font-size="16">[ 1, 2, 3 ]</text></svg>""",
"After <code>b = a</code> both names point to the same list.", "Two variable names pointing at one list")}
<p>The game uses this on purpose. The window's key-press set is <em>shared</em> with the local player, so when the window records a key,
the player sees it straight away:</p>
{snippet_between("game/game_view.py", "self.local.keys = self.keys", "self.local.keys = self.keys")}
<p>If you need a real, separate copy, ask for one. When an alien is created it copies its settings dictionary first, so changing one
alien's numbers does not change the settings for all aliens:</p>
{snippet_between("game/aliens.py", "cfg = dict(settings.get", "cfg.update(overrides or {})")}

{try_it("make a copy", """<p>Open Python (or Thonny) and type:</p><pre class="inline"><code>a = [1, 2, 3]
b = a
b.append(4)
print(a)
c = list(a)      # a real copy
c.append(5)
print(a, c)</code></pre><p>Predict the output of both <code>print</code> lines before you run it.</p>""")}

{quiz([
    ("Which data structure would you use to store a player's name, score and ship type together, and look each one up by name?", "A dictionary, for example <code>{\"name\": \"Medi\", \"score\": 120, \"ship\": \"medic\"}</code>."),
    ("<code>players = [\"Pilot\", \"Medi\"]</code>. What is <code>players[1]</code>?", "<code>\"Medi\"</code>. Indexes start at 0."),
    ("Why is a set a good choice for the keys that are held down?", "A key is either held or not, never twice, and order does not matter."),
    ("After <code>b = a</code> where <code>a</code> is a list, you add an item to <code>b</code>. Does <code>a</code> change?", "Yes. Both names point at the same list."),
    ("How do you make a separate copy of a dictionary?", "Use <code>dict(original)</code> or <code>original.copy()</code>."),
])}
'''
    build_page("memory-and-data", "2. Memory and data", body,
               "How Python stores information, and which container to choose.")


def classes_and_objects():
    body = f'''
{intentions(
    ["understand the difference between a class and an object",
     "use attributes and methods",
     "see how <code>__init__</code> and <code>self</code> work",
     "read the <code>Player</code>, <code>Rock</code> and <code>Ship</code> classes"],
    ["explain a class using a real-life blueprint",
     "name the attributes and methods of a class in the game",
     "write a small class of my own"])}

<h2>The blueprint idea</h2>
<p>A <strong>class</strong> is a blueprint. An <strong>object</strong> is one thing built from the blueprint. The game has a
<code>Rock</code> class (the blueprint) and many rock objects floating around, each with its own position, size and speed.</p>
{diagram("""<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg">
<rect x="20" y="20" width="200" height="160" rx="10" fill="#e6f0ff" stroke="#17306b" stroke-width="2"/>
<text x="120" y="48" text-anchor="middle" font-size="18" font-weight="bold">class Rock</text>
<text x="35" y="78" font-size="14">attributes:</text><text x="45" y="98" font-size="14">size_class, vx, vy, hp</text>
<text x="35" y="128" font-size="14">methods:</text><text x="45" y="148" font-size="14">update_rock(), split()</text>
<line x1="220" y1="100" x2="300" y2="50" stroke="#0f7a8a" stroke-width="2"/><line x1="220" y1="100" x2="300" y2="100" stroke="#0f7a8a" stroke-width="2"/><line x1="220" y1="100" x2="300" y2="150" stroke="#0f7a8a" stroke-width="2"/>
<rect x="300" y="25" width="170" height="50" rx="8" fill="#fff" stroke="#17306b"/><text x="310" y="47" font-size="13">rock1: size 3, normal</text><text x="310" y="65" font-size="13">vx 60, vy -60</text>
<rect x="300" y="78" width="170" height="50" rx="8" fill="#fff" stroke="#17306b"/><text x="310" y="100" font-size="13">rock2: size 1, ice</text><text x="310" y="118" font-size="13">vx -80, vy 80</text>
<rect x="300" y="131" width="170" height="50" rx="8" fill="#fff" stroke="#17306b"/><text x="310" y="153" font-size="13">rock3: size 2, gold</text><text x="310" y="171" font-size="13">vx 30, vy 30</text>
<text x="490" y="105" font-size="15">&#8592; objects (instances)</text></svg>""",
"One class, many objects. Each object keeps its own values.", "A Rock class and three Rock objects")}

<h2>Parts of a class</h2>
<ul>
<li><strong>Attributes</strong> are variables that belong to an object (its data).</li>
<li><strong>Methods</strong> are functions that belong to an object (what it can do).</li>
<li><code>__init__</code> is the special method that runs when an object is made. It sets up the starting values. We call it the <strong>constructor</strong>.</li>
<li><code>self</code> means "this particular object". Inside a method, <code>self.health</code> is <em>this</em> object's health.</li>
</ul>

<h2>A small class: <code>Player</code></h2>
<p>A player owns a ship, a set of weapons, a score and some credits. Read the code and find the attributes:</p>
{snippet("game/player.py", "Player")}
<p>The attributes are made inside <code>__init__</code> and <code>reset</code>. The method <code>reset</code> builds a fresh ship and score for a
new game. The method <code>revive</code> brings a player back to life at half health.</p>
{box("tip", "Creating an object",
     "<p>You make an object by <em>calling the class like a function</em>: <code>me = Player(1, \"Pilot\")</code>. "
     "Python runs <code>__init__</code> for you. Then <code>me.score</code> reads an attribute and <code>me.revive()</code> runs a method.</p>")}

<h2>Another class: <code>Rock</code></h2>
{snippet("game/sprites.py", "Rock",
         note="A rock has a <em>kind</em> (normal, ice, explosive, gold or metal). The kind decides its colour tint and how many hits it takes. "
              "The method <code>split</code> makes smaller rocks when it breaks.")}
<p>Notice <code>self.mass = ROCK_SIZE_SCALE[size_class] ** 2</code>. Bigger rocks have more <strong>mass</strong>, so they pull harder
with gravity. A rule from physics is stored as one line in a class.</p>

<h2>Properties: attributes that are worked out</h2>
<p>Sometimes an attribute is not stored but <em>calculated</em> when asked. The ship has yes/no properties such as <code>cloaked</code>:</p>
{snippet_between("game/sprites.py", "def _on(self, kind):", "healing = property")}
<p><code>self.cloaked</code> looks like a normal attribute, but it checks "is the ability a cloak, and is it still active?" every time.</p>

<h2>Why use classes?</h2>
<ul>
<li><strong>Keeps related data and actions together.</strong> A ship's health, speed and steering live in one place.</li>
<li><strong>Makes copies easy.</strong> Make one ship or a hundred rocks with the same blueprint.</li>
<li><strong>Makes changes safer.</strong> To change how rocks split, you only edit <code>Rock.split</code>.</li>
</ul>

{try_it("write your own class", """<p>Write a tiny class in Python and make two objects from it:</p><pre class="inline"><code>class Alien:
    def __init__(self, name, health):
        self.name = name
        self.health = health

    def hit(self, damage):
        self.health = self.health - damage
        if self.health &lt;= 0:
            print(self.name, "was destroyed!")

a = Alien("Zog", 30)
b = Alien("Blip", 10)
a.hit(15)
b.hit(15)</code></pre><p>What prints? Which object has changed health? Add an <code>is_alive</code> method that returns <code>True</code> or <code>False</code>.</p>""")}

{quiz([
    ("What is the difference between a class and an object?", "A class is the blueprint. An object is one thing made from it, with its own values."),
    ("What does <code>self</code> mean inside a method?", "The object that the method is running on."),
    ("Name two attributes of a <code>Rock</code>.", "For example <code>size_class</code>, <code>vx</code>, <code>vy</code>, <code>hp</code>, <code>mass</code>, <code>kind</code>."),
    ("When does <code>__init__</code> run?", "Automatically, when a new object is created."),
    ("Why does a bigger rock pull harder?", "Its <code>mass</code> is larger, and the gravity rule multiplies by mass."),
])}
'''
    build_page("classes-and-objects", "3. Classes and objects", body,
               "Blueprints for the things in the game.")


def build():
    index()
    python_basics()
    memory_and_data()
    classes_and_objects()
