from time import sleep
from typing import Optional

from core.cpu import CPU
from core.input_ import Input_
from core.memory import Memory
from core.display import Display
from configs import TARGET_IPS

class Emulator:
    cpu: CPU
    input_: Input_
    memory: Memory
    display: Display
    delay_between_ops: float
    cpu_cycles: int
    cpu_cycles_max: int

    def __init__(self, game: Optional[str] = None):
        self.input_ = Input_()
        self.memory = Memory()
        if game:
            self.memory.load_game(game)
        self.display = Display()
        self.cpu = CPU(self.memory, self.display, self.input_)
        self.delay_between_ops = 1.0 / TARGET_IPS
        self.cpu_cycles = 0
        self.cpu_cycles_max = TARGET_IPS // 60
        

    def emulate(self):
        while True:
            self.cpu.cycle()
            sleep(self.delay_between_ops)
            self.cpu_cycles += 1
            if self.cpu_cycles >= self.cpu_cycles_max:
                self.cpu_cycles = 0
                self.display.refresh()
                self.cpu.update_timers()
            


            

