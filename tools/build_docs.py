"""Build the learning site into docs/ :  python tools/build_docs.py

Run it again whenever the game code changes so the snippets, line numbers, tables and
diagrams stay in step with the real code. Needs the game's own requirements installed (pip install -r requirements.txt).
"""
import importlib
import pathlib
import sys

here = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(here / "docs"))
sys.path.insert(0, str(here.parent))

for name in ("pages_a", "pages_b", "pages_c", "pages_d"):
    mod = importlib.import_module(name)
    mod.build()
print("Built the learning site in docs/")
