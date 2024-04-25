from typing import Tuple, List
from enum import Enum

import random
import pygame
import itertools
import math

FORMAT_CACHE = {}


def format_string(s: str, seed: int = 0):
    """Formats the string using custom the format"""
    global FORMAT_CACHE
    # String formating is expensive. Check whether we have already formated the string
    rnd = random.Random(seed)
    cache_key = f"{s}_{seed}"
    if cache_key in FORMAT_CACHE:
        # Limit the cache up to 1024 entries
        result = FORMAT_CACHE[cache_key]
        FORMAT_CACHE = dict(itertools.islice(FORMAT_CACHE.items(), 1024))
        return result

    # Format the string
    rnd_range = ["", ""]
    mode = 0
    result_string = ""
    for char in s:
        # Check if we're in mode 0 (just appending characters to the result).
        # Any other mode is used for formating part of the string
        if mode == 0:
            if char != "%":
                result_string += char
            else:
                mode = 1
        elif mode == 1:
            if char == '-':
                # Go to the next mode
                mode = 2
            elif char.isdigit():
                rnd_range[0] += char
            else:
                # Invalid value
                mode = 0
        elif mode == 2:
            if char.isdigit():
                rnd_range[1] += char
            else:
                # We successfully parsed the formatting. Add it to the result string and go back to mode 0
                result_string += str(random.randint(int(rnd_range[0]), int(rnd_range[1]))) + char
                mode = 0
    if mode == 2:
        result_string += str(rnd.randint(int(rnd_range[0]), int(rnd_range[1])))

    # Save in cache and return
    FORMAT_CACHE[cache_key] = result_string
    return result_string


def ease_in_out_circ(v: float) -> float:
    if v < 0.5:
        return (1 - math.sqrt(1 - math.pow(2 * v, 2))) / 2
    return (math.sqrt(1 - math.pow(-2 * v + 2, 2)) + 1) / 2


def direction_position(pos0, pos1, strength: int = 1) -> List[int]:
    dst = math.sqrt((pos0[0] - pos1[0]) * (pos0[0] - pos1[0]) + (pos0[1] - pos1[1]) * (pos0[1] - pos1[1]))
    if dst == 0:
        return [0, 0]
    dx = (pos1[0] - pos0[0]) / dst
    dy = (pos1[1] - pos0[1]) / dst
    return [min(max(dx, -1), 1) * strength, min(max(dy, -1), 1) * strength]


class Direction(Enum):
    NORTH: int = 0
    SOUTH: int = 1
    EAST: int = 2
    WEST: int = 3


class Primitives:
    @classmethod
    def rect(cls, surf: pygame.Surface, rect: pygame.Rect, color: Tuple[int, int, int]):
        pygame.draw.rect(surf, color, rect, 2)

    @classmethod
    def circle(cls, surf: pygame.Surface, position: Tuple[float, float], radius, color: Tuple[int, int, int]):
        pygame.draw.circle(surf, color, position, radius)


DIRECTIONS = [Direction.WEST, Direction.EAST, Direction.SOUTH, Direction.NORTH]
