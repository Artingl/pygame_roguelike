from .player import Player
from .tiles import DirtTile, CoinPowerupTile, GrassBladeTile, \
        HpPowerupTile, GrassTile, DoubleFireballPowerupTile, \
        CloudTile, ShieldPowerupTile, FastShootingPowerupTile, LeavesTile, \
        WoodTile, LeftSignTile, RightSignTile, CactusTile, SmallTreeTile, MineTile
from .gui import LevelGui
from .powerup import PowerupTypes, PowerupProps
from .enemies import FlyEnemy, RobotEnemy, Enemy
from engine import Tile, Level, Entity

import random


class MainLevel(Level):
    def __init__(self):
        super(MainLevel, self).__init__("main.level", Player([1024, 1024]))
        self.set_bg_color((65, 201, 226))
        
        # Create objects map, which will be used to determine object types in level file
        self.objects_map = {
            "D": DirtTile(),
            "C": CoinPowerupTile(),
            "B": GrassBladeTile(),
            "G": GrassTile(),
            "H": HpPowerupTile(),
            "O": CloudTile(),
            "W": WoodTile(),
            ">": RightSignTile(),
            "<": LeftSignTile(),
            "K": CactusTile(),
            "M": MineTile(),
            "T": SmallTreeTile(),
            "L": LeavesTile(),
            "S": ShieldPowerupTile(),
            "Z": FastShootingPowerupTile(),
            "V": DoubleFireballPowerupTile(),
            "R": RobotEnemy(),
            "F": FlyEnemy(),
        }
        
        self.set_gui(LevelGui(self._player))
        self.capture_entity(self._player)
        
        self.powerup_spawn_timeout = -1
        self.enemy_spawn_timeout = -1
        self.total_kills = 0
        self.alive_time = 0
        self.best_time = 0
        self.coins = 10
        self.powerups = {}
        self.active_powerups = {}
    
    def killed_entity(self, entity: Entity):
        # Player killed an entity
        self.total_kills += 1
        
        if isinstance(entity, RobotEnemy):
            self.coins += min(4 * max(1, (self.alive_time / 60)), 16)
        if isinstance(entity, FlyEnemy):
            self.coins += min(4 * max(1, (self.alive_time / 60)), 8)
    
    def respawn(self):
        # Move the player back to the spawn point
        self._player.set_position(self.get_spawn_point())

        # Reset all values to default
        self._player.max_hp = 10
        self._player.shoot_rate = 1
        self._player.hp = self._player.max_hp
        self.alive_time = 0
        self.total_kills = 0
        self.enemy_spawn_timeout = -1
        self.active_powerups = {}
        self.coins = 10
        self._gui.powerups = [
            [PowerupTypes.HP, 1],
            [PowerupTypes.DOUBLE_FIREBALL_POWERUP, 1],
            [PowerupTypes.SHIELD_POWERUP, 1],
            [PowerupTypes.FAST_SHOOTING, 1],
        ]
        
        # Remove all entities except the player from the level
        entities = self.get_entities()
        for entity in entities:
            if entity != self._player:
                self.remove_entity(entity)
        
        # Remove all powerups from the level
        for position, powerup in self.powerups.items():
            self.set_tile(None, position, layer="layer0")
        self.powerups = {}
    
    def add_powerup(self, powerup_type: PowerupTypes, cost: int = 0, custom_duration: int = None):
        # Add powerup based on its type
        if self.coins - cost < 0:
            return False

        collected = False
        props: PowerupProps = powerup_type.value
        if powerup_type == PowerupTypes.COIN:
            self.coins += 1
            collected = True
        elif powerup_type == PowerupTypes.HP:
            if self._player.add_hp(1):
                collected = True
        else:
            duration = props.duration
            if custom_duration:
                duration = custom_duration
            
            if powerup_type in self.active_powerups:
                self.active_powerups[powerup_type][0] += duration
            else:
                self.active_powerups[powerup_type] = [
                    self._ticks + duration,
                    props.sprite,
                ]
            collected = True
        
        if collected:
            self.coins -= cost
            # Player the powerup sound
            self._game.get_sound_engine().play("powerup", no_delay=True)
        
        return collected
    
    def collect_powerup(self, powerup):
        # Remove the added if we collected it successfully
        if self.add_powerup(powerup.TYPE):
            pos = powerup.get_position()
            if pos in self.powerups:
                self.powerups.pop(pos)
            powerup.destroy()
    
    def has_powerup(self, powerup: PowerupTypes):
        return powerup in self.active_powerups
    
    def update(self, game, dt) -> None:
        super().update(game, dt)
        
        # Remove all expired active powerups
        for key, powerup in self.active_powerups.copy().items():
            if self._ticks > powerup[0]:
                self.active_powerups.pop(key)
        
        # Update the alive time if player is not dead
        if not self._is_paused:
            if self._player.hp > 0:
                self.alive_time += 1 * dt
            if self.alive_time > self.best_time:
                self.best_time = self.alive_time
        
        enemies = [RobotEnemy, FlyEnemy]
        powerups = [HpPowerupTile, CoinPowerupTile, DoubleFireballPowerupTile, ShieldPowerupTile, FastShootingPowerupTile]
        
        # Spawn powerup every 3 seconds randomly on the map
        # (only if there are less than 22 powerups already on the map)
        # FIXME: lags...
        if False:  # self.powerup_spawn_timeout == -1 or self.powerup_spawn_timeout + 3 < self._ticks and len(self.powerups) < 22:
            self.powerup_spawn_timeout = self._ticks
            powerup_position = None
            center = list(self.get_spawn_point())
            center[0] //= Tile.TILE_SIZE
            center[1] //= Tile.TILE_SIZE
            
            # Find free spot for the powerup on the map
            while not powerup_position:
                # Generate random position in the world
                random_line = center[1] + random.randint(-70, 70)
                
                # Try to find spot where the powerup can be placed within the line
                while random_line < 90:
                    random_line_position = center[0] + random.randint(-70, 70)
                    while random_line_position < 160:
                        # Check that there are no tiles at the position we're right now, and there's solid tile one tile below
                        check_position = (random_line_position * Tile.TILE_SIZE, random_line * Tile.TILE_SIZE)
                        tile = self.get_tile(check_position, layer="layer0")
                        tile_below = self.get_tile((random_line_position * Tile.TILE_SIZE, (random_line - 1) * Tile.TILE_SIZE), layer="layer0")
                        
                        if not tile and tile_below:
                            powerup_position = check_position
                            break
                        random_line_position += 1
                    random_line += 1
                    if powerup_position:
                        break
            
            # Spawn the powerup
            powerup = random.choice(powerups)
            print(f"main_level: spawning powerup {powerup} at {check_position}")

            self.set_tile(powerup(), powerup_position, "layer0")
            self.powerups[powerup_position] = powerup
                    
        # Spawn enemies if none of them were found 30 tiles around the player.
        # Also calculate the timeout and about of entities that should be around the player based on kills amount
        spawn_timeout = max(3, 10 - (self.alive_time / 60))
        amount_of_entities = min(20, 2 * round(self.alive_time / 60))
        entities = self.get_entities()
        if self.enemy_spawn_timeout == -1 or self.enemy_spawn_timeout + spawn_timeout < self._ticks:
            self.enemy_spawn_timeout = self._ticks
            
            min_distance = -1
            near_entities = 0
            for entity in entities:
                if entity == self._player:
                    continue
                dst = entity.distance(self._player) / Tile.TILE_SIZE
                if min_distance == -1 or min_distance > dst:
                    min_distance = dst
                if dst < 20:
                    near_entities += 1
            
            if min_distance > 20 or min_distance == -1 or near_entities < amount_of_entities:
                enemy_instance = random.choice(enemies)()
                
                # Find position around the player where we can place the enemy
                player_position = list(self._player.get_position())
                player_position[0] = int(player_position[0] / Tile.TILE_SIZE) * Tile.TILE_SIZE + random.randint(-3, 3) * Tile.TILE_SIZE
                player_position[1] = int(player_position[1] / Tile.TILE_SIZE) * Tile.TILE_SIZE + random.randint(-3, 3) * Tile.TILE_SIZE
                found_position = None
                for x in range(-5, 5):
                    for y in range(-6, 6):
                        y *= -1
                        pos = player_position[0] + x * Tile.TILE_SIZE, player_position[1] + y * Tile.TILE_SIZE
                        if not self.get_tile(pos, "layer0"):
                            # For the robot we also need to check that there's solid tile under it
                            if isinstance(enemy_instance, RobotEnemy):
                                if self.get_tile([pos[0], pos[1] - Tile.TILE_SIZE], "layer0"):
                                    found_position = pos
                                    break
                            else:
                                found_position = pos
                                break
                    if found_position:
                        break
                
                if found_position:
                    enemy_instance.set_position(found_position)
                    self.add_entity(enemy_instance)
