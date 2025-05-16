"""NPK File Reader"""

import io
import struct
from typing import Optional, List, Dict

from arc4 import ARC4

from core.npk.decompression import check_nxs3, decompress_entry, unpack_nxs3
from core.npk.decryption import decrypt_entry
from core.npk.enums import NPKFileType

from .detection import get_ext
from .keys import KeyGenerator
from .types import NPKEntryDataFlags, NPKIndex, NPKEntry, CompressionType, DecryptionType

# Data readers
def read_uint64(f):
    """Extract unsigned 64-bit integer from binary stream."""
    return struct.unpack('Q', f.read(8))[0]
def read_uint32(f):
    """Extract unsigned 32-bit integer from binary stream."""
    return struct.unpack('I', f.read(4))[0]
def read_uint16(f):
    """Extract unsigned 16-bit integer from binary stream."""
    return struct.unpack('H', f.read(2))[0]
def read_uint8(f):
    """Extract unsigned 8-bit integer from binary stream."""
    return struct.unpack('B', f.read(1))[0]

class NPKFile:
    """Main class for handling NPK files."""

    def __init__(self, file_path: str, decrypt_key: Optional[int] = None):
        """Initialize the NPK file handler.

        Args:
            file_path: Optional path to an NPK file to open
        """
        self.file_path = file_path
        self.entries: Dict[int, NPKEntry] = {}
        self.indices: List[NPKIndex] = []

        # NPK header information
        self.file_count: int = 0
        self.index_offset: int = 0
        self.hash_mode: int = 0
        self.encrypt_mode: int = 0
        self.info_size: int = 0

        # Optional parameters
        self.decrypt_key: Optional[int] = decrypt_key
        self.aes_key: Optional[bytes] = None

        # NXFN file information
        self.nxfn_files = None

        # Key generator for advanced decryption
        self.key_generator = KeyGenerator()

        with open(self.file_path, 'rb') as file:
            # Read NPK header.
            self._read_header(file)

            # Read the indices but don't load data yet
            self._read_indices(file)

    def _read_header(self, file: io.BufferedReader) -> bool:
        """Open an NPK file and read its header information.

        Args:
            file_path: Path to the NPK file

        Returns:
            bool: True if the file was successfully opened
        """

        # Read NPK header
        magic = file.read(4)
        if magic == b'NXPK':
            self.file_type = NPKFileType.NXPK
        elif magic == b'EXPK':
            self.file_type = NPKFileType.EXPK
        else:
            file.close()
            raise ValueError(f"Not a valid NPK file: {self.file_path}")

        # Read basic header info
        self.file_count = read_uint32(file)
        _var1 = read_uint32(file)  # Unknown variable
        self.encrypt_mode = read_uint32(file)
        self.hash_mode = read_uint32(file)
        self.index_offset = read_uint32(file)

        # Determine index entry size
        self.info_size = self._determine_info_size(file)

        if self.hash_mode == 2:
            print("HASHING MODE 2 DETECTED, COMPATIBILITY IS NOT GURANTEED")
        elif self.hash_mode == 3:
            self.arc_key = ARC4(b'61ea476e-8201-11e5-864b-fcaa147137b7')
        elif self.encrypt_mode == 256:
            file.seek(self.index_offset + (self.file_count * self.info_size) + 16)
            self.nxfn_files = [x for x in (file.read()).split(b'\x00') if x != b'']

        return True

    def __enter__(self):
        return self

    def _determine_info_size(self, file: io.BufferedReader) -> int:
        """Determine the size of each index entry."""
        if self.encrypt_mode == 256:
            return 0x1C  # 28 bytes

        current_pos = file.tell()
        file.seek(self.index_offset)
        buf = file.read()
        file.seek(current_pos)

        # The total size of the index divided by number of files gives us the entry size
        return len(buf) // self.file_count

    def _read_indices(self, file: io.BufferedReader) -> None:
        """Read all the index entries from the NPK file."""
        self.indices = []

        file.seek(self.index_offset)
        index_data = file.read(self.file_count * self.info_size)

        if self.file_type == NPKFileType.EXPK:
            index_data = self.key_generator.decrypt(index_data)
        if self.hash_mode == 3:
            index_data = self.arc_key.decrypt(index_data)

        with io.BytesIO(index_data) as buf:
            for i in range(self.file_count):
                index = NPKIndex()

                # Read the file signature
                if self.info_size == 28:
                    # 32-bit file signature
                    index.file_signature = read_uint32(buf)
                elif self.info_size == 32:
                    # 64-bit file signature (NeoX 2.0)
                    index.file_signature = read_uint64(buf)

                # Read the rest of the index entry
                index.file_offset = read_uint32(buf)
                index.file_length = read_uint32(buf)
                index.file_original_length = read_uint32(buf)
                index.zcrc = read_uint32(buf)
                index.crc = read_uint32(buf)

                zip_flag = read_uint16(buf)
                if zip_flag == 5:
                    # Still LZ4
                    zip_flag = 2
                index.zip_flag = CompressionType(zip_flag)

                encrypt_flag = read_uint16(buf)
                if encrypt_flag == 3:
                    # Still Advanced XOR
                    encrypt_flag = 2

                index.encrypt_flag = DecryptionType(encrypt_flag)

                # Store file structure name if available
                index.file_structure = self.nxfn_files[i] if self.nxfn_files else None

                self.indices.append(index)

    def get_entry_count(self) -> int:
        """Get the number of entries in the NPK file."""
        return self.file_count

    def get_entry(self, index: int) -> NPKEntry:
        """Get an entry by its index.

        If the entry has been loaded before, returns the cached entry.
        Otherwise, loads the entry from the NPK file.

        Args:
            index: The index of the entry to load

        Returns:
            NPKEntry: The loaded entry
        """
        if index in self.entries:
            return self.entries[index]

        if not 0 <= index < len(self.indices):
            raise IndexError(f"Entry index out of range: {index}")

        # Create a new entry based on the index
        entry = NPKEntry()
        idx = self.indices[index]

        # Copy index attributes to entry
        for attr in vars(idx):
            setattr(entry, attr, getattr(idx, attr))

        with open(self.file_path, 'rb') as file:
            # Load the actual data
            self._load_entry_data(entry, file)

        # Generate a filename
        entry.filename = f"{entry.file_structure.decode("utf-8")
                            if entry.file_structure else hex(entry.file_signature)}.{entry.extension}"

        # Store in the cache
        self.entries[index] = entry
        return entry

    def _load_entry_data(self, entry: NPKEntry, file: io.BufferedReader) -> None:
        """Load the data for an entry from the NPK file."""
        # Position file pointer to the file data
        file.seek(entry.file_offset)

        # Read the file data
        entry.data = file.read(entry.file_length)

        # Decrypt EXPK data if needed
        if self.file_type == NPKFileType.EXPK:
            entry.data = self.key_generator.decrypt(entry.data)

        # Decrypt if needed
        if entry.encrypt_flag != DecryptionType.NONE:
            entry.data = decrypt_entry(entry, self.decrypt_key)

        # Decompress if needed
        if entry.zip_flag != CompressionType.NONE:
            entry.data = decompress_entry(entry)

        # Check for NXS3 wrapping
        if check_nxs3(entry):
            entry.data_flags |= NPKEntryDataFlags.NXS3_PACKED
            entry.data = unpack_nxs3(entry.data)

        # Detect file extension if not already set
        if not entry.extension:
            entry.extension = get_ext(entry.data)
