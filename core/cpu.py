from typing import List
from random import randint

from core.memory import Memory
from core.display import Display
from configs import REGISTER_COUNT, ROM_START_IDX, STACK_SIZE


class CPU:
    memory: Memory
    display: Display
    registers: List[int]
    pc: int
    pc_modified: bool
    i: int
    stack: List[int]
    sp: int
    opcode: int

    def __init__(self):
        self.memory = Memory()
        self.display = Display()
        self.registers = [0] * REGISTER_COUNT
        self.pc = ROM_START_IDX
        self.pc_modified = False
        self.i = 0
        self.stack = [0] * STACK_SIZE
        self.sp = 0

    def high_nibble_dispatch(self):
        """
        This function acts as a top level categorization for opcodes. Codes 0x3??? 
        through 0x7??? are grouped together, since those codes are for skipping lines,
        and altering register with outside values.
        """
        match self.opcode & 0xF000:
            case 0x0000:
                self.dispatch_sys_control()
            case 0x1000 | 0xB000:
                self.jump()
            case 0x2000:
                self.call()
            case 0x3000 | 0x4000 | 0x5000 | 0x9000:
                self.dispatch_comparison()
            case 0x6000:
                self.set_reg()
            case 0x7000:
                self.add_nn_no_carry()
            case 0x8000:
                self.dispatch_reg_arithmetic()
            case 0xA000:
                self.set_i()
            case 0xC000:
                self.set_random_byte()
            case 0xD000:
                self.draw_sprite()
            case 0xE000:
                pass
            case 0xF000:
                pass
            case _:
                raise ValueError(f"Code {self.opcode} not supported.")

    def _second_nibble(self):
        return (self.opcode & 0x0F00) >> 8
    
    def _third_nibble(self):
        return (self.opcode & 0x00F0) >> 4
    
    def _fourth_nibble(self):
        return self.opcode & 0x000F
    
    def _second_byte(self):
        return self.opcode & 0x00FF
    
    def _last_3_nibbles(self):
        return self.opcode & 0x0FFF
    
    def dispatch_sys_control(self):
        match self.opcode & 0x0FFF:
            case 0x00E0:
                self.display.clear_screen()
            case 0x00EE:
                self.return_from_subroutine()
            case _:
                raise ValueError(f"Code {self.opcode} not supported.")
            
    def return_from_subroutine(self):
        self.sp -= 1
        self.pc = self.stack[self.sp]

    def jump(self):
        destination = self.opcode & 0x0FFF
        match self.opcode & 0xF000:
            case 0x1000:
                self.pc = destination
            case 0xB000:
                self.pc = destination + self.registers[0]
            case _:
                raise ValueError(f"Code {self.opcode} not supported.")
        self.pc_modified = True

    def call(self):
        self.stack[self.sp] = self.pc
        self.sp += 1
        self.pc = self.opcode & 0x0FFF
        self.pc_modified = True

    def dispatch_comparison(self):
        match self.opcode & 0xF000:
            case 0x3000 | 0x4000:
                self.skip_eq_neq_nn(self.opcode)
            case 0x5000 | 0x9000:
                self.skip_eq_neq_reg(self.opcode)
    
    def skip_eq_neq_nn(self):
        reg_value = self.registers[self._second_nibble(self.opcode)]
        value = self._second_byte(self.opcode)
        if (
            (self.opcode & 0xF000 == 0x3000 and value == reg_value) or 
            (self.opcode & 0xF000 == 0x4000 and value != reg_value)
        ):
            self.pc += 2

    def skip_eq_neq_reg(self):
        reg1_value = self.registers[self._second_nibble(self.opcode)]
        reg2_value = self.registers[self._third_nibble(self.opcode)]
        if (
            (self.opcode & 0xF00F == 0x5000 and reg1_value == reg2_value) or 
            (self.opcode & 0xF00F == 0x9000 and reg1_value != reg2_value)
        ):
            self.pc += 2

    def set_reg(self):
        reg_idx = self._second_nibble(self.opcode)
        self.registers[reg_idx] = self._second_byte(self.opcode)

    def add_nn_no_carry(self):
        reg_idx = self._second_nibble(self.opcode)
        value = self._second_byte(self.opcode)
        self.registers[reg_idx] = (self.registers[reg_idx] + value) % 256

    def dispatch_reg_arithmetic(self):
        reg1_idx = self._second_nibble(self.opcode)
        reg1_value = self.registers[reg1_idx]
        reg2_value = self.registers[self._third_nibble(self.opcode)]
        match self.opcode & 0x000F:
            case 0x0000:
                self.registers[reg1_idx] = reg2_value
            case 0x0001:
                self.registers[reg1_idx] = reg1_value | reg2_value
            case 0x0002:
                self.registers[reg1_idx] = reg1_value & reg2_value
            case 0x0003:
                self.registers[reg1_idx] = reg1_value ^ reg2_value
            case 0x0004:
                self.add_reg_carry(reg1_idx, reg1_value, reg2_value)
            case 0x0005:
                self.sub_reg_borrow(reg1_idx, reg1_value, reg2_value)
            case 0x0006:
                self.shift_reg_right(reg1_idx, reg1_value)
            case 0x0007:
                self.sub_reg_borrow(reg1_idx, reg2_value, reg1_value)
            case 0x000E:
                self.shift_reg_left(reg1_idx, reg1_value)
            case _:
                ValueError(f"Code {self.opcode} not supported.")

    def add_reg_carry(self, reg_idx: int, value1: int, value2: int):
        sum_ = value1 + value2
        self.registers[-1] = 1 if sum_ > 255 else 0
        self.registers[reg_idx] = sum_ % 256

    def sub_reg_borrow(self, reg_idx: int, value1: int, value2: int):
        diff = value1 - value2
        self.registers[-1] = 0 if diff < 0 else 1
        self.registers[reg_idx] = (diff + 256) % 256

    def shift_reg_right(self, reg_idx: int, value1: int):
        self.registers[-1] = value1 & 0b0000_0001
        self.registers[reg_idx] = value1 >> 1

    def shift_reg_left(self, reg_idx: int, value1: int):
        self.registers[-1] = value1 & 0b1000_0000
        self.registers[reg_idx] = (value1 & 0b0111_1111) << 1

    def set_i(self):
        self.i = self._last_3_nibbles(self.opcode)

    def set_random_byte(self):
        reg_idx = self._second_nibble(self.opcode)
        value = self._second_byte(self.opcode)
        self.registers[reg_idx] = value & randint(0, 255)

    def draw_sprite(self):
        x = self._second_nibble(self.opcode)
        y = self._third_nibble(self.opcode)
        size = self._fourth_nibble(self.opcode)
        byte_array = [self.memory.read_byte(self.i + j) for j in range(size)]
        collision = self.display.draw_sprite(x, y, byte_array)
        self.registers[-1] = collision
    
