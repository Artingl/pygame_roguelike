from pgzero.rect import Rect
from engine import Entity, Sprite, Tile, Direction

from .player import Player
from .weapon import *
from engine import direction_position

from typing import Tuple, List

import random
import math


class Enemy(Entity):
    def __init__(self, position: List[float], size: List[float], sprite: Sprite = None):
        super().__init__(position, size, sprite)
        self.enable_ai = True
        self.prey: Entity | None = None
        self.prey_search_timeout = 0
        self.hit_strength = 1
        self.despawn_timeout = -1

    def on_collision(self, game, obj, top, bottom, right, left):
        if isinstance(obj, Player) and obj.hp > 0 and self.hp > 0:
            obj.hit(self, self.hit_strength)
    
    def update(self, game, level, dt):
        super().update(game, level, dt)

        if self.prey:
            if self.prey.hp <= 0 or not isinstance(self.prey, Player):
                # The prey has died
                self.prey = None
            elif self.prey.distance(self) / Tile.TILE_SIZE > 30:
                # We're too far from the prey
                self.prey = None

        if self.despawn_timeout != -1 and self.despawn_timeout < self._tick:
            self.destroy()
            return
        
        if self.hp <= 0:
            if self.despawn_timeout == -1:
                self.mass = 1
                self.despawn_timeout = self._tick + 5
                self.get_sprite().enable_animation(False)
                self.set_velocity(0, 1)
            return
        
        # Find prey to attack
        if self.prey is None:
            if self.prey_search_timeout + 2 < self._tick:
                self.prey_search_timeout = self._tick
                self.prey = self.find_prey(level)
        else:
            # Search for new prey if current one is dead
            if self.prey.hp <= 0:
                self.prey = None

    def shoot(self, direction: Tuple[int, int]):
        firebool = Fireball(self, list(self.get_position()), direction)
        self._level.add_entity(firebool)
    
    def find_prey(self, level) -> Entity | None:
        if not self.enable_ai:
            return None
        
        entities = level.get_entities()
        for entity in entities:
            if not isinstance(entity, Player) or entity.hp <= 0:
                continue
            dst = entity.distance(self) / Tile.TILE_SIZE
            if dst < 20:
                return entity
        
        return None


class RobotEnemy(Enemy):
    def __init__(self):
        super().__init__([0, 0], [Tile.TILE_SIZE, Tile.TILE_SIZE], sprite=Sprite(["robot0", "robot1"], interval=0.1))
        w, h = self._rect.width * 0.96, self._rect.height * 0.96
        self.set_bounding_box(Rect((self._rect.width - w) // 2, (self._rect.height - h) // 2, w, h))
        self.moving_direction = -1
        self.shoot_timeout = 0
        self.was_following = False
        self.jump_attack_timeout = 0
        self.position_check_timeout = 0
        self.last_position = [0, 0]
        self.speed = 1
        self.has_to_jump = False
        
        self.max_hp = 20
        self.hp = 20
    
    def on_collision(self, game, obj, top, bottom, right, left):
        super().on_collision(game, obj, top, bottom, right, left)
        
        # Jump if there's solid tile in front of the robot
        if not top and not bottom and (left or right):# and obj.is_static and obj.has_collision:
            self.has_to_jump = True

    def update(self, game, level, dt):
        super().update(game, level, dt)
        if self.hp <= 0:
            return
        
        if self.has_to_jump:
            self.has_to_jump = False
            if self.is_on_ground():
                self.jump()
        
        # Set moving direction towards prey if any
        if self.prey:
            self.speed = 1.4
            self.was_following = True
            self.moving_direction = round(self.direction(self.prey)[0])
            
            # Shoot at the player after timeout
            if self.shoot_timeout + 3 < self._tick and self.prey.distance(self) / Tile.TILE_SIZE < 10:
                self.shoot_timeout = self._tick
                self.shoot(self.direction(self.prey, strength=3))
            
            # Make a jump attack if the robot is two tiles away from the player.
            # Do this only once every second
            if self.jump_attack_timeout + 1 < self._tick and self.distance(self.prey) <= Tile.TILE_SIZE * 2 and self.is_on_ground():
                self.jump_attack_timeout = self._tick
                self.jump()
        elif self.was_following:
            self.was_following = False
            self.moving_direction *= -1
            self.speed = 1
        
        # If the robot would fall going one more tile, change its direction.
        # Only do this if we're not attacking the prey
        pos = list(self.get_position())
        change_direction = False
        if not self.prey:
            found_tile = False
            for i in range(5):
                pos[0] = pos[0] // Tile.TILE_SIZE * Tile.TILE_SIZE + Tile.TILE_SIZE * self.moving_direction
                pos[1] = pos[1] // Tile.TILE_SIZE * Tile.TILE_SIZE - (Tile.TILE_SIZE * i)
                tile = self._level.get_tile(pos, layer="layer0")
                if tile:
                    found_tile = True
                    break
            if not found_tile:
                change_direction = True
        
        # If the robot's position haven't changed in last 2 seconds, change direction
        if self.position_check_timeout + 2 < self._tick:
            self.position_check_timeout = self._tick
            if self.last_position == self.get_position():
                change_direction = True
            self.last_position = self.get_position()
        
        if change_direction:
            self.moving_direction *= -1
        
        self.add_velocity(self.moving_direction * self.speed, 0)
        self.set_facing_direction(Direction.EAST if self.moving_direction == 1 else Direction.WEST)


class FlyEnemy(Enemy):
    def __init__(self):
        super().__init__([0, 0], [Tile.TILE_SIZE * 0.9, Tile.TILE_SIZE * 0.9], sprite=Sprite(["fly0", "fly1", "fly2", "fly1"], interval=0.1))
        w, h = self._rect.width * 0.6, self._rect.height * 0.6
        self.set_bounding_box(Rect((self._rect.width - w) // 2, (self._rect.height - h) // 2, w, h))
        self.flying_around_pos = None
        self.shoot_timeout = 0
        self.hit_strength = 2
        self.speed = 1
        self.mass = 0

        self.max_hp = 10
        self.hp = 10

    def update(self, game, level, dt):
        super().update(game, level, dt)
        if self.hp <= 0:
            return
        self.mass = 0
        
        # Fly around current position
        if not self.flying_around_pos:
            self.flying_around_pos = list(self.get_position())
        
        pos0 = self.get_position()
        pos1 = self.flying_around_pos.copy()
        pos1[0] += Tile.TILE_SIZE * math.sin(self._tick / 2 * self.speed) * 4# * 2
        pos1[1] += Tile.TILE_SIZE * math.cos(self._tick) / 8
        direction = direction_position(pos0, pos1)
        self.add_velocity(
            direction[0],
            direction[1] * 0.2)

        vel = self.get_velocity()
        self.set_velocity(max(min(vel[0], 6), -6), max(min(vel[1], 6), -6))
        self.set_facing_direction(Direction.WEST if self.get_velocity()[0] < 0 else Direction.EAST)
        
        if self.prey:
            prey_pos = list(self.prey.get_position())
            
            # Shoot at the player after timeout
            if self.shoot_timeout + 3 < self._tick and self.prey.distance(self) / Tile.TILE_SIZE < 10:
                self.shoot_timeout = self._tick
                self.shoot(self.direction(self.prey, strength=3))
            
            self.speed = 2
            
            # Follow the player. Also try not to be too close to the ground
            distance_to_ground = self.prey.distance_ground(max_iterations=6)
            prey_pos[1] += (6 - distance_to_ground) * Tile.TILE_SIZE
            
            self.flying_around_pos[0] += (prey_pos[0] - self.flying_around_pos[0]) * 0.002
            self.flying_around_pos[1] += (prey_pos[1] - self.flying_around_pos[1]) * 0.002
        else:
            self.speed = 1
