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
    Acts as a memory module as well as containing some useful methods for
    memory management, binary file loading.

    Attributes:
        _memory: The list which will store bytes read from ROM file.
    """

    _memory: List[int]
    rom_loaded: bool

    def __init__(self):
        self._memory = [0] * MEMORY_SIZE_IN_BYTES
        self._load_fontset()
        self.rom_loaded = False

    def load_rom(self, file_path: str):
        """
        Reads bytes from ROM file and replaces same-size sub-array in memory.
        """
        if self.rom_loaded:
            return
        with open(file_path, "rb") as f:
            byte_array = bytearray(f.read())
        end_idx = ROM_START_IDX + len(byte_array)
        self._memory[ROM_START_IDX:end_idx] = byte_array
        self.rom_loaded = True

    def load_game(self, game: str):
        self.load_rom(f"roms/{game.upper()}")

    def _load_fontset(self):
        for digit in range(0x10):
            for byte_idx in range(5):
                memory_idx = FONTSET_START_ADDRESS + 5 * digit + byte_idx
                self._memory[memory_idx] = FONTSET[5 * digit + byte_idx]

    def read_byte(self, addr: int) -> int:
        """
        Reads and returns a single byte on given address.

        Parameters:
            addr: absolute address (not relative to ROM_START_IDX) to memory address
        to read.

        Returns:
            value of a single byte as int
        """

        if addr >= MEMORY_SIZE_IN_BYTES:
            raise MemoryOutOfBoundsError("Memory access out of bounds")
        return self._memory[addr]

    def read_word(self, addr: int) -> int:
        """
        Reads and returns 2 bytes on given address.

        Parameters:
            addr: absolute address (not relative to ROM_START_IDX) to memory address
        to read.

        Returns:
            value of 2 bytes as int
        """

        if addr + 2 > MEMORY_SIZE_IN_BYTES:
            raise MemoryOutOfBoundsError("Memory access out of bounds")
        return self._memory[addr] << 8 | self._memory[addr + 1]

    def write_byte(self, addr: int, value: int):
        """
        Writes a given value on given address.

        Parameters:
            addr: absolute address (not relative to ROM_START_IDX) to memory address
        to read
            value: value to write
        """

        if addr >= MEMORY_SIZE_IN_BYTES:
            raise MemoryOutOfBoundsError("Memory access out of bounds")
        if value > 255 or value < 0:
            raise ByteOverflowError("Given value larger than 1 byte")
        self._memory[addr] = value

    def get_sprite_address(self, digit: int) -> int:
        """Returns memory address of font of the given digit."""
        return FONTSET_START_ADDRESS + 5 * digit        
