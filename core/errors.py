class UnsupportedOpcodeError(ValueError):
    pass

class MemoryOutOfBoundsError(IndexError):
    pass

class ByteOverflowError(ValueError):
    """Raised when a value exceeds the size of a byte (255)."""
    pass