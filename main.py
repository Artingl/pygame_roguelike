import random

from pgzero.screen import Screen
from pgzero.rect import Rect
from pgzero.clock import Clock
from pgzero.loaders import SoundLoader
from pgzero.keyboard import Keyboard
from pgzero import music
from typing import Literal, Dict, Any, List, Tuple

from game import MainLevel, MainMenu
from engine import Level, AnimationPresets, AnimationProvider, Tile

import sys
import time
import json
import os


class SoundEngine:
    def __init__(self, game):
        self._game = game
        self._timeout = {}
        self._volume = 0.3
        self._is_enabled = game.get_options().is_sound_enabled()

    def init(self):
        if self._is_enabled:
            music.play("music0")
            music.set_volume(self._volume / 3)

    def enable_sounds(self, state: bool):
        game.get_options().set_option("sound_enabled", state)
        self._is_enabled = state
        if not state:
            music.stop()
        else:
            music.play("music0")

    def set_volume(self, volume: float):
        self._volume = volume
        music.set_volume(self._volume / 3)

    def get_volume(self) -> float:
        return self._volume

    def play(self, sound: str | List[str], volume: int = None, no_delay: bool = False):
        if not self._is_enabled:
            return
        
        # Choose random sound if we have list of strings
        sounds_list = [sound]
        if type(sound) is list:
            sounds_list = sound
            sound = random.choice(sound)

        # Check if the previous played sound (if any) has stopped playing
        if self._check_timeout(sounds_list) or no_delay:
            sounds.load(sound).set_volume(volume if volume else self._volume)
            sounds.load(sound).play()
            self._timeout[sound] = time.time() + sounds.load(sound).get_length()

    def _check_timeout(self, sound_list: List[str]):
        for i in sound_list:
            found_sound = self._timeout.get(i)
            if found_sound is not None and found_sound > time.time():
                return False
            elif found_sound is not None:
                self._timeout.pop(i)
        return True


class Options:
    def __init__(self, game):
        self._game = game
        self._options: Dict[str, Any] = {}

        # Try to load the settings from the file
        if os.path.isfile("settings.json"):
            with open("options.json", 'r', encoding='utf-8') as file:
                self._options = json.load(file)

        # Save the options. This is useful if the file does not exist, so it'll create an empty one
        self.save()
    
    def init(self):
        pass
    
    def save(self):
        """Save current options to the options.json file"""
        with open("options.json", 'w') as file:
            json.dump(self._options, file)

    def set_option(self, key: str, value: Any) -> Any:
        """Sets custom option with the provided key"""
        self._options[key] = value
        return value

    def get_options(self, key: str) -> Any | None:
        """Returns options by the key. If the option does not exist, None is returned"""
        return self._options.get(key, None)

    def is_debug_enabled(self) -> bool:
        return self._options.get("debug", False)

    def get_tile_size(self) -> bool:
        return self._options.get("tile_size", 54)

    def is_sound_enabled(self) -> bool:
        return self._options.get("sound_enabled", True)


class Game:
    def __init__(self):
        self._current_level: Level | None = None
        self._next_level: Level | None = None
        self._level_switch_animation = AnimationProvider(AnimationPresets.ZOOM, speed=2)
        self._options = Options(self)
        self._sound_engine = SoundEngine(self)
        self._fps = 0
        self._is_loading = False
        self._initialized = False
        self._pressed_mouse_buttons: List[int] = []
        self._mouse_position = [0, 0]

        self._levels = {
            "main_menu": MainMenu(),
            "test_level": MainLevel()
        }
        self.switch_level("main_menu")

    def get_options(self) -> Options:
        return self._options

    def get_sound_engine(self) -> SoundEngine:
        return self._sound_engine

    @classmethod
    def _set_title(cls, title: str):
        # Sorry for this hacky way, but I've no clue how to do it differently
        import pygame
        pygame.display.set_caption(title)

    def switch_level(self, level_name: str):
        if self._next_level:
            # We're already switching levels
            return
        
        if not (level := self._levels.get(level_name)):
            print(f"game: level '{level_name}' does not exist")
            return
        print(f"game: switching level to '{level_name}'")
        if self._current_level is None:
            self._current_level = level
            level.shown(self)
        else:
            self._next_level = level
            self._level_switch_animation.set_state(0.01)
        self._is_loading = True

    def draw(self):
        # Render the engine if any is set
        if self._current_level is not None:
            screen.fill(self._current_level.get_bg_color())

            # Change the title of the window.
            title = self._current_level.get_title(self)
            self._set_title(title)

            # Render the engine
            self._current_level.draw(self)

        # Play level switching animation
        if self._next_level:
            if self._level_switch_animation.get_state() >= 1:
                self._current_level.hidden(self)
                self._current_level = self._next_level
                self._next_level.shown(self)

            if self._level_switch_animation.get_state() <= 0:
                self._next_level = None
                self._is_loading = False
            else:
                rect = self._level_switch_animation.animate_rect(
                    Rect(screen.width // 2, screen.height // 2, screen.width, screen.height)
                )
                screen.draw.filled_rect(rect, (0, 0, 0))

    def update(self, dt):
        if not self._initialized:
            self._initialized = True
            self.get_options().init()
            self.get_sound_engine().init()
        
        # Limit the delta value to 0.016, because we might see some value spikes during the loading
        if self._is_loading:
            dt = 0.016
        
        self._level_switch_animation.update(self, dt)

        # Update the engine if any is set
        if self._current_level is not None:
            self._current_level.update(self, dt)

            # Send mouse pressed event to level
            for button in self._pressed_mouse_buttons:
                self._current_level.on_mouse_pressed(self, self._mouse_position, button)

        self._fps = 1 / dt
    
    def get_fps(self):
        return round(self._fps, 2)

    def on_mouse_down(self, pos, button):
        self._mouse_position = pos
        self._pressed_mouse_buttons.append(button)
        if self._current_level is not None:
            self._current_level.on_mouse_down(self, pos, button)

    def on_mouse_up(self, pos, button):
        self._mouse_position = pos
        if button in self._pressed_mouse_buttons:
            self._pressed_mouse_buttons.remove(button)
        if self._current_level is not None:
            self._current_level.on_mouse_up(self, pos, button)

    def on_mouse_move(self, pos):
        self._mouse_position = pos
        if self._current_level is not None:
            self._current_level.on_mouse_move(self, pos)
    
    def exit(self, code: int = 0):
        sys.exit(code)

    @classmethod
    def get_surface(cls):
        return screen.surface

    @classmethod
    def get_size(cls) -> Tuple[int, int]:
        return screen.width, screen.height

    @classmethod
    def get_screen(cls) -> Screen:
        return screen

    @classmethod
    def get_clock(cls) -> Clock:
        return clock

    @classmethod
    def get_keyboard(cls) -> Keyboard:
        return keyboard

    @classmethod
    def get_sounds(cls) -> SoundLoader:
        return sounds


def draw():
    game.draw()


def update(dt):
    game.update(dt)


def on_mouse_up(pos, button):
    game.on_mouse_up(pos, button)
    

def on_mouse_down(pos, button):
    game.on_mouse_down(pos, button)


def on_mouse_move(pos):
    game.on_mouse_move(pos)


# The game instance
game = Game()

if __name__ == "__main__":
    # Define pgzero global variables, so the IDE won't complain about them
    screen: Screen
    clock: Clock
    keyboard: Keyboard
    sounds: SoundLoader

    # Run the pgzero
    WIDTH = 1280
    HEIGHT = 720
    import pgzrun

    pgzrun.go()

    # Save settings
    game.get_options().save()
