from pgzero.rect import Rect
from typing import Dict, Tuple, Iterable, List

from .level_objects import Tile
from .misc import Primitives

import pygame


class Chunk:
    CHUNK_SIZE = 8

    def __init__(self, layer: str, x: int, y: int):
        self._tiles: Dict[Tuple[int, int], Tile] = {}
        self._rect: Rect = Rect(x, y, Chunk.CHUNK_SIZE, Chunk.CHUNK_SIZE)
        self._ticks = 0
        self._layer = layer
        
        width = self._rect.width * Tile.TILE_SIZE
        height = self._rect.height * Tile.TILE_SIZE
        self._is_dirty = True
        self._tiles_dirty = True
        self._prerendered_frame: pygame.Surface = pygame.Surface(
            (width, height),
            pygame.SRCALPHA
        )

    def get_layer(self) -> str:
        return self._layer

    def get_position(self) -> Tuple[int, int]:
        return self._rect.x, self._rect.y
    
    def set_tile(self, tile: Tile, position: Tuple[int, int]):
        position = tuple(position)
        if tile:
            self._tiles[position] = tile
        else:
            self._tiles.pop(position)

        # Render the frame again since changes were made to the chunk
        self.mark_dirty()

    def get_tile(self, position: Tuple[int, int]) -> Tile | None:
        position = tuple(position)
        return self._tiles.get(position)

    def get_tiles(self) -> List[Tile]:
        return list(self._tiles.values())

    def draw(self, game, level, surface):
        translated_rect = Rect(self._rect)
        translated_rect.x = Chunk.world_coords(translated_rect.x) * Tile.TILE_SIZE
        translated_rect.y = Chunk.world_coords(translated_rect.y + 1) * Tile.TILE_SIZE - Tile.TILE_SIZE
        width = self._rect.width * Tile.TILE_SIZE
        height = self._rect.height * Tile.TILE_SIZE
        if self._is_dirty:
            # Prerender the frame, so we won't need to always render all tiles.
            # If the chunk contains animated tiles, we'd need to always render it render
            self._prerendered_frame.fill((0, 0, 0, 0))
            
            for tile in self._tiles.values():
                tile._level = level
                tile.draw_chunk(game, level, self._prerendered_frame)

                # If the debug is enabled, render the bounding box of the object
                if game.get_options().is_debug_enabled():
                    self._render_tile_bondingbox(tile, self._prerendered_frame)
            self._is_dirty = False
        position = level.translate_world_local(translated_rect)
        surface.blit(
            self._prerendered_frame, (position.x, position.y)
        )

        # Render chunk's borders if debug is enabled
        if game.get_options().is_debug_enabled():
            player_rect = Rect(0, 0, 0, 0)
            world_rect = Rect(self._rect)
            world_rect.x = int(world_rect.x) * Chunk.CHUNK_SIZE * Tile.TILE_SIZE
            world_rect.y = int(world_rect.y) * Chunk.CHUNK_SIZE * Tile.TILE_SIZE
            world_rect.width *= Tile.TILE_SIZE
            world_rect.height *= Tile.TILE_SIZE
            if player := level.get_player():
                player_rect = player.get_rect()
            
            size = Tile.TILE_SIZE * Chunk.CHUNK_SIZE
            translated_rect = level.translate_world_local(
                Rect(int(self._rect.x * Tile.TILE_SIZE) * Chunk.CHUNK_SIZE,
                     int((self._rect.y + 1) * Tile.TILE_SIZE) * Chunk.CHUNK_SIZE, size, size)
            )
            
            Primitives.rect(surface, translated_rect, (255, 0, 0) if world_rect.colliderect(player_rect) else (0, 255, 0))

    def update(self, game, level, dt):
        self._ticks += 1 * dt

        for tile in self.get_tiles():
            tile._level = level
            tile.update(game, level, dt)

            if self._tiles_dirty:
                tile.update_tile(game, level)

        self._tiles_dirty = False

    def mark_dirty(self):
        """Mark this chunk as a dirty one. The pre-rendered frame will be generated again during next draw call"""
        self._is_dirty = True
        self._tiles_dirty = True

    def on_mouse_down(self, game, level, pos, button):
        for tile in self.get_tiles():
            tile.on_mouse_down(game, level, pos, button)

    def on_mouse_up(self, game, level, pos, button):
        for tile in self.get_tiles():
            tile.on_mouse_up(game, level, pos, button)

    def on_mouse_move(self, game, level, pos):
        for tile in self.get_tiles():
            tile.on_mouse_move(game, level, pos)
    
    def on_mouse_pressed(self, game, level, pos, button):
        for tile in self.get_tiles():
            tile.on_mouse_pressed(game, level, pos, button)

    @classmethod
    def local_coords(cls, v) -> Tuple[int, int] | int:
        if isinstance(v, Iterable):
            v = list(v)
            return int(v[0]) // Chunk.CHUNK_SIZE, int(v[1]) // Chunk.CHUNK_SIZE
        else:
            return int(v) // Chunk.CHUNK_SIZE

    @classmethod
    def world_coords(cls, v) -> Tuple[int, int] | int:
        if isinstance(v, Iterable):
            v = list(v)
            return int(v[0]) * Chunk.CHUNK_SIZE, int(v[1]) * Chunk.CHUNK_SIZE
        else:
            return int(v) * Chunk.CHUNK_SIZE

    @classmethod
    def _render_tile_bondingbox(cls, tile, surface):
        # Draw the bounding boxes of the tile
        rect = tile.get_rect()
        rect.y *= -1
        rect.y -= Tile.TILE_SIZE
        rect.x %= Chunk.CHUNK_SIZE * Tile.TILE_SIZE
        rect.y %= Chunk.CHUNK_SIZE * Tile.TILE_SIZE
        bounding_box = tile.get_bounding_box()
        bounding_rect = Rect(bounding_box.x + rect.x, bounding_box.y + rect.y, bounding_box.width, bounding_box.height)

        Primitives.circle(surface, rect.midtop, 4, (0, 255, 0))
        Primitives.circle(surface, rect.midbottom, 4, (0, 255, 0))
        Primitives.circle(surface, rect.midleft, 4, (0, 255, 0))
        Primitives.circle(surface, rect.midright, 4, (0, 255, 0))
        Primitives.rect(surface, bounding_rect, (0, 255, 255))

