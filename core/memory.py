from typing import List

from core.errors import MemoryOutOfBoundsError, ByteOverflowError
from configs import (
    MEMORY_SIZE_IN_BYTES,
    ROM_START_IDX, 
    FONTSET_START_ADDRESS, 
    FONTSET
)


class Memory:
    """
   CHIP-8 Memory Management System
   
   Implements the 4KB memory space of the CHIP-8 system with proper memory mapping,
   ROM loading capabilities, and built-in fontset management. Handles byte and word
   operations with bounds checking and error handling.
   
   Memory Layout:
   ┌──────────────┬─────────────┬──────────────────────┐
   │   Address    │    Size     │      Purpose         │
   ├──────────────┼─────────────┼──────────────────────┤
   │ 0x000-0x04F  │   80 bytes  │ Available space      │
   │ 0x050-0x09F  │   80 bytes  │ Built-in fontset     │
   │ 0x0A0-0x1FF  │  352 bytes  │ Available space      │
   │ 0x200-0xFFF  │ 3584 bytes  │ ROM/Program space    │
   └──────────────┴─────────────┴──────────────────────┘
   
   The fontset area contains 5-byte sprite data for hexadecimal digits 0-F,
   loaded automatically during initialization.
   
   Attributes:
       _memory: Internal 4KB byte array storing all memory contents
       rom_loaded: Flag indicating whether a ROM has been loaded
   """

    _memory: List[int]
    rom_loaded: bool

    def __init__(self):
        self._memory = [0] * MEMORY_SIZE_IN_BYTES
        self._load_fontset()
        self.rom_loaded = False

    def load_rom(self, file_path: str):
        """
       Load ROM file into memory starting at address 0x200.
       
       Reads binary ROM data and places it in the program area without
       overwriting the fontset region. Prevents multiple ROM loads to
       maintain system state integrity.
       
       Args:
           file_path: Path to the CHIP-8 ROM file (.ch8 format)
           
       Note:
           ROM loading is a one-time operation. Subsequent calls are ignored
           if a ROM has already been loaded.
       """
        if self.rom_loaded:
            return
        with open(file_path, "rb") as f:
            byte_array = bytearray(f.read())
        end_idx = ROM_START_IDX + len(byte_array)
        self._memory[ROM_START_IDX:end_idx] = byte_array
        self.rom_loaded = True

    def load_game(self, game: str):
        """
       Load a game ROM by name from the roms directory.
       
       Convenience method that constructs the full path and loads the ROM.
       Automatically converts game name to uppercase for consistent naming.
       
       Args:
           game: Name of the game file (without path or extension)
           
       Example:
           memory.load_game("pong")  # Loads "roms/PONG"
       """
        self.load_rom(f"roms/{game.upper()}")

    def _load_fontset(self):
        """
       Load built-in character sprites into fontset memory region.
       
       Internal method that initializes the fontset area (0x050-0x09F) with
       5-byte sprite data for hexadecimal characters 0-F. Each character
       occupies exactly 5 consecutive bytes representing an 8x5 pixel sprite.
       
       Called automatically during Memory initialization.
       """
        for digit in range(0x10):
            for byte_idx in range(5):
                memory_idx = FONTSET_START_ADDRESS + 5 * digit + byte_idx
                self._memory[memory_idx] = FONTSET[5 * digit + byte_idx]

    def read_byte(self, addr: int) -> int:
        """
       Read a single byte from memory.
       
       Args:
           addr: Memory address (0x000-0xFFF)
           
       Returns:
           Byte value (0-255) at the specified address
           
       Raises:
           MemoryOutOfBoundsError: If address exceeds memory bounds
       """
        if addr >= MEMORY_SIZE_IN_BYTES:
            raise MemoryOutOfBoundsError("Memory access out of bounds")
        return self._memory[addr]

    def read_word(self, addr: int) -> int:
        """
       Read a 16-bit word from memory using big-endian byte order.
       
       Combines two consecutive bytes into a single 16-bit value. The byte
       at 'addr' becomes the high byte, and 'addr+1' becomes the low byte.
       
       Args:
           addr: Starting memory address (0x000-0xFFE)
           
       Returns:
           16-bit word value (0-65535) in big-endian format
           
       Raises:
           MemoryOutOfBoundsError: If addr+1 would exceed memory bounds
           
       Example:
           Memory[0x200] = 0x12, Memory[0x201] = 0x34
           read_word(0x200) returns 0x1234
       """
        if addr + 2 > MEMORY_SIZE_IN_BYTES:
            raise MemoryOutOfBoundsError("Memory access out of bounds")
        return self._memory[addr] << 8 | self._memory[addr + 1]

    def write_byte(self, addr: int, value: int):
        """
       Write a single byte to memory.
       
       Args:
           addr: Memory address (0x000-0xFFF)
           value: Byte value to write (0-255)
           
       Raises:
           MemoryOutOfBoundsError: If address exceeds memory bounds
           ByteOverflowError: If value exceeds byte range (0-255)
       """
        if addr >= MEMORY_SIZE_IN_BYTES:
            raise MemoryOutOfBoundsError("Memory access out of bounds")
        if value > 255 or value < 0:
            raise ByteOverflowError("Given value larger than 1 byte")
        self._memory[addr] = value

    def get_sprite_address(self, digit: int) -> int:
        """
       Get memory address of a built-in character sprite.
       
       Returns the starting address of the 5-byte sprite data for the
       specified hexadecimal digit. Used by the Fx29 instruction to
       set the I register to point to character sprites.
       
       Args:
           digit: Hexadecimal digit (0x0-0xF)
           
       Returns:
           Memory address of the sprite's first byte
           
       Example:
           get_sprite_address(0x0) returns address of '0' character sprite
           get_sprite_address(0xA) returns address of 'A' character sprite
       """
        return FONTSET_START_ADDRESS + 5 * digit        
