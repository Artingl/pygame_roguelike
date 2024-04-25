from engine import Level
from game import MainMenuGui
from .tiles import DirtTile, GrassBladeTile, GrassTile, CloudTile
from .enemies import FlyEnemy, RobotEnemy, Enemy

import random


class MainMenu(Level):
    def __init__(self):
        super(MainMenu, self).__init__("main_menu_bg.level")
        self.set_bg_color((65, 201, 226))

        # Create objects map, which will be used to determine object types in level file
        self.objects_map = {
            "D": DirtTile(),
            "B": GrassBladeTile(),
            "G": GrassTile(),
            "R": RobotEnemy(),
            "F": FlyEnemy(),
            "O": CloudTile(),
        }
        
        self.set_gui(MainMenuGui())

    def update(self, game, dt) -> None:
        super().update(game, dt)
        
        # Spectate to random entity, if we're not spectating to any
        if not self._captured_object:
            self.capture_entity(random.choice(self.get_entities()), offset=(0, -60))
        
        # Disable AI for all enemies on menu level
        for entity in self.get_entities():
            if isinstance(entity, Enemy):
                entity.enable_ai = False
