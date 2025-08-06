from typing import List

class Display:
    screen: List[List[bool]]
    
    def __init__(self):
        self.screen = [[False] * 64 for _ in range(32)]

    def clear_screen(self):
        self.screen = [[False] * 64 for _ in range(32)]

    def draw_sprite(self, x0: int, y0: int, byte_array: List[int]) -> bool:
        collided = False
        for i in range(len(byte_array)):
            for j in range(len(bytes_str := format(byte_array[i], "08b"))):
                x = (x0 + j) % 64
                y = (y0 + i) % 32
                if self.screen[y][x] and bytes_str[j]:
                    collided = True
                self.screen[y][x] ^= True if bytes_str[j] == "1" else False

        return collided
    
    def refresh(self):
        print("\033[2J\033[H", end="")
        for i in self.screen:
            for j in i:
                if j:
                    print("██", end="")
                else:
                    print("  ", end="")
            print()
    
    
