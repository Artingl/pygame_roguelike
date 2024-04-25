from engine import Entity, Sprite, Tile

from typing import Tuple, List


class Explosion(Entity):
    def __init__(self, source: Entity, position: List[float], knockback: bool = False):
        super().__init__(position, [96, 96], sprite=Sprite([f"explosion{i}" for i in range(7)], interval=0.05))
        self.has_collision = False
        self.is_static = True
        self.despawn_timeout = 0.05 * 7
        self.initialized = False
        self.source = source
        self.knockback = knockback
    
    def update(self, game, level, dt):
        super().update(game, level, dt)
        
        if not self.initialized:
            self.initialized = False
            
            # Shake the camera and play explosion sound
            self._level.shake_camera(4)
            game.get_sound_engine().play('explosion')
        
            # Damage all entities which are close to the explosion
            entities = level.get_entities()
            for entity in entities:
                if entity == self:
                    continue
                dst = entity.distance(self) / Tile.TILE_SIZE
                if dst > 8 or entity.hp <= 0 or entity == self.source:
                    continue
                strength = round(min(max(8 - dst * 3, 0), 4))
                if strength > 0:
                    entity.hit(self, strength)
                    if self.knockback:
                        entity.add_velocity(strength*3, strength)
                
                # If the hit source is the player and the entity is an enemy, check if we killed the entity
                from .player import Player
                from .enemies import Enemy
                if isinstance(self.source, Player) and isinstance(entity, Enemy) and entity.hp <= 0:
                    self._level.killed_entity(entity)
        
        if self.despawn_timeout < self._tick:
            self.destroy()


class Fireball(Entity):
    def __init__(self, source: Entity, position: List[float], direction: Tuple[int, int]):
        super().__init__(position, [32, 32], sprite=Sprite([f"fireball{i}" for i in range(5)], interval=0.1))
        self._x_vel_multiplier = 1
        self.fireball_direction = list(direction)
        self.has_collision = False
        self.exploded = False
        self.despawn_timeout = 5
        self.no_collision_timeout = 0.2
        self.source = source
        self.mass = 0
    
    def update(self, game, level, dt):
        super().update(game, level, dt)
        self._velocity[0] += self.fireball_direction[0] * 0.1
        self._velocity[1] += self.fireball_direction[1] * 0.1
        
        if self.despawn_timeout < self._tick:
            self.destroy()

    def on_collision(self, game, obj, top, bottom, right, left):
        if obj != self.source and obj.has_collision:
            # Hit the entity if we didn't collide with a tile.
            # If we collided with a tile, make explosion at the collision coordinates
            if isinstance(obj, Entity) and obj.hp > 0:
                obj.hit(self, 1)
                self.destroy()
                
                # If the hit source is the player and the entity is an enemy, check if we killed the entity
                from .player import Player
                from .enemies import Enemy
                if isinstance(self.source, Player) and isinstance(obj, Enemy) and obj.hp <= 0:
                    self._level.killed_entity(obj)
            elif not self.exploded and self.no_collision_timeout < self._tick:
                self.exploded = True
                self._level.add_entity(Explosion(self.source, self.get_position()))
                self.destroy()
