from typing import Optional

from core.cpu import CPU
from core.input_ import Input_
from core.memory import Memory
from core.display import Display

class Emulator:
    cpu: CPU
    input_: Input_
    memory: Memory
    display: Display

    def __init__(self, game: Optional[str] = None):
        self.input_ = Input_()
        self.memory = Memory()
        if game:
            self.memory.load_game(game)
        self.display = Display()
        self.cpu = CPU(self.memory, self.display, self.input_)

    def emulate(self):
        while True:
            self.cpu.cycle()
            self.display.refresh()

            

