from typing import List

from configs import MEMORY_SIZE_IN_BYTES, ROM_START_IDX, FILE_PATH


class Memory:
    _memory: List[int]

    def __init__(self):
        self._memory = [0] * MEMORY_SIZE_IN_BYTES

    def load_rom(self):
        with open(FILE_PATH, "rb") as f:
            byte_array = bytearray(f.read())
        for i in range(0, len(byte_array), 2):
            self._memory[ROM_START_IDX + i // 2] = (
                byte_array[i] << 8 | byte_array[i + 1]
            )

    def read(self, addr: int):
        if addr > MEMORY_SIZE_IN_BYTES:
            raise IndexError("Memory access out of bounds")
        return self._memory[addr]

    def write(self, addr: int, value: int):
        if addr > MEMORY_SIZE_IN_BYTES:
            raise IndexError("Memory access out of bounds")
        if value > 65535:
            raise ValueError("Given value larger than 2 bytes")
        self._memory[addr] = value
