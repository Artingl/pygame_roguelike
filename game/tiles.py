from pgzero.rect import Rect

from engine import Tile, Entity, Sprite, AnimationPresets, PhysObject
from .player import Player
from .enemies import Enemy
from .powerup import PowerupTypes
from .weapon import Explosion


class Powerup(Tile):
    TYPE = None
    
    def __init__(self):
        super(Powerup, self).__init__(sprite=self.TYPE.value.sprite)
        self.has_collision = False
        self.set_animation_preset(AnimationPresets.FLOATING)
        
    def on_collision(self, game, obj, top, bottom, right, left):
        super().on_collision(obj, game, top, bottom, right, left)
        if not isinstance(obj, Player):
            return
        if obj.hp <= 0:
            return
        
        # Tell the level player collected the powerup
        self.get_level().collect_powerup(self)
                


class CoinPowerupTile(Powerup):
    TYPE = PowerupTypes.COIN


class HpPowerupTile(Powerup):
    TYPE = PowerupTypes.HP


class DoubleFireballPowerupTile(Powerup):
    TYPE = PowerupTypes.DOUBLE_FIREBALL_POWERUP
    

class FastShootingPowerupTile(Powerup):
    TYPE = PowerupTypes.FAST_SHOOTING


class ShieldPowerupTile(Powerup):
    TYPE = PowerupTypes.SHIELD_POWERUP


class DirtTile(Tile):
    SPRITE_RULES = {
        "dirt_all_neighbours%0-1": ["AAA",
                                    "ACA",
                                    "AAA"],

        "dirt_no_neighbours": ["000",
                               "0C0",
                               "000"],

        "dirt_single_center_horiz": [" 0 ",
                                     "ACA",
                                     " 0 "],

        "dirt_single_center_vert": [" A ",
                                    "0C0",
                                    " A "],

        "dirt_single_up": [" A ",
                           "0C0",
                           " 0 "],

        "dirt_single_down": [" 0 ",
                             "0C0",
                             " A "],

        "dirt_single_left": [" 0 ",
                             "AC0",
                             " 0 "],

        "dirt_single_right": [" 0 ",
                              "0CA",
                              " 0 "],

        "dirt_left": [" A ",
                      "0CA",
                      " A "],

        "dirt_right": [" A ",
                       "AC0",
                       " A "],

        "dirt_bottom": [" A ",
                        "ACA",
                        " 0 "],

        "dirt_top": [" 0 ",
                     "ACA",
                     " A "],

        "dirt_top_left": [" 0 ",
                          "0CA",
                          " A "],

        "dirt_top_right": [" 0 ",
                           "AC0",
                           " A "],

        "dirt_bottom_left": [" A ",
                             "0CA",
                             " 0 "],

        "dirt_bottom_right": [" A ",
                              "AC0",
                              " 0 "],

        "dirt_corner_top_bottom_left": ["0A ",
                                        "ACA",
                                        "0A "],

        "dirt_corner_top_bottom_right": [" A0",
                                         "ACA",
                                         " A0"],

        "dirt_corner_bottom_right_left": [" A ",
                                          "ACA",
                                          "0A0"],

        "dirt_corner_top_right_left": ["0A0",
                                       "ACA",
                                       " A "],

        "dirt_corner_top_left": ["0A ",
                                 "AC ",
                                 "   "],

        "dirt_corner_top_right": [" A0",
                                  " CA",
                                  "   "],

        "dirt_corner_bottom_right": ["   ",
                                     " CA",
                                     " A0"],

        "dirt_corner_bottom_left": ["   ",
                                    "AC ",
                                    "0A "],
    }

    def __init__(self):
        super(DirtTile, self).__init__(sprite=Sprite(["dirt_all_neighbours0"]))
        self._connects_with = [GrassTile]


class GrassBladeTile(Tile):
    def __init__(self):
        super(GrassBladeTile, self).__init__(sprite=Sprite(["small_grass"]))
        self.has_collision = False


class CactusTile(Tile):
    def __init__(self):
        super(CactusTile, self).__init__(sprite=Sprite(["small_cactus"]))
        self.has_collision = False


class SmallTreeTile(Tile):
    def __init__(self):
        super(SmallTreeTile, self).__init__(sprite=Sprite(["small_tree"]))
        self.has_collision = False


class GrassTile(Tile):
    SPRITE_RULES = {
        "dirt_all_neighbours%0-1": ["AAA",
                                    "ACA",
                                    "AAA"],

        "grass_no_neighbours": [" 0 ",
                                "0C0",
                                " 0 "],
        
        "grass_top_bottom": [" 0 ",
                             "ACA",
                             " 0 "],
        
        "dirt_bottom": [" A ",
                        "ACA",
                        " 0 "],
        
        "dirt_single_up": [" A ",
                           "0C0",
                           " 0 "],
        
        "grass_top_left_right": [" 0 ",
                                 "0C0",
                                 "   "],
        
        "grass_top_bottom_left": [" 0 ",
                                  "0CA",
                                  " 0 "],
        
        "grass_top_bottom_right": [" 0 ",
                                   "AC0",
                                   " 0 "],
        
        "grass_top_left": [" 0 ",
                           "0CA",
                           "   "],
        
        "grass_top_right": [" 0 ",
                            "AC0",
                            " A "],
        
        "grass_top": [" 0 ",
                      "ACA",
                      "   "],
    }

    def __init__(self):
        super(GrassTile, self).__init__()
        self._sprite = Sprite(["grass_top"])
        self._connects_with = [DirtTile]


class CloudTile(Tile):
    SPRITE_RULES = {
        "cloud_single": ["   ",
                         "0C0",
                         "   "],
        
        "cloud_left": ["   ",
                       "0CA",
                       "   "],
        
        "cloud_right": ["   ",
                        "AC0",
                        "   "],
        
        "cloud_center": ["   ",
                         "ACA",
                         "   "],
    }

    def __init__(self):
        super(CloudTile, self).__init__()
        self._sprite = Sprite(["cloud_single"])


class LeavesTile(Tile):
    SPRITE_RULES = {
        
        "leaves_all_neighbours": [" A ",
                                  "ACA",
                                  " A "],

        "leaves_no_neighbours": [" 0 ",
                                 "0C0",
                                 " 0 "],

        "leaves_left": [" A ",
                        "AC0",
                        " A "],

        "leaves_right": [" A ",
                         "AC0",
                         " A "],

        "leaves_left": [" A ",
                        "0CA",
                        " A "],
        
        "leaves_all_nbottom": [" 0 ",
                               "0C0",
                               " A "],
        
        "leaves_top_right": [" 0 ",
                             "AC0",
                             " A "],
        
        "leaves_top_left": [" 0 ",
                            "0CA",
                            " A "],
        
        "leaves_bottom_left": [" A ",
                               "0CA",
                               " 0 "],
        
        "leaves_bottom_right": [" A ",
                                "AC0",
                                " 0 "],
        
        "leaves_top": [" 0 ",
                       "ACA",
                       " A "],
        
        "leaves_bottom": [" A ",
                          "ACA",
                          " 0 "],
    }
    
    def __init__(self):
        super(LeavesTile, self).__init__()
        self._sprite = Sprite(["leaves_no_neighbours"])
        # self.has_collision = False


class WoodTile(Tile):
    SPRITE_RULES = {
        "wood_center": [" A ",
                        "0C0",
                        " A "],
        
        "wood_center_left": [" A ",
                             "AC0",
                             " A "],
        
        "wood_center_right": [" A ",
                              "0CA",
                              " A "],
        
        "wood_center_both": [" A ",
                             "ACA",
                             " A "],
        
        "wood_bottom": [" A ",
                        "0C0",
                        " 0 "],
        
        "wood_horiz_center": [" 0 ",
                              "ACA",
                              " 0 "],
        
        "wood_end_left": [" 0 ",
                          "0CA",
                          " 0 "],
        
        "wood_end_right": [" 0 ",
                           "AC0",
                           " 0 "],
        
    }
    
    def __init__(self):
        super(WoodTile, self).__init__()
        self._sprite = Sprite(["wood_center"])
        self._connects_with = [LeavesTile]
        self.has_collision = False


class LeftSignTile(Tile):
    def __init__(self):
        super(LeftSignTile, self).__init__()
        self._sprite = Sprite(["left_sign"])
        self.has_collision = False


class RightSignTile(Tile):
    def __init__(self):
        super(RightSignTile, self).__init__()
        self._sprite = Sprite(["right_sign"])
        self.has_collision = False


class MineTile(Tile):
    def __init__(self):
        super(MineTile, self).__init__()
        self._sprite = Sprite(["mine0"])
        self.until_explosion = -1
        self.next_sound = 0
        self.current_sound = 0
        self.has_collision = False
        self.colliding = False
        self.timeout = 0
    
    def update(self, game, level, dt):
        super().update(game, level, dt)
        
        if not self.colliding:
            self.until_explosion = -1
            self.current_sound = 0

        if self.until_explosion != -1:
            self._sprite.set_image(0, "mine1")
            if self.next_sound + 0.2 < self._tick and self.current_sound <= 2:
                self.next_sound = self._tick
                game.get_sound_engine().play(f"mine{self.current_sound}")
                self.current_sound += 1
            
            if self.until_explosion < self._tick:
                self._level.add_entity(Explosion(None, self.get_position(), knockback=True))
                self.timeout = self._tick + 1
                self.until_explosion = -1
        else:
            self._sprite.set_image(0, "mine0")
        self.colliding = False
    
    def on_collision(self, game, obj, top, bottom, right, left):
        super().on_collision(game, obj, top, bottom, right, left)
        
        if self.timeout > self._tick:
            return
        
        if isinstance(obj, Player) and obj.hp > 0:
            self.colliding = True
            if self.until_explosion == -1:
                self.until_explosion = self._tick + 0.7
                self.next_sound = 0
                self.current_sound = 0
