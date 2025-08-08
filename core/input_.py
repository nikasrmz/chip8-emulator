from typing import Dict
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
        return not keyboard.is_pressed(self.chip8_to_qwerty(key)) 

    def wait_store_key(self) -> int:
        pass # TODO
