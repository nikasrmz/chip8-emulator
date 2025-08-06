import pytest
from unittest.mock import patch, mock_open

from core.memory import Memory
from configs import ROM_START_IDX, FONTSET_START_ADDRESS 

def test_rom_loading():
    dummy_data = b"\x01\x02\x03\x04"

    m = Memory()
    with patch("core.memory.open", mock_open(read_data=dummy_data), create=True):
        m.load_rom("path.ch8")

    assert m._memory[ROM_START_IDX:ROM_START_IDX + len(dummy_data)] == list(dummy_data)

def test_get_sprite_address():
    m = Memory()
    
    for i in range(0x10):
        addr = m.get_sprite_address(i)
        correct_addr = FONTSET_START_ADDRESS + 5 * i
        assert addr == correct_addr

def test_write_read():
    m = Memory()

    m.write_byte(200, 0xFF)

    assert m._memory[200] == 0xFF

    assert m.read_byte(200) == 0xFF
    
        