#!/usr/bin/env python3
"""
CHIP-8 Emulator Main Entry Point

Usage:
    python main.py <game_name>
    
Example:
    python main.py PONG
    python main.py TETRIS
"""

import argparse
import sys
import os
from pathlib import Path

from core.emulator import Emulator


def validate_game_file(game_name: str) -> bool:
    """Check if the game file exists in the roms directory."""
    roms_dir = Path("roms")
    game_path = roms_dir / game_name.upper()
    
    if not roms_dir.exists():
        print(f"Error: 'roms' directory not found.")
        return False
    
    if not game_path.exists():
        print(f"Error: Game '{game_name}' not found in roms directory.")
        print(f"Looking for: {game_path}")
        
        # List available games
        if roms_dir.is_dir():
            rom_files = [f.name for f in roms_dir.iterdir() if f.is_file()]
            if rom_files:
                print(f"Available games: {', '.join(rom_files)}")
        
        return False
    
    return True


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="CHIP-8 Emulator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py PONG
  python main.py TETRIS
  python main.py INVADERS
        """
    )
    
    parser.add_argument(
        "game",
        help="Name of the game ROM to load (without path or extension)"
    )
    
    return parser.parse_args()


def main():
    """Main entry point for the CHIP-8 emulator."""
    try:
        # Parse command line arguments
        args = parse_arguments()
        
        # Validate game file exists
        if not validate_game_file(args.game):
            sys.exit(1)
        
        print(f"Loading game: {args.game}")
        print("Press Ctrl+C to quit")
        print()
        
        # Create and start emulator
        emulator = Emulator(game=args.game)
        emulator.emulate()
        
    except KeyboardInterrupt:
        print("\nEmulator stopped by user.")
        sys.exit(0)
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
        
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()