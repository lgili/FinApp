"""
UUID ↔ Integer ID conversion helpers for SQLite compatibility.

SQLite uses Integer IDs while the domain uses UUIDs.
These helpers provide consistent conversion between the two formats.
"""

from uuid import UUID


def uuid_to_int(uuid: UUID) -> int:
    """
    Convert UUID to Integer ID for database storage.
    
    Uses the first 4 bytes of the UUID to generate a unique integer.
    This keeps the value within SQLite INTEGER range (64-bit signed).
    
    Args:
        uuid: UUID to convert
        
    Returns:
        Integer ID (max 2^32 = 4,294,967,296)
    """
    # Take first 4 bytes and convert to integer
    return int.from_bytes(uuid.bytes[:4], byteorder='big', signed=False)


def int_to_uuid(id: int) -> UUID:
    """
    Convert Integer ID back to UUID.
    
    Pads the integer to 16 bytes to create a valid UUID.
    Note: This generates a consistent UUID for the same integer ID,
    but cannot recover the original UUID if it was truncated.
    
    Args:
        id: Integer ID to convert
        
    Returns:
        UUID representation
    """
    # Convert int to 4 bytes, pad with zeros to make 16 bytes
    int_bytes = id.to_bytes(4, byteorder='big', signed=False)
    padded_bytes = int_bytes + b'\x00' * 12
    return UUID(bytes=padded_bytes)
