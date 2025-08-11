from time import sleep
from typing import Optional

from core.cpu import CPU
from core.input_ import Input_
from core.memory import Memory
from core.display import Display
from configs import TARGET_IPS

class Emulator:
   """
   CHIP-8 Emulator Coordinator
   
   Main emulation controller that orchestrates all CHIP-8 subsystems and manages
   the primary emulation loop. Handles timing, component initialization, and
   coordinates the execution cycle between CPU instructions, display updates,
   and timer management.
   
   Architecture:
   The emulator follows a precise timing model:
   - CPU runs at TARGET_IPS (instructions per second)
   - Display refreshes at 60Hz (every TARGET_IPS/60 CPU cycles)
   - Timers update at 60Hz synchronized with display refresh
   - Sleep timing maintains consistent instruction rate
   
   This timing separation allows the CPU to run faster than 60Hz while
   maintaining proper display and timer frequencies for authentic CHIP-8 behavior.
   
   Attributes:
       cpu: Central processing unit handling instruction execution
       input_: Keyboard input handler for user interaction
       memory: Memory management system with ROM and fontset
       display: Graphics display with terminal rendering
       delay_between_ops: Sleep duration to maintain TARGET_IPS timing
       cpu_cycles: Current cycle count since last 60Hz update
       cpu_cycles_max: Cycles per 60Hz period (TARGET_IPS / 60)
   """
   cpu: CPU
   input_: Input_
   memory: Memory
   display: Display
   delay_between_ops: float
   cpu_cycles: int
   cpu_cycles_max: int

   def __init__(self, game: Optional[str]):
       """
       Initialize emulator with all subsystems and game loading.
       
       Creates and connects all CHIP-8 components in proper initialization order.
       Memory and input are initialized first as they have no dependencies,
       followed by display, then CPU which requires references to all others.
       
       Args:
           game: Optional game name to load immediately (from roms directory)
                If None, emulator starts with empty memory for manual ROM loading
       
       Note:
           Timing is calculated based on TARGET_IPS configuration. The emulator
           maintains separate timing for CPU instructions vs. display/timer updates.
       """
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
       """
       Run the main emulation loop indefinitely.
       
       Executes the core emulation cycle:
       1. Execute one CPU instruction
       2. Sleep to maintain TARGET_IPS timing
       3. Track cycles for 60Hz synchronization  
       4. Every cpu_cycles_max cycles (60Hz):
          - Refresh display with latest graphics
          - Update delay and sound timers
          - Reset cycle counter
       
       The loop runs until manually interrupted (Ctrl+C) or system exit.
       Timing precision ensures authentic CHIP-8 behavior regardless of
       host system performance.
       """
       while True:
           self.cpu.cycle()
           sleep(self.delay_between_ops)
           self.cpu_cycles += 1
           if self.cpu_cycles >= self.cpu_cycles_max:
               self.cpu_cycles = 0
               self.display.refresh()
               self.cpu.update_timers()