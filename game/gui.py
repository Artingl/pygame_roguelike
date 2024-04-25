from pgzero.rect import Rect
from engine import Gui, Sprite, Entity, Button, Alignment,\
    AnimationProvider, Panel, Text, Image, ImageButton, ease_in_out_circ

from .powerup import PowerupTypes

import random

MENU_INFO_TEXT = """Управление:
    AD - перемещение по уровню
    Пробел или W - прыжок
    ЛКМ - Стрельба"""


class LevelGui(Gui):
    ICON_SIZE = 48

    def __init__(self, player: Entity):
        super(LevelGui, self).__init__()
        self.player = player
        self.heart_sprite = Sprite(["heart_full"])
        self.escape_pressed = False
        
        # Setting up the game over panel
        self.game_over_panel = Panel(Rect(0, 0, 400, 400))
        self.panel_best_time_text = Text("Рекорд: 0", [0, -100], font_size=20, color=(252, 249, 141))
        self.panel_time_text = Text("Время: 0", [0, -64], font_size=20)
        self.panel_kills_text = Text("Убийств: 0", [0, -28], font_size=20)
        self.game_over_panel.hide()
        
        self.game_over_panel.add_element(Text("Вы проиграли!", [0, -150], font_size=32), align=Alignment.CENTER)
        self.game_over_panel.add_element(Button("Заново", rect=Rect(0, 76, 160, 64), handler=self._restart_game), align=Alignment.CENTER)
        self.game_over_panel.add_element(self.panel_time_text, align=Alignment.CENTER)
        self.game_over_panel.add_element(self.panel_kills_text, align=Alignment.CENTER)
        self.game_over_panel.add_element(self.panel_best_time_text, align=Alignment.CENTER)
        
        # Debug and time information
        self.time_text = Text("Время: 0", [14, LevelGui.ICON_SIZE + 80], font_size=20)
        self.total_kills_text = Text("Убийств: 0", [14, LevelGui.ICON_SIZE + 112], font_size=20)
        self.fps_text = Text("FPS: 0", [14, -70], font_size=20)
        self.mute_music = ImageButton(Sprite(["mute0", "mute1"]), Rect(5, -5, 48, 48), handler=self._toggle_music, is_toggle=True)

        # Powerups
        self.coin_image = Image(Sprite(["coin0"]), Rect(5, LevelGui.ICON_SIZE + 16, LevelGui.ICON_SIZE, LevelGui.ICON_SIZE))
        self.coin_text = Text("0", [64, LevelGui.ICON_SIZE + 18], font_size=28)
        
        # Powerups shop
        self.powerups_shop_panel = Panel(Rect(0, 0, 400, 400))
        y_offset = 0
        self.powerup_shop_text = {}
        self.powerups = [
            [PowerupTypes.HP, 1],
            [PowerupTypes.DOUBLE_FIREBALL_POWERUP, 1],
            [PowerupTypes.SHIELD_POWERUP, 1],
            [PowerupTypes.FAST_SHOOTING, 1],
        ]
        for idx, data in enumerate(self.powerups):
            powerup, cost = data
            text = Text(str(cost), [-10, -14 + y_offset], font_size=28)
            self.powerup_shop_text[idx] = text
            self.powerups_shop_panel.add_element(
                ImageButton(powerup.value.sprite, rect=Rect(-74, -5 + y_offset, 64, 64), handler=self._buy_powerup(idx)),
                align=Alignment.BOTTOM | Alignment.RIGHT)
            self.powerups_shop_panel.add_element(
                Image(Sprite(["coin0"]), Rect(-10, -14 + y_offset, LevelGui.ICON_SIZE, LevelGui.ICON_SIZE)),
                align=Alignment.BOTTOM | Alignment.RIGHT)
            self.powerups_shop_panel.add_element(text, align=Alignment.BOTTOM | Alignment.RIGHT)
            y_offset -= LevelGui.ICON_SIZE + 18
        
        # Pause panel
        self.pause_panel = Panel(Rect(0, 0, 400, 400))
        self.pause_text = Text("Пауза", [0, -200], font_size=20)
        self.pause_resume_btn = Button("Продолжить", rect=Rect(0, -64, 160, 64), handler=self._resume)
        self.pause_exit_btn = Button("Выйти", rect=Rect(0, 16, 160, 64), handler=self._close_game)
        self.pause_debug_btn = Button("Отладка", rect=Rect(0, 120, 160, 64), handler=self._toggle_debug, is_toggle=True, btn_type=1)
        self.pause_panel.add_element(self.pause_text, align=Alignment.CENTER)
        self.pause_panel.add_element(self.pause_resume_btn, align=Alignment.CENTER)
        self.pause_panel.add_element(self.pause_exit_btn, align=Alignment.CENTER)
        self.pause_panel.add_element(self.pause_debug_btn, align=Alignment.CENTER)
        
        self.add_element(self.game_over_panel, Alignment.CENTER)
        self.add_element(self.fps_text, align=Alignment.BOTTOM)
        self.add_element(self.time_text)
        self.add_element(self.coin_image)
        self.add_element(self.coin_text)
        self.add_element(self.total_kills_text)
        self.add_element(self.pause_panel, align=Alignment.CENTER)
        self.add_element(self.mute_music, align=Alignment.BOTTOM)
        self.add_element(self.powerups_shop_panel, align=Alignment.BOTTOM | Alignment.RIGHT)

    def _toggle_music(self, element, game, pos, button):
        game.get_sound_engine().enable_sounds(not element.get_state())
        
    def _resume(self, element, game, pos, button):
        self._level.toggle_pause()

    def _toggle_debug(self, element, game, pos, button):
        game.get_options().set_option("debug", not game.get_options().is_debug_enabled())
        self._level.update_all_chunks(game)

    def _close_game(self, element, game, pos, button):
        game.switch_level('main_menu')
        self._level.respawn()
        self._level.toggle_pause()
    
    def _buy_powerup(self, idx):
        def handler(element, game, pos, button):
            powerup_type, cost = self.powerups[idx]
            if self._level.add_powerup(powerup_type, cost, custom_duration=30):
                self.powerups[idx][1] = min(round(self.powerups[idx][1] * (1 + random.randint(10, 25) / 10)), 64)
                self.powerup_shop_text[idx].set_text(str(self.powerups[idx][1]))
        
        return handler

    def _restart_game(self, element, game, pos, button):
        self._level.respawn()
        for idx in range(len(self.powerups)):
            self.powerup_shop_text[idx].set_text(str(self.powerups[idx][1]))


    def draw(self, game, level, surface):
        super().draw(game, level, surface)
        
        # Draw player HP
        width, height = game.get_size()
        hp = self.player.get_hp()
        for i in range(self.player.get_max_hp()):
            rect = Rect(5 + i * LevelGui.ICON_SIZE, 5, LevelGui.ICON_SIZE, LevelGui.ICON_SIZE)
            if hp >= 1:
                self.heart_sprite.set_image(0, "heart_full")
                hp -= 1
            elif hp > 0:
                self.heart_sprite.set_image(0, "heart_half")
                hp = 0
            else:
                self.heart_sprite.set_image(0, "heart_empty")

            self.heart_sprite.draw(game, rect, surface)
        
        # Draw all active powerups
        y_offset = 10
        for ticks, sprite in self._level.active_powerups.values():
            # Draw the sprite and time left until the powerup expires
            rect = Rect(width - LevelGui.ICON_SIZE * 3, y_offset, LevelGui.ICON_SIZE, LevelGui.ICON_SIZE)
            sprite.draw(game, rect, surface)
            
            expire = int(ticks - self._level._ticks)
            self.draw_text(
                game, f"{expire} c.",
                position=[width - LevelGui.ICON_SIZE * 2 + 18, y_offset],
                font_size=28
            )
            
            y_offset += LevelGui.ICON_SIZE

    def update(self, game, level, dt):
        super().update(game, level, dt)
        self.heart_sprite.update(game, dt)
        
        # Shot the game over panel if player is dead
        if self.player.hp <= 0:
            self.game_over_panel.show()
            self.powerups_shop_panel.hide()
        else:
            self.game_over_panel.hide()
            self.powerups_shop_panel.show()
        
        # Pause the game if player is alive
        if self.player.hp > 0:
            kb = game.get_keyboard()
            if kb.escape and not self.escape_pressed:
                level.toggle_pause()
                self.escape_pressed = True
            elif not kb.escape:
                self.escape_pressed = False

            if level.is_paused():
                self.pause_panel.show()
                self.powerups_shop_panel.hide()
            else:
                self.pause_panel.hide()
                self.powerups_shop_panel.show()
        
        # Update texts
        self.fps_text.set_text(f"FPS: {game.get_fps()}")
        self.time_text.set_text(f"Время: {int(level.alive_time)} секунд")
        self.panel_best_time_text.set_text(f"Рекорд: {int(level.best_time)} секунд")
        self.panel_time_text.set_text(f"Время: {int(level.alive_time)} секунд")
        self.total_kills_text.set_text(f"Убийств: {int(level.total_kills)}")
        self.panel_kills_text.set_text(f"Убийств: {int(level.total_kills)}")
        self.coin_text.set_text(str(int(level.coins)))
        
        if game.get_options().is_debug_enabled():
            self.fps_text.show()
        else:
            self.fps_text.hide()


class MainMenuGui(Gui):
    def __init__(self):
        super().__init__()
        
        self.title_animation = AnimationProvider(speed=0.6)
        
        self.new_game_btn = Button("Начать игру", rect=Rect(0, -64, 160, 64), handler=self._start_game)
        self.exit_btn = Button("Выйти", rect=Rect(0, 16, 160, 64), handler=self._close_game)
        self.debug_btn = Button("Отладка", rect=Rect(0, 120, 160, 64), handler=self._toggle_debug, is_toggle=True, btn_type=1)
        self.title_text = Text("Super mega game", [0, 0], font_size=32, color=(252, 249, 141))
        self.mute_music = ImageButton(Sprite(["mute0", "mute1"]), Rect(5, -5, 48, 48), handler=self._toggle_music, is_toggle=True)
        self.info_text = Text(MENU_INFO_TEXT, [10, 10], font_size=20)
        
        self.add_element(self.new_game_btn, align=Alignment.CENTER)
        self.add_element(self.exit_btn, align=Alignment.CENTER)
        self.add_element(self.debug_btn, align=Alignment.CENTER)
        self.add_element(self.mute_music, align=Alignment.BOTTOM)
        self.add_element(self.info_text)
        self.add_element(self.title_text, align=Alignment.CENTER | Alignment.TOP)

    def _start_game(self, element, game, pos, button):
        game.switch_level("test_level")
    
    def update(self, game, level, dt):
        super().update(game, level, dt)
        self.title_animation.update(game, dt)
        self.debug_btn.set_toggle_state(game.get_options().is_debug_enabled())
        
        # Update the title text color
        state = ease_in_out_circ((self.title_animation.get_state() + 0.2) % 1) * 1
        color0 = (252, 249, 141)
        color1 = (252, 214, 99)
        self.title_text.set_color((
            color0[0] * state + (1 - state) * color1[0],
            color0[1] * state + (1 - state) * color1[1],
            color0[2] * state + (1 - state) * color1[2]
        ))

        # Animate the title text
        width, _ = game.get_size()
        state = ease_in_out_circ(self.title_animation.get_state())
        self.title_text.set_position(0, 40 + 15 * state)

    def _toggle_debug(self, element, game, pos, button):
        game.get_options().set_option("debug", not game.get_options().is_debug_enabled())
        self._level.update_all_chunks(game)

    def _toggle_music(self, element, game, pos, button):
        game.get_sound_engine().enable_sounds(not element.get_state())

    def _close_game(self, element, game, pos, button):
        game.exit()
