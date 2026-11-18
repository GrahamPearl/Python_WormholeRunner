"""Wormhole Runner - run with:  python main.py"""
import arcade

from game import placeholder_art
from game.constants import SCREEN_HEIGHT, SCREEN_TITLE, SCREEN_WIDTH
from game.menu_view import MenuView


def main():
    placeholder_art.generate_missing()     # only creates files that are missing
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    window.show_view(MenuView())
    arcade.run()


if __name__ == "__main__":
    main()
