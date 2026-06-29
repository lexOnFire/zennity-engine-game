import pygame
from typing import Tuple, Dict

class Input:
    """Manages input states (keyboard, mouse) with support for key transitions."""
    _keys_current = pygame.key.ScancodeWrapper()
    _keys_previous = pygame.key.ScancodeWrapper()
    
    _mouse_current = (False, False, False)
    _mouse_previous = (False, False, False)
    _mouse_position = (0, 0)
    _mouse_rel = (0, 0)

    @classmethod
    def update(cls) -> None:
        """Updates keyboard and mouse states. Should be called once per frame by the engine core."""
        # Keyboard
        cls._keys_previous = cls._keys_current
        cls._keys_current = pygame.key.get_pressed()
        
        # Mouse
        cls._mouse_previous = cls._mouse_current
        cls._mouse_current = pygame.mouse.get_pressed()
        cls._mouse_position = pygame.mouse.get_pos()
        cls._mouse_rel = pygame.mouse.get_rel()

    # Keyboard methods
    @classmethod
    def get_key(cls, key: int) -> bool:
        """Returns True if the key is currently held down."""
        if not cls._keys_current:
            return False
        try:
            return bool(cls._keys_current[key])
        except IndexError:
            return False

    @classmethod
    def get_key_down(cls, key: int) -> bool:
        """Returns True only in the frame the key was pressed down."""
        if not cls._keys_current or not cls._keys_previous:
            return False
        try:
            return bool(cls._keys_current[key]) and not bool(cls._keys_previous[key])
        except IndexError:
            return False

    @classmethod
    def get_key_up(cls, key: int) -> bool:
        """Returns True only in the frame the key was released."""
        if not cls._keys_current or not cls._keys_previous:
            return False
        try:
            return not bool(cls._keys_current[key]) and bool(cls._keys_previous[key])
        except IndexError:
            return False

    # Mouse methods
    @classmethod
    def get_mouse_position(cls) -> Tuple[int, int]:
        """Returns the current mouse position as (x, y)."""
        return cls._mouse_position

    @classmethod
    def get_mouse_rel(cls) -> Tuple[int, int]:
        """Returns the relative mouse movement since the last frame as (dx, dy)."""
        return cls._mouse_rel

    @classmethod
    def get_mouse_button(cls, button: int) -> bool:
        """Returns True if the mouse button (0: Left, 1: Middle, 2: Right) is held."""
        try:
            return bool(cls._mouse_current[button])
        except IndexError:
            return False

    @classmethod
    def get_mouse_button_down(cls, button: int) -> bool:
        """Returns True if the mouse button (0: Left, 1: Middle, 2: Right) was pressed this frame."""
        try:
            return bool(cls._mouse_current[button]) and not bool(cls._mouse_previous[button])
        except IndexError:
            return False

    @classmethod
    def get_mouse_button_up(cls, button: int) -> bool:
        """Returns True if the mouse button (0: Left, 1: Middle, 2: Right) was released this frame."""
        try:
            return not bool(cls._mouse_current[button]) and bool(cls._mouse_previous[button])
        except IndexError:
            return False

    # Input helpers
    @classmethod
    def get_axis_horizontal(cls) -> float:
        """Returns -1.0 for left movement, 1.0 for right, or 0.0."""
        val = 0.0
        if cls.get_key(pygame.K_LEFT) or cls.get_key(pygame.K_a):
            val -= 1.0
        if cls.get_key(pygame.K_RIGHT) or cls.get_key(pygame.K_d):
            val += 1.0
        return val

    @classmethod
    def get_axis_vertical(cls) -> float:
        """Returns -1.0 for up movement (in standard game controls), 1.0 for down, or 0.0."""
        val = 0.0
        if cls.get_key(pygame.K_UP) or cls.get_key(pygame.K_w):
            val -= 1.0
        if cls.get_key(pygame.K_DOWN) or cls.get_key(pygame.K_s):
            val += 1.0
        return val
