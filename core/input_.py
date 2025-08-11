from time import sleep
from typing import Dict, List, Optional

import keyboard

class Input_: 
    """
   CHIP-8 Input Handler
   
   Manages keyboard input by mapping QWERTY keys to the CHIP-8 hexadecimal keypad.
   Provides both immediate key state checking and event-based key press detection
   for different emulation scenarios.
   
   CHIP-8 Keypad Layout (mapped to QWERTY):
   ┌───────────────┐    ┌───────────────┐
   │ 1 │ 2 │ 3 │ C │    │ 1 │ 2 │ 3 │ 4 │
   ├───┼───┼───┼───┤ -> ├───┼───┼───┼───┤
   │ 4 │ 5 │ 6 │ D │    │ Q │ W │ E │ R │
   ├───┼───┼───┼───┤    ├───┼───┼───┼───┤
   │ 7 │ 8 │ 9 │ E │    │ A │ S │ D │ F │
   ├───┼───┼───┼───┤    ├───┼───┼───┼───┤
   │ A │ 0 │ B │ F │    │ Z │ X │ C │ V │
   └───────────────┘    └───────────────┘
   
   Attributes:
       qwerty_to_chip8: Maps QWERTY key strings to CHIP-8 hex values (0x0-0xF)
       chip8_to_qwerty: Reverse mapping from CHIP-8 hex values to QWERTY keys
       last_key_states: Previous frame key states for change detection
   """
    qwerty_to_chip8: Dict[str, int]
    chip8_to_qwerty: Dict[int, str]

    def __init__(self):
        self.qwerty_to_chip8 = {
            "1": 0x1, "2": 0x2, "3": 0x3, "4": 0xC,
            "q": 0x4, "w": 0x5, "e": 0x6, "r": 0xD,
            "a": 0x7, "s": 0x8, "d": 0x9, "f": 0xE,
            "z": 0xA, "x": 0x0, "c": 0xB, "v": 0xF
        }
        self.chip8_to_qwerty = {v: k for k, v in self.qwerty_to_chip8.items()}

    def key_pressed(self, key: int) -> bool:
        """
       Check if a CHIP-8 key is currently pressed.
       
       Used for immediate key state queries (e.g., skip instructions Ex9E/ExA1).
       
       Args:
           key: CHIP-8 key code (0x0-0xF)
           
       Returns:
           True if the key is currently pressed, False otherwise
           
       Raises:
           KeyError: If key is not in valid range (0x0-0xF)
       """
        return keyboard.is_pressed(self.chip8_to_qwerty[key])

    def key_not_pressed(self, key: int) -> bool:
        """
       Check if a CHIP-8 key is currently not pressed.
       
       Convenience method for inverted key checking logic.
       
       Args:
           key: CHIP-8 key code (0x0-0xF)
           
       Returns:
           True if the key is not pressed, False if pressed
       """
        return not self.key_pressed(key)
    
    def start_waiting(self):
        """
       Begin waiting for key press events.
       
       Captures current key states as baseline for detecting new key presses.
       Must be called before using check_keystates_changed(). Used by the
       Fx0A instruction to wait for user input.
       """
        self.last_key_states = self._key_states()
        
    def check_keystates_changed(self) -> Optional[int]:
        """
       Detect newly pressed keys since start_waiting() was called.
       
       Compares current key states with the baseline captured by start_waiting().
       Returns the first key that transitioned from not-pressed to pressed.
       Updates internal state to prevent duplicate detection.
       
       Returns:
           CHIP-8 key code (0x0-0xF) of newly pressed key, or None if no new presses
           
       Note:
           Only detects key press events (down transitions), not releases.
           Call start_waiting() first to establish baseline state.
       """
        curr_key_states = self._key_states()
        for idx in range(len(curr_key_states)):
            if curr_key_states[idx] and not self.last_key_states[idx]:
                self.last_key_states = curr_key_states
                return idx
        self.last_key_states = curr_key_states
        return None

    def _key_states(self) -> List[bool]:
        """
       Get current state of all 16 CHIP-8 keys.
       
       Internal helper method that polls all mapped keys and returns their
       current pressed/released states.
       
       Returns:
           List of 16 boolean values, indexed by CHIP-8 key code (0x0-0xF).
           True indicates the key is currently pressed.
       """
        key_states = [False] * 16
        for k in self.chip8_to_qwerty.keys():
            if self.key_pressed(k):
                key_states[k] = True
        return key_states
