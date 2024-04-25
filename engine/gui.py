from pgzero.rect import Rect
from .sprite import Sprite

from typing import List, Callable, Tuple


class Alignment:
    CENTER: int = 1 << 0
    LEFT: int = 1 << 1
    RIGHT: int = 1 << 2
    TOP: int = 1 << 3
    BOTTOM: int = 1 << 4


class GuiElement:
    def __init__(self, rect: Rect):
        self._original_rect: Rect = Rect(rect)
        self._rect: Rect = Rect(rect)
        self._gui: Gui = None
        self._parent = None
        self._align: Alignment = None
        self._shown = True

    def set_size(self, width: int, height: int):
        self._rect.width = width
        self._rect.height = height
        self._original_rect.width = width
        self._original_rect.height = height

    def set_position(self, x: int, y: int):
        self._original_rect.x = x
        self._original_rect.y = y
    
    def get_parent(self):
        return self._parent
    
    def is_shown(self) -> bool:
        return self._shown
    
    def show(self):
        self._shown = True

    def set_alignment(self, alignment: Alignment):
        self._align = alignment

    def hide(self):
        self._shown = False
    
    def get_rect(self) -> Rect:
        rect = Rect(self._rect)
        if self._parent:
            parent_rect = self._parent.get_rect()
            rect.x += parent_rect.x
            rect.y += parent_rect.y
        return rect

    def get_gui(self):
        return self._gui
    
    def draw(self, game): ...
    
    def update(self, game, dt):
        if self._parent:
            width, height = self._parent._rect.width, self._parent._rect.height
        else:
            width, height = game.get_size()
        
        # Change rect position based on alignment
        if self._align is not None:
            if self._align & Alignment.CENTER:
                self._rect.x = self._original_rect.x + (width - self._rect.width) // 2
                self._rect.y = self._original_rect.y + (height - self._rect.height) // 2
            if self._align & Alignment.LEFT:
                self._rect.x = self._original_rect.x
            if self._align & Alignment.RIGHT:
                self._rect.x = self._original_rect.x + width - self._rect.width
            if self._align & Alignment.TOP:
                self._rect.y = self._original_rect.y
            if self._align & Alignment.BOTTOM:
                self._rect.y = self._original_rect.y + height - self._rect.height
    
    def on_typing(self, game, char: str): ...
    
    def on_hover(self, game, pos): ...
    
    def on_mouse_pressed(self, game, pos, button) -> bool:
        return False
    
    def on_mouse_down(self, game, pos, button) -> bool:
        return False
    
    def on_mouse_up(self, game, pos, button) -> bool:
        return False
    
    def on_mouse_move(self, game, pos): ...


class Panel(GuiElement):
    def __init__(self, rect: Rect):
        super().__init__(rect)
        self._elements: List[GuiElement] = []
        self._clicked_element: GuiElement | None = None
        self._hovered_element: GuiElement | None = None
        self._mouse_rect = Rect(0, 0, 14, 18)
    
    def get_mouse_rect(self):
        return self._mouse_rect

    def add_element(self, element: GuiElement, align: Alignment = None) -> GuiElement:
        element._align = align
        self._elements.append(element)
        return element

    def draw(self, game):
        super().draw(game)
        
        screen = game.get_screen()

        # Check if hovered element is still hovered
        if self._hovered_element and \
            (not self.get_mouse_rect().colliderect(self._hovered_element.get_rect()) or not self._hovered_element.is_shown()):
            self._hovered_element = None
        elif self._hovered_element:
            self._hovered_element.on_hover(game, (self._mouse_rect.x, self._mouse_rect.y))
        
        # Draw all elements on the screen
        for element in self._elements:
            if not element.is_shown():
                continue

            element._gui = self._gui
            element._parent = self
            element.draw(game)
        
        # Debug stuff
        if game.get_options().is_debug_enabled():
        
            # Draw outline around hovered element if any
            if self._hovered_element:
                screen.draw.rect(self._hovered_element.get_rect(), (255, 0, 0))
        
            # Draw mouse outline
            screen.draw.rect(self.get_mouse_rect(), (0, 255, 0))

    def update(self, game, dt):
        super().update(game, dt)
        
        # Update all elements
        for element in self._elements:
            if not element.is_shown():
                continue
            element._gui = self._gui
            element._parent = self
            element.update(game, dt)
            
            # Check if mouse has hovered the element
            if self.get_mouse_rect().colliderect(element.get_rect()):
                self._hovered_element = element

    def on_mouse_down(self, game, pos, button):
        if self._hovered_element and self._hovered_element.is_shown() and not self._clicked_element:
            self._clicked_element = self._hovered_element
            return self._hovered_element.on_mouse_down(game, pos, button)
        return False

    def on_mouse_up(self, game, pos, button):
        if self._clicked_element:
            elem = self._clicked_element
            self._clicked_element = None
            return elem.on_mouse_up(game, pos, button)
        return False

    def on_mouse_pressed(self, game, pos, button):
        if self._hovered_element:
            return self._hovered_element.on_mouse_pressed(game, pos, button)
        return False

    def on_mouse_move(self, game, pos):
        self._mouse_rect = Rect(pos[0], pos[1], 14, 18)
        if self._hovered_element:
            return self._hovered_element.on_mouse_move(game, pos)
        return False


class Text(GuiElement):
    def __init__(self,
                  text,
                  position: Tuple[int, int] | Rect = [0, 0],
                  font_size: int = 16,
                  outline: bool = True,
                  outline_color: Tuple[int, int, int] = (0, 0, 0),
                  color: Tuple[int, int, int] = (255, 255, 255)):
        super().__init__(Rect(position[0], position[1], 0, 0))
        self._text = text
        self._font_size = font_size
        self._outline = outline
        self._outline_color = outline_color
        self._color = color
    
    def set_text(self, text: str):
        self._text = text
    
    def get_text(self) -> str:
        return self._text
    
    def set_font_size(self, font_size: int):
        self._font_size = font_size
    
    def get_font_size(self) -> int:
        return self._font_size
    
    def set_color(self, color: Tuple[int, int, int]):
        self._color = color
    
    def get_color(self) -> Tuple[int, int, int]:
        return self._color
    
    def draw(self, game):
        super().draw(game)
        
        # Draw the text using all provided parameters
        rect = self.get_rect()
        self._gui.draw_text(
            game,
            self._text,
            [rect.x, rect.y],
            font_size=self._font_size,
            outline=self._outline,
            outline_color=self._outline_color,
            color=self._color,
        )
    
    def update(self, game, dt):
        super().update(game, dt)
        # Roughly estimate the text size and update it
        width, height = (len(self._text) * self._font_size) * 0.7, self._font_size * 1.3
        self.set_size(width, height)


class Image(GuiElement):
    def __init__(self, image: Sprite | str, rect: Rect):
        super().__init__(rect)
        self._sprite = image
        if type(image) is str:
            self._sprite = Sprite([image])
    
    def draw(self, game):
        super().draw(game)
        self._sprite.draw(game, self.get_rect(), game.get_surface())
    
    def update(self, game, dt):
        super().update(game, dt)
        self._sprite.update(game, dt)


class ImageButton(GuiElement):
    def __init__(self,
                 image: Sprite | str,
                 rect: Rect,
                 handler: Callable | None = None,
                 is_toggle: bool = False):
        super().__init__(rect)
        self._icon = image
        if type(image) is str:
            self._icon = Sprite([image])
        self._click_handler = handler
        self._is_toggle = is_toggle
        self._toggled_state = False
        self._hovered = False
        self._button_state = False
        self._sprite = Sprite([f"button_small_unpressed"])
        
        self._icon.enable_animation(False)
        self._unpressed_icon = None
        self._pressed_icon = None
    
    def get_state(self) -> bool:
        return self._toggled_state
    
    def draw(self, game):
        rect = self.get_rect()
        
        if not self._unpressed_icon or not self._pressed_icon:
            return
        
        # Draw the button
        if self._button_state:
            self._sprite.set_image(0, f"button_small_pressed")
            self._icon.set_image(0, self._pressed_icon)
        else:
            self._icon.set_image(0, self._unpressed_icon)
            if self._hovered:
                self._sprite.set_image(0, f"button_small_hovered")
            else:
                self._sprite.set_image(0, f"button_small_unpressed")
        
        self._sprite.draw(game, rect, game.get_surface())
        
        # Draw image
        rect.x += (rect.width - rect.width // 2) // 2
        rect.y += (rect.height - rect.height // 2) // 4
        rect.width //= 2
        rect.height //= 2
        self._icon.draw(game, rect, game.get_surface())
    
    def update(self, game, dt):
        super().update(game, dt)
        self._icon.update(game, dt)
        self._sprite.update(game, dt)
        
        if not self._unpressed_icon and not self._pressed_icon:
            self._unpressed_icon = self._icon.get_image(0)
            self._pressed_icon = self._icon.get_image(1)
            if not self._pressed_icon:
                self._pressed_icon = self._unpressed_icon

    def on_hover(self, game, pos):
        super().on_hover(game, pos)
        self._hovered = True
    
    def on_mouse_down(self, game, pos, button):
        super().on_mouse_down(game, pos, button)
        if self._is_toggle:
            self._button_state = not self._toggled_state
        else:
            self._button_state = True
        return True
    
    def on_mouse_up(self, game, pos, button):
        if self._is_toggle:
            self._toggled_state = self._button_state
        else:
            self._button_state = False
        if self._click_handler:
            self._click_handler(self, game, pos, button)
        return True

    def on_mouse_pressed(self, game, pos, button) -> bool:
        return True


class Button(GuiElement):
    def __init__(self,
                 text: str,
                 rect: Rect = Rect(0, 0, 100, 50),
                 sprite: Sprite | None = None,
                 handler: Callable | None = None,
                 is_toggle: bool = False,
                 btn_type: int = 0):
        super(Button, self).__init__(rect)
        self._text = text
        self._sprite = sprite
        self._click_handler = handler
        self._is_toggle = is_toggle
        self._toggled_state = False
        self._hovered = False
        self._button_state = False
        self._btn_type = btn_type
        self._sprite = Sprite([f"button{self._btn_type}_unpressed"])
    
    def get_state(self) -> bool:
        return self._toggled_state
    
    def set_toggle_state(self, state: bool):
        self._toggled_state = state
        self._button_state = state
    
    def get_text(self) -> str:
        return self._text
    
    def get_color(self) -> Tuple[int, int, int]:
        return self._color
    
    def set_color(self, color: Tuple[int, int, int]):
        self._color = color
    
    def set_text(self, text: str):
        self._text = text
    
    def draw(self, game):
        super().draw(game)
        rect = self.get_rect()
        
        # Draw the button
        if self._button_state:
            self._sprite.set_image(0, f"button{self._btn_type}_pressed")
        else:
            if self._hovered:
                self._sprite.set_image(0, f"button{self._btn_type}_hovered")
            else:
                self._sprite.set_image(0, f"button{self._btn_type}_unpressed")
        
        self._sprite.draw(game, rect, game.get_surface())

        # Prepare color for the text based on current button state
        color = (252, 249, 141)
        font_size = 16
        if self._button_state:
            color = (255, 184, 121)
            font_size = 15
        
        # Draw the text
        position = [
            rect.x + (rect.width - (len(self._text) * font_size) * 0.7) // 2,
            rect.y + rect.height // 2 - font_size * 1.3
        ]
        self._gui.draw_text(
            game,
            self._text,
            position,
            color=color,
            font_size=font_size
        )
    
    def update(self, game, dt):
        super().update(game, dt)
        self._sprite.update(game, dt)
        self._hovered = False
    
    def on_hover(self, game, pos):
        super().on_hover(game, pos)
        self._hovered = True
    
    def on_mouse_down(self, game, pos, button):
        super().on_mouse_down(game, pos, button)
        if self._is_toggle:
            self._button_state = not self._toggled_state
        else:
            self._button_state = True
        return True
    
    def on_mouse_up(self, game, pos, button):
        if self._is_toggle:
            self._toggled_state = self._button_state
        else:
            self._button_state = False
        if self._click_handler:
            self._click_handler(self, game, pos, button)
        return True

    def on_mouse_pressed(self, game, pos, button) -> bool:
        return True


class Gui:    
    def __init__(self):
        self._level = None
        self._root_panel = Panel(Rect(0, 0, 0, 0))
        self._root_panel._gui = self
    
    def get_root_panel(self) -> Panel:
        return self._root_panel
    
    def draw_text(self,
                  game,
                  text,
                  position: Tuple[int, int] | Rect,
                  font_size: int = 16,
                  outline: bool = True,
                  outline_color: Tuple[int, int, int] = (0, 0, 0),
                  color: Tuple[int, int, int] = (255, 255, 255)):
        if isinstance(position, Rect):
            position = [position.x, position.y]

        outline_width = 0
        if outline:
            outline_width = 2

        screen = game.get_screen()
        screen.draw.text(
            text,
            position,
            fontname="font",
            color=color,
            fontsize=font_size,
            owidth=outline_width,
            ocolor=outline_color,
        )
    
    def get_mouse_rect(self):
        return self._root_panel.get_mouse_rect()

    def add_element(self, element: GuiElement, align: Alignment = None) -> GuiElement:
        return self._root_panel.add_element(element, align)

    def draw(self, game, level, surface):
        self._root_panel.draw(game)

    def update(self, game, level, dt):
        width, height = game.get_size()
        self._root_panel._rect.width = width
        self._root_panel._rect.height = height
        self._root_panel._original_rect.width = width
        self._root_panel._original_rect.height = height
        self._root_panel.update(game, dt)

    def on_mouse_down(self, game, level, pos, button) -> bool:
        return self._root_panel.on_mouse_down(game, pos, button)

    def on_mouse_up(self, game, level, pos, button) -> bool:
        return self._root_panel.on_mouse_up(game, pos, button)

    def on_mouse_move(self, game, level, pos):
        self._root_panel.on_mouse_move(game, pos)
        
    def on_mouse_pressed(self, game, level, pos, button) -> bool:
        return self._root_panel.on_mouse_pressed(game, pos, button)
