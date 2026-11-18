"""Pages: web development, tutorial prompts, glossary, teacher notes."""
from lib import (box, build_page, diagram, file_link, intentions, prompt, quiz, snippet, snippet_between,
                 symbol_link, table, try_it)


def web_development():
    body = f'''
{intentions(
    ["see that a website is made from HTML, CSS and JavaScript",
     "read real HTML, CSS and JavaScript from this site",
     "see how Python can <em>write</em> web pages",
     "follow a simple design process for a digital outcome",
     "publish a static website"],
    ["name the job of HTML, CSS and JavaScript",
     "make a small web page with headings, links, a list and a table",
     "explain what makes a page accessible",
     "describe how I would test and improve my page"])}

<h2>You are reading a web project</h2>
<p>This learning site is a <strong>static website</strong>: a folder of files that a browser just opens. No database and no server program. That makes it easy to host for free on GitHub Pages.
A website is built from three languages that work as a team:</p>
{table(["Language", "Job", "Like a&hellip;"],
       [["<strong>HTML</strong>", "the structure and the content: headings, paragraphs, links, tables", "the skeleton and the words of a magazine page"],
        ["<strong>CSS</strong>", "the look: colours, fonts, spacing, layout", "the design and the paint"],
        ["<strong>JavaScript</strong>", "the behaviour: buttons that do things", "the electricity that makes things move"]])}

<h2>HTML: structure</h2>
<p>HTML is written with <strong>tags</strong> in angle brackets, such as <code>&lt;h1&gt;</code>. Most tags come in pairs. Tags can have <strong>attributes</strong>, such as <code>href</code> on a link.
Here is the top part of this site's first page:</p>
{snippet_between("docs/index.html", "<!DOCTYPE html>", "</head>")}
<ul>
<li><code>&lt;meta name="viewport"&gt;</code> makes the page fit a phone screen.</li>
<li><code>&lt;link rel="stylesheet"&gt;</code> loads the CSS file. <code>&lt;script&gt;</code> loads JavaScript.</li>
<li><code>lang="en-NZ"</code> tells screen readers which language to use.</li>
</ul>
<p>Good HTML uses <strong>semantic</strong> tags that say what each part <em>is</em>: <code>&lt;header&gt;</code>, <code>&lt;nav&gt;</code>, <code>&lt;main&gt;</code>, <code>&lt;footer&gt;</code>, <code>&lt;h1&gt;</code>&ndash;<code>&lt;h6&gt;</code>, <code>&lt;ul&gt;</code>, <code>&lt;table&gt;</code>.
Screen readers and search engines rely on them.</p>
<h3>Links: relative and absolute</h3>
<p>A link such as <code>href="physics.html"</code> is <strong>relative</strong>: it means "the file called physics.html in the same folder". Relative links keep working when the whole site is moved to a different address. A link such as
<code>https://github.com/...</code> is <strong>absolute</strong>.</p>

<h2>CSS: style</h2>
<p>CSS is a list of <strong>rules</strong>. Each rule has a <strong>selector</strong> (what to style) and <strong>properties</strong> (how). Here are the real rules for the coloured boxes on these pages:</p>
{snippet_between("docs/assets/style.css", "/* start:boxes */", "/* end:boxes */")}
<p>The <code>:root</code> block at the top of the file defines <strong>variables</strong> such as <code>--learn</code>, so colours can be changed in one place. The file also has a rule that swaps to dark colours if the person's device is set to dark mode.
And a <strong>media query</strong> that rearranges the page on a narrow phone screen. This is called <strong>responsive design</strong>.</p>
{snippet_between("docs/assets/style.css", "/* start:buttons */", "/* end:buttons */")}

<h2>JavaScript: behaviour</h2>
<p>JavaScript runs in the browser. This site uses a few lines to set the GitHub links. Compare it with the Python you have learned. The ideas (variables, <code>if</code>, loops, functions) are the same, only the spelling changes.</p>
{snippet_between("docs/assets/app.js", "function fixLinks", "function copyButtons", include_end=False)}
{table(["Idea", "Python", "JavaScript"],
       [["variable", "<code>score = 10</code>", "<code>let score = 10;</code>"],
        ["decision", "<code>if x &gt; 5:</code>", "<code>if (x &gt; 5) { ... }</code>"],
        ["loop", "<code>for item in items:</code>", "<code>for (const item of items) { ... }</code>"],
        ["function", "<code>def hit(d):</code>", "<code>function hit(d) { ... }</code>"],
        ["list", "<code>[1, 2, 3]</code>", "<code>[1, 2, 3]</code>"],
        ["dictionary", '<code>{"a": 1}</code>', "<code>{ a: 1 }</code> (an object)"]])}

<h2>Python writes this website</h2>
<p>These pages were not typed by hand. A Python program in <code>tools/build_docs.py</code> builds them. It reads the game's real source code, cuts out the snippets, makes the tables from the game's settings
and writes out the HTML files. That is why the code in the boxes always matches the game. Here is a small function from that program. It turns a list of questions into HTML using a <code>for</code> loop and an f-string:</p>
{snippet("tools/docs/lib.py", "quiz")}
<p>Programs that write other programs or pages are everywhere. This is how many websites are made.</p>

<h2>A design process for a digital outcome</h2>
<p>When you make a website or any digital outcome, follow these steps. You will often go back to an earlier step. That is normal and is called <strong>iteration</strong>.</p>
<ol>
<li><strong>Understand the need.</strong> Who is it for? What do they want to do?</li>
<li><strong>Plan.</strong> Sketch the pages on paper. List the content.</li>
<li><strong>Build.</strong> Write HTML first, then CSS, then JavaScript.</li>
<li><strong>Test.</strong> Try it on a phone and a laptop. Ask someone else to use it.</li>
<li><strong>Improve.</strong> Fix problems. Then evaluate: did it meet the need?</li>
</ol>
{box("tip", "Accessible and inclusive",
     "<ul><li>Give every picture a short description in <code>alt=\"...\"</code>.</li><li>Use headings in order (one <code>h1</code>, then <code>h2</code>, and so on).</li>"
     "<li>Make sure text has strong contrast with its background.</li><li>Do not rely on colour alone to give meaning.</li>"
     "<li>Make sure everything works with the keyboard.</li><li>Use plain language and explain new words. Where it is right to, use te reo M&#257;ori alongside English.</li></ul>")}
{box("tip", "Respect other people's work",
     "<p>Use pictures, sounds and code you made yourself, or that have a licence that lets you use them. Say where things came from. The pictures in this game are drawn by a small program, so there is nothing to copy.</p>")}

<h2>Project 1: a ship trading card</h2>
<p><strong>Brief:</strong> make a web page with a "trading card" for one ship from the game. Use the ships table on the <a href="ships.html">Ships page</a> as your data.</p>
<p>Start with this skeleton, then add your own content and CSS:</p>
<pre class="inline"><code>&lt;!DOCTYPE html&gt;
&lt;html lang="en-NZ"&gt;
&lt;head&gt;
  &lt;meta charset="utf-8"&gt;
  &lt;meta name="viewport" content="width=device-width, initial-scale=1"&gt;
  &lt;title&gt;Medic - ship card&lt;/title&gt;
  &lt;link rel="stylesheet" href="card.css"&gt;
&lt;/head&gt;
&lt;body&gt;
  &lt;main&gt;
    &lt;article class="card"&gt;
      &lt;h1&gt;Medic&lt;/h1&gt;
      &lt;img src="medic.png" alt="A white spaceship with a green cross"&gt;
      &lt;p&gt;Support ship that heals itself and its partner.&lt;/p&gt;
      &lt;table&gt;
        &lt;tr&gt;&lt;th scope="row"&gt;Hull&lt;/th&gt;&lt;td&gt;95&lt;/td&gt;&lt;/tr&gt;
        &lt;tr&gt;&lt;th scope="row"&gt;Ability&lt;/th&gt;&lt;td&gt;Repair Burst&lt;/td&gt;&lt;/tr&gt;
      &lt;/table&gt;
    &lt;/article&gt;
  &lt;/main&gt;
&lt;/body&gt;
&lt;/html&gt;</code></pre>
<p><strong>Success criteria:</strong> valid HTML with a sensible heading order; an <code>alt</code> description on the image; a CSS file with at least five rules, including one colour variable; looks good on a phone-sized window.</p>

<h2>Project 2: all the ships with JavaScript</h2>
<p>Once your card works, show <em>all</em> ships by using a loop, so you only write the card once:</p>
<pre class="inline"><code>const ships = [
  {{ name: "Phantom", hull: 80,  ability: "Cloak" }},
  {{ name: "Medic",   hull: 95,  ability: "Repair Burst" }}
];
const list = document.getElementById("cards");
for (const s of ships) {{
  const card = document.createElement("article");
  card.className = "card";
  card.innerHTML = "&lt;h2&gt;" + s.name + "&lt;/h2&gt;&lt;p&gt;Hull: " + s.hull + "&lt;/p&gt;";
  list.appendChild(card);
}}</code></pre>
<p><strong>Extension:</strong> add a button that shows only ships with hull above 90 (a decision!).</p>

<h2>Publishing with GitHub Pages</h2>
<ol>
<li>Put your files in a GitHub repository (this site is in a folder called <code>docs</code>).</li>
<li>Open the repository's <strong>Settings</strong> and choose <strong>Pages</strong>.</li>
<li>Choose <em>Deploy from a branch</em>, pick <code>main</code> and the <code>/docs</code> folder, then save.</li>
<li>After a minute your site is live at <code>https://your-user.github.io/your-repo/</code>.</li>
</ol>
<p>Because every link on this site is relative, it works at that address with no changes. Open <code>docs/site-config.js</code> and type your user and repository name so the code links point to your repository.</p>

{try_it("view the source", "<p>In your browser, right-click this page and choose <em>View page source</em>. Find the <code>&lt;nav&gt;</code> and the <code>&lt;main&gt;</code>. Then open the browser's developer tools and change a colour in the CSS to see what happens. (Your change disappears when you reload.)</p>")}

{quiz([
    ("What are the jobs of HTML, CSS and JavaScript?", "HTML gives structure and content, CSS gives the look, JavaScript gives behaviour."),
    ("Why does this site use <em>relative</em> links?", "They keep working wherever the site is hosted."),
    ("What is the point of the <code>alt</code> attribute?", "It describes a picture for people who cannot see it, such as someone using a screen reader."),
    ("What is a media query used for?", "To change the layout for different screen sizes, such as phones."),
    ("Which step of the design process comes after testing?", "Improving (and evaluating) the outcome."),
])}
'''
    build_page("web-development", "12. Web development", body, "How websites work, using the one you are reading.")


def tutorial_steps():
    steps = [
        ("A window and a menu", "Using Python 3.10+ and the Arcade 3 library, write a program that opens a 1280x720 window with a dark blue background and shows the title 'Wormhole Runner'. Use a class that inherits from arcade.View for the menu, and a main() function that starts it.",
         "A window with the title text.", ["main.py", "game/menu_view.py"], "Add a second menu item and move between items with the UP and DOWN keys."),
        ("A ship that turns", "Add a Ship class that inherits from arcade.Sprite. Draw a simple triangle ship with the Pillow library and save it as a PNG in assets/images. Show the ship in the centre and make it turn left and right with the arrow keys.",
         "A ship in the middle that rotates.", ["game/sprites.py", "game/placeholder_art.py"], "Make a different picture for the ship using Pillow's ImageDraw."),
        ("Speed and direction", "Make UP and DOWN change the ship's speed and move the ship in the direction it faces using sine and cosine. Multiply movement by delta time so the speed is the same on every computer.",
         "The ship flies where it points and speeds up and down.", ["game/sprites.py"], "Add a maximum speed and make the ship stop at the screen edge."),
        ("Rocks and wrap-around", "Add a Rock class that moves along diagonal lines at different sizes. Make rocks and the ship wrap around the screen edges using the modulo operator. Put the world size in a World class with wrap() and a delta() method that finds the shortest vector across the edge.",
         "Rocks drifting across and reappearing on the opposite side.", ["game/world.py", "game/sprites.py"], "Draw a diagram showing why delta() is needed."),
        ("Collisions and health", "Detect when the ship touches a rock using circle distance (math.hypot). Give the ship health, a health bar, and a short invincible time after a hit. End the game when health reaches zero and show Game Over.",
         "Hitting a rock lowers health and flashes the ship.", ["game/game_view.py"], "Make bigger rocks do more damage."),
        ("Gravity", "Make every rock pull the ship using pull = G x mass / distance squared, with a softening distance and a maximum pull. Add the pull to a 'drift' velocity that slowly fades with damping. Use a function for the pull maths.",
         "The ship curves toward big rocks.", ["game/physics.py", "game/game_view.py"], "Plot the pull against distance using a graph or a table."),
        ("Power-ups and wormholes", "Add power-ups for speed, health and invincibility that appear at random places and run on timers shown on the screen. Add a wormhole that appears and disappears at random times. Flying into it starts the next level with more rocks.",
         "Collectable items and a swirling wormhole that ends the level.", ["game/sprites.py", "game/game_view.py"], "Add a fourth power-up of your own."),
        ("Settings in a dictionary", "Move every number (gravity, speeds, timings) into one nested dictionary of settings. Write a Config class that loads and saves it as JSON and finds values using dotted names such as 'physics.gravity'.",
         "A config.json file you can edit to change the game.", ["game/config.py"], "Add a new setting and use it in the game."),
        ("Sound", "Write an AudioManager class that maps event names like 'crash' and 'powerup' to sound files in a settings dictionary. It must stay silent, not crash, if a file is missing. Add looping background music.",
         "Sounds play when things happen, and music loops.", ["game/audio.py"], "Add a sound for a new event."),
        ("Animated pictures and an editor", "Load pictures as tile sequences: a sheet cut into frames of a given size and played at a given speed. Then add an in-game editor screen where I can choose image files and change the settings with the keyboard.",
         "Animated sprites and an editor screen that saves your changes.", ["game/assets.py", "game/editor_view.py"], "Add one more setting to the editor."),
        ("Weapons", "Add bullets fired with the space bar. Make a WeaponSystem class with several weapons chosen with the number keys. Give them different damage, speed, ammo and an unlock level. Include a spread shot and a homing missile that turns toward targets.",
         "Different weapons and bullets crossing the screen.", ["game/weapons.py"], "Design a new weapon and add it as key 7."),
        ("Aliens with AI", "Create an Alien base class with a think() method. Make subclasses: a Drifter that moves along a wave, a Chaser that turns toward the ship, a Sniper that keeps its distance and leads its shots, and a Swarm that orbits the ship. Aliens can be shot and can shoot back.",
         "Different enemies that behave in different ways.", ["game/aliens.py"], "Make your own alien with a new movement idea."),
        ("Splitting rocks and a growing world", "Make rocks split into smaller rocks when they are hit. Make the map bigger each level and zoom the camera out so all of it stays visible, easing smoothly to the new zoom.",
         "Bigger levels and rocks that break into pieces.", ["game/sprites.py", "game/game_view.py"], "Change how fast the world grows."),
        ("Ships, abilities and credits", "Describe each ship in a dictionary: price, health, speed multipliers, an ability and its own weapon. Add abilities (cloak, hyperjump, hyperspace, deflect, repair) on the SHIFT key with cooldowns. Add in-game credits earned by playing, a Hangar shop screen and a profile.json file that saves them.",
         "A shop where credits buy ships with different abilities.", ["game/game_features.py", "game/profile.py", "game/hangar_view.py"], "Add a new ship using only a settings entry."),
        ("Hazards, objectives and perks", "Add an Expedition mode with hazards (nebula, black hole, ion storm, solar flare), different rock types, objectives that must be completed before the wormhole opens, and a choice of one of three random perks after each level. Keep a Classic mode without them.",
         "A game mode that adds new rules each level.", ["game/game_features.py", "game/hazards.py", "game/perks.py"], "Invent a new hazard class."),
        ("Multiplayer on a local network", "Add two-player multiplayer on a local network. One player hosts and runs the whole game; the other sends key presses and draws snapshots using JSON over TCP. Use a UDP broadcast so players can find games, and also allow typing an IPv4 address.",
         "Two computers flying on the same map.", ["game/net.py", "game/client_view.py", "game/net_views.py"], "Write a short safety poster for online games."),
    ]
    cards = "".join(prompt(i, *s) for i, s in enumerate(steps, 1))
    body = f'''
{intentions(
    ["learn to break a big project into small steps",
     "write clear prompts that ask an AI helper for one feature at a time",
     "test and check code before trusting it",
     "compare my result with a finished example"],
    ["write a prompt that names the language, the library and one clear goal",
     "run, test and explain the code I am given",
     "find the same feature in the real game code"])}
<p>You can rebuild the whole game in <strong>16 small steps</strong>. Each step has a short <strong>prompt</strong> you can give to an AI helper (or use as a to-do list if you are writing the code yourself).
Do the steps in order, because each one builds on the last.</p>

<h2>How to work with an AI helper</h2>
{box("tip", "A good routine for every step",
     "<ol><li><strong>Paste</strong> the prompt, plus your current code if it is a later step.</li>"
     "<li><strong>Read</strong> the answer. Can you explain each part? If not, ask the helper to explain it in simple words.</li>"
     "<li><strong>Run</strong> it. If there is an error, copy the full message and ask what it means.</li>"
     "<li><strong>Test</strong> against the &lsquo;You should see&rsquo; line.</li>"
     "<li><strong>Compare</strong> with the real code using the links. Your version does not need to match exactly. Different code that works is fine.</li>"
     "<li><strong>Save</strong> your work before the next step.</li></ol>")}
{box("warn", "Remember",
     "<p>The AI can make mistakes and may use old library versions. Always say <em>Python 3.10+ and Arcade 3</em>. You are responsible for understanding and checking what you hand in. Say clearly when you used an AI helper.</p>")}
<h2>The 16 steps</h2>
{cards}
<h2>When your result is different</h2>
<p>Your game will not look exactly like this one, and that is good. If something does not work: re-read your prompt for missing details, make the step smaller, or ask the helper to add <em>only</em> the missing part. Make sure your names for things are clear so you can come back to the code later.</p>
'''
    build_page("tutorial-steps", "13. Rebuild it: prompts", body, "Sixteen short prompts that build the game step by step.")


def glossary():
    terms = [
        ("Algorithm", "A set of steps to solve a problem."),
        ("Aotearoa", "The M&#257;ori name for New Zealand."),
        ("Attribute", "A variable that belongs to an object, such as <code>health</code>."),
        ("Bearing", "A direction measured in degrees clockwise from up, like a compass."),
        ("Boolean", "A value that is <code>True</code> or <code>False</code>."),
        ("Broadcast", "A message sent to every computer on a local network."),
        ("Class", "A blueprint for making objects."),
        ("Client", "The computer that joins and asks, in a network."),
        ("Collision", "When two things touch."),
        ("Composition", "A class that <em>has</em> other objects as parts (a Player has a Ship)."),
        ("Conditional statement", "Code that chooses what to do, such as <code>if</code>/<code>elif</code>/<code>else</code>."),
        ("CSS", "The language that styles web pages."),
        ("Delta time (dt)", "How long the last frame took, in seconds."),
        ("Dictionary", "A collection of key: value pairs."),
        ("Easing", "Moving a value a small step toward a target each frame so the change looks smooth."),
        ("Event", "Something that happens that a program can react to, like a key press."),
        ("Frame", "One picture in the game loop. About 60 are drawn every second."),
        ("Function", "A named, reusable block of code."),
        ("Game loop", "The repeating cycle of read input, update, draw."),
        ("Hangarau Matihiko", "The M&#257;ori name for Digital Technologies in the New Zealand Curriculum."),
        ("HTML", "The language that gives a web page its structure and content."),
        ("Index", "A position number in a list, starting at 0."),
        ("Inheritance", "A class taking over the features of a parent class (an <em>is-a</em> link)."),
        ("Iteration", "Repeating steps, usually with a loop."),
        ("JSON", "A text format for saving data such as dictionaries and lists."),
        ("Kaiako", "Teacher."),
        ("&#256;konga", "Learner or student."),
        ("List", "An ordered collection of items."),
        ("Loop", "Code that repeats: <code>for</code> or <code>while</code>."),
        ("Mass", "How much matter something has. Heavier rocks pull harder."),
        ("Method", "A function that belongs to a class."),
        ("Mixin", "A parent class made only to share a group of methods."),
        ("Modulo (<code>%</code>)", "The remainder after dividing. Used for wrap-around."),
        ("Mutable", "Able to be changed after it is made (lists, dictionaries, sets)."),
        ("Object", "One thing made from a class."),
        ("Parameter", "An input to a function."),
        ("Polymorphism", "Different classes responding to the same method name in their own way."),
        ("Prediction", "Guessing what will happen next, so the game feels quick."),
        ("Reference", "A name pointing to an object in memory."),
        ("Selection", "Choosing between paths, using <code>if</code>."),
        ("Self", "Inside a method, the object the method is working on."),
        ("Sequence", "Steps done one after the other."),
        ("Server (host)", "The computer that runs the real game in a networked game."),
        ("Set", "A collection of unique items, with no order."),
        ("Snapshot", "A record of where everything is at one moment."),
        ("Sprite", "A picture that moves around in a game."),
        ("State machine", "A design where something is in one state at a time and changes state when something happens."),
        ("Tuple", "A list that cannot be changed."),
        ("Type", "The kind of data, such as <code>int</code>, <code>float</code>, <code>str</code>."),
        ("Variable", "A name that points to a value."),
        ("View", "One screen of the game, such as the menu or the hangar."),
        ("Wrap-around", "Leaving one edge of the map and reappearing on the opposite edge."),
    ]
    rows = [[f"<strong>{t}</strong>", d] for t, d in sorted(terms, key=lambda x: x[0].lower().replace("&#256;", "a").replace("&#257;", "a"))]
    body = f'''
<p>Look here when you meet a word you do not know. Some words are te reo M&#257;ori: <em>&#257;konga</em> means learner and <em>kaiako</em> means teacher.</p>
{table(["Word", "Meaning"], rows)}
'''
    build_page("glossary", "Glossary", body, "Words used on these pages.")


def teachers():
    plan = table(["Week", "Focus", "Pages", "Outcome"],
                 [["1", "Get it running; explore the game", "Start here", "Game runs; learners can name three things in it that are 'data' and three that are 'actions'."],
                  ["2", "Variables, selection, iteration", "1", "Learners predict what small code boxes do and complete the 'Try it' tasks."],
                  ["3", "Memory and data structures", "2", "Memory diagrams for lists/dicts; the copy-vs-reference experiment."],
                  ["4", "Classes and objects", "3", "Learners write a small class of their own."],
                  ["5", "Inheritance and design; game loop", "4, 5", "Class diagram of an extension (a new alien)."],
                  ["6", "Physics and maths in code", "6", "Modify gravity and wrap-around; explain results."],
                  ["7", "Systems: levels, ships, aliens, rules", "7&ndash;10", "Add a new ship using the settings; tune an alien."],
                  ["8", "Web development", "12", "Design brief, planning and the first version of a ship card page."],
                  ["9", "Build and test", "12", "Peer testing (phone and laptop), accessibility check, improvements."],
                  ["10", "Showcase and reflect", "11, 13", "Publish, present, evaluate; reflect on using AI helpers."]])
    mapping = table(["Curriculum area (Technology: Digital Technologies and Hangarau Matihiko)", "Where learners meet it"],
                    [["<strong>Computational thinking for digital technologies</strong>: algorithms and programming concepts (sequence, selection, iteration), variables and data, decomposition, testing and debugging",
                      "Pages 1, 2, 5, 6, 9; every 'Try it' task; the tutorial prompts"],
                     ["<strong>Computational thinking</strong>: data representation and structures (lists, dictionaries, JSON), abstraction (classes, functions)",
                      "Pages 2, 3, 4, 8"],
                     ["<strong>Designing and developing digital outcomes</strong>: design process, user needs, iteration, accessibility, ethics and legal considerations, evaluation",
                      "Page 12; page 11 (safety); tutorial page (using AI helpers responsibly)"],
                     ["<strong>Web development context</strong>: HTML, CSS, JavaScript, hosting and publishing a static site",
                      "Page 12 and the site itself"]])
    body = f'''
<h2>About this resource</h2>
<p>These pages help learners in Years 9 and 10 (about ages 13&ndash;15) understand programming by exploring a complete, working game. They are written in New Zealand English with short sentences, new words explained on first use, and a glossary.
Every code box is real code from the game, linked to the same lines on GitHub.</p>

<h2>Curriculum links</h2>
<p>The resource is designed to sit in the <strong>Technology</strong> learning area of <em>The New Zealand Curriculum</em>, in the <strong>Digital Technologies and Hangarau Matihiko</strong> content, with <strong>web development</strong> as the context for the design and make tasks.
Please confirm the alignment against the current documents on the Ministry of Education's T&#257;h&#363;rangi curriculum site and your own school's programme, because the wording and progress outcomes are refreshed from time to time.</p>
{mapping}
<p>The skills lead into senior digital technologies courses and NCEA. The activities support the key competencies, especially <em>thinking</em>, <em>using language, symbols and texts</em>, and <em>managing self</em>.</p>

<h2>Suggested ten-week plan</h2>
{plan}

<h2>Assessment ideas</h2>
<ul>
<li><strong>Formative:</strong> the 'Check your understanding' questions, 'Try it' tasks, and learners explaining a code box to a partner.</li>
<li><strong>Summative (web development):</strong> a ship or alien page. Suggested criteria: valid, semantic HTML; a CSS file with variables and a media query; alt text and strong contrast; evidence of testing on two devices; a short evaluation saying what was improved and why.</li>
<li><strong>Using AI helpers:</strong> ask learners to keep a short log: the prompt, what was wrong, how they fixed it, and what they learned. Learners should be able to explain any code they submit.</li>
<li>Invite whānau to a showcase where learners explain their pages.</li>
</ul>

<h2>Setting up</h2>
<ol>
<li>Install <strong>Python 3.10 or newer</strong> from python.org (on Windows tick &lsquo;Add Python to PATH&rsquo;). Linux usually has it already.</li>
<li>Unzip the game. On Windows double-click <code>run_windows.bat</code>. On Linux or Mac run <code>./run_linux.sh</code>. The first run creates a private Python environment and installs Arcade and Pillow, so it needs internet access once.</li>
<li>For learners who want to experiment, <a href="https://thonny.org">Thonny</a> or Visual Studio Code both work well.</li>
<li><strong>School networks:</strong> two-player mode uses port 5555 on the local network only. Check with your network manager before using it. Single player needs no network.</li>
</ol>

<h2>Publishing this website</h2>
<ol>
<li>Create a GitHub repository and upload the project (including the <code>docs</code> folder).</li>
<li>In <code>docs/site-config.js</code> change <code>YOUR-USER</code> to your GitHub user name and check the repository name and branch.</li>
<li>In the repository's Settings choose Pages, deploy from the <code>main</code> branch and the <code>/docs</code> folder.</li>
</ol>
<p>If you change the game's code, run <code>python tools/build_docs.py</code> to refresh the snippets, line numbers, tables and diagrams.</p>
<p>Check that GitHub's age and privacy rules suit your school before asking learners to create their own accounts. Teachers can publish the shared site instead.</p>

<h2>Differentiation</h2>
<ul>
<li><strong>Support:</strong> use pages 1&ndash;3 with the 'Try it' tasks; let learners work in pairs; use the glossary; focus on changing numbers before changing code.</li>
<li><strong>Extend:</strong> write a new alien class, add a new hazard, build the JavaScript card page, or complete the later tutorial prompts.</li>
</ul>

<h2>Safety and ethics</h2>
<ul>
<li>Credits are an in-game score only. The game never uses real money and collects no personal data. The profile is a small file on the learner's own computer.</li>
<li>Multiplayer is for people on the same local network. Discuss the safety points on page 11.</li>
<li>The pictures and sounds are generated by the program and may be replaced. If you use other people's media, check its licence. The Arcade and Pillow libraries are open-source; read their licences if you plan to share the game widely.</li>
</ul>
'''
    build_page("teachers", "Teacher notes", body, "Curriculum links, a unit plan, set-up and publishing.")


def build():
    web_development()
    tutorial_steps()
    glossary()
    teachers()
