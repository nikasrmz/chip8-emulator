from typing import List
from random import randint
from time import perf_counter

from core.memory import Memory
from core.display import Display
from core.input_ import Input_
from core.errors import UnsupportedOpcodeError
from configs import REGISTER_COUNT, ROM_START_IDX, STACK_SIZE, VF_IDX


class CPU:
   """
   CHIP-8 Central Processing Unit
   
   Implements the complete CHIP-8 instruction set with fetch-decode-execute cycle,
   register management, stack operations, and timer handling. Supports all 35
   standard CHIP-8 instructions with proper flag handling and control flow.
   
   Architecture:
   - 16 8-bit general-purpose registers (V0-VF)
   - 16-bit program counter (PC)
   - 16-bit index register (I)
   - 16-level stack for subroutine calls
   - 8-bit delay and sound timers (60Hz countdown)
   
   The CPU operates at configurable speed and integrates with memory, display,
   and input subsystems to provide complete CHIP-8 emulation.
   
   Attributes:
       memory: Memory subsystem reference
       display: Display subsystem reference  
       input_: Input subsystem reference
       registers: 16 8-bit registers (V0-VF, where VF is flags register)
       pc: 16-bit program counter
       pc_modified: Flag to prevent auto-increment after jumps/calls
       i: 16-bit index register
       stack: 16-level call stack
       sp: Stack pointer (0-15)
       opcode: Currently executing 16-bit instruction
       delay_timer: 8-bit delay timer (decrements at 60Hz)
       sound_timer: 8-bit sound timer (decrements at 60Hz)
       last_timer_update: Timestamp for 60Hz timer management
       waiting_for_key: Flag indicating CPU is blocked waiting for input
   """
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
   last_timer_update: float

   def __init__(self, memory: Memory, display: Display, input_: Input_):
       """
       Initialize CPU with default state and component references.
       
       Sets up registers, timers, and internal state for emulation start.
       Program counter begins at ROM_START_IDX (0x200) following CHIP-8 convention.
       
       Args:
           memory: Memory management system
           display: Graphics display system
           input_: Keyboard input handler
       """
       self.memory = memory
       self.display = display
       self.input_ = input_
       self.registers = [0] * REGISTER_COUNT
       self.pc = ROM_START_IDX
       self.pc_modified = False
       self.i = 0
       self.stack = [0] * STACK_SIZE
       self.sp = 0
       self.delay_timer = 0
       self.sound_timer = 0
       self.last_timer_update = perf_counter()
       self.waiting_for_key = False

   def cycle(self):
       """
       Execute one CPU cycle: fetch, decode, execute.
       
       Performs the standard CPU cycle unless blocked waiting for input.
       Fetches 16-bit instruction from memory at PC, dispatches to appropriate
       handler, and increments PC unless modified by jump/call instructions.
       """
       if not self.waiting_for_key:
           self.opcode = self.memory.read_word(self.pc)
           self.dispatch()
           if not self.pc_modified:
               self.pc += 2
           self.pc_modified = False
       else: 
           self.waiting_for_key = not self.check_any_key_pressed()
           

   def update_timers(self):
       """
       Update delay and sound timers at 60Hz frequency.
       
       Decrements both timers if they are non-zero and sufficient time has
       elapsed since last update. Maintains accurate 60Hz timing regardless
       of CPU instruction frequency.
       """
       time_now = perf_counter()
       if time_now - self.last_timer_update >= 1 / 60:
           if self.delay_timer > 0:
               self.delay_timer -= 1
           if self.sound_timer > 0:
               self.sound_timer -= 1
           self.last_timer_update = time_now


   def dispatch(self):
       """
       Decode and dispatch instruction to appropriate handler.
       
       Top-level instruction categorization based on the first nibble.
       Routes opcodes to specialized handlers or secondary dispatchers
       for complete instruction set coverage.
       
       Raises:
           UnsupportedOpcodeError: For unimplemented or invalid opcodes
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
       Extract second nibble from current opcode.
       
       Returns:
           Second 4-bit nibble (e.g., 0x2 from 0x1234)
       """
       return (self.opcode & 0x0F00) >> 8
   
   def _third_nibble(self):
       """
       Extract third nibble from current opcode.
       
       Returns:
           Third 4-bit nibble (e.g., 0x3 from 0x1234)
       """
       return (self.opcode & 0x00F0) >> 4
   
   def _fourth_nibble(self):
       """
       Extract fourth nibble from current opcode.
       
       Returns:
           Fourth 4-bit nibble (e.g., 0x4 from 0x1234)
       """
       return self.opcode & 0x000F
   
   def _second_byte(self):
       """
       Extract second byte from current opcode.
       
       Returns:
           Lower 8 bits (e.g., 0x34 from 0x1234)
       """
       return self.opcode & 0x00FF
   
   def _last_3_nibbles(self):
       """
       Extract last three nibbles from current opcode.
       
       Returns:
           Lower 12 bits (e.g., 0x234 from 0x1234)
       """
       return self.opcode & 0x0FFF
   
   def dispatch_sys_control(self):
       """
       Handle system and flow control instructions (0x0xxx).
       
       Processes display clearing (00E0) and subroutine returns (00EE).
       Other 0x0xxx opcodes are considered invalid in standard CHIP-8.
       
       Raises:
           UnsupportedOpcodeError: For unrecognized 0x0xxx instructions
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
       Return from subroutine call (00EE).
       
       Pops return address from stack and restores program counter.
       Decrements stack pointer and resumes execution at caller location.
       
       Raises:
           RuntimeError: If attempting to return with empty stack
       """
       if self.sp == 0:
           raise RuntimeError("RET called with empty stack")
       self.sp -= 1
       self.pc = self.stack[self.sp]

   def jump(self):
       """
       Handle jump instructions (1nnn, Bnnn).
       
       1nnn: Jump to address nnn
       Bnnn: Jump to address nnn + V0 (jump with offset)
       
       Sets pc_modified flag to prevent automatic PC increment.
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
       Call subroutine at address nnn (2nnn).
       
       Pushes current PC to stack, increments stack pointer, and jumps
       to subroutine address. Sets pc_modified to prevent auto-increment.
       """
       self.stack[self.sp] = self.pc
       self.sp += 1
       self.pc = self.opcode & 0x0FFF
       self.pc_modified = True

   def dispatch_comparison(self):
       """
       Handle conditional skip instructions (3xxx, 4xxx, 5xxx, 9xxx).
       
       Routes to appropriate comparison handlers based on instruction format:
       - 3xxx/4xxx: Compare register with immediate value
       - 5xxx/9xxx: Compare register with register
       """
       match self.opcode & 0xF000:
           case 0x3000 | 0x4000:
               self.skip_eq_neq_nn()
           case 0x5000 | 0x9000:
               self.skip_eq_neq_reg()
   
   def skip_eq_neq_nn(self):
       """
       Skip instructions based on register-immediate comparison.
       
       3xkk: Skip next instruction if Vx == kk
       4xkk: Skip next instruction if Vx != kk
       
       Advances PC by additional 2 bytes when condition is met.
       """
       reg_value = self.registers[self._second_nibble()]
       value = self._second_byte()
       if (
           (self.opcode & 0xF000 == 0x3000 and value == reg_value) or 
           (self.opcode & 0xF000 == 0x4000 and value != reg_value)
       ):
           self.pc += 2

   def skip_eq_neq_reg(self):
       """
       Skip instructions based on register-register comparison.
       
       5xy0: Skip next instruction if Vx == Vy
       9xy0: Skip next instruction if Vx != Vy
       
       Advances PC by additional 2 bytes when condition is met.
       """
       reg1_value = self.registers[self._second_nibble()]
       reg2_value = self.registers[self._third_nibble()]
       if (
           (self.opcode & 0xF00F == 0x5000 and reg1_value == reg2_value) or 
           (self.opcode & 0xF00F == 0x9000 and reg1_value != reg2_value)
       ):
           self.pc += 2

   def set_reg(self):
       """
       Set register Vx to immediate value kk (6xkk).
       
       Loads 8-bit immediate value into specified register.
       """
       reg_idx = self._second_nibble()
       self.registers[reg_idx] = self._second_byte()

   def add_nn_no_carry(self):
       """
       Add immediate value to register without carry (7xkk).
       
       Adds 8-bit immediate value to Vx with automatic wraparound.
       Does not affect the VF carry flag.
       """
       reg_idx = self._second_nibble()
       value = self._second_byte()
       self.registers[reg_idx] = (self.registers[reg_idx] + value) % 256

   def dispatch_reg_arithmetic(self):
       """
       Handle register-to-register arithmetic operations (8xxx).
       
       Processes all arithmetic and bitwise operations between registers,
       including assignment, bitwise operations, addition/subtraction with
       flags, and bit shifting operations.
       
       Sets VF flag register for operations that produce carry/borrow.
       """
       reg1_idx = self._second_nibble()
       reg1_value = self.registers[reg1_idx]
       reg2_value = self.registers[self._third_nibble()]
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
       Add two register values with carry flag (8xy4).
       
       Adds Vy to Vx, sets VF to 1 if carry occurs, 0 otherwise.
       Result is stored in Vx with automatic wraparound.
       
       Args:
           reg_idx: Target register index
           value1: First operand (Vx value)
           value2: Second operand (Vy value)
       """
       sum_ = value1 + value2
       self.registers[VF_IDX] = 1 if sum_ > 255 else 0
       self.registers[reg_idx] = sum_ % 256

   def sub_reg_borrow(self, reg_idx: int, value1: int, value2: int):
       """
       Subtract register values with borrow flag (8xy5, 8xy7).
       
       Subtracts value2 from value1, sets VF to 0 if borrow occurs, 1 otherwise.
       Result is stored in target register with automatic wraparound.
       
       Args:
           reg_idx: Target register index
           value1: Minuend value
           value2: Subtrahend value
       """
       diff = value1 - value2
       self.registers[VF_IDX] = 0 if diff < 0 else 1
       self.registers[reg_idx] = (diff + 256) % 256

   def shift_reg_right(self, reg_idx: int, value1: int):
       """
       Shift register right by one bit (8xy6).
       
       Stores LSB in VF flag register, then shifts Vx right by 1.
       
       Args:
           reg_idx: Target register index
           value1: Value to shift
       """
       self.registers[VF_IDX] = value1 & 0b0000_0001
       self.registers[reg_idx] = value1 >> 1

   def shift_reg_left(self, reg_idx: int, value1: int):
       """
       Shift register left by one bit (8xyE).
       
       Stores MSB in VF flag register, then shifts Vx left by 1.
       Result is masked to 8 bits.
       
       Args:
           reg_idx: Target register index
           value1: Value to shift
       """
       self.registers[VF_IDX] = (value1 & 0b1000_0000) >> 7
       self.registers[reg_idx] = (value1 & 0b0111_1111) << 1

   def set_i(self):
       """
       Set index register I to address nnn (Annn).
       
       Loads 12-bit address into the I register for memory operations.
       """
       self.i = self._last_3_nibbles()

   def set_random_byte(self):
       """
       Set register to random value AND immediate (Cxkk).
       
       Generates random byte (0-255), performs bitwise AND with immediate
       value kk, and stores result in Vx.
       """
       reg_idx = self._second_nibble()
       value = self._second_byte()
       self.registers[reg_idx] = value & randint(0, 255)

   def draw_sprite(self):
       """
       Draw sprite to display with collision detection (Dxyn).
       
       Reads n bytes from memory starting at I, draws 8xn sprite at
       coordinates (Vx, Vy) using XOR logic. Sets VF to 1 if any
       pixels were erased (collision), 0 otherwise.
       """
       x = self.registers[self._second_nibble()]
       y = self.registers[self._third_nibble()]
       size = self._fourth_nibble()
       byte_array = [self.memory.read_byte(self.i + j) for j in range(size)]
       collision = self.display.draw_sprite(x, y, byte_array)
       self.registers[VF_IDX] = collision

   def process_input(self):
       """
       Handle key press conditional skips (Ex9E, ExA1).
       
       Ex9E: Skip next instruction if key Vx is pressed
       ExA1: Skip next instruction if key Vx is not pressed
       
       Advances PC by additional 2 bytes when condition is met.
       """
       key = self.registers[self._second_nibble()]
       low_byte = self._second_byte()
       if (
           (low_byte == 0x9E and self.input_.key_pressed(key)) or
           (low_byte == 0xA1 and self.input_.key_not_pressed(key))
       ):
           self.pc += 2

   def dispatch_misc_fx(self):
       """
       Handle miscellaneous Fx instructions.
       
       Processes timer operations, memory operations, BCD conversion,
       register dumps/loads, and font sprite addressing.
       
       Raises:
           UnsupportedOpcodeError: For unrecognized Fx instructions
       """
       reg_idx = self._second_nibble()
       match self.opcode & 0x00FF:
           case 0x0007:
               self.registers[reg_idx] = self.delay_timer
           case 0x000A:
               self.input_.start_waiting()
               self.waiting_for_key = True
           case 0x0015:
               self.delay_timer = self.registers[reg_idx]
           case 0x0018:
               self.sound_timer = self.registers[reg_idx]
           case 0x001E:
               self.i += self.registers[reg_idx]
           case 0x0029:
               self.i = self.memory.get_sprite_address(self.registers[reg_idx])
           case 0x0033:
               self.store_bcd()
           case 0x0055:
               self.exchange_regs_memory(write=True)
           case 0x0065:
               self.exchange_regs_memory(write=False)
           case _:
               raise UnsupportedOpcodeError(f"Code {self.opcode} not supported.")

   def check_any_key_pressed(self) -> bool:
       """
       Check for key press events during wait state.
       
       Used by Fx0A instruction to detect when any key is pressed.
       Stores the pressed key value in the target register and
       clears the waiting state.
       
       Returns:
           True if a key was pressed, False if still waiting
       """
       key = self.input_.check_keystates_changed()
       if key is not None:
           reg_idx = self._second_nibble()
           self.registers[reg_idx] = key
           self.waiting_for_key = False
           return True
       return False

   def store_bcd(self):
       """
       Store BCD representation of register value (Fx33).
       
       Converts Vx to three decimal digits and stores them at
       memory locations I, I+1, and I+2 (hundreds, tens, ones).
       """
       val = self.registers[self._second_nibble()]
       for j in range(3):
           digit = (val // (10 ** (2 - j))) % 10
           self.memory.write_byte(self.i + j, digit)

   def exchange_regs_memory(self, write: bool):
       """
       Exchange registers with memory (Fx55, Fx65).
       
       Fx55: Store registers V0-Vx to memory starting at I
       Fx65: Load registers V0-Vx from memory starting at I
       
       Args:
           write: True for store operation, False for load operation
       """
       reg_idx = self._second_nibble()
       for idx in range(reg_idx + 1):
           if write:
               self.memory.write_byte(self.i + idx, self.registers[idx])
           else:
               self.registers[idx] = self.memory.read_byte(self.i + idx)