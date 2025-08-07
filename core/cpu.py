from typing import List
from random import randint
from datetime import datetime

from core.memory import Memory
from core.display import Display
from core.input_ import Input_
from core.errors import UnsupportedOpcodeError
from configs import REGISTER_COUNT, ROM_START_IDX, STACK_SIZE, VF_IDX


class CPU:
    memory: Memory
    display: Display
    input_: Input_
    registers: List[int]
    pc: int
    pc_modified: bool
    i: int
    stack: List[int]
    sp: int
    opcode: int
    delay_timer: int
    sound_timer: int
    last_timer_update: datetime

    def __init__(self, memory: Memory, display: Display, input_: Input_):
        self.memory = memory
        self.display = display
        self.input_ = input_
        self.registers = [0] * REGISTER_COUNT
        self.pc = ROM_START_IDX
        self.pc_modified = False
        self.i = 0
        self.stack = [0] * STACK_SIZE
        self.sp = 0
        self.last_timer_update = datetime.now()

    def cycle(self):
        self.opcode = self.memory.read_word(self.pc)
        self.dispatch()
        if not self.pc_modified:
            self.pc += 2
        self.pc_modified = False
        self.display.refresh()
        self.update_timers()
            

    def update_timers(self):
        time_now = datetime.now()
        if time_now - self.last_timer_update >= 1 / 60:
            if self.delay_timer > 0:
                self.delay_timer -= 1
            if self.sound_timer > 0:
                self.sound_timer -= 1
            self.last_timer_update = time_now


    def dispatch(self):
        """
        This method acts as a top level categorization for opcodes. Some codes (ex: the
        ones starting on 0x1, 0xB) are grouped together, since those codes share 
        similar purposes and/or use the same function. Some codes are passed to second
        layer of categorization.
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
                self.process_input()
            case 0xF000:
                self.dispatch_misc_fx()
            case _:
                raise UnsupportedOpcodeError(f"Code {self.opcode} not supported.")

    def _second_nibble(self):
        """
        Returns second nibble (4 bits) of current opcode. (ex: 2 from 0x1234)
        """
        return (self.opcode & 0x0F00) >> 8
    
    def _third_nibble(self):
        """
        Returns third nibble (4 bits) of current opcode. (ex: 3 from 0x1234)
        """
        return (self.opcode & 0x00F0) >> 4
    
    def _fourth_nibble(self):
        """
        Returns fourth nibble (4 bits) of current opcode. (ex: 4 from 0x1234)
        """
        return self.opcode & 0x000F
    
    def _second_byte(self):
        """
        Returns second byte (8 bits) of current opcode. (ex: 34 from 0x1234)
        """
        return self.opcode & 0x00FF
    
    def _last_3_nibbles(self):
        """
        Returns last three nibbles (12 bits) of current opcode. (ex: 234 from 0x1234)
        """
        return self.opcode & 0x0FFF
    
    def dispatch_sys_control(self):
        """
        Second layer categorization, system & flow control. (codes starting on 0x0)
        """
        match self.opcode & 0x0FFF:
            case 0x00E0:
                self.display.clear_screen()
            case 0x00EE:
                self.return_from_subroutine()
            case _:
                raise UnsupportedOpcodeError(f"Code {self.opcode} not supported.")
            
    def return_from_subroutine(self):
        """
        Handler for code 00EE - RET.
        """
        if self.sp == 0:
            raise RuntimeError("RET called with empty stack")
        self.sp -= 1
        self.pc = self.stack[self.sp]

    def jump(self):
        """
        Handler for codes: 1nnn - JP nnn and Bnnn - JP V0, nnn
        """
        destination = self.opcode & 0x0FFF
        match self.opcode & 0xF000:
            case 0x1000:
                self.pc = destination
            case 0xB000:
                self.pc = destination + self.registers[0]
            case _:
                raise UnsupportedOpcodeError(f"Code {self.opcode} not supported.")
        self.pc_modified = True

    def call(self):
        """
        Handler for code 2nnn - CALL nnn
        """
        self.stack[self.sp] = self.pc
        self.sp += 1
        self.pc = self.opcode & 0x0FFF
        self.pc_modified = True

    def dispatch_comparison(self):
        """
        Second layer categorization, equality and inequality (codes starting on
        0x3, 0x4, 0x5, 0x9) 
        """
        match self.opcode & 0xF000:
            case 0x3000 | 0x4000:
                self.skip_eq_neq_nn()
            case 0x5000 | 0x9000:
                self.skip_eq_neq_reg()
    
    def skip_eq_neq_nn(self):
        """
        Handler for codes: 3xkk - SE Vx, kk; 4xkk - SNE Vx, kk.
        """
        reg_value = self.registers[self._second_nibble(self.opcode)]
        value = self._second_byte(self.opcode)
        if (
            (self.opcode & 0xF000 == 0x3000 and value == reg_value) or 
            (self.opcode & 0xF000 == 0x4000 and value != reg_value)
        ):
            self.pc += 2

    def skip_eq_neq_reg(self):
        """
        Handler for codes: 5xy0 - SE Vx, Vy; 9xy0 - SNE Vx, Vy.
        """
        reg1_value = self.registers[self._second_nibble(self.opcode)]
        reg2_value = self.registers[self._third_nibble(self.opcode)]
        if (
            (self.opcode & 0xF00F == 0x5000 and reg1_value == reg2_value) or 
            (self.opcode & 0xF00F == 0x9000 and reg1_value != reg2_value)
        ):
            self.pc += 2

    def set_reg(self):
        """
        Handler for code 6xkk - LD Vx, kk.
        """
        reg_idx = self._second_nibble(self.opcode)
        self.registers[reg_idx] = self._second_byte(self.opcode)

    def add_nn_no_carry(self):
        """
        Handler for code 7xkk - ADD Vx, kk
        """
        reg_idx = self._second_nibble(self.opcode)
        value = self._second_byte(self.opcode)
        self.registers[reg_idx] = (self.registers[reg_idx] + value) % 256

    def dispatch_reg_arithmetic(self):
        """
        Second layer categorization, arithmetic operations between registers. (codes
        starting with 0x8)

        8xy0 - LD Vx Vy
        8xy1, 8xy2 and 8xy3, Bitwise operation assignment between registers.  
        """
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
                UnsupportedOpcodeError(f"Code {self.opcode} not supported.")

    def add_reg_carry(self, reg_idx: int, value1: int, value2: int):
        """
        Handler for code 8xy4 - ADD Vx, Vy
        """
        sum_ = value1 + value2
        self.registers[VF_IDX] = 1 if sum_ > 255 else 0
        self.registers[reg_idx] = sum_ % 256

    def sub_reg_borrow(self, reg_idx: int, value1: int, value2: int):
        """
        Handler for codes: 8xy5 - SUB Vx, Vy; 8xy7 - SUBN Vx, Vy
        """
        diff = value1 - value2
        self.registers[VF_IDX] = 0 if diff < 0 else 1
        self.registers[reg_idx] = (diff + 256) % 256

    def shift_reg_right(self, reg_idx: int, value1: int):
        """
        Handler for code 8xy6 - SHR Vx {, Vy}
        """
        self.registers[VF_IDX] = value1 & 0b0000_0001
        self.registers[reg_idx] = value1 >> 1

    def shift_reg_left(self, reg_idx: int, value1: int):
        """
        Handler for code 8xyE - SHL Vx {, Vy}
        """
        self.registers[VF_IDX] = (value1 & 0b1000_0000) >> 7
        self.registers[reg_idx] = (value1 & 0b0111_1111) << 1

    def set_i(self):
        """
        Handler for code Annn - LD I nnn
        """
        self.i = self._last_3_nibbles(self.opcode)

    def set_random_byte(self):
        """
        Handler for code Cxkk - RND Vx, kk
        """
        reg_idx = self._second_nibble(self.opcode)
        value = self._second_byte(self.opcode)
        self.registers[reg_idx] = value & randint(0, 255)

    def draw_sprite(self):
        """
        Handler for code Dxyn - DRW, Vx, Vy, n
        """
        x = self._second_nibble(self.opcode)
        y = self._third_nibble(self.opcode)
        size = self._fourth_nibble(self.opcode)
        byte_array = [self.memory.read_byte(self.i + j) for j in range(size)]
        collision = self.display.draw_sprite(x, y, byte_array)
        self.registers[VF_IDX] = collision

    def process_input(self):
        key = self.registers[self._second_nibble(self.opcode)]
        low_byte = self._second_byte(self.opcode)
        if (
            (low_byte == 0x9E and self.input_.key_pressed(key)) or
            (low_byte == 0xA1 and self.input_.key_not_pressed(key))
        ):
            self.pc += 2

    def dispatch_misc_fx(self):
        reg_idx = self._second_nibble(self.opcode)
        match self.opcode & 0x00FF:
            case 0x0007:
                self.registers[reg_idx] = self.delay_timer
            case 0x000A:
                self.registers[reg_idx] = self.input_.wait_store_key()
            case 0x0015:
                self.delay_timer = self.registers[reg_idx]
            case 0x0018:
                self.sound_timer = self.registers[reg_idx]
            case 0x001E:
                self.i += self.registers[reg_idx]
            case 0x0029:
                self.memory.get_sprite_address(self.registers[reg_idx])
            case 0x0033:
                self.store_bcd()
            case 0x0055:
                self.exchange_regs_memory(write=True)
            case 0x0065:
                self.exchange_regs_memory(write=False)
            case _:
                UnsupportedOpcodeError(f"Code {self.opcode} not supported.")

    def store_bcd(self):
        val = self.registers[self._second_nibble(self.opcode)]
        for j in range(3):
            digit = (val // (10 ** (2 - j))) % 10
            self.memory.write_byte(self.i + j, digit)

    def exchange_regs_memory(self, write: bool):
        reg_idx = self._second_nibble(self.opcode)
        for idx in range(reg_idx):
            if write:
                self.memory.write_byte(self.i + idx, self.registers[idx])
            else:
                self.registers[idx] = self.memory.read_byte(self.i + idx)
