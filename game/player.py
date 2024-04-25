from pgzero.rect import Rect
from typing import List

from .weapon import *
from .powerup import *
from engine import Entity, Sprite, Direction, Tile, direction_position


class Player(Entity):
    def __init__(self, position: List[float]):
        super(Player, self).__init__(
            position,
            [Tile.TILE_SIZE, Tile.TILE_SIZE],
            sprite=Sprite(["player0", "player1"]))
        w, h = self._rect.width * 0.96, self._rect.height * 0.96
        self.set_bounding_box(Rect((self._rect.width - w) // 2, (self._rect.height - h) // 2, w, h))
        self.speed = 3
        self.dx = 0
        self.slope = 0.3
        self.double_jump = False
        self.jump_key_down = False
        self.last_shoot = 0
        
        self.hp = 10
        self.max_hp = 10

    def update(self, game, level, dt) -> None:
        super(Player, self).update(game, level, dt)
        
        if self.is_on_ground():
            self.double_jump = True

        # Player movement
        kb = game.get_keyboard()
        speed_multiplier = 1
        dx = 0

        # Sprint
        if kb.lshift:
            speed_multiplier = 1.6

        # Left/Right
        if kb.left or kb.a and self.hp > 0:
            dx -= self.speed * speed_multiplier
            self.set_facing_direction(Direction.WEST)
        if kb.right or kb.d and self.hp > 0:
            dx += self.speed * speed_multiplier
            self.set_facing_direction(Direction.EAST)

        # Do not move if both right and left keys are pressed
        if (kb.left and kb.right) or (kb.a and kb.d):
            dx = 0

        # Jump (only if we're on the ground)
        if (kb.up or kb.w or kb.space) and self.hp > 0:
            if self.is_on_ground():
                self.jump()
            elif self.double_jump and not self.jump_key_down:
                self.jump()
                self.double_jump = False
            self.jump_key_down = True
        else:
            self.jump_key_down = False

        if self.hp > 0:
            # Animate the sprite if we're moving and on the ground
            self.get_sprite().enable_animation(self.is_on_ground() and dx)
            self.get_sprite().set_interval(0.05 if speed_multiplier > 1 else 0.1)

            # Update delta
            self.dx = min(max(self.dx + dx, -7 * speed_multiplier), 7 * speed_multiplier)
            self.dx *= 1 - self.slope
            self.move(self.dx, 0)
        else:
            self.get_sprite().enable_animation(False)

    def shoot(self, direction: Tuple[int, int]):
        pos = self.get_position()
        firebool = Fireball(self, [pos[0] + direction[0], pos[1] + direction[1]], direction)
        firebool.add_velocity(direction[0] * 3, direction[1] * 3)
        self._level.add_entity(firebool)
        
        # Shoot second fireball if we have such powerup
        if self._level.has_powerup(PowerupTypes.DOUBLE_FIREBALL_POWERUP):
            firebool = Fireball(self, [pos[0] + direction[0] * 16, pos[1] + direction[1] * 16], direction)
            firebool.add_velocity(direction[0] * 3, direction[1] * 3)
            self._level.add_entity(firebool)

    def on_mouse_pressed(self, game, level, pos, button):
        super().on_mouse_pressed(game, level, pos, button)
        
        # Change the shooting rate if we have powerup
        rate = 1
        if self._level.has_powerup(PowerupTypes.FAST_SHOOTING):
            rate = 5
        
        if self.last_shoot + (1 / rate) < self._tick and self.hp > 0:
            self.last_shoot = self._tick
            direction = direction_position(pos, level.translate_world_local(self.get_rect()), strength=3)
            direction[0] *= -1
            self.shoot(direction)

    def hit(self, entity, hp: int):
        # If we have the shield powerup, we should not take any damage
        if self._level.has_powerup(PowerupTypes.SHIELD_POWERUP):
            direction = self.direction(entity)
            self.add_velocity(direction[0] * 2 * -1, direction[1] * 2 * -1)
            return False
        hit_result = super().hit(entity, hp)
        self._level.shake_camera(5)
        return hit_result
