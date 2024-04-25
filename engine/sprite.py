from pgzero.actor import Actor

from typing import List, Tuple

from .animation import *
from .misc import Direction


class Sprite:
    def __init__(self, images: List[str], interval: float = 0.1):
        self._images = images
        self._actors: List[Actor] = []
        self._current_frame = 0
        self._tick = 0
        self._interval = interval
        self._last_frame_change = 0
        self._is_enabled = True

        # The init method of the class might be called when pygame hasn't initialized yet,
        # so we'd do lazy initialization during first draw call
        self._initialized = False

        self._blink_color = (0, 0, 0)
        self._blink_timeout = -1

    def blink(self, color: Tuple[int, int, int]):
        """Blink with color"""
        self._blink_color = color
        self._blink_timeout = self._tick + 0.7

    def set_image(self, idx: int, image: str):
        """Sets an image at an index"""
        if idx >= len(self._actors):
            return
        self._images[idx] = image
        self._actors[idx].image = image

    def get_image(self, idx: int) -> str:
        """Returns an image at an index"""
        if idx >= len(self._actors):
            return ""
        return self._images[idx]

    def get_interval(self) -> float:
        """Returns the interval between animation frames in MS"""
        return self._interval

    def set_interval(self, interval: float):
        """Sets the interval between animation frames in MS"""
        self._interval = interval

    def enable_animation(self, state: bool):
        self._is_enabled = state

    def draw(self, game, rect: Rect, surface, direction: Direction = Direction.WEST):
        if not self._actors:
            return
        
        # Render current frame at provided position
        actor = self._actors[self._current_frame % len(self._actors)]

        # As far as I can see there's no native method in pgzero that would allow to flip the image.
        # Because of this I'll make a little hack using standard pygame to flip the image.
        # Also I'll use it to scale the image for now
        import pygame
        scaled_frame = pygame.transform.scale(actor._surf, (rect.width, rect.height))

        # Blink effect
        if self._blink_timeout != -1:
            state = round(self._tick * 10) % 2
            clr = self._blink_color
            color_img = pygame.Surface(scaled_frame.get_size(), pygame.SRCALPHA)
            color_img.fill(((255 - clr[0]) * state, (255 - clr[1]) * state, (255 - clr[2]) * state))
            scaled_frame.blit(color_img, (0, 0), special_flags=pygame.BLEND_RGB_SUB)

        frame = pygame.transform.flip(scaled_frame, direction == Direction.EAST, direction == Direction.NORTH)
        surface.blit(frame, (rect.x, rect.y))

    def update(self, game, dt):
        # Initialize the sprite if we haven't yet
        if not self._initialized:
            for img in self._images:
                self._actors.append(Actor(img))
            self._initialized = True
        
        ticks_per_second = 1 * dt
        self._tick += ticks_per_second
        if self._tick > self._last_frame_change + self._interval and self._is_enabled:
            self._current_frame += 1
            self._last_frame_change = self._interval + self._tick

        if self._blink_timeout < self._tick:
            self._blink_timeout = -1

        # If the animation is disabled, only show the first frame
        if not self._is_enabled:
            self._current_frame = 0