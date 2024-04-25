import math

from pgzero.rect import Rect
from typing import Dict, Tuple, List
from uuid import UUID, uuid4

from .level_objects import WorldObject, Entity, Tile
from .particles import ParticlesEngine
from .misc import Primitives
from .chunk import Chunk
from .gui import Gui
from .animation import AnimationProvider

import random
import os


class Level:
    def __init__(self, level_source: str | None = None, player: Entity | None = None):
        self._entities: Dict[UUID, Entity] = {}
        self._chunk_layers: Dict[str, Dict[Tuple[int, int], Chunk]] = {}
        self._bg_color = (0, 0, 0)
        self._screen_size = (800, 600)
        self._camera_position = [0.0, 0.0]
        self._capture_offset = (0.0, 0.0)
        self._gui: Gui | None = None
        self._captured_object: Entity | None = None
        self._shake_strength = 0
        self._spawn_point = [0, 0]
        self._shake_value = [0, 0]
        self._chunks_updates = []
        self._gravity = (0, -1)
        self._ticks = 0
        self._counter = 0
        self._player = player
        self._last_player_chunk = None
        self._level_prepared = False
        self._game = None
        self._level_source_file = level_source
        self._synchronized_animations = []
        self._is_paused = False
        
        self.particles_engine = ParticlesEngine()
        self.objects_map = {}
        self.add_entity(player)
    
    def is_paused(self) -> bool:
        return self._is_paused
    
    def toggle_pause(self):
        self._is_paused = not self._is_paused
    
    def synchronize_animation(self, animation: AnimationProvider):
        self._synchronized_animations.append(animation)
    
    def desynchronize_animation(self, animation: AnimationProvider):
        if animation in self._synchronized_animations:
            self._synchronized_animations.pop(animation)
    
    def get_spawn_point(self) -> Tuple[int, int]:
        return tuple(self._spawn_point)

    def get_bg_color(self) -> Tuple[int, int, int]:
        return self._bg_color

    def set_bg_color(self, color: Tuple[int, int, int]):
        self._bg_color = color

    def get_gravity(self) -> Tuple[float, float]:
        return self._gravity

    def set_gravity(self, gravity: Tuple[float, float]):
        self._gravity = tuple(gravity)

    def get_camera_position(self):
        # Apply shake value to current camera position
        position = self._camera_position.copy()
        position[0] += self._shake_value[0] + self._capture_offset[0]
        position[1] += self._shake_value[1] + self._capture_offset[1]
        return position

    def shake_camera(self, strength: float):
        self._shake_strength = strength

    def set_gui(self, gui: Gui):
        if gui is not None:
            gui._level = self
            self._gui = gui

    def get_gui(self) -> Gui:
        return self._gui

    def get_neighbors_chunks(self, chunk: Chunk) -> List[Chunk]:
        if not chunk:
            return []
        
        neighbors = []
        for i in range(-1, 2):
            for j in range(-1, 2):
                if i == 0 and j == 0:
                    # Do not the chunk we are checking neighbors with
                    continue
                pos = chunk.get_position()
                target = self.get_chunk((pos[0] + i, pos[1] + j), chunk.get_layer())
                if target:
                    neighbors.append(target)
                
        return neighbors

    def get_player_chunk(self, layer: str = "layer0") -> Chunk | None:
        if not self._player:
            return None
        position = self._player.get_position()
        chunk_position = Chunk.local_coords((position[0] // Tile.TILE_SIZE, position[1] // Tile.TILE_SIZE))
        return self.get_chunk(chunk_position, layer)

    def get_chunk(self, position: Tuple[int, int], layer: str) -> Chunk | None:
        if layer not in self._chunk_layers:
            return None
        return self._chunk_layers[layer].get(tuple(position))

    def get_chunk_tile_position(self, position: Tuple[int, int], layer: str) -> Chunk | None:
        if layer not in self._chunk_layers:
            return None
        return (self._chunk_layers[layer]
                .get(Chunk.local_coords((position[0] // Tile.TILE_SIZE, position[1] // Tile.TILE_SIZE))))

    def get_chunks(self, layer: str) -> List[Chunk]:
        if layer not in self._chunk_layers:
            return []
        return list(self._chunk_layers[layer].values())

    def get_tile(self, position: Tuple[int, int], layer: str) -> Tile | None:
        position = tuple(position)
        chunk_position = Chunk.local_coords((position[0] // Tile.TILE_SIZE, position[1] // Tile.TILE_SIZE))
        chunk = self.get_chunk(chunk_position, layer)
        if chunk is not None:
            return chunk.get_tile(position)
        return None

    def set_tile(self, tile: Tile | None, position: Tuple[int, int], layer: str) -> Tile | None:
        position = tuple(position)

        if tile:
            tile.set_position(position)
            tile.set_layer(layer)
            tile._level = self

        # Add the tile to a chunk
        chunk_position = Chunk.local_coords((position[0] // Tile.TILE_SIZE, position[1] // Tile.TILE_SIZE))
        chunk = self.get_chunk(chunk_position, layer)

        # If the chunk does not exist, generate a new one
        if chunk is None:
            chunk = self._generate_chunk(*chunk_position, layer)
        
        if old_tile := chunk.get_tile(position):
            old_tile.being_destroyed(self._game, self)

        chunk.set_tile(tile, position)
        return tile

    def capture_entity(self, entity: Entity | None, offset: Tuple[int, int] = (0, 0)) -> Entity:
        """The captured entity will always be at the center of the camera.
        If none is provided, no entities would be captured"""
        self._captured_object = entity
        self._capture_offset = offset
        self._camera_position = list(entity.get_position())
        return entity

    def add_entity(self, entity: Entity) -> Entity:
        """Add the entity to the dictionary and update its private variable"""
        # Check that we don't have this entity on the engine already
        if entity is None or entity.get_uuid() in self._entities:
            return entity

        # Add the entity
        uuid = uuid4()
        entity._level = self
        entity._uuid = uuid
        self._entities[uuid] = entity
        return entity

    def remove_entity(self, key: UUID | Entity) -> None:
        """Remove the entity from the dictionary if it contains it"""
        if type(key) is UUID:
            if key in self._entities:
                entity = self._entities.pop(key)
        else:
            # FIXME: Bad approach, but it *should* works
            values = list(self._entities.values())
            keys = list(self._entities.keys())

            if key in values:
                key_idx = values.index(key)
                entity = self._entities.pop(keys[key_idx])
        entity.being_destroyed(self._game, self)

    def get_entity(self, uuid: UUID) -> Entity | None:
        return self._entities.get(uuid)

    def get_entities(self) -> List[Entity]:
        return list(self._entities.values())

    def get_title(self, game) -> str:
        return "Level"

    def shown(self, game) -> None:
        ...

    def hidden(self, game) -> None:
        ...

    def translate_world_local(self, val: Rect) -> Rect:
        """Translates world position to local screen position, which can later be used for rendering"""
        width, height = self._screen_size
        cam_x, cam_y = self.get_camera_position()
        return Rect((val.x + width // 2) - round(cam_x), (-val.y + height // 2) + round(cam_y), val.width,
                    val.height)

    def get_player(self) -> Entity | None:
        return self._player

    def draw(self, game) -> None:
        surf = game.get_screen().surface
        self._screen_size = game.get_size()

        # Draw all visible chunks on each layer
        for layer in self._chunk_layers.keys():
            visible_chunks = self._get_visible_chunks(layer)
            for chunk in visible_chunks:
                chunk.draw(game, self, surf)

        # Draw entities
        for entity in self._entities.values():
            entity._level = self
            entity.draw(game, self, surf)

            # If the debug is enabled, render it on top of the object
            if game.get_options().is_debug_enabled():
                self._render_entity_bondingbox(game, self, entity, surf)

        # Draw the gui
        if self._gui is not None:
            self._gui.draw(game, self, surf)
        
    def update(self, game, dt) -> None:
        # Update the gui
        if self._gui is not None:
            self._gui.update(game, self, dt)
            
        if self._is_paused:
            return
        
        self._game = game
        
        for animation in self._synchronized_animations:
            animation.update(game, dt)
        
        # Prepare the level if we haven't yet
        if not self._level_prepared:
            self._level_prepared = True
            
            # Load the level from the source file and set player to spawn position
            if self._level_source_file:
                self._spawn_point = self.load_level(
                    self._level_source_file,
                    self.objects_map,
                    step=(Tile.TILE_SIZE, Tile.TILE_SIZE)
                )
                
                if not self._spawn_point:
                    # We could not load the level file
                    game.exit()
                
                if self._player:
                    self._player.set_position(self._spawn_point)
                    self._camera_position = list(self._player.get_position())
            self.update_all_chunks(game)
        
        # Update all chunks which were added to the update list
        for chunk_position in self._chunks_updates:
            for neighbor_chunks in self._chunk_layers.values():
                if (chunk := neighbor_chunks.get(chunk_position)) is not None:
                    chunk.update(game, self, dt)
        self._chunks_updates.clear()
        self._ticks += 1 * dt
        self._counter += 1
        
        # Update all visible chunks on each layer
        chunk = self.get_player_chunk()
        if chunk:
            if chunk != self._last_player_chunk:
                if self._last_player_chunk:
                    self._last_player_chunk.mark_dirty()
                    self._last_player_chunk.update(game, self, dt)
                self._last_player_chunk = chunk
                chunk.mark_dirty()
            chunk.update(game, self, dt)
        
        # Update ONLY neighbor chunks to the chunk where player is right now
        neighbor_chunks = self.get_neighbors_chunks(chunk)
        for chunk in neighbor_chunks:
            chunk.update(game, self, dt)

        # Update camera
        if self._captured_object is not None:
            rect = self._captured_object.get_rect()
            self._camera_position[0] += (rect.x - self._camera_position[0]) * 0.1
            self._camera_position[1] += (rect.y - self._camera_position[1]) * 0.1
            self._shake_strength *= 0.9
            self._shake_value = [
                random.randint(-1, 1) * self._shake_strength,
                random.randint(-1, 1) * self._shake_strength]

        # Update entities
        for entity in self.get_entities():
            entity._level = self
            entity.update(game, self, dt)

    def on_mouse_pressed(self, game, pos, button):
        # Send mouse event to the gui
        if self._gui is not None:
            result = self._gui.on_mouse_pressed(game, self, pos, button)
            if result:
                return
        
        # Send mouse event to all visible chunks on each layer
        for layer in self._chunk_layers.keys():
            for chunk in self._get_visible_chunks(layer):
                chunk.on_mouse_pressed(game, self, pos, button)

        # Send mouse event to entities
        for entity in self.get_entities():
            entity._level = self
            entity.on_mouse_pressed(game, self, pos, button)

    def on_mouse_down(self, game, pos, button):
        # Send mouse event to the gui
        if self._gui is not None:
            result = self._gui.on_mouse_down(game, self, pos, button)
            if result:
                return
        
        # Send mouse event to all visible chunks on each layer
        for layer in self._chunk_layers.keys():
            for chunk in self._get_visible_chunks(layer):
                chunk.on_mouse_down(game, self, pos, button)

        # Send mouse event to entities
        for entity in self.get_entities():
            entity._level = self
            entity.on_mouse_down(game, self, pos, button)

    def on_mouse_up(self, game, pos, button):
        # Send mouse event to the gui
        if self._gui is not None:
            result = self._gui.on_mouse_up(game, self, pos, button)
            if result:
                return
        
        # Send mouse event to all visible chunks on each layer
        for layer in self._chunk_layers.keys():
            for chunk in self._get_visible_chunks(layer):
                chunk.on_mouse_up(game, self, pos, button)

        # Send mouse event to entities
        for entity in self.get_entities():
            entity._level = self
            entity.on_mouse_up(game, self, pos, button)

    def on_mouse_move(self, game, pos):
        # Send mouse event to all visible chunks on each layer
        for layer in self._chunk_layers.keys():
            for chunk in self._get_visible_chunks(layer):
                chunk.on_mouse_move(game, self, pos)

        # Send mouse event to entities
        for entity in self.get_entities():
            entity._level = self
            entity.on_mouse_move(game, self, pos)

        # Send mouse event to the gui
        if self._gui is not None:
            self._gui.on_mouse_move(game, self, pos)

    def _get_visible_chunks(self, layer: str) -> List[Chunk]:
        chunks = []
        cam_x, cam_y = self.get_camera_position()
        width = Chunk.local_coords(math.ceil(self._screen_size[0] / Tile.TILE_SIZE)) + 2
        height = Chunk.local_coords(math.ceil(self._screen_size[1] / Tile.TILE_SIZE)) + 4
        start_x = Chunk.local_coords(cam_x / Tile.TILE_SIZE) - (width // 2)
        end_x = Chunk.local_coords(cam_x / Tile.TILE_SIZE) + (width // 2)
        start_y = Chunk.local_coords(cam_y / Tile.TILE_SIZE) - (height // 2)
        end_y = Chunk.local_coords(cam_y / Tile.TILE_SIZE) + (height // 2)

        # Iterate through all possible chunks coordinates in the screen bounds
        for x in range(start_x, end_x + 1):
            for y in range(start_y, end_y + 1):
                chunk = self.get_chunk((x, y), layer)
                if chunk is not None:
                    chunks.append(chunk)
        return chunks

    def load_level(self,
                   filepath: str,
                   objects_map: Dict[str, WorldObject],
                   offset: Tuple[int, int] = (0, 0),
                   step: Tuple[int, int] = (1, 1)) -> Tuple[int, int] | None:
        """Loads level objects from file using the map. Returns position where player should spawn, or None on error"""
        if not os.path.isfile(filepath):
            print(f"{self.__class__.__name__}: level file {filepath} does not exist")
            return None

        # Load the level file
        layers = {}
        level_data = []
        current_layer = None
        with open(filepath, "r", encoding="utf-8") as file:
            content = file.read().replace("\t", "    ")
            for line in content.split("\n"):
                # Remove comments
                if "#" in line:
                    line = line[0:line.find("#")]

                if line.endswith(":"):
                    if current_layer is not None:
                        layers[current_layer] = level_data
                    level_data = []
                    current_layer = line[:-1]
                    continue

                level_data.append(line)
        if level_data and current_layer:
            layers[current_layer] = level_data

        print(f"{self.__class__.__name__}: loaded {len(layers)} layer(s)")

        # Parse its contents and add all objects according to the map
        spawn_x, spawn_y = 0, 0
        for layer_name, layer in layers.items():
            position = list(offset)
            for row in layer:
                for obj_id in row:
                    if obj_id in ['0', ' ']:
                        # We got air. Skip it
                        position[0] += step[0]
                        continue
                    elif obj_id == 'P':
                        # Player spawn
                        spawn_x = position[0]
                        spawn_y = position[1]
                        position[0] += step[0]
                        continue

                    obj = objects_map.get(obj_id)
                    if obj is None:
                        print(f"{self.__class__.__name__}: invalid object '{obj_id}' in level file {filepath}")
                        return None

                    # Add the object and set its position
                    if isinstance(obj, Entity):
                        entity = obj.__class__()
                        entity.set_position(position)
                        self.add_entity(entity)
                    elif isinstance(obj, Tile):
                        self.set_tile(obj.__class__(), (int(position[0]), int(position[1])), layer=layer_name)
                    position[0] += step[0]
                position[0] = offset[0]
                position[1] -= step[1]

        return (spawn_x, spawn_y)

    def update_all_chunks(self, game):
        for layer, chunks in self._chunk_layers.items():
            for chunk in chunks.values():
                print(f"{self.__class__.__name__}: updating chunk {chunk.get_position()} at layer '{layer}'")
                chunk.mark_dirty()
                chunk.update(game, self, 1)

    def _generate_chunk(self, x: int, y: int, layer: str) -> Chunk:
        print(f"{self.__class__.__name__}: generating chunk at {x} {y}")
        chunk = Chunk(layer, x, y)
        if layer not in self._chunk_layers:
            self._chunk_layers[layer] = {}
        self._chunk_layers[layer][(x, y)] = chunk

        # Update neighbor chunks
        for i in range(-1, 2):
            for j in range(-1, 2):
                chunk_position = (i + x) * Chunk.CHUNK_SIZE, (j + y) * Chunk.CHUNK_SIZE
                self._chunks_updates.append(chunk_position)
        self._chunks_updates.append((x, y))

        return chunk

    @classmethod
    def _render_entity_bondingbox(cls, game, level, entity, surface):
        # Draw the bounding boxes of the entity
        rect = level.translate_world_local(entity.get_rect())
        bounding_box = entity.get_bounding_box()
        bounding_rect = Rect(bounding_box.x + rect.x, bounding_box.y + rect.y, bounding_box.width, bounding_box.height)

        Primitives.circle(surface, rect.midtop, 4, (0, 255, 0))
        Primitives.circle(surface, rect.midbottom, 4, (0, 255, 0))
        Primitives.circle(surface, rect.midleft, 4, (0, 255, 0))
        Primitives.circle(surface, rect.midright, 4, (0, 255, 0))
        Primitives.rect(surface, bounding_rect, (0, 255, 255))
