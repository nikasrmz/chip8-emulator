from typing import List

from configs import REGISTER_COUNT, ROM_START_IDX, STACK_SIZE
from core import Memory, Display


class CPU:
    memory: Memory
    display: Display
    registers: List[int]
    pc: int
    pc_modified: bool
    i: int
    stack: List[int]
    sp: int

    def __init__(self):
        self.memory = Memory()
        self.display = Display()
        self.registers = [0] * REGISTER_COUNT
        self.pc = ROM_START_IDX
        self.pc_modified = False
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
                self.dispatch_sys_control(opcode)
            case 0x1000 | 0xB000:
                self.jump(opcode)
            case 0x2000:
                self.call(opcode)
            case 0x3000 | 0x4000 | 0x5000 | 0x9000:
                self.dispatch_comparison(opcode)
            case 0x6000 | 0x7000:
                pass
            case 0x8000:
                pass
            case 0xA000:
                self.set_i(opcode)
            case 0xC000:
                pass
            case 0xD000:
                pass
            case 0xE000:
                pass
            case 0xF000:
                pass
            case _:
                raise ValueError(f"Code {opcode} not supported.")

    def _second_nibble(self, opcode: int):
        return (opcode & 0x0F00) >> 8
    
    def _third_nibble(self, opcode: int):
        return (opcode & 0x00F0) >> 4
    
    def _fourth_nibble(self, opcode: int):
        return opcode & 0x000F
    
    def _second_byte(self, opcode: int):
        return opcode & 0x00FF
    
    def _last_3_nibbles(self, opcode: int):
        return opcode & 0x0FFF
    
    def dispatch_sys_control(self, opcode: int):
        match opcode & 0x0FFF:
            case 0x00E0:
                self.display.clear_screen()
            case 0x00EE:
                self.return_from_subroutine()
            case _:
                raise ValueError(f"Code {opcode} not supported.")
            
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
                raise ValueError(f"Code {opcode} not supported.")
        self.pc_modified = True

    def call(self, opcode: int):
        self.stack[self.sp] = self.pc
        self.sp += 1
        self.pc = opcode & 0x0FFF
        self.pc_modified = True

    def dispatch_comparison(self, opcode: int):
        match opcode & 0xF000:
            case 0x3000 | 0x4000:
                self.skip_eq_neq_nn(opcode)
            case 0x5000 | 0x9000:
                self.skip_eq_neq_reg(opcode)
    
    def skip_eq_neq_nn(self, opcode: int):
        reg_value = self.registers[self._second_nibble(opcode)]
        value = self._second_byte(opcode)
        if (
            (opcode & 0xF000 == 0x3000 and value == reg_value) or 
            (opcode & 0xF000 == 0x4000 and value != reg_value)
        ):
            self.pc += 2

    def skip_eq_neq_reg(self, opcode: int):
        reg1_value = self.registers[self._second_nibble(opcode)]
        reg2_value = self.registers[self._third_nibble(opcode)]
        if (
            (opcode & 0xF00F == 0x5000 and reg1_value == reg2_value) or 
            (opcode & 0xF00F == 0x9000 and reg1_value != reg2_value)
        ):
            self.pc += 2

    def set_i(self, opcode: int):
        self.i = self._last_3_nibbles(opcode)
    