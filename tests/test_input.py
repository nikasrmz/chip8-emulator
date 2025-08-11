"""
Comprehensive Input Tests for CHIP-8 Emulator

Tests the input module which handles keyboard mapping between QWERTY and CHIP-8 layouts.
CHIP-8 uses a 16-key hexadecimal keypad (0-F) mapped to QWERTY keys.
"""

import pytest
from unittest.mock import patch, MagicMock

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


class TestKeyStateTracking:
    @patch('core.input_.keyboard.is_pressed')
    def test_start_waiting_captures_initial_state(self, mock_is_pressed):
        """start_waiting should capture current key states."""
        input_handler = Input_()
        
        # Simulate some keys being pressed initially
        def mock_side_effect(key):
            return key in ['1', 'q']
        
        mock_is_pressed.side_effect = mock_side_effect
        
        input_handler.start_waiting()
        
        # Should have captured the initial state
        expected_states = [False] * 16
        expected_states[0x1] = True  # '1' key
        expected_states[0x4] = True  # 'q' key
        
        assert input_handler.last_key_states == expected_states

    @patch('core.input_.keyboard.is_pressed')
    def test_check_keystates_changed_detects_new_press(self, mock_is_pressed):
        """Should detect when a key transitions from not pressed to pressed."""
        input_handler = Input_()
        
        # Initial state: no keys pressed
        mock_is_pressed.return_value = False
        input_handler.start_waiting()
        
        # Now 'x' (CHIP-8 key 0) gets pressed
        def mock_side_effect(key):
            return key == 'x'
        
        mock_is_pressed.side_effect = mock_side_effect
        
        result = input_handler.check_keystates_changed()
        
        assert result == 0x0  # Should return CHIP-8 key 0

    @patch('core.input_.keyboard.is_pressed')
    def test_check_keystates_changed_ignores_already_pressed(self, mock_is_pressed):
        """Should ignore keys that were already pressed."""
        input_handler = Input_()
        
        # Initial state: 'x' already pressed
        def initial_mock(key):
            return key == 'x'
        
        mock_is_pressed.side_effect = initial_mock
        input_handler.start_waiting()
        
        # 'x' still pressed - should return None
        result = input_handler.check_keystates_changed()
        
        assert result is None

    @patch('core.input_.keyboard.is_pressed')
    def test_check_keystates_changed_returns_first_new_press(self, mock_is_pressed):
        """Should return the first key that becomes newly pressed."""
        input_handler = Input_()
        
        # Initial state: no keys pressed
        mock_is_pressed.return_value = False
        input_handler.start_waiting()
        
        # Multiple keys become pressed
        def mock_side_effect(key):
            return key in ['q', 'w']  # Both become pressed
        
        mock_is_pressed.side_effect = mock_side_effect
        
        result = input_handler.check_keystates_changed()
        
        # Should return one of them (0x4 for 'q' or 0x5 for 'w')
        assert result in [0x4, 0x5]

    @patch('core.input_.keyboard.is_pressed')
    def test_check_keystates_changed_updates_last_states(self, mock_is_pressed):
        """Should update last_key_states after checking."""
        input_handler = Input_()
        
        # Initial: no keys
        mock_is_pressed.return_value = False
        input_handler.start_waiting()
        
        # New state: 'x' pressed
        def mock_side_effect(key):
            return key == 'x'
        
        mock_is_pressed.side_effect = mock_side_effect
        
        # First check should detect the change
        result1 = input_handler.check_keystates_changed()
        assert result1 == 0x0
        
        # Second check with same state should return None
        result2 = input_handler.check_keystates_changed()
        assert result2 is None

    @patch('core.input_.keyboard.is_pressed')
    def test_check_keystates_changed_no_change_returns_none(self, mock_is_pressed):
        """Should return None when no keys change state."""
        input_handler = Input_()
        
        # Consistent state: same keys pressed
        def mock_side_effect(key):
            return key in ['1', '2']
        
        mock_is_pressed.side_effect = mock_side_effect
        input_handler.start_waiting()
        
        # Check with same state should return None
        result = input_handler.check_keystates_changed()
        
        assert result is None


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

    @patch('core.input_.keyboard.is_pressed')
    def test_start_waiting_without_prior_state(self, mock_is_pressed):
        """start_waiting should work on first call without prior state."""
        mock_is_pressed.return_value = False
        input_handler = Input_()
        
        # Should not raise any exceptions
        input_handler.start_waiting()
        
        # Should have captured initial state
        assert hasattr(input_handler, 'last_key_states')
        assert len(input_handler.last_key_states) == 16

    @patch('core.input_.keyboard.is_pressed')
    def test_check_keystates_changed_without_start_waiting(self, mock_is_pressed):
        """check_keystates_changed should handle case where start_waiting wasn't called."""
        mock_is_pressed.return_value = False
        input_handler = Input_()
        
        # This might raise AttributeError or handle gracefully depending on implementation
        # The current implementation expects start_waiting to be called first
        try:
            result = input_handler.check_keystates_changed()
            # If it handles gracefully, result should be reasonable
            assert result is None or isinstance(result, int)
        except AttributeError:
            # This is acceptable behavior - start_waiting should be called first
            pass


class TestIntegrationScenarios:
    @patch('core.input_.keyboard.is_pressed')
    def test_typical_key_waiting_workflow(self, mock_is_pressed):
        """Should handle typical key waiting workflow correctly."""
        input_handler = Input_()
        
        # Phase 1: Start waiting with no keys pressed
        mock_is_pressed.return_value = False
        input_handler.start_waiting()
        
        # Phase 2: Check while no keys pressed - should return None
        result1 = input_handler.check_keystates_changed()
        assert result1 is None
        
        # Phase 3: Key gets pressed
        def mock_side_effect(key):
            return key == 'x'
        
        mock_is_pressed.side_effect = mock_side_effect
        
        # Should detect the new key press
        result2 = input_handler.check_keystates_changed()
        assert result2 == 0x0
        
        # Phase 4: Same key still pressed - should return None
        result3 = input_handler.check_keystates_changed()
        assert result3 is None

    @patch('core.input_.keyboard.is_pressed')
    def test_multiple_key_transitions(self, mock_is_pressed):
        """Should handle multiple key state transitions correctly."""
        input_handler = Input_()
        
        # Start with 'x' pressed
        def initial_state(key):
            return key == 'x'
        
        mock_is_pressed.side_effect = initial_state
        input_handler.start_waiting()
        
        # Release 'x', press '1'
        def new_state(key):
            return key == '1'
        
        mock_is_pressed.side_effect = new_state
        
        # Should detect the new key press (even though another was released)
        result = input_handler.check_keystates_changed()
        assert result == 0x1