"""
Comprehensive Memory Tests for CHIP-8 Emulator

Memory Layout:
- 0x000-0x04F (0-79):     Available for use (initialized to zero)
- 0x050-0x09F (80-159):   Fontset area (contains sprite data, NOT zero)
- 0x0A0-0x1FF (160-511):  Available for use (initialized to zero)  
- 0x200+ (512+):          ROM area
"""

import pytest
from unittest.mock import patch, mock_open
import tempfile
import os

from core.memory import Memory
from core.errors import MemoryOutOfBoundsError, ByteOverflowError
from configs import ROM_START_IDX, FONTSET_START_ADDRESS, MEMORY_SIZE_IN_BYTES, FONTSET


class TestMemoryInitialization:
    def test_memory_initialized_to_zero(self):
        """Memory should be initialized to all zeros except fontset area."""
        m = Memory()
        
        # Check memory before fontset area is zero
        for addr in range(0, FONTSET_START_ADDRESS):
            assert m.read_byte(addr) == 0
            
        # Check memory after fontset area is zero (before ROM area)
        fontset_end = FONTSET_START_ADDRESS + len(FONTSET)
        for addr in range(fontset_end, ROM_START_IDX):
            assert m.read_byte(addr) == 0

    def test_fontset_loaded_correctly(self):
        """Fontset should be loaded at correct addresses on initialization."""
        m = Memory()
        
        for i in range(len(FONTSET)):
            addr = FONTSET_START_ADDRESS + i
            assert m.read_byte(addr) == FONTSET[i]

    def test_sprite_addresses_match_fontset_locations(self):
        """Sprite addresses should point to correct fontset locations."""
        m = Memory()
        
        for digit in range(0x10):
            sprite_addr = m.get_sprite_address(digit)
            expected_addr = FONTSET_START_ADDRESS + 5 * digit
            assert sprite_addr == expected_addr
            
            # Verify the sprite data is actually there
            for byte_offset in range(5):
                actual_byte = m.read_byte(sprite_addr + byte_offset)
                expected_byte = FONTSET[5 * digit + byte_offset]
                assert actual_byte == expected_byte


class TestByteOperations:
    def test_write_read_single_byte(self):
        """Should be able to write and read single bytes."""
        m = Memory()
        # Avoid fontset area (80-159), use safe addresses
        test_cases = [(200, 0xFF), (300, 0x42), (0, 0x00), (MEMORY_SIZE_IN_BYTES - 1, 0xAB)]
        
        for addr, value in test_cases:
            m.write_byte(addr, value)
            assert m.read_byte(addr) == value

    def test_write_read_boundary_values(self):
        """Should handle min/max byte values correctly."""
        m = Memory()
        addr = 500
        
        # Test boundary values
        m.write_byte(addr, 0x00)
        assert m.read_byte(addr) == 0x00
        
        m.write_byte(addr, 0xFF)
        assert m.read_byte(addr) == 0xFF

    @pytest.mark.parametrize("addr", [0, MEMORY_SIZE_IN_BYTES - 1])
    def test_write_read_at_memory_boundaries(self, addr):
        """Should handle reads/writes at memory boundaries."""
        m = Memory()
        value = 0x42
        
        m.write_byte(addr, value)
        assert m.read_byte(addr) == value


class TestWordOperations:
    def test_read_word_big_endian(self):
        """Word operations should use big-endian byte order."""
        m = Memory()
        addr = 1000
        
        # Write two bytes manually
        m.write_byte(addr, 0x12)
        m.write_byte(addr + 1, 0x34)
        
        # Read as word should combine them big-endian style
        word = m.read_word(addr)
        assert word == 0x1234

    def test_read_word_boundary_cases(self):
        """Word reads should work at valid boundaries."""
        m = Memory()
        
        # Test at address 0
        m.write_byte(0, 0xAB)
        m.write_byte(1, 0xCD)
        assert m.read_word(0) == 0xABCD
        
        # Test at second-to-last address
        last_word_addr = MEMORY_SIZE_IN_BYTES - 2
        m.write_byte(last_word_addr, 0xEF)
        m.write_byte(last_word_addr + 1, 0x01)
        assert m.read_word(last_word_addr) == 0xEF01

    def test_read_word_with_zeros(self):
        """Word reads should handle zero values correctly."""
        m = Memory()
        addr = 600
        
        # Memory initialized to zero, so word should be 0x0000
        assert m.read_word(addr) == 0x0000
        
        # Test with one byte zero, one non-zero
        m.write_byte(addr, 0x00)
        m.write_byte(addr + 1, 0x42)
        assert m.read_word(addr) == 0x0042


class TestROMLoading:
    def test_load_rom_basic(self):
        """Should load ROM data starting at ROM_START_IDX."""
        dummy_data = b"\x01\x02\x03\x04\xFF"
        m = Memory()
        
        with patch("core.memory.open", mock_open(read_data=dummy_data), create=True):
            m.load_rom("test.ch8")
        
        # Verify ROM data was loaded at correct location
        for i, byte_val in enumerate(dummy_data):
            assert m.read_byte(ROM_START_IDX + i) == byte_val

    def test_load_rom_doesnt_overwrite_fontset(self):
        """ROM loading should not affect fontset area."""
        dummy_data = b"\xFF" * 100  # Large ROM
        m = Memory()
        
        # Store original fontset
        original_fontset = [m.read_byte(FONTSET_START_ADDRESS + i) for i in range(len(FONTSET))]
        
        with patch("core.memory.open", mock_open(read_data=dummy_data), create=True):
            m.load_rom("test.ch8")
        
        # Verify fontset unchanged
        for i, expected_byte in enumerate(original_fontset):
            assert m.read_byte(FONTSET_START_ADDRESS + i) == expected_byte

    def test_load_empty_rom(self):
        """Should handle empty ROM files gracefully."""
        m = Memory()
        
        with patch("core.memory.open", mock_open(read_data=b""), create=True):
            m.load_rom("empty.ch8")
        
        # Memory at ROM area should remain zero
        assert m.read_byte(ROM_START_IDX) == 0

    def test_load_large_rom(self):
        """Should handle large ROM files that fill available space."""
        # Create ROM that fills from ROM_START_IDX to end of memory
        rom_size = MEMORY_SIZE_IN_BYTES - ROM_START_IDX
        dummy_data = bytes(range(256)) * (rom_size // 256) + bytes(range(rom_size % 256))
        
        m = Memory()
        with patch("core.memory.open", mock_open(read_data=dummy_data), create=True):
            m.load_rom("large.ch8")
        
        # Verify data loaded correctly
        for i in range(min(len(dummy_data), rom_size)):
            assert m.read_byte(ROM_START_IDX + i) == dummy_data[i]

    def test_load_rom_file_operations(self):
        """Should properly handle file operations."""
        # Test with actual temporary file
        test_data = b"\xA1\xB2\xC3\xD4"
        
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(test_data)
            tmp_path = tmp.name
        
        try:
            m = Memory()
            m.load_rom(tmp_path)
            
            for i, byte_val in enumerate(test_data):
                assert m.read_byte(ROM_START_IDX + i) == byte_val
        finally:
            os.unlink(tmp_path)


class TestErrorConditions:
    def test_read_byte_out_of_bounds(self):
        """Should raise exception for out-of-bounds reads."""
        m = Memory()
        
        with pytest.raises(MemoryOutOfBoundsError):
            m.read_byte(MEMORY_SIZE_IN_BYTES)
            
        with pytest.raises(MemoryOutOfBoundsError):
            m.read_byte(MEMORY_SIZE_IN_BYTES + 1000)

    def test_read_word_out_of_bounds(self):
        """Should raise exception for out-of-bounds word reads."""
        m = Memory()
        
        # Word read at last byte should fail (needs 2 bytes)
        with pytest.raises(MemoryOutOfBoundsError):
            m.read_word(MEMORY_SIZE_IN_BYTES - 1)
            
        with pytest.raises(MemoryOutOfBoundsError):
            m.read_word(MEMORY_SIZE_IN_BYTES)

    def test_write_byte_out_of_bounds(self):
        """Should raise exception for out-of-bounds writes."""
        m = Memory()
        
        with pytest.raises(MemoryOutOfBoundsError):
            m.write_byte(MEMORY_SIZE_IN_BYTES, 0x42)

    def test_write_byte_overflow(self):
        """Should raise exception for byte overflow."""
        m = Memory()
        
        with pytest.raises(ByteOverflowError):
            m.write_byte(100, 256)
            
        with pytest.raises(ByteOverflowError):
            m.write_byte(100, 1000)

    @pytest.mark.parametrize("invalid_value", [256, 257, 1000, -1])
    def test_write_byte_invalid_values(self, invalid_value):
        """Should reject invalid byte values."""
        m = Memory()
        
        with pytest.raises((ByteOverflowError, ValueError)):
            m.write_byte(100, invalid_value)


class TestSpriteOperations:
    @pytest.mark.parametrize("digit", range(0x10))
    def test_all_sprite_addresses(self, digit):
        """All 16 sprite addresses should be valid and correct."""
        m = Memory()
        sprite_addr = m.get_sprite_address(digit)
        
        # Should point to correct location
        expected_addr = FONTSET_START_ADDRESS + 5 * digit
        assert sprite_addr == expected_addr
        
        # Should be able to read sprite data
        for i in range(5):
            byte_val = m.read_byte(sprite_addr + i)
            assert 0 <= byte_val <= 255

    def test_sprite_data_integrity(self):
        """Sprite data should match expected fontset patterns."""
        m = Memory()
        
        # Test specific known sprites
        # Sprite for '0' should be: 0xF0, 0x90, 0x90, 0x90, 0xF0
        sprite_0_addr = m.get_sprite_address(0)
        expected_0 = [0xF0, 0x90, 0x90, 0x90, 0xF0]
        
        for i, expected_byte in enumerate(expected_0):
            assert m.read_byte(sprite_0_addr + i) == expected_byte


class TestMemoryIsolation:
    def test_operations_dont_interfere(self):
        """Different memory operations should not interfere with each other."""
        m = Memory()
        
        # Write to different areas (avoiding fontset area)
        m.write_byte(200, 0xAA)
        m.write_byte(300, 0xBB)
        m.write_byte(400, 0xCC)
        
        # All should retain their values
        assert m.read_byte(200) == 0xAA
        assert m.read_byte(300) == 0xBB
        assert m.read_byte(400) == 0xCC
        
        # Areas in between should still be zero (avoiding fontset area)
        assert m.read_byte(250) == 0x00
        assert m.read_byte(350) == 0x00

    def test_word_read_doesnt_affect_memory(self):
        """Reading words should not modify memory."""
        m = Memory()
        addr = 400
        
        m.write_byte(addr, 0x12)
        m.write_byte(addr + 1, 0x34)
        
        # Read word multiple times
        word1 = m.read_word(addr)
        word2 = m.read_word(addr)
        
        # Should be consistent and not modify memory
        assert word1 == word2 == 0x1234
        assert m.read_byte(addr) == 0x12
        assert m.read_byte(addr + 1) == 0x34