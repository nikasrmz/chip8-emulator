from time import sleep
from typing import Dict, List

import keyboard

class Input_: 
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
        return keyboard.is_pressed(self.chip8_to_qwerty(key))

    def key_not_pressed(self, key: int) -> bool:
        return not self.key_pressed(key)

    def wait_store_key(self) -> int:
        prev_key_states = self._key_states()
        while True:
            curr_key_states = self._key_states()
            for idx in range(len(curr_key_states)):
                if curr_key_states[idx] and not prev_key_states[idx]:
                    return idx
            prev_key_states = curr_key_states
            sleep(0.01)

    def _key_states(self) -> List[int]:
        key_states = [False] * 16
        for k in self.chip8_to_qwerty.keys():
            if self.key_pressed(k):
                key_states[k] = True
        return key_states
