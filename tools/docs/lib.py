"""Helpers for building the documentation site.

Code shown on the pages is pulled straight from the project's source files (found with
Python's own `ast` module), so the snippets and their GitHub line links always match the
real code. Re-run `python tools/build_docs.py` after changing the game to refresh them.
"""
import ast
import html
import io
import keyword
import pathlib
import textwrap
import tokenize

ROOT = pathlib.Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"

# slug, nav title (order = reading order)
PAGES = [
    ("index", "Start here"),
    ("python-basics", "1. Python basics"),
    ("memory-and-data", "2. Memory and data"),
    ("classes-and-objects", "3. Classes and objects"),
    ("inheritance", "4. Inheritance and design"),
    ("game-loop", "5. The game loop"),
    ("physics", "6. Physics"),
    ("levels-and-world", "7. Levels and the world"),
    ("ships", "8. Ships and credits"),
    ("aliens", "9. Alien AI"),
    ("rocks-hazards-rules", "10. Rocks, hazards, rules"),
    ("going-further", "11. Going further"),
    ("web-development", "12. Web development"),
    ("tutorial-steps", "13. Rebuild it: prompts"),
    ("glossary", "Glossary"),
    ("teachers", "Teacher notes"),
]
TITLES = dict(PAGES)

_ast_cache = {}


def _source(path):
    p = ROOT / path
    return p.read_text(encoding="utf-8").splitlines()


def _find(path, name):
    """Return (start, end) 1-based lines of a class/function/method like 'Ship.update_ship'."""
    key = (path, "ast")
    if key not in _ast_cache:
        _ast_cache[key] = ast.parse((ROOT / path).read_text(encoding="utf-8"))
    node = _ast_cache[key]
    for part in name.split("."):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and child.name == part:
                node = child
                break
        else:
            raise KeyError(f"{path}: cannot find {name}")
    start = min([node.lineno] + [d.lineno for d in getattr(node, "decorator_list", [])])
    return start, node.end_lineno


# ---------------------------------------------------------------- code highlighting
def _highlight(code):
    """Colour Python code with spans using the tokenize module (works without JavaScript)."""
    lines = code.splitlines(keepends=True)
    offsets, total = [], 0
    for line in lines:
        offsets.append(total)
        total += len(line)
    marks = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(code).readline):
            kind = None
            if tok.type == tokenize.COMMENT:
                kind = "c"
            elif tok.type == tokenize.STRING or tok.type in (
                    getattr(tokenize, "FSTRING_START", -1), getattr(tokenize, "FSTRING_MIDDLE", -1),
                    getattr(tokenize, "FSTRING_END", -2)):
                kind = "s"
            elif tok.type == tokenize.NUMBER:
                kind = "n"
            elif tok.type == tokenize.NAME and keyword.iskeyword(tok.string):
                kind = "k"
            elif tok.type == tokenize.NAME and tok.string in ("self", "cls"):
                kind = "self"
            if kind:
                a = offsets[tok.start[0] - 1] + tok.start[1]
                b = offsets[tok.end[0] - 1] + tok.end[1] if tok.end[0] - 1 < len(offsets) else total
                marks.append((a, b, kind))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        pass
    out, pos = [], 0
    for a, b, kind in sorted(marks):
        if a < pos:
            continue
        out.append(html.escape(code[pos:a]))
        out.append(f'<span class="t-{kind}">{html.escape(code[a:b])}</span>')
        pos = b
    out.append(html.escape(code[pos:]))
    return "".join(out)


def _figure(path, start, end, shown, note=None, title=None):
    code = textwrap.dedent("\n".join(shown)).rstrip("\n")
    cap = title or path
    lines = f"lines {start}&ndash;{end}" if start != end else f"line {start}"
    link = (f'<a class="code-link" data-file="{path}" data-start="{start}" data-end="{end}" '
            f'href="https://github.com/">View on GitHub</a>')
    extra = f'<p class="code-note">{note}</p>' if note else ""
    return (f'<figure class="code"><figcaption><span class="file">{html.escape(path)}</span> '
            f'<span class="lines">{lines}</span> {link}</figcaption>'
            f'<pre><code>{_highlight(code)}</code></pre>{extra}</figure>')


def snippet(path, name, first=None, last=None, note=None, title=None):
    """Show a whole class / function / method, or lines first..last (1-based, inside it)."""
    start, end = _find(path, name)
    src = _source(path)
    a, b = start, end
    if first:
        a = start + first - 1
    if last:
        b = start + last - 1
    return _figure(path, a, b, src[a - 1:b], note, title)


def snippet_between(path, start_text, end_text, note=None, title=None, include_end=True):
    """Show the lines from the first line containing start_text to the next line containing end_text."""
    src = _source(path)
    a = next(i for i, l in enumerate(src, 1) if start_text in l)
    b = next(i for i in range(a, len(src) + 1) if end_text in src[i - 1])
    if not include_end:
        b -= 1
    return _figure(path, a, b, src[a - 1:b], note, title)


def lineno(path, text):
    return next(i for i, l in enumerate(_source(path), 1) if text in l)


def file_link(path, label=None, start=None, end=None):
    attrs = f'data-file="{path}"'
    if start:
        attrs += f' data-start="{start}" data-end="{end or start}"'
    return f'<a class="code-link" {attrs} href="https://github.com/">{label or path}</a>'


def symbol_link(path, name, label=None):
    start, end = _find(path, name)
    return file_link(path, label or f"{path} ({name})", start, end)


# ---------------------------------------------------------------- page parts
def box(kind, title, body):
    return f'<aside class="box {kind}"><h3>{title}</h3>{body}</aside>'


def intentions(learn, success):
    li = lambda items: "".join(f"<li>{i}</li>" for i in items)
    return (f'<div class="goals"><div class="box learn"><h3>Learning intentions</h3><ul>{li(learn)}</ul></div>'
            f'<div class="box success"><h3>Success criteria: I can&hellip;</h3><ul>{li(success)}</ul></div></div>')


def quiz(items):
    out = ['<section class="check"><h2>Check your understanding</h2>']
    for i, (q, a) in enumerate(items, 1):
        out.append(f'<details><summary><strong>{i}.</strong> {q}</summary><div class="answer">{a}</div></details>')
    out.append("</section>")
    return "".join(out)


def try_it(title, body):
    return box("tryit", f"Try it: {title}", body)


def table(headers, rows, cls=""):
    head = "".join(f"<th scope=\"col\">{h}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f'<div class="tablewrap"><table class="{cls}"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def diagram(svg, caption, label):
    return (f'<figure class="diagram">{svg}<figcaption>{caption}</figcaption></figure>'
            .replace("<svg ", f'<svg role="img" aria-label="{html.escape(label)}" ', 1))


def prompt(n, title, text, expect, files, challenge):
    links = ", ".join(file_link(f) for f in files)
    return (f'<article class="step" id="step{n}"><h3><span class="num">{n}</span> {title}</h3>'
            f'<div class="prompt"><button class="copy" type="button" aria-label="Copy prompt">Copy</button>'
            f'<pre><code>{html.escape(text)}</code></pre></div>'
            f'<p><strong>You should see:</strong> {expect}</p>'
            f'<p><strong>Compare with the real code:</strong> {links}</p>'
            f'<p class="challenge"><strong>Challenge (by hand):</strong> {challenge}</p></article>')


def build_page(slug, title, body, lede=""):
    idx = [s for s, _ in PAGES].index(slug)
    prev_ = PAGES[idx - 1] if idx > 0 else None
    next_ = PAGES[idx + 1] if idx < len(PAGES) - 1 else None
    nav = "".join(
        f'<li><a href="{s}.html"{" aria-current=\"page\"" if s == slug else ""}>{html.escape(t)}</a></li>'
        for s, t in PAGES)
    pn = '<nav class="pager" aria-label="Previous and next page">'
    pn += f'<a class="prev" href="{prev_[0]}.html">&larr; {html.escape(prev_[1])}</a>' if prev_ else "<span></span>"
    pn += f'<a class="next" href="{next_[0]}.html">{html.escape(next_[1])} &rarr;</a>' if next_ else "<span></span>"
    pn += "</nav>"
    lede_html = f'<p class="lede">{lede}</p>' if lede else ""
    page = f'''<!DOCTYPE html>
<html lang="en-NZ">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)} - Wormhole Runner: learn Python by exploring a game</title>
<link rel="stylesheet" href="assets/style.css">
<script src="site-config.js" defer></script>
<script src="assets/app.js" defer></script>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="top"><div class="brand"><a href="index.html">Wormhole Runner</a><span>Learn Python by exploring a real game</span></div>
<button class="menu-btn" type="button" aria-expanded="false" aria-controls="sidenav">Pages</button></header>
<div class="layout">
<nav class="side" id="sidenav" aria-label="Pages"><ol>{nav}</ol></nav>
<main id="main">
<h1>{html.escape(title)}</h1>
{lede_html}
{body}
{pn}
</main>
</div>
<footer><p>Wormhole Runner learning site. Written for Years 9&ndash;10 in Aotearoa New Zealand. Code links open the project on GitHub.</p></footer>
</body>
</html>
'''
    (DOCS / f"{slug}.html").write_text(page, encoding="utf-8")
