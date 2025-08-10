"""
Comprehensive CPU Tests for CHIP-8 Emulator

Tests all CPU instructions, state management, and edge cases.
Organized by instruction categories matching the CPU's dispatch structure.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from time import perf_counter

from core.cpu import CPU
from core.memory import Memory
from core.display import Display
from core.input_ import Input_
from core.errors import UnsupportedOpcodeError
from configs import ROM_START_IDX, REGISTER_COUNT, STACK_SIZE, VF_IDX


class TestCPUInitialization:
    def test_cpu_initializes_with_correct_defaults(self):
        """CPU should initialize with proper default state."""
        memory = Mock(spec=Memory)
        display = Mock(spec=Display)
        input_ = Mock(spec=Input_)
        
        cpu = CPU(memory, display, input_)
        
        assert cpu.registers == [0] * REGISTER_COUNT
        assert cpu.pc == ROM_START_IDX
        assert cpu.i == 0
        assert cpu.sp == 0
        assert cpu.stack == [0] * STACK_SIZE
        assert cpu.delay_timer == 0
        assert cpu.sound_timer == 0
        assert cpu.pc_modified is False
        assert cpu.waiting_for_key is False

    def test_cpu_stores_component_references(self):
        """CPU should store references to all components."""
        memory = Mock(spec=Memory)
        display = Mock(spec=Display)
        input_ = Mock(spec=Input_)
        
        cpu = CPU(memory, display, input_)
        
        assert cpu.memory is memory
        assert cpu.display is display
        assert cpu.input_ is input_


class TestCycleExecution:
    def test_normal_cycle_fetches_and_executes(self):
        """Normal cycle should fetch opcode and execute instruction."""
        memory = Mock(spec=Memory)
        display = Mock(spec=Display)
        input_ = Mock(spec=Input_)
        
        memory.read_word.return_value = 0x00E0  # Clear screen
        display.clear_screen = Mock()
        
        cpu = CPU(memory, display, input_)
        initial_pc = cpu.pc
        
        cpu.cycle()
        
        memory.read_word.assert_called_once_with(initial_pc)
        display.clear_screen.assert_called_once()
        assert cpu.pc == initial_pc + 2  # PC should increment

    def test_cycle_when_waiting_for_key(self):
        """When waiting for key, should not execute instructions."""
        memory = Mock(spec=Memory)
        display = Mock(spec=Display)
        input_ = Mock(spec=Input_)
        
        cpu = CPU(memory, display, input_)
        cpu.waiting_for_key = True
        cpu.check_any_key_pressed = Mock(return_value=False)
        
        cpu.cycle()
        
        memory.read_word.assert_not_called()
        assert cpu.waiting_for_key is True

    def test_cycle_pc_modified_prevents_increment(self):
        """When pc_modified is True, PC should not auto-increment."""
        memory = Mock(spec=Memory)
        display = Mock(spec=Display)
        input_ = Mock(spec=Input_)
        
        memory.read_word.return_value = 0x1200  # Jump to 0x200
        
        cpu = CPU(memory, display, input_)
        initial_pc = cpu.pc
        
        cpu.cycle()
        
        assert cpu.pc == 0x200  # Should be at jump destination
        assert cpu.pc != initial_pc + 2  # Should not have incremented


class TestSystemControlOpcodes:
    def test_clear_screen_00E0(self):
        """00E0 should clear the display."""
        memory = Mock(spec=Memory)
        display = Mock(spec=Display)
        input_ = Mock(spec=Input_)
        
        memory.read_word.return_value = 0x00E0
        
        cpu = CPU(memory, display, input_)
        cpu.cycle()
        
        display.clear_screen.assert_called_once()

    def test_return_from_subroutine_00EE(self):
        """00EE should return from subroutine."""
        memory = Mock(spec=Memory)
        display = Mock(spec=Display)
        input_ = Mock(spec=Input_)
        
        memory.read_word.return_value = 0x00EE
        
        cpu = CPU(memory, display, input_)
        cpu.stack[0] = 0x300
        cpu.sp = 1
        
        cpu.cycle()
        
        assert cpu.pc == 0x300 + 2
        assert cpu.sp == 0

    def test_return_empty_stack_raises_error(self):
        """00EE with empty stack should raise error."""
        memory = Mock(spec=Memory)
        display = Mock(spec=Display)
        input_ = Mock(spec=Input_)
        
        cpu = CPU(memory, display, input_)
        cpu.opcode = 0x00EE
        cpu.sp = 0
        
        with pytest.raises(RuntimeError, match="RET called with empty stack"):
            cpu.return_from_subroutine()


class TestJumpOpcodes:
    def test_jump_1nnn(self):
        """1nnn should jump to address nnn."""
        memory = Mock(spec=Memory)
        display = Mock(spec=Display)
        input_ = Mock(spec=Input_)
        
        memory.read_word.return_value = 0x1234
        
        cpu = CPU(memory, display, input_)
        cpu.cycle()
        
        assert cpu.pc == 0x234

    def test_jump_with_offset_Bnnn(self):
        """Bnnn should jump to address nnn + V0."""
        memory = Mock(spec=Memory)
        display = Mock(spec=Display)
        input_ = Mock(spec=Input_)
        
        memory.read_word.return_value = 0xB234
        
        cpu = CPU(memory, display, input_)
        cpu.registers[0] = 0x10
        cpu.cycle()
        
        assert cpu.pc == 0x234 + 0x10


class TestSubroutineOpcodes:
    def test_call_subroutine_2nnn(self):
        """2nnn should call subroutine at nnn."""
        memory = Mock(spec=Memory)
        display = Mock(spec=Display)
        input_ = Mock(spec=Input_)
        
        memory.read_word.return_value = 0x2345
        
        cpu = CPU(memory, display, input_)
        initial_pc = cpu.pc
        
        cpu.cycle()
        
        assert cpu.stack[0] == initial_pc
        assert cpu.sp == 1
        assert cpu.pc == 0x345


class TestConditionalSkipOpcodes:
    def test_skip_if_equal_immediate_3xkk_true(self):
        """3xkk should skip if Vx == kk."""
        memory = Mock(spec=Memory)
        display = Mock(spec=Display)
        input_ = Mock(spec=Input_)
        
        memory.read_word.return_value = 0x3142  # Skip if V1 == 0x42
        
        cpu = CPU(memory, display, input_)
        cpu.registers[1] = 0x42
        initial_pc = cpu.pc
        
        cpu.cycle()
        
        assert cpu.pc == initial_pc + 4  # Should skip next instruction

    def test_skip_if_equal_immediate_3xkk_false(self):
        """3xkk should not skip if Vx != kk."""
        memory = Mock(spec=Memory)
        display = Mock(spec=Display)
        input_ = Mock(spec=Input_)
        
        memory.read_word.return_value = 0x3142
        
        cpu = CPU(memory, display, input_)
        cpu.registers[1] = 0x43  # Different value
        initial_pc = cpu.pc
        
        cpu.cycle()
        
        assert cpu.pc == initial_pc + 2  # Normal increment

    def test_skip_if_not_equal_immediate_4xkk(self):
        """4xkk should skip if Vx != kk."""
        memory = Mock(spec=Memory)
        display = Mock(spec=Display)
        input_ = Mock(spec=Input_)
        
        memory.read_word.return_value = 0x4142
        
        cpu = CPU(memory, display, input_)
        cpu.registers[1] = 0x43  # Different value
        initial_pc = cpu.pc
        
        cpu.cycle()
        
        assert cpu.pc == initial_pc + 4  # Should skip

    def test_skip_if_equal_register_5xy0(self):
        """5xy0 should skip if Vx == Vy."""
        memory = Mock(spec=Memory)
        display = Mock(spec=Display)
        input_ = Mock(spec=Input_)
        
        memory.read_word.return_value = 0x5120  # Skip if V1 == V2
        
        cpu = CPU(memory, display, input_)
        cpu.registers[1] = 0x42
        cpu.registers[2] = 0x42
        initial_pc = cpu.pc
        
        cpu.cycle()
        
        assert cpu.pc == initial_pc + 4

    def test_skip_if_not_equal_register_9xy0(self):
        """9xy0 should skip if Vx != Vy."""
        memory = Mock(spec=Memory)
        display = Mock(spec=Display)
        input_ = Mock(spec=Input_)
        
        memory.read_word.return_value = 0x9120
        
        cpu = CPU(memory, display, input_)
        cpu.registers[1] = 0x42
        cpu.registers[2] = 0x43  # Different
        initial_pc = cpu.pc
        
        cpu.cycle()
        
        assert cpu.pc == initial_pc + 4


class TestRegisterOpcodes:
    def test_set_register_6xkk(self):
        """6xkk should set Vx to kk."""
        memory = Mock(spec=Memory)
        display = Mock(spec=Display)
        input_ = Mock(spec=Input_)
        
        memory.read_word.return_value = 0x6142  # Set V1 to 0x42
        
        cpu = CPU(memory, display, input_)
        cpu.cycle()
        
        assert cpu.registers[1] == 0x42

    def test_add_immediate_7xkk(self):
        """7xkk should add kk to Vx (no carry)."""
        memory = Mock(spec=Memory)
        display = Mock(spec=Display)
        input_ = Mock(spec=Input_)
        
        memory.read_word.return_value = 0x7110  # Add 0x10 to V1
        
        cpu = CPU(memory, display, input_)
        cpu.registers[1] = 0x20
        cpu.cycle()
        
        assert cpu.registers[1] == 0x30

    def test_add_immediate_7xkk_overflow(self):
        """7xkk should wrap around on overflow."""
        memory = Mock(spec=Memory)
        display = Mock(spec=Display)
        input_ = Mock(spec=Input_)
        
        memory.read_word.return_value = 0x7110
        
        cpu = CPU(memory, display, input_)
        cpu.registers[1] = 0xFF
        cpu.cycle()
        
        assert cpu.registers[1] == 0x0F  # (0xFF + 0x10) % 256


class TestArithmeticOpcodes:
    def test_register_copy_8xy0(self):
        """8xy0 should copy Vy to Vx."""
        memory = Mock(spec=Memory)
        display = Mock(spec=Display)
        input_ = Mock(spec=Input_)
        
        memory.read_word.return_value = 0x8120  # Copy V2 to V1
        
        cpu = CPU(memory, display, input_)
        cpu.registers[2] = 0x42
        cpu.cycle()
        
        assert cpu.registers[1] == 0x42

    def test_bitwise_or_8xy1(self):
        """8xy1 should OR Vx with Vy."""
        memory = Mock(spec=Memory)
        display = Mock(spec=Display)
        input_ = Mock(spec=Input_)
        
        memory.read_word.return_value = 0x8121
        
        cpu = CPU(memory, display, input_)
        cpu.registers[1] = 0b11110000
        cpu.registers[2] = 0b00001111
        cpu.cycle()
        
        assert cpu.registers[1] == 0b11111111

    def test_bitwise_and_8xy2(self):
        """8xy2 should AND Vx with Vy."""
        memory = Mock(spec=Memory)
        display = Mock(spec=Display)
        input_ = Mock(spec=Input_)
        
        memory.read_word.return_value = 0x8122
        
        cpu = CPU(memory, display, input_)
        cpu.registers[1] = 0b11110000
        cpu.registers[2] = 0b11001100
        cpu.cycle()
        
        assert cpu.registers[1] == 0b11000000

    def test_bitwise_xor_8xy3(self):
        """8xy3 should XOR Vx with Vy."""
        memory = Mock(spec=Memory)
        display = Mock(spec=Display)
        input_ = Mock(spec=Input_)
        
        memory.read_word.return_value = 0x8123
        
        cpu = CPU(memory, display, input_)
        cpu.registers[1] = 0b11110000
        cpu.registers[2] = 0b11001100
        cpu.cycle()
        
        assert cpu.registers[1] == 0b00111100

    def test_add_with_carry_8xy4_no_carry(self):
        """8xy4 should add with carry flag."""
        memory = Mock(spec=Memory)
        display = Mock(spec=Display)
        input_ = Mock(spec=Input_)
        
        memory.read_word.return_value = 0x8124
        
        cpu = CPU(memory, display, input_)
        cpu.registers[1] = 0x10
        cpu.registers[2] = 0x20
        cpu.cycle()
        
        assert cpu.registers[1] == 0x30
        assert cpu.registers[VF_IDX] == 0  # No carry

    def test_add_with_carry_8xy4_with_carry(self):
        """8xy4 should set carry flag on overflow."""
        memory = Mock(spec=Memory)
        display = Mock(spec=Display)
        input_ = Mock(spec=Input_)
        
        memory.read_word.return_value = 0x8124
        
        cpu = CPU(memory, display, input_)
        cpu.registers[1] = 0xFF
        cpu.registers[2] = 0x02
        cpu.cycle()
        
        assert cpu.registers[1] == 0x01  # (0xFF + 0x02) % 256
        assert cpu.registers[VF_IDX] == 1  # Carry set

    def test_subtract_8xy5_no_borrow(self):
        """8xy5 should subtract Vy from Vx."""
        memory = Mock(spec=Memory)
        display = Mock(spec=Display)
        input_ = Mock(spec=Input_)
        
        memory.read_word.return_value = 0x8125
        
        cpu = CPU(memory, display, input_)
        cpu.registers[1] = 0x30
        cpu.registers[2] = 0x10
        cpu.cycle()
        
        assert cpu.registers[1] == 0x20
        assert cpu.registers[VF_IDX] == 1  # No borrow

    def test_subtract_8xy5_with_borrow(self):
        """8xy5 should handle underflow with borrow."""
        memory = Mock(spec=Memory)
        display = Mock(spec=Display)
        input_ = Mock(spec=Input_)
        
        memory.read_word.return_value = 0x8125
        
        cpu = CPU(memory, display, input_)
        cpu.registers[1] = 0x10
        cpu.registers[2] = 0x20
        cpu.cycle()
        
        assert cpu.registers[1] == 0xF0  # (0x10 - 0x20 + 256) % 256
        assert cpu.registers[VF_IDX] == 0  # Borrow occurred

    def test_shift_right_8xy6(self):
        """8xy6 should shift Vx right and set VF to LSB."""
        memory = Mock(spec=Memory)
        display = Mock(spec=Display)
        input_ = Mock(spec=Input_)
        
        memory.read_word.return_value = 0x8126
        
        cpu = CPU(memory, display, input_)
        cpu.registers[1] = 0b11010111
        cpu.cycle()
        
        assert cpu.registers[1] == 0b01101011  # Shifted right
        assert cpu.registers[VF_IDX] == 1  # LSB was 1

    def test_subtract_reverse_8xy7(self):
        """8xy7 should subtract Vx from Vy."""
        memory = Mock(spec=Memory)
        display = Mock(spec=Display)
        input_ = Mock(spec=Input_)
        
        memory.read_word.return_value = 0x8127
        
        cpu = CPU(memory, display, input_)
        cpu.registers[1] = 0x10
        cpu.registers[2] = 0x30
        cpu.cycle()
        
        assert cpu.registers[1] == 0x20  # V2 - V1
        assert cpu.registers[VF_IDX] == 1  # No borrow

    def test_shift_left_8xyE(self):
        """8xyE should shift Vx left and set VF to MSB."""
        memory = Mock(spec=Memory)
        display = Mock(Display)
        input_ = Mock(spec=Input_)
        
        memory.read_word.return_value = 0x812E
        
        cpu = CPU(memory, display, input_)
        cpu.registers[1] = 0b11010111
        cpu.cycle()
        
        assert cpu.registers[1] == 0b10101110  # Shifted left, masked
        assert cpu.registers[VF_IDX] == 1  # MSB was 1


class TestMemoryOpcodes:
    def test_set_index_Annn(self):
        """Annn should set I register to nnn."""
        memory = Mock(spec=Memory)
        display = Mock(spec=Display)
        input_ = Mock(spec=Input_)
        
        memory.read_word.return_value = 0xA234
        
        cpu = CPU(memory, display, input_)
        cpu.cycle()
        
        assert cpu.i == 0x234

    def test_add_to_index_Fx1E(self):
        """Fx1E should add Vx to I."""
        memory = Mock(spec=Memory)
        display = Mock(spec=Display)
        input_ = Mock(spec=Input_)
        
        memory.read_word.return_value = 0xF11E  # Add V1 to I
        
        cpu = CPU(memory, display, input_)
        cpu.registers[1] = 0x10
        cpu.i = 0x200
        cpu.cycle()
        
        assert cpu.i == 0x210


class TestRandomOpcode:
    @patch('core.cpu.randint')
    def test_random_Cxkk(self, mock_randint):
        """Cxkk should set Vx to random & kk."""
        mock_randint.return_value = 0b11110000
        
        memory = Mock(spec=Memory)
        display = Mock(spec=Display)
        input_ = Mock(spec=Input_)
        
        memory.read_word.return_value = 0xC13F  # Random for V1, mask 0x3F
        
        cpu = CPU(memory, display, input_)
        cpu.cycle()
        
        assert cpu.registers[1] == (0b11110000 & 0x3F)
        mock_randint.assert_called_once_with(0, 255)


class TestDisplayOpcodes:
    def test_draw_sprite_Dxyn(self):
        """Dxyn should draw sprite and set VF on collision."""
        memory = Mock(spec=Memory)
        display = Mock(spec=Display)
        input_ = Mock(spec=Input_)
        
        memory.read_word.return_value = 0xD123  # Draw at V1,V2, height 3
        memory.read_byte.side_effect = [0xF0, 0x90, 0x90]  # Sprite data
        display.draw_sprite.return_value = True  # Collision
        
        cpu = CPU(memory, display, input_)
        cpu.registers[1] = 10  # x
        cpu.registers[2] = 20  # y
        cpu.i = 0x300
        cpu.cycle()
        
        display.draw_sprite.assert_called_once_with(10, 20, [0xF0, 0x90, 0x90])
        assert cpu.registers[VF_IDX] == 1  # Collision flag


class TestInputOpcodes:
    def test_skip_if_key_pressed_Ex9E(self):
        """Ex9E should skip if key Vx is pressed."""
        memory = Mock(spec=Memory)
        display = Mock(spec=Display)
        input_ = Mock(spec=Input_)
        
        memory.read_word.return_value = 0xE19E  # Skip if key V1 pressed
        input_.key_pressed.return_value = True
        
        cpu = CPU(memory, display, input_)
        cpu.registers[1] = 0x5  # Key 5
        initial_pc = cpu.pc
        cpu.cycle()
        
        input_.key_pressed.assert_called_once_with(0x5)
        assert cpu.pc == initial_pc + 4  # Should skip

    def test_skip_if_key_not_pressed_ExA1(self):
        """ExA1 should skip if key Vx is not pressed."""
        memory = Mock(spec=Memory)
        display = Mock(spec=Display)
        input_ = Mock(spec=Input_)
        
        memory.read_word.return_value = 0xE1A1
        input_.key_not_pressed.return_value = True
        
        cpu = CPU(memory, display, input_)
        cpu.registers[1] = 0x5
        initial_pc = cpu.pc
        cpu.cycle()
        
        input_.key_not_pressed.assert_called_once_with(0x5)
        assert cpu.pc == initial_pc + 4

    def test_wait_for_key_Fx0A(self):
        """Fx0A should wait for key press."""
        memory = Mock(spec=Memory)
        display = Mock(spec=Display)
        input_ = Mock(spec=Input_)
        
        memory.read_word.return_value = 0xF10A
        input_.start_waiting = Mock()
        
        cpu = CPU(memory, display, input_)
        cpu.cycle()
        
        input_.start_waiting.assert_called_once()
        assert cpu.waiting_for_key is True


class TestTimerOpcodes:
    def test_set_delay_timer_Fx15(self):
        """Fx15 should set delay timer to Vx."""
        memory = Mock(spec=Memory)
        display = Mock(spec=Display)
        input_ = Mock(spec=Input_)
        
        memory.read_word.return_value = 0xF115
        
        cpu = CPU(memory, display, input_)
        cpu.registers[1] = 0x42
        cpu.cycle()
        
        assert cpu.delay_timer == 0x42

    def test_set_sound_timer_Fx18(self):
        """Fx18 should set sound timer to Vx."""
        memory = Mock(spec=Memory)
        display = Mock(spec=Display)
        input_ = Mock(spec=Input_)
        
        memory.read_word.return_value = 0xF118
        
        cpu = CPU(memory, display, input_)
        cpu.registers[1] = 0x42
        cpu.cycle()
        
        assert cpu.sound_timer == 0x42

    def test_get_delay_timer_Fx07(self):
        """Fx07 should set Vx to delay timer."""
        memory = Mock(spec=Memory)
        display = Mock(spec=Display)
        input_ = Mock(spec=Input_)
        
        memory.read_word.return_value = 0xF107
        
        cpu = CPU(memory, display, input_)
        cpu.delay_timer = 0x42
        cpu.cycle()
        
        assert cpu.registers[1] == 0x42

    @patch('core.cpu.perf_counter')
    def test_update_timers_decrements_at_60hz(self, mock_perf_counter):
        """Timers should decrement at 60Hz."""
        mock_perf_counter.side_effect = [0.0, 1.0/60 + 0.001]  # Just over 60Hz
        
        memory = Mock(spec=Memory)
        display = Mock(spec=Display)
        input_ = Mock(spec=Input_)
        
        cpu = CPU(memory, display, input_)
        cpu.delay_timer = 5
        cpu.sound_timer = 3
        cpu.last_timer_update = 0.0
        
        cpu.update_timers()
        
        assert cpu.delay_timer == 4
        assert cpu.sound_timer == 2


class TestBCDAndMemoryOpcodes:
    def test_store_bcd_Fx33(self):
        """Fx33 should store BCD representation."""
        memory = Mock(spec=Memory)
        display = Mock(spec=Display)
        input_ = Mock(spec=Input_)
        
        memory.read_word.return_value = 0xF133
        
        cpu = CPU(memory, display, input_)
        cpu.registers[1] = 123
        cpu.i = 0x300
        cpu.cycle()
        
        # Should store 1, 2, 3 at I, I+1, I+2
        memory.write_byte.assert_any_call(0x300, 1)
        memory.write_byte.assert_any_call(0x301, 2)
        memory.write_byte.assert_any_call(0x302, 3)

    def test_store_registers_Fx55(self):
        """Fx55 should store V0-Vx to memory."""
        memory = Mock(spec=Memory)
        display = Mock(spec=Display)
        input_ = Mock(spec=Input_)
        
        memory.read_word.return_value = 0xF255  # Store V0-V2
        
        cpu = CPU(memory, display, input_)
        cpu.registers[0] = 0x10
        cpu.registers[1] = 0x20
        cpu.registers[2] = 0x30
        cpu.i = 0x300
        cpu.cycle()
        
        memory.write_byte.assert_any_call(0x300, 0x10)
        memory.write_byte.assert_any_call(0x301, 0x20)
        memory.write_byte.assert_any_call(0x302, 0x30)

    def test_load_registers_Fx65(self):
        """Fx65 should load V0-Vx from memory."""
        memory = Mock(spec=Memory)
        display = Mock(spec=Display)
        input_ = Mock(spec=Input_)
        
        memory.read_word.return_value = 0xF265
        memory.read_byte.side_effect = [0x10, 0x20, 0x30]
        
        cpu = CPU(memory, display, input_)
        cpu.i = 0x300
        cpu.cycle()
        
        assert cpu.registers[0] == 0x10
        assert cpu.registers[1] == 0x20
        assert cpu.registers[2] == 0x30

    def test_font_location_Fx29(self):
        """Fx29 should set I to font location."""
        memory = Mock(spec=Memory)
        display = Mock(spec=Display)
        input_ = Mock(spec=Input_)
        
        memory.read_word.return_value = 0xF129
        memory.get_sprite_address.return_value = 0x150
        
        cpu = CPU(memory, display, input_)
        cpu.registers[1] = 0xA  # Font for 'A'
        cpu.cycle()
        
        memory.get_sprite_address.assert_called_once_with(0xA)
        assert cpu.i == 0x150


class TestErrorHandling:
    def test_unsupported_opcode_raises_error(self):
        """Unsupported opcodes should raise UnsupportedOpcodeError."""
        memory = Mock(spec=Memory)
        display = Mock(spec=Display)
        input_ = Mock(spec=Input_)
        
        memory.read_word.return_value = 0xFFFF  # Invalid opcode
        
        cpu = CPU(memory, display, input_)
        
        with pytest.raises(UnsupportedOpcodeError):
            cpu.cycle()

    def test_invalid_sys_opcode_raises_error(self):
        """Invalid system opcodes should raise error."""
        memory = Mock(spec=Memory)
        display = Mock(spec=Display)
        input_ = Mock(spec=Input_)
        
        cpu = CPU(memory, display, input_)
        cpu.opcode = 0x0123  # Invalid system opcode
        
        with pytest.raises(UnsupportedOpcodeError):
            cpu.dispatch_sys_control()


class TestHelperMethods:
    def test_nibble_extraction_methods(self):
        """Helper methods should extract correct nibbles."""
        memory = Mock(spec=Memory)
        display = Mock(spec=Display)
        input_ = Mock(spec=Input_)
        
        cpu = CPU(memory, display, input_)
        cpu.opcode = 0x1234
        
        assert cpu._second_nibble() == 0x2
        assert cpu._third_nibble() == 0x3
        assert cpu._fourth_nibble() == 0x4
        assert cpu._second_byte() == 0x34
        assert cpu._last_3_nibbles() == 0x234


class TestKeyWaitingLogic:
    def test_check_any_key_pressed_returns_key(self):
        """Should detect key press and store in register."""
        memory = Mock(spec=Memory)
        display = Mock(spec=Display)
        input_ = Mock(spec=Input_)
        
        input_.check_keystates_changed.return_value = 0x5
        
        cpu = CPU(memory, display, input_)
        cpu.opcode = 0xF10A  # Wait for key in V1
        
        result = cpu.check_any_key_pressed()
        
        assert result is True
        assert cpu.registers[1] == 0x5
        assert cpu.waiting_for_key is False

    def test_check_any_key_pressed_no_key(self):
        """Should return False when no key pressed."""
        memory = Mock(spec=Memory)
        display = Mock(spec=Display)
        input_ = Mock(spec=Input_)
        
        input_.check_keystates_changed.return_value = None
        
        cpu = CPU(memory, display, input_)
        
        result = cpu.check_any_key_pressed()
        
        assert result is False


class TestEdgeCases:
    def test_bcd_with_single_digit(self):
        """BCD should handle single digit numbers."""
        memory = Mock(spec=Memory)
        display = Mock(spec=Display)
        input_ = Mock(spec=Input_)
        
        cpu = CPU(memory, display, input_)
        cpu.opcode = 0xF133
        cpu.registers[1] = 7
        cpu.i = 0x300
        
        cpu.store_bcd()
        
        memory.write_byte.assert_any_call(0x300, 0)  # Hundreds
        memory.write_byte.assert_any_call(0x301, 0)  # Tens
        memory.write_byte.assert_any_call(0x302, 7)  # Ones

    def test_bcd_with_max_value(self):
        """BCD should handle 255 (max byte value)."""
        memory = Mock(spec=Memory)
        display = Mock(spec=Display)
        input_ = Mock(spec=Input_)
        
        cpu = CPU(memory, display, input_)
        cpu.opcode = 0xF133
        cpu.registers[1] = 255
        cpu.i = 0x300
        
        cpu.store_bcd()
        
        memory.write_byte.assert_any_call(0x300, 2)  # Hundreds
        memory.write_byte.assert_any_call(0x301, 5)  # Tens
        memory.write_byte.assert_any_call(0x302, 5)  # Ones

    def test_shift_operations_with_zero(self):
        """Shift operations should handle zero correctly."""
        memory = Mock(spec=Memory)
        display = Mock(spec=Display)
        input_ = Mock(spec=Input_)
        
        cpu = CPU(memory, display, input_)
        
        # Test right shift with 0
        cpu.shift_reg_right(1, 0)
        assert cpu.registers[1] == 0
        assert cpu.registers[VF_IDX] == 0
        
        # Test left shift with 0
        cpu.shift_reg_left(1, 0)
        assert cpu.registers[1] == 0
        assert cpu.registers[VF_IDX] == 0

    def test_stack_overflow_scenario(self):
        """Should handle deep call stack correctly."""
        memory = Mock(spec=Memory)
        display = Mock(spec=Display)
        input_ = Mock(spec=Input_)
        
        cpu = CPU(memory, display, input_)
        
        # Fill stack to near capacity
        for i in range(STACK_SIZE - 1):
            cpu.stack[i] = 0x200 + i * 2
            cpu.sp = i + 1
        
        # Should still be able to make one more call
        cpu.opcode = 0x2345
        cpu.call()
        
        assert cpu.sp == STACK_SIZE
        assert cpu.pc == 0x345

    def test_register_operations_dont_affect_other_registers(self):
        """Register operations should be isolated."""
        memory = Mock(spec=Memory)
        display = Mock(spec=Display)
        input_ = Mock(spec=Input_)
        
        cpu = CPU(memory, display, input_)
        
        # Set all registers to known values
        for i in range(REGISTER_COUNT):
            cpu.registers[i] = i * 10
        
        # Modify one register
        cpu.opcode = 0x6542  # Set V5 to 0x42
        cpu.set_reg()
        
        # Check only V5 changed
        for i in range(REGISTER_COUNT):
            if i == 5:
                assert cpu.registers[i] == 0x42
            else:
                assert cpu.registers[i] == i * 10

    def test_timer_edge_cases(self):
        """Timer operations should handle edge cases."""
        memory = Mock(spec=Memory)
        display = Mock(spec=Display)
        input_ = Mock(spec=Input_)
        
        cpu = CPU(memory, display, input_)
        
        # Test timer at 0 doesn't underflow
        cpu.delay_timer = 0
        cpu.sound_timer = 0
        
        with patch('core.cpu.perf_counter', side_effect=[0.0, 1.0/60 + 0.001]):
            cpu.update_timers()
        
        assert cpu.delay_timer == 0
        assert cpu.sound_timer == 0

    def test_memory_register_exchange_boundary(self):
        """Memory/register exchange should handle all registers."""
        memory = Mock(spec=Memory)
        display = Mock(spec=Display)
        input_ = Mock(spec=Input_)
        
        # Test storing all 16 registers
        memory.read_word.return_value = 0xFF55  # Store V0-VF
        
        cpu = CPU(memory, display, input_)
        for i in range(16):
            cpu.registers[i] = i * 10
        cpu.i = 0x300
        
        cpu.cycle()
        
        # Should have called write_byte 16 times
        assert memory.write_byte.call_count == 16
        for i in range(16):
            memory.write_byte.assert_any_call(0x300 + i, i * 10)


class TestInstructionTiming:
    def test_pc_increment_timing(self):
        """PC should increment after instruction execution."""
        memory = Mock(spec=Memory)
        display = Mock(spec=Display)
        input_ = Mock(spec=Input_)
        
        memory.read_word.return_value = 0x6142  # Set V1 to 0x42
        
        cpu = CPU(memory, display, input_)
        initial_pc = cpu.pc
        
        cpu.cycle()
        
        assert cpu.registers[1] == 0x42  # Instruction executed
        assert cpu.pc == initial_pc + 2  # PC incremented

    def test_pc_modified_flag_reset(self):
        """pc_modified flag should reset after each cycle."""
        memory = Mock(spec=Memory)
        display = Mock(spec=Display)
        input_ = Mock(spec=Input_)
        
        memory.read_word.side_effect = [0x1234, 0x6142]  # Jump, then normal instruction
        
        cpu = CPU(memory, display, input_)
        
        # First cycle: jump instruction
        cpu.cycle()
        assert cpu.pc_modified is False  # Should be reset
        assert cpu.pc == 0x234
        
        # Second cycle: normal instruction
        saved_pc = cpu.pc
        cpu.cycle()
        assert cpu.pc_modified is False
        assert cpu.pc == saved_pc + 2


class TestComplexScenarios:
    def test_nested_subroutine_calls(self):
        """Should handle nested subroutine calls correctly."""
        memory = Mock(spec=Memory)
        display = Mock(spec=Display)
        input_ = Mock(spec=Input_)
        
        cpu = CPU(memory, display, input_)
        initial_pc = cpu.pc
        
        # First call
        cpu.opcode = 0x2300
        cpu.call()
        assert cpu.stack[0] == initial_pc
        assert cpu.sp == 1
        assert cpu.pc == 0x300
        
        # Second call (nested)
        saved_pc = cpu.pc
        cpu.opcode = 0x2400
        cpu.call()
        assert cpu.stack[1] == saved_pc
        assert cpu.sp == 2
        assert cpu.pc == 0x400
        
        # First return
        cpu.opcode = 0x00EE
        cpu.return_from_subroutine()
        assert cpu.pc == saved_pc
        assert cpu.sp == 1
        
        # Second return
        cpu.return_from_subroutine()
        assert cpu.pc == initial_pc
        assert cpu.sp == 0

    def test_conditional_skip_chains(self):
        """Should handle multiple conditional skips correctly."""
        memory = Mock(spec=Memory)
        display = Mock(spec=Display)
        input_ = Mock(spec=Input_)
        
        cpu = CPU(memory, display, input_)
        cpu.registers[1] = 0x42
        initial_pc = cpu.pc
        
        # Skip if V1 == 0x42 (should skip)
        cpu.opcode = 0x3142
        cpu.skip_eq_neq_nn()
        assert cpu.pc == initial_pc + 2  # Skipped
        
        # Reset PC for next test
        cpu.pc = initial_pc
        
        # Skip if V1 != 0x43 (should skip)
        cpu.opcode = 0x4143
        cpu.skip_eq_neq_nn()
        assert cpu.pc == initial_pc + 2  # Skipped

    def test_sprite_drawing_integration(self):
        """Should integrate properly with display for sprite drawing."""
        memory = Mock(spec=Memory)
        display = Mock(spec=Display)
        input_ = Mock(spec=Input_)
        
        # Setup sprite data
        sprite_data = [0xF0, 0x90, 0x90, 0x90, 0xF0]  # Font '0'
        memory.read_word.return_value = 0xD125  # Draw at V1,V2, height 5
        memory.read_byte.side_effect = sprite_data
        display.draw_sprite.return_value = False  # No collision
        
        cpu = CPU(memory, display, input_)
        cpu.registers[1] = 10  # x coordinate
        cpu.registers[2] = 15  # y coordinate
        cpu.i = 0x050  # Font location
        
        cpu.cycle()
        
        # Verify memory reads for sprite data
        for i in range(5):
            memory.read_byte.assert_any_call(0x050 + i)
        
        # Verify display call
        display.draw_sprite.assert_called_once_with(10, 15, sprite_data)
        
        # Verify collision flag
        assert cpu.registers[VF_IDX] == 0  # No collision