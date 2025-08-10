"""
Comprehensive Display Tests for CHIP-8 Emulator

Tests the Display class which handles:
- 64x32 pixel monochrome screen
- Sprite drawing with XOR logic
- Collision detection
- Screen clearing and refresh
- Terminal output rendering
"""

import pytest
from unittest.mock import patch, Mock, call
import sys
from io import StringIO

from core.display import Display


class TestDisplayInitialization:
    def test_display_initializes_with_correct_dimensions(self):
        """Display should initialize with 64x32 screen."""
        with patch('builtins.print'):
            display = Display()
        
        assert len(display.screen) == 32  # Height
        assert len(display.screen[0]) == 64  # Width
        assert len(display.prev_screen) == 32
        assert len(display.prev_screen[0]) == 64

    def test_display_initializes_all_pixels_false(self):
        """All pixels should be False (off) initially."""
        with patch('builtins.print'):
            display = Display()
        
        for row in display.screen:
            for pixel in row:
                assert pixel is False
        
        for row in display.prev_screen:
            for pixel in row:
                assert pixel is False

    @patch('sys.platform', 'win32')
    @patch('os.system')
    def test_windows_initialization_calls_os_system(self, mock_os_system):
        """On Windows, should call os.system to enable ANSI."""
        with patch('builtins.print'):
            Display()
        
        mock_os_system.assert_called_once_with('')

    @patch('sys.platform', 'linux')
    @patch('os.system')
    def test_non_windows_initialization_no_os_system(self, mock_os_system):
        """On non-Windows, should not call os.system."""
        with patch('builtins.print'):
            Display()
        
        mock_os_system.assert_not_called()

    @patch('builtins.print')
    def test_initialization_clears_terminal(self, mock_print):
        """Should clear terminal and move cursor to home on init."""
        Display()
        
        mock_print.assert_called_with("\033[2J\033[H", end="")


class TestClearScreen:
    def test_clear_screen_sets_all_pixels_false(self):
        """clear_screen should set all pixels to False."""
        with patch('builtins.print'):
            display = Display()
        
        # Set some pixels to True first
        display.screen[5][10] = True
        display.screen[15][25] = True
        display.screen[30][60] = True
        
        display.clear_screen()
        
        for row in display.screen:
            for pixel in row:
                assert pixel is False

    def test_clear_screen_preserves_dimensions(self):
        """clear_screen should maintain screen dimensions."""
        with patch('builtins.print'):
            display = Display()
        
        display.clear_screen()
        
        assert len(display.screen) == 32
        assert len(display.screen[0]) == 64

    def test_clear_screen_doesnt_affect_prev_screen(self):
        """clear_screen should not modify prev_screen."""
        with patch('builtins.print'):
            display = Display()
        
        # Set some pixels in prev_screen
        display.prev_screen[5][10] = True
        display.prev_screen[15][25] = True
        
        original_prev_screen = [row[:] for row in display.prev_screen]
        
        display.clear_screen()
        
        assert display.prev_screen == original_prev_screen


class TestSpriteDrawing:
    def test_draw_simple_sprite_no_collision(self):
        """Should draw sprite correctly without collision."""
        with patch('builtins.print'):
            display = Display()
        
        # Simple 2x2 sprite: 11
        #                     10
        sprite_data = [0b11000000, 0b10000000]  # 0xC0, 0x80
        
        collision = display.draw_sprite(0, 0, sprite_data)
        
        assert display.screen[0][0] is True   # First row, first pixel
        assert display.screen[0][1] is True   # First row, second pixel
        assert display.screen[1][0] is True   # Second row, first pixel
        assert display.screen[1][1] is False  # Second row, second pixel
        assert collision is False

    def test_draw_sprite_with_collision(self):
        """Should detect collision when sprite overlaps existing pixels."""
        with patch('builtins.print'):
            display = Display()
        
        # Set a pixel that will collide
        display.screen[0][0] = True
        
        # Draw sprite that overlaps
        sprite_data = [0b11000000]  # 0xC0
        
        collision = display.draw_sprite(0, 0, sprite_data)
        
        assert collision is True
        assert display.screen[0][0] is False  # XOR: True ^ True = False
        assert display.screen[0][1] is True   # XOR: False ^ True = True

    def test_draw_sprite_xor_logic(self):
        """Should use XOR logic for pixel drawing."""
        with patch('builtins.print'):
            display = Display()
        
        # Set some existing pixels
        display.screen[0][0] = True
        display.screen[0][1] = False
        display.screen[0][2] = True
        display.screen[0][3] = False
        
        # Draw sprite: 1010 (0xA0)
        sprite_data = [0b10100000]
        
        collision = display.draw_sprite(0, 0, sprite_data)
        
        # XOR results:
        assert display.screen[0][0] is False  # True ^ True = False
        assert display.screen[0][1] is False   # False ^ False = False
        assert display.screen[0][2] is False  # True ^ True = False
        assert display.screen[0][3] is False  # False ^ False = False
        assert collision is True  # Collision on pixels 0 and 2

    def test_draw_sprite_wrapping_horizontal(self):
        """Should wrap horizontally when sprite goes off right edge."""
        with patch('builtins.print'):
            display = Display()
        
        # Draw sprite at x=63 (last column)
        sprite_data = [0b11000000]  # Two pixels wide
        
        collision = display.draw_sprite(63, 0, sprite_data)
        
        assert display.screen[0][63] is True  # Last column
        assert display.screen[0][0] is True   # Wrapped to first column
        assert collision is False

    def test_draw_sprite_wrapping_vertical(self):
        """Should wrap vertically when sprite goes off bottom edge."""
        with patch('builtins.print'):
            display = Display()
        
        # Draw sprite at y=31 (last row)
        sprite_data = [0b10000000, 0b10000000]  # Two pixels tall
        
        collision = display.draw_sprite(0, 31, sprite_data)
        
        assert display.screen[31][0] is True  # Last row
        assert display.screen[0][0] is True   # Wrapped to first row
        assert collision is False

    def test_draw_sprite_at_various_positions(self):
        """Should draw sprites correctly at different positions."""
        with patch('builtins.print'):
            display = Display()
        
        positions = [(10, 15), (32, 8), (50, 25), (63, 31)]
        
        for x, y in positions:
            sprite_data = [0b10000000]  # Single pixel
            collision = display.draw_sprite(x, y, sprite_data)
            
            assert display.screen[y][x] is True
            assert collision is False

    def test_draw_empty_sprite(self):
        """Should handle empty sprite data gracefully."""
        with patch('builtins.print'):
            display = Display()
        
        collision = display.draw_sprite(10, 10, [])
        
        assert collision is False
        # No pixels should be affected
        for row in display.screen:
            for pixel in row:
                assert pixel is False

    def test_draw_sprite_all_zeros(self):
        """Should handle sprite with all zero bytes."""
        with patch('builtins.print'):
            display = Display()
        
        sprite_data = [0x00, 0x00, 0x00]
        collision = display.draw_sprite(10, 10, sprite_data)
        
        assert collision is False
        # No pixels should be set
        for row in display.screen:
            for pixel in row:
                assert pixel is False

    def test_draw_sprite_all_ones(self):
        """Should handle sprite with all 0xFF bytes."""
        with patch('builtins.print'):
            display = Display()
        
        sprite_data = [0xFF, 0xFF]  # Two rows of all pixels
        collision = display.draw_sprite(0, 0, sprite_data)
        
        assert collision is False
        # First 8 pixels of first two rows should be True
        for row_idx in range(2):
            for col_idx in range(8):
                assert display.screen[row_idx][col_idx] is True

    def test_draw_complex_sprite_pattern(self):
        """Should draw complex sprite patterns correctly."""
        with patch('builtins.print'):
            display = Display()
        
        # Draw a cross pattern
        cross_sprite = [
            0b00100000,  # ..1.....
            0b01110000,  # .111....
            0b00100000,  # ..1.....
        ]
        
        collision = display.draw_sprite(10, 10, cross_sprite)
        
        # Verify cross pattern
        assert display.screen[10][12] is True  # Top center
        assert display.screen[11][11] is True  # Middle left
        assert display.screen[11][12] is True  # Middle center
        assert display.screen[11][13] is True  # Middle right
        assert display.screen[12][12] is True  # Bottom center
        
        # Verify surrounding pixels are False
        assert display.screen[10][11] is False
        assert display.screen[10][13] is False
        assert collision is False


class TestCollisionDetection:
    def test_collision_single_pixel_overlap(self):
        """Should detect collision on single pixel overlap."""
        with patch('builtins.print'):
            display = Display()
        
        display.screen[5][5] = True
        sprite_data = [0b00010000]  # Single pixel at bit position 3
        
        collision = display.draw_sprite(2, 5, sprite_data)  # x=2, so pixel lands at 2+3=5
        
        assert collision is True

    def test_collision_multiple_pixel_overlap(self):
        """Should detect collision when multiple pixels overlap."""
        with patch('builtins.print'):
            display = Display()
        
        # Set multiple existing pixels
        display.screen[10][10] = True
        display.screen[10][12] = True
        
        # Draw sprite that overlaps both
        sprite_data = [0b10100000]  # Pixels at positions 0 and 2
        
        collision = display.draw_sprite(10, 10, sprite_data)
        
        assert collision is True

    def test_no_collision_adjacent_pixels(self):
        """Should not detect collision for adjacent but non-overlapping pixels."""
        with patch('builtins.print'):
            display = Display()
        
        # Set existing pixels
        display.screen[5][5] = True
        display.screen[5][7] = True
        
        # Draw sprite between them
        sprite_data = [0b01000000]  # Single pixel at position 1
        
        collision = display.draw_sprite(5, 5, sprite_data)  # Lands at position 6
        
        assert collision is False
        assert display.screen[5][6] is True  # New pixel should be set

    def test_collision_across_multiple_rows(self):
        """Should detect collision across multiple sprite rows."""
        with patch('builtins.print'):
            display = Display()
        
        # Set pixels in different rows
        display.screen[8][10] = True
        display.screen[10][12] = True
        
        sprite_data = [
            0b10000000,  # Row 8, pixel 10
            0b00000000,  # Row 9, no pixels
            0b00100000,  # Row 10, pixel 12
        ]
        
        collision = display.draw_sprite(10, 8, sprite_data)
        
        assert collision is True


class TestScreenRefresh:

    @patch('builtins.print')
    def test_refresh_no_output_when_no_changes(self, mock_print):
        """refresh should produce minimal output when nothing changed."""
        display = Display()
        
        # Both screens start as all False
        display.refresh()
        
        # Should only print final flush
        final_call = mock_print.call_args_list[-1]
        assert final_call == call("", end="", flush=True)

    @patch('builtins.print')
    def test_refresh_updates_prev_screen(self, mock_print):
        """refresh should update prev_screen to match current screen."""
        display = Display()
        
        # Change some pixels
        display.screen[1][2] = True
        display.screen[3][4] = False  # Already False, but testing
        
        display.refresh()
        
        # prev_screen should now match screen
        for row_idx in range(32):
            for col_idx in range(64):
                assert display.prev_screen[row_idx][col_idx] == display.screen[row_idx][col_idx]

class TestEdgeCases:
    def test_sprite_drawing_maximum_size(self):
        """Should handle maximum sprite size (15 rows)."""
        with patch('builtins.print'):
            display = Display()
        
        # Create 15-row sprite (maximum for CHIP-8)
        sprite_data = [0xFF] * 15
        
        collision = display.draw_sprite(0, 0, sprite_data)
        
        # First 8 pixels of first 15 rows should be True
        for row_idx in range(15):
            for col_idx in range(8):
                assert display.screen[row_idx][col_idx] is True
        
        assert collision is False

    def test_sprite_drawing_with_wrapping_edge_cases(self):
        """Should handle edge cases of screen wrapping."""
        with patch('builtins.print'):
            display = Display()
        
        # Draw at bottom-right corner
        sprite_data = [0b11000000, 0b11000000]  # 2x2 sprite
        
        collision = display.draw_sprite(63, 31, sprite_data)
        
        # Should wrap to all four corners
        assert display.screen[31][63] is True  # Bottom-right
        assert display.screen[31][0] is True   # Bottom-left (wrapped)
        assert display.screen[0][63] is True   # Top-right (wrapped)
        assert display.screen[0][0] is True    # Top-left (wrapped both ways)
        assert collision is False

    def test_screen_state_isolation(self):
        """Screen modifications should not affect other instances."""
        with patch('builtins.print'):
            display1 = Display()
            display2 = Display()
        
        # Modify first display
        display1.screen[5][5] = True
        display1.draw_sprite(10, 10, [0xFF])
        
        # Second display should be unaffected
        for row in display2.screen:
            for pixel in row:
                assert pixel is False

    def test_large_coordinate_values(self):
        """Should handle large coordinate values with proper wrapping."""
        with patch('builtins.print'):
            display = Display()
        
        # Use coordinates larger than screen dimensions
        sprite_data = [0b10000000]
        
        collision = display.draw_sprite(100, 50, sprite_data)  # Will wrap
        
        # 100 % 64 = 36, 50 % 32 = 18
        assert display.screen[18][36] is True
        assert collision is False

    def test_binary_string_formatting_edge_cases(self):
        """Should handle edge cases in binary string formatting."""
        with patch('builtins.print'):
            display = Display()
        
        # Test various byte values
        test_bytes = [0x01, 0x80, 0x55, 0xAA, 0x7F]
        
        for byte_val in test_bytes:
            display.clear_screen()
            sprite_data = [byte_val]
            collision = display.draw_sprite(0, 0, sprite_data)
            
            # Verify correct bit interpretation
            bit_string = format(byte_val, "08b")
            for bit_idx, bit_char in enumerate(bit_string):
                expected_state = bit_char == "1"
                assert display.screen[0][bit_idx] == expected_state
            
            assert collision is False


class TestIntegrationScenarios:
    def test_multiple_sprite_overlays(self):
        """Should handle multiple overlapping sprites correctly."""
        with patch('builtins.print'):
            display = Display()
        
        # Draw first sprite
        sprite1 = [0b11110000]  # 1111....
        collision1 = display.draw_sprite(0, 0, sprite1)
        
        # Draw overlapping sprite
        sprite2 = [0b01111000]  # .1111...
        collision2 = display.draw_sprite(0, 0, sprite2)
        
        # Result should be XOR of both sprites
        # 11110000 XOR 01111000 = 10001000
        expected_result = [True, False, False, False, True, False, False, False]
        
        for i in range(8):
            assert display.screen[0][i] == expected_result[i]
        
        assert collision1 is False
        assert collision2 is True  # Collision on overlapping bits

    def test_clear_and_redraw_cycle(self):
        """Should handle clear->draw->clear cycles correctly."""
        with patch('builtins.print'):
            display = Display()
        
        # Draw initial pattern
        sprite_data = [0xFF, 0x81, 0xFF]  # Border pattern
        display.draw_sprite(10, 10, sprite_data)
        
        # Verify pixels are set
        assert display.screen[10][10] is True
        assert display.screen[11][10] is True
        
        # Clear screen
        display.clear_screen()
        
        # Verify all pixels are off
        for row in display.screen:
            for pixel in row:
                assert pixel is False
        
        # Redraw same pattern
        collision = display.draw_sprite(10, 10, sprite_data)
        
        # Should be identical to first draw
        assert display.screen[10][10] is True
        assert display.screen[11][10] is True
        assert collision is False

    @patch('builtins.print')
    def test_refresh_after_multiple_operations(self, mock_print):
        """Should handle refresh after complex drawing operations."""
        display = Display()
        
        # Perform multiple operations
        display.draw_sprite(0, 0, [0xFF])
        display.draw_sprite(32, 16, [0xF0, 0x90, 0xF0])
        display.draw_sprite(0, 0, [0x0F])  # Partial overlap
        
        # Should handle refresh of complex state
        display.refresh()
        
        # Verify final flush call
        final_call = mock_print.call_args_list[-1]
        assert final_call == call("", end="", flush=True)
        
        # Should have output for changed pixels
        assert mock_print.call_count > 1