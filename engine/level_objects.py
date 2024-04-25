from typing import List, Tuple
from uuid import UUID

from .animation import *
from .misc import Direction, Primitives, format_string, direction_position
from .sprite import Sprite

import math
import random


class WorldObject:
    def __init__(self, position: List[float], size: List[float]):
        self._rect = Rect(*position, *size)
        self.seed = random.randint(0, 0xfffffff)
        self._should_be_removed = False
        self._tick = 0
        self._counter = 0

        self._level = None
        self._game = None

    def distance(self, obj):
        pos0 = self.get_position()
        pos1 = obj.get_position()
        return math.sqrt((pos0[0] - pos1[0]) * (pos0[0] - pos1[0]) + (pos0[1] - pos1[1]) * (pos0[1] - pos1[1]))
    
    def get_level(self):
        return self._level

    def get_game(self):
        return self._game

    def destroy(self):
        self._should_be_removed = True

    def get_position(self) -> Tuple[float, float]:
        return self._rect.x, self._rect.y

    def set_position(self, position):
        self._rect.x = position[0]
        self._rect.y = position[1]

    def being_destroyed(self, game, level): ...

    def draw(self, game, level, surface): ...

    def update(self, game, level, dt):
        self._game = game
        self._level = level

        self._tick += 1 * dt
        self._counter += 1

        if self._should_be_removed:
            if isinstance(self, Entity):
                level.remove_entity(self)
            else:
                level.set_tile(None, self.get_position(), "layer0")

    def on_mouse_pressed(self, game, level, pos, button): ...

    def on_mouse_down(self, game, level, pos, button): ...

    def on_mouse_up(self, game, level, pos, button): ...

    def on_mouse_move(self, game, level, pos): ...

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"{self.__class__.__name__}{{rect={self._rect}}}"


class PhysObject(WorldObject):
    def __init__(self, position: List[float], size: List[float], static: bool = True, mass: float = 0):
        super().__init__(position, size)
        self._velocity = [0.0, 0.0]
        self._rect = Rect(*position, *size)
        self._bounding_box = Rect(0, 0, *size)
        self._x_vel_multiplier = 0.8
        self._animations = {}
        self._animations_to_synchronize = []

        self.is_static = static
        self.has_collision = True
        self.mass = mass
        self.seed = random.randint(-0xffff, 0xffff)
    
    def get_rect(self):
        """Returns rect with applied animations to it (only if the object is static)"""
        rect = Rect(self._rect)
        if self.is_static:
            for animation in self._animations.values():
                rect = animation.animate_rect(rect)
        return rect

    def set_animation_preset(self, preset: AnimationPresets, speed: float = 1.2):
        """Replaces or adds animation to the object using presents. The object must be static!"""
        if not self.is_static:
            print("world_objects: couldn't add animation, the object is not static!")
            return

        if preset not in self._animations:
            self._animations[preset] = AnimationProvider(preset, speed=speed)
            self._animations_to_synchronize.append(self._animations[preset])

    def remove_animation_preset(self, preset: AnimationPresets):
        """Removes the animation preset from the object"""
        if preset in self._animations:
            animation = self._animations.pop(preset)
            self._level.desynchronize_animation(animation)

    def being_destroyed(self, game, level):
        super().being_destroyed(game, level)
        for animation in self._animations:
            level.desynchronize_animation(animation)

    def set_bounding_box(self, bounding_box: Rect):
        self._bounding_box = bounding_box

    def add_velocity(self, x: float, y: float):
        self._velocity[0] += x
        self._velocity[1] += y

    def set_velocity(self, x: float, y: float):
        self._velocity[0] = x
        self._velocity[1] = y

    def get_velocity(self) -> List[float]:
        return self._velocity

    def get_bounding_box(self) -> Rect:
        return self._bounding_box

    def update(self, game, level, dt):
        super().update(game, level, dt)
        for animation in self._animations_to_synchronize:
            self._level.synchronize_animation(animation)
        self._animations_to_synchronize = []

    def update_physics(self, game, level):
        # Add gravity to the velocity
        gravity = level.get_gravity()
        self._velocity[0] += gravity[0] * self.mass
        self._velocity[1] += gravity[1] * self.mass
        self._velocity[1] = max(min(self._velocity[1], 20), -20)
        self._velocity[0] *= self._x_vel_multiplier

        # Check the collision with other objects
        if not self.is_static:
            delta = self._compute_collision(game, level)
            self._rect.x += delta[0]
            self._rect.y += delta[1]

    def _compute_collision(self, game, level) -> List[float]:
        """Computes the delta that needs to be added to the position based on collisions with all objects"""
        delta = self._velocity.copy()

        # Get chunk where the entity is located right now, as well as neighbour chunks
        from engine import Chunk
        cx = Chunk.local_coords(self._rect.x / Tile.TILE_SIZE)
        cy = Chunk.local_coords(self._rect.y / Tile.TILE_SIZE)
        chunks = [
            level.get_chunk((cx, cy), "layer0"),
            level.get_chunk((cx + 1, cy), "layer0"),
            level.get_chunk((cx, cy + 1), "layer0"),
            level.get_chunk((cx - 1, cy), "layer0"),
            level.get_chunk((cx, cy - 1), "layer0"),
            level.get_chunk((cx + 1, cy + 1), "layer0"),
            level.get_chunk((cx - 1, cy + 1), "layer0"),
            level.get_chunk((cx + 1, cy - 1), "layer0"),
            level.get_chunk((cx - 1, cy - 1), "layer0")
        ]

        # Iterate through all chunks' tiles and try to collide with them
        for chunk in chunks:
            if chunk is None:
                continue

            for tile in chunk.get_tiles():
                delta, result = self._collision_check(game, tile, delta)
                if result[1]:
                    self._on_ground = True
                if result[0] or result[1]:
                    self._velocity[1] = 0
                if result[2] or result[3]:
                    self._velocity[0] = 0

        # Collide with entities
        for entity in level.get_entities():
            delta, result = self._collision_check(game, entity, delta, trigger=True)
            if result[1]:
                self._on_ground = True
            if result[0] or result[1]:
                self._velocity[1] = 0
            if result[2] or result[3]:
                self._velocity[0] = 0

        return delta

    def on_collision(self, game, obj, top, bottom, right, left): ...

    def _collision_check(self, game, obj, delta, trigger: bool = False) -> Tuple[List[float], Tuple[bool, bool, bool, bool]]:
        """Checks collision with an object.
        Returns tuple with the new delta and collided sides TOP, BOTTOM, LEFT, RIGHT"""
        top, bottom, left, right = False, False, False, False
        other_rect: Rect = obj.get_rect()
        rect: Rect = Rect(
            self._bounding_box.x + self._rect.x,
            self._bounding_box.y + self._rect.y,
            self._bounding_box.width,
            self._bounding_box.height)

        delta[0] = int(delta[0])
        delta[1] = int(delta[1])

        # Check that we didn't collide with ourselves
        if obj != self:
            if self.has_collision and obj.has_collision and not trigger:
                if other_rect.colliderect(Rect(rect.x + delta[0], rect.y, rect.width, rect.height)):
                    if delta[0] < 0:
                        left = True
                    else:
                        right = True
                    delta[0] = 0
                if other_rect.colliderect(Rect(rect.x, rect.y + delta[1], rect.width, rect.height)):
                    if delta[1] < 0:
                        bottom = True
                        delta[1] = round(other_rect.bottom - rect.top)
                    else:
                        top = True
                        delta[1] = round(other_rect.top - rect.bottom)
                if top or bottom or left or right:
                    self.on_collision(game, obj, top, bottom, left, right)
                    obj.on_collision(game, self, top, bottom, left, right)
            elif other_rect.colliderect(rect):
                self.on_collision(game, obj, True, True, True, True)
                obj.on_collision(game, self, True, True, True, True)
        return delta, (top, bottom, left, right)


class Tile(PhysObject):
    SPRITE_RULES = {}
    TILE_SIZE = 54

    def __init__(self, sprite: Sprite = None):
        super(Tile, self).__init__([0, 0], [Tile.TILE_SIZE, Tile.TILE_SIZE])
        self._connects_with = []
        self._sprite = sprite
        self._layer = ""
    
    def set_layer(self, layer: str):
        self._layer = layer

    def get_sprite(self):
        return self._sprite

    def draw_chunk(self, game, level, surface):
        from engine import Chunk
        # Translate current tile's world position to local chunk's surface position.
        rect = self.get_rect()
        rect.y *= -1
        rect.y -= Tile.TILE_SIZE
        rect.x %= Chunk.CHUNK_SIZE * Tile.TILE_SIZE
        rect.y %= Chunk.CHUNK_SIZE * Tile.TILE_SIZE

        # Render the tile as a rectangle if no sprite is set
        if self._sprite is None:
            Primitives.rect(surface, rect, (255, 255, 255))
        else:
            self._sprite.draw(game, rect, surface)

    def update(self, game, level, dt):
        super().update(game, level, dt)
        self.update_physics(game, level)

        # If we have any animations, we need to always re-render chunk's frame
        if any(self._animations):
            level.get_chunk_tile_position(self.get_position(), layer=self._layer).mark_dirty()

        # Update the sprite
        if self._sprite is not None:
            self._sprite.update(game, dt)

    def update_tile(self, game, level):
        # Update tile's sprite
        self._update_sprite(game, level)

    def get_position_tile(self) -> Tuple[int, int]:
        return self._rect.x // Tile.TILE_SIZE, self._rect.y // Tile.TILE_SIZE

    def _update_sprite(self, game, level):
        target_sprite = None

        # Set different sprite textures for the tile based on its neighbours.
        for sprite, rule in self.SPRITE_RULES.items():
            # If the provided rule can be applied to this tile, set the sprite as the target one
            if self._tile_check_rule(level, rule):
                target_sprite = sprite
                break

        # Update the sprite if we found appropriate one
        if target_sprite is not None:
            target_sprite = format_string(target_sprite, seed=self.seed)
            if self._sprite.get_image(0) != target_sprite:
                # Mark the chunk dirty, so we can notice the change of the sprite
                level.get_chunk_tile_position(self.get_position(), layer=self._layer).mark_dirty()
                self._sprite.set_image(0, target_sprite)

    def _tile_check_rule(self, level, rule) -> bool:
        # The rule should have this form, where 0 means there
        # must be object of a different type, A means there must be a tile of the same type,
        # C means where our tile is located in the rule:
        #   0A0
        #   ACA
        #   0A0
        is_relative = lambda x, y: x and x.__class__ == y.__class__ or \
            (x and y.__class__ in x._connects_with or x.__class__ in y._connects_with)
        x, y = self.get_position()

        # Find the C locating in the rule
        x_offset, y_offset = 0, 0
        center_x, center_y = 0, 0
        for row in rule:
            for char in row:
                if char == 'C':
                    center_x = x_offset
                    center_y = y_offset
                    break
                x_offset += 1
            x_offset = 0
            y_offset -= 1

        # Iterate through the rule rows and test whether it applies to this tile.
        x_offset, y_offset = 0, 0
        for row in rule:
            for char in row:
                if char == ' ':
                    # Skip this tile
                    x_offset += 1
                    continue

                position = (x + (x_offset - center_x) * Tile.TILE_SIZE, y + (y_offset - center_y) * Tile.TILE_SIZE)
                tile = level.get_tile(position, self._layer)
                if (char == '0' and is_relative(tile, self)) or (char == 'A' and not is_relative(tile, self)):
                    collision_static = True if tile is None else tile.has_collision and tile.is_static
                    if tile != self and collision_static:
                        # The tile didn't apply to the rule
                        return False
                x_offset += 1
            x_offset = 0
            y_offset -= 1

        return True


class Entity(PhysObject):
    def __init__(self,
                 position: List[float],
                 size: List[float],
                 sprite: Sprite = None):
        super(Entity, self).__init__(position, size, static=False, mass=1)
        self._uuid = None
        self._delta = [0.0, 0.0]
        self._sprite = sprite
        self._on_ground = False
        self._direction = Direction.WEST
        self._last_jump = 0
        self._last_hit = 0
        self.hp = 4
        self.max_hp = 4

    def direction(self, entity, strength: int = 1) -> Tuple[int, int]:
        pos0 = self.get_position()
        pos1 = entity.get_position()
        return direction_position(pos0, pos1, strength=strength)

    def distance_ground(self, max_iterations: int = 16, layer: str = "layer0") -> int:
        if not self._level:
            return max_iterations
        
        x = self.get_position()[0] // Tile.TILE_SIZE * Tile.TILE_SIZE
        y = self.get_position()[1] // Tile.TILE_SIZE * Tile.TILE_SIZE
        for i in range(max_iterations):
            tile = self._level.get_tile((x, y - i * Tile.TILE_SIZE), layer)
            if tile is not None and tile.is_static and tile.has_collision:
                return i
        
        return max_iterations

    def set_hp(self, value: float) -> bool:
        self.hp = value
        if self.hp > self.max_hp or self.hp < 0:
            self.hp = min(max(self.hp, 0), self.max_hp)
            return False
        return True

    def hit(self, entity, hp: int) -> bool:
        # Delay between hits
        if self._last_hit + 0.2 > self._tick or not isinstance(entity, Entity):
            return False
        self._last_hit = self._tick
        if self._sprite != None:
            self._sprite.blink((230, 50, 50))
        self.hp -= hp
        self.hp = min(max(self.hp, 0), self.max_hp)
        direction = self.direction(entity)
        self.add_velocity(direction[0] * 2 * -1, direction[1] * 2 * -1)
        
        # Play hit sound
        sounds = ['hit0', 'hit1', 'hit2']
        self._game.get_sound_engine().play(sounds)
        return True

    def get_hp(self) -> float:
        return self.hp

    def get_max_hp(self) -> int:
        return self.max_hp

    def add_hp(self, value: float) -> bool:
        if self.hp + value > self.max_hp or self.hp <= 0:
            return False
        self.hp += value
        self.hp = min(max(self.hp, 0), self.max_hp)
        return True

    def set_max_hp(self, value: int):
        self.max_hp = int(round(value))

    def get_uuid(self) -> UUID | None:
        return self._uuid

    def get_sprite(self):
        return self._sprite

    def set_facing_direction(self, direction: Direction):
        self._direction = direction

    def get_facing_direction(self):
        return self._direction

    def move(self, dx: float, dy: float):
        self._delta[0] += dx
        self._delta[1] += dy

    def jump(self, force: bool = False) -> bool:
        # Delay between jump
        if self._last_jump + 0.1 > self._tick and not force:
            return False

        self._last_jump = self._tick
        self._velocity[1] += 20
        return True

    def is_on_ground(self) -> bool:
        return self._on_ground

    def draw(self, game, level, surface):
        # Translate current entity's world position to local screen position.
        rect = level.translate_world_local(self.get_rect())

        # Render the entity as a rectangle if no sprite is set
        if self._sprite is None:
            game.get_screen().draw.rect(rect, (255, 255, 255))
        else:
            self._sprite.draw(game, rect, surface, direction=self._direction)

    def update(self, game, level, dt):
        super().update(game, level, dt)
        self.update_physics(game, level)
        self._delta = [0, 0]
        self.hp = min(max(self.hp, 0), self.max_hp)

        # Update the sprite
        if self._sprite is not None:
            self._sprite.update(game, dt)

    def _compute_collision(self, game, level) -> List[float]:
        """Computes the delta that needs to be added to the position based on collisions with all objects"""
        self._on_ground = False
        delta = self._delta.copy()
        delta[0] += self._velocity[0]
        delta[1] += self._velocity[1]

        # Get chunk where the entity is located right now, as well as neighbour chunks
        from engine import Chunk
        cx = Chunk.local_coords(self._rect.x / Tile.TILE_SIZE)
        cy = Chunk.local_coords(self._rect.y / Tile.TILE_SIZE)
        chunks = [
            level.get_chunk((cx, cy), "layer0"),
            level.get_chunk((cx + 1, cy), "layer0"),
            level.get_chunk((cx, cy + 1), "layer0"),
            level.get_chunk((cx - 1, cy), "layer0"),
            level.get_chunk((cx, cy - 1), "layer0"),
            level.get_chunk((cx + 1, cy + 1), "layer0"),
            level.get_chunk((cx - 1, cy + 1), "layer0"),
            level.get_chunk((cx + 1, cy - 1), "layer0"),
            level.get_chunk((cx - 1, cy - 1), "layer0")
        ]

        # Iterate through all chunks' tiles and try to collide with them
        for chunk in chunks:
            if chunk is None:
                continue

            for tile in chunk.get_tiles():
                delta, result = self._collision_check(game, tile, delta)
                if result[1]:
                    self._on_ground = True
                if result[0] or result[1]:
                    self._velocity[1] = 0

        # Collide with entities
        for entity in level.get_entities():
            delta, result = self._collision_check(game, entity, delta, trigger=True)
            if result[1]:
                self._on_ground = True
            if result[0] or result[1]:
                self._velocity[1] = 0
            if result[2] or result[3]:
                self._velocity[0] = 0

        return delta
