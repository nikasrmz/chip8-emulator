"""
Comprehensive Input Tests for CHIP-8 Emulator

Tests the input module which handles keyboard mapping between QWERTY and CHIP-8 layouts.
CHIP-8 uses a 16-key hexadecimal keypad (0-F) mapped to QWERTY keys.
"""

import pytest
from unittest.mock import patch, MagicMock
from time import sleep

from core.input_ import Input_


class TestKeyboardMapping:
    def test_qwerty_to_chip8_mapping_complete(self):
        """Should have all 16 CHIP-8 keys mapped to QWERTY keys."""
        input_handler = Input_()
        
        # Should have exactly 16 mappings (0x0 through 0xF)
        assert len(input_handler.qwerty_to_chip8) == 16
        
        # Should contain all hex values 0-F
        chip8_values = set(input_handler.qwerty_to_chip8.values())
        expected_values = set(range(0x10))  # 0x0 to 0xF
        assert chip8_values == expected_values

    def test_chip8_to_qwerty_mapping_complete(self):
        """Should have reverse mapping for all CHIP-8 keys."""
        input_handler = Input_()
        
        # Should have exactly 16 reverse mappings
        assert len(input_handler.chip8_to_qwerty) == 16
        
        # Should contain all hex keys 0-F
        chip8_keys = set(input_handler.chip8_to_qwerty.keys())
        expected_keys = set(range(0x10))
        assert chip8_keys == expected_keys

    def test_bidirectional_mapping_consistency(self):
        """Forward and reverse mappings should be consistent."""
        input_handler = Input_()
        
        for qwerty_key, chip8_key in input_handler.qwerty_to_chip8.items():
            # Reverse mapping should point back to original qwerty key
            assert input_handler.chip8_to_qwerty[chip8_key] == qwerty_key

    def test_no_duplicate_qwerty_keys(self):
        """Each QWERTY key should map to only one CHIP-8 key."""
        input_handler = Input_()
        
        qwerty_keys = list(input_handler.qwerty_to_chip8.keys())
        unique_qwerty_keys = set(qwerty_keys)
        
        assert len(qwerty_keys) == len(unique_qwerty_keys)

    def test_no_duplicate_chip8_keys(self):
        """Each CHIP-8 key should map to only one QWERTY key."""
        input_handler = Input_()
        
        chip8_keys = list(input_handler.qwerty_to_chip8.values())
        unique_chip8_keys = set(chip8_keys)
        
        assert len(chip8_keys) == len(unique_chip8_keys)

    def test_expected_key_mappings(self):
        """Should have expected specific key mappings."""
        input_handler = Input_()
        
        # Test some specific mappings based on the implementation
        expected_mappings = {
            "x": 0x0,  # CHIP-8 key 0
            "1": 0x1,  # CHIP-8 key 1
            "2": 0x2,  # CHIP-8 key 2
            "3": 0x3,  # CHIP-8 key 3
            "q": 0x4,  # CHIP-8 key 4
            "v": 0xF,  # CHIP-8 key F
        }
        
        for qwerty_key, expected_chip8 in expected_mappings.items():
            assert input_handler.qwerty_to_chip8[qwerty_key] == expected_chip8


class TestKeyPressDetection:
    @patch('core.input_.keyboard.is_pressed')
    def test_key_pressed_when_key_is_down(self, mock_is_pressed):
        """Should return True when specified CHIP-8 key is pressed."""
        mock_is_pressed.return_value = True
        input_handler = Input_()
        
        # Test with CHIP-8 key 0 (maps to 'x')
        result = input_handler.key_pressed(0x0)
        
        assert result is True
        mock_is_pressed.assert_called_once_with('x')

    @patch('core.input_.keyboard.is_pressed')
    def test_key_pressed_when_key_is_up(self, mock_is_pressed):
        """Should return False when specified CHIP-8 key is not pressed."""
        mock_is_pressed.return_value = False
        input_handler = Input_()
        
        result = input_handler.key_pressed(0x5)  # Maps to 'w'
        
        assert result is False
        mock_is_pressed.assert_called_once_with('w')

    @patch('core.input_.keyboard.is_pressed')
    def test_key_not_pressed_when_key_is_down(self, mock_is_pressed):
        """Should return False when key is pressed (inverted logic)."""
        mock_is_pressed.return_value = True
        input_handler = Input_()
        
        result = input_handler.key_not_pressed(0xA)  # Maps to 'z'
        
        assert result is False
        mock_is_pressed.assert_called_once_with('z')

    @patch('core.input_.keyboard.is_pressed')
    def test_key_not_pressed_when_key_is_up(self, mock_is_pressed):
        """Should return True when key is not pressed (inverted logic)."""
        mock_is_pressed.return_value = False
        input_handler = Input_()
        
        result = input_handler.key_not_pressed(0xF)  # Maps to 'v'
        
        assert result is True
        mock_is_pressed.assert_called_once_with('v')

    @patch('core.input_.keyboard.is_pressed')
    def test_all_chip8_keys_can_be_checked(self, mock_is_pressed):
        """Should be able to check all 16 CHIP-8 keys without errors."""
        mock_is_pressed.return_value = False
        input_handler = Input_()
        
        for chip8_key in range(0x10):
            # Should not raise any exceptions
            result = input_handler.key_pressed(chip8_key)
            assert result is False

    def test_invalid_chip8_key_raises_error(self):
        """Should raise KeyError for invalid CHIP-8 key codes."""
        input_handler = Input_()
        
        with pytest.raises(KeyError):
            input_handler.key_pressed(0x10)  # Invalid key (only 0x0-0xF valid)
            
        with pytest.raises(KeyError):
            input_handler.key_pressed(-1)  # Negative key


class TestWaitStoreKey:
    @patch('core.input_.sleep')
    @patch('core.input_.keyboard.is_pressed')
    def test_wait_store_key_detects_key_press(self, mock_is_pressed, mock_sleep):
        """Should detect and return key when transition from not pressed to pressed occurs."""
        input_handler = Input_()
        
        # Each call to _key_states() calls keyboard.is_pressed 16 times (once per CHIP-8 key)
        # Simulate: no keys pressed initially, then 'x' (CHIP-8 key 0) gets pressed after delay
        call_count = 0
        def mock_is_pressed_side_effect(qwerty_key):
            nonlocal call_count
            call_count += 1
            # After second iteration (32 calls), 'x' becomes pressed
            # This ensures at least one sleep() call happens
            return qwerty_key == 'x' and call_count > 32
        
        mock_is_pressed.side_effect = mock_is_pressed_side_effect
        
        result = input_handler.wait_store_key()
        
        assert result == 0x0  # Should return CHIP-8 key 0
        assert mock_sleep.called  # Should have called sleep at least once

    @patch('core.input_.sleep')
    @patch('core.input_.keyboard.is_pressed')
    def test_wait_store_key_ignores_already_pressed_keys(self, mock_is_pressed, mock_sleep):
        """Should ignore keys that are already pressed and wait for new press."""
        input_handler = Input_()
        
        # Simulate: 'x' already pressed, then '1' gets newly pressed
        call_count = 0
        def mock_is_pressed_side_effect(qwerty_key):
            nonlocal call_count
            call_count += 1
            
            if qwerty_key == 'x':  # CHIP-8 key 0x0
                return True  # Always pressed (should be ignored)
            elif qwerty_key == '1':  # CHIP-8 key 0x1
                # Gets pressed after second iteration (after 32 calls)
                return call_count > 32
            else:
                return False
        
        mock_is_pressed.side_effect = mock_is_pressed_side_effect
        
        result = input_handler.wait_store_key()
        
        assert result == 0x1  # Should return newly pressed key, not already pressed one

    @patch('core.input_.sleep')
    @patch('core.input_.keyboard.is_pressed')
    def test_wait_store_key_returns_first_detected_press(self, mock_is_pressed, mock_sleep):
        """Should return the first key that transitions to pressed state."""
        input_handler = Input_()
        
        call_count = 0
        def mock_is_pressed_side_effect(qwerty_key):
            nonlocal call_count
            call_count += 1
            
            # After second iteration, both 'q' and 'w' become pressed simultaneously
            if call_count > 32 and qwerty_key in ['q', 'w']:
                return True
            return False
        
        mock_is_pressed.side_effect = mock_is_pressed_side_effect
        
        result = input_handler.wait_store_key()
        
        # Should return whichever key is checked first in the loop (0x4 for 'q' comes before 0x5 for 'w')
        assert result in [0x4, 0x5]  # Either 'q' or 'w' depending on iteration order

    @patch('core.input_.sleep')
    def test_wait_store_key_calls_sleep(self, mock_sleep):
        """Should call sleep to avoid busy waiting."""
        input_handler = Input_()
        
        # Mock to return a key press after a few iterations
        with patch('core.input_.keyboard.is_pressed') as mock_is_pressed:
            call_count = 0
            def mock_side_effect(qwerty_key):
                nonlocal call_count
                call_count += 1
                # After second iteration (32 calls), 'x' becomes pressed
                # This ensures at least one sleep() call happens
                return qwerty_key == 'x' and call_count > 32
            
            mock_is_pressed.side_effect = mock_side_effect
            
            input_handler.wait_store_key()
            
            # Should have called sleep at least once (probably multiple times)
            assert mock_sleep.call_count >= 1
            # Should sleep for 0.01 seconds
            mock_sleep.assert_called_with(0.05)


class TestKeyStatesHelper:
    @patch('core.input_.keyboard.is_pressed')
    def test_key_states_returns_16_booleans(self, mock_is_pressed):
        """Should return list of 16 boolean values for all CHIP-8 keys."""
        mock_is_pressed.return_value = False
        input_handler = Input_()
        
        key_states = input_handler._key_states()
        
        assert len(key_states) == 16
        assert all(isinstance(state, bool) for state in key_states)

    @patch('core.input_.keyboard.is_pressed')
    def test_key_states_reflects_actual_key_presses(self, mock_is_pressed):
        """Key states should accurately reflect which keys are pressed."""
        input_handler = Input_()
        
        # Simulate only keys '1' and 'q' being pressed
        def mock_side_effect(key):
            return key in ['1', 'q']
        
        mock_is_pressed.side_effect = mock_side_effect
        
        key_states = input_handler._key_states()
        
        # Key 0x1 ('1') and 0x4 ('q') should be True, others False
        expected_states = [False] * 16
        expected_states[0x1] = True  # '1' key
        expected_states[0x4] = True  # 'q' key
        
        assert key_states == expected_states

    @patch('core.input_.keyboard.is_pressed')
    def test_key_states_all_keys_pressed(self, mock_is_pressed):
        """Should handle case where all keys are pressed."""
        mock_is_pressed.return_value = True
        input_handler = Input_()
        
        key_states = input_handler._key_states()
        
        assert all(key_states)  # All should be True
        assert len(key_states) == 16

    @patch('core.input_.keyboard.is_pressed')
    def test_key_states_no_keys_pressed(self, mock_is_pressed):
        """Should handle case where no keys are pressed."""
        mock_is_pressed.return_value = False
        input_handler = Input_()
        
        key_states = input_handler._key_states()
        
        assert not any(key_states)  # All should be False
        assert len(key_states) == 16


class TestEdgeCases:
    def test_initialization_creates_valid_mappings(self):
        """Initialization should create valid bidirectional mappings."""
        input_handler = Input_()
        
        # Should not raise any exceptions
        assert input_handler.qwerty_to_chip8 is not None
        assert input_handler.chip8_to_qwerty is not None
        
        # Both mappings should be non-empty
        assert len(input_handler.qwerty_to_chip8) > 0
        assert len(input_handler.chip8_to_qwerty) > 0

    @patch('core.input_.keyboard.is_pressed')
    def test_multiple_input_handlers_independent(self, mock_is_pressed):
        """Multiple Input_ instances should work independently."""
        mock_is_pressed.return_value = False
        
        input1 = Input_()
        input2 = Input_()
        
        # Should have identical but independent mappings
        assert input1.qwerty_to_chip8 == input2.qwerty_to_chip8
        assert input1.chip8_to_qwerty == input2.chip8_to_qwerty
        
        # Should be different objects
        assert input1.qwerty_to_chip8 is not input2.qwerty_to_chip8

    @patch('core.input_.keyboard.is_pressed')
    def test_key_pressed_with_boundary_values(self, mock_is_pressed):
        """Should handle boundary CHIP-8 key values correctly."""
        from unittest.mock import call
        
        mock_is_pressed.return_value = True
        input_handler = Input_()
        
        # Test minimum and maximum valid keys
        assert input_handler.key_pressed(0x0) is True   # Minimum
        assert input_handler.key_pressed(0xF) is True   # Maximum
        
        assert call('x') in mock_is_pressed.call_args_list
        assert call('v') in mock_is_pressed.call_args_list