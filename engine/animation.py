from pgzero.rect import Rect
from enum import Enum

from .misc import ease_in_out_circ


class AnimationPresets(Enum):
    FLOATING: int = 0
    ZOOM: int = 1


class AnimationProvider:
    def __init__(self, preset: AnimationPresets = None, speed: float = 1.2):
        self._preset = preset
        self._speed = speed
        self._state = 0
        self._direction = 2

    def get_state(self) -> float:
        return self._state

    def set_state(self, state: float):
        self._direction = 1
        self._state = max(min(state, 1), 0)

    def animate_rect(self, rect: Rect) -> Rect:
        match self._preset:
            case AnimationPresets.FLOATING:
                rect.y += ease_in_out_circ(self._state) * 10

            case AnimationPresets.ZOOM:
                rect.width *= ease_in_out_circ(self._state)
                rect.height *= ease_in_out_circ(self._state)
                rect.x -= rect.width // 2
                rect.y -= rect.height // 2

            case _:
                pass
        return rect

    def update(self, game, dt):
        self._state += self._direction * (dt * self._speed)
        self._state = max(min(self._state, 1), 0)

        if self._state >= 1 or self._state <= 0:
            self._direction *= -1
