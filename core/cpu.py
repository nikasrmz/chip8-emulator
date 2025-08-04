from typing import List

from configs import REGISTER_COUNT, ROM_START_IDX, STACK_SIZE
from core import Memory, Display


class CPU:
    memory: Memory
    display: Display
    registers: List[int]
    pc: int
    i: int
    stack: List[int]
    sp: int

    def __init__(self):
        self.memory = Memory()
        self.display = Display()
        self.registers = [0] * REGISTER_COUNT
        self.pc = ROM_START_IDX
        self.i = 0
        self.stack = [0] * STACK_SIZE
        self.sp = 0

    def high_nibble_dispatch(self, opcode: int):
        """
        This function acts as a top level categorization for opcodes. Codes 0x3??? 
        through 0x7??? are grouped together, since those codes are for skipping lines,
        and altering register with outside values.

        Parameters:
            opcode: code to be dispatched
        """
        match opcode & 0xF000:
            case 0x0000:
                self.sys_control(opcode)
            case 0x1000 | 0xB000:
                self.jump(opcode)
            case 0x2000:
                self.call(opcode)
            case 0x3000 | 0x4000 | 0x5000 | 0x6000 | 0x7000:
                pass
            case 0x8000:
                pass
            case 0x9000:
                pass
            case 0xA000:
                pass
            case 0xC000:
                pass
            case 0xD000:
                pass
            case 0xE000:
                pass
            case 0xF000:
                pass
            case _:
                raise NotImplementedError(f"Code {opcode} not supported.")

    def sys_control(self, opcode: int):
        match opcode & 0x0FFF:
            case 0x00E0:
                self.display.clear_screen()
            case 0x00EE:
                self.return_from_subroutine()
            case _:
                raise NotImplementedError(f"Code {opcode} not supported.")
            
    def return_from_subroutine(self):
        self.sp -= 1
        self.pc = self.stack[self.sp]

    def jump(self, opcode: int):
        destination = opcode & 0x0FFF
        match opcode & 0xF000:
            case 0x1000:
                self.pc = destination
            case 0xB000:
                self.pc = destination + self.registers[0]
            case _:
                raise 

    def call(self, opcode: int):
        self.stack[self.sp] = self.pc
        self.sp += 1
        self.pc = opcode & 0x0FFF

        
