from enum import Enum

from engine import Sprite


class PowerupProps:
    def __init__(self, sprite: Sprite, duration: int):
        self.sprite = sprite
        self.duration = duration


class PowerupTypes(Enum):
    DOUBLE_FIREBALL_POWERUP: PowerupProps = PowerupProps(Sprite(["firefball_double"]), 16)
    SHIELD_POWERUP: PowerupProps = PowerupProps(Sprite(["shield"]), 16)
    FAST_SHOOTING: PowerupProps = PowerupProps(Sprite(["crosshair"]), 16)
    HP: PowerupProps = PowerupProps(Sprite(["heart_full"]), 0)
    COIN: PowerupProps = PowerupProps(Sprite(["coin0", "coin1"], interval=0.5), 0)
