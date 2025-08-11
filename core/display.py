import os
import sys

from typing import List

class Display:
    """
    CHIP-8 Display Handler
    
    Manages a 64x32 monochrome display with XOR pixel drawing logic.
    Provides terminal-based rendering using ANSI escape sequences for 
    real-time emulation output.
    
    Attributes:
        screen: Current 64x32 pixel state (True = on, False = off)
        prev_screen: Previous frame state for differential rendering
    """
    screen: List[List[bool]]
    prev_screen: List[List[bool]]
    
    def __init__(self):
        """
        Initialize display with blank 64x32 screen and enable ANSI colors.
        
        Sets up screen buffers, enables ANSI escape sequences on Windows,
        and clears the terminal for rendering.
        """
        self.screen = [[False] * 64 for _ in range(32)]
        self.prev_screen = [[False] * 64 for _ in range(32)]
        if sys.platform == "win32":
            os.system('')
        print("\033[2J\033[H", end="")

    def clear_screen(self):
        """
        Clear all pixels on the display.
        
        Sets all pixels to False (off state). Used by the CLS instruction (00E0).
        """
        self.screen = [[False] * 64 for _ in range(32)]

    def draw_sprite(self, x0: int, y0: int, byte_array: List[int]) -> bool:
        """
        Draw sprite at specified coordinates using XOR logic.
        
        Args:
            x0: Starting X coordinate (wraps at 64)
            y0: Starting Y coordinate (wraps at 32) 
            byte_array: Sprite data as list of bytes (each byte = 8 pixels wide)
            
        Returns:
            bool: True if any pixels were erased (collision detected), False otherwise
            
        Note:
            Uses XOR logic: existing pixels are flipped when sprite pixels are 1.
            Coordinates wrap around screen edges automatically.
        """
        collided = False
        for i in range(len(byte_array)):
            for j in range(len(bytes_str := format(byte_array[i], "08b"))):
                x = (x0 + j) % 64
                y = (y0 + i) % 32
                if self.screen[y][x] and int(bytes_str[j]):
                    collided = True
                self.screen[y][x] ^= True if bytes_str[j] == "1" else False

        return collided
    
    def refresh(self):
        """
        Update terminal display with changed pixels only.
        
        Performs differential rendering by comparing current screen with 
        previous frame. Only redraws pixels that changed state, improving
        performance. Updates prev_screen to match current state.
        """
        for i in range(len(self.screen)):
            for j in range(len(self.screen[0])):
                if self.screen[i][j] != self.prev_screen[i][j]:
                    print(f"\033[{i+1};{j*2+1}H", end="")
                    if self.screen[i][j]:
                        print("██", end="")
                    else:
                        print("  ", end="")
        self.prev_screen = [row[:] for row in self.screen]
        print("", end="", flush=True)
    
    
