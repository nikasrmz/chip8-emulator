from typing import List

from configs import MEMORY_SIZE_IN_BYTES, ROM_START_IDX, FILE_PATH


class Memory:
    """
    Acts as a memory module as well as containing some useful methods for
    memory management, binary file loading.

    Attributes:
        _memory: The list which will store bytes read from ROM file.
    """

    _memory: List[int]

    def __init__(self):
        self._memory = [0] * MEMORY_SIZE_IN_BYTES

    def load_rom(self):
        """
        Reads bytes from ROM file and replaces same-size sub-array in memory.
        """

        with open(FILE_PATH, "rb") as f:
            byte_array = bytearray(f.read())
        end_idx = ROM_START_IDX + len(byte_array)
        self._memory[ROM_START_IDX:end_idx] = byte_array

    def read_byte(self, addr: int) -> int:
        """
        Reads and returns a single byte on given address.

        Parameters:
            addr: absolute address (not relative to ROM_START_IDX) to memory address
        to read.

        Returns:
            value of a single byte as int
        """

        if addr > MEMORY_SIZE_IN_BYTES:
            raise IndexError("Memory access out of bounds")
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

        if addr + 1 > MEMORY_SIZE_IN_BYTES:
            raise IndexError("Memory access out of bounds")
        return self._memory[addr] << 8 | self._memory[addr + 1]

    def write_byte(self, addr: int, value: int):
        """
        Writes a given value on given address.

        Parameters:
            addr: absolute address (not relative to ROM_START_IDX) to memory address
        to read
            value: value to write
        """

        if addr > MEMORY_SIZE_IN_BYTES:
            raise IndexError("Memory access out of bounds")
        if value > 255:
            raise ValueError("Given value larger than 1 byte")
        self._memory[addr] = value
