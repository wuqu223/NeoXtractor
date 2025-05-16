"""NPK File Reader"""

# todo: modularize this file

import io
import os
import struct
from typing import Optional, List, Dict

import zlib
import lz4.block
import zstandard
from arc4 import ARC4

from core.npk.enums import NPKFileType

from .detection import get_ext
from .keys import KeyGenerator
from .types import NPKIndex, NPKEntry, CompressionType, DecryptionType

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

# Map info_size values to their appropriate reader functions
INFO_SIZE_MAP = {
    28: read_uint32,  # 32-bit file signature
    30: read_uint32,  # 32-bit file signature
    32: read_uint64,  # 64-bit file signature (NeoX 2.0)
    49: read_uint32,  # 32-bit file signature
    65: read_uint32,  # 32-bit file signature
    78: read_uint32,  # 32-bit file signature
    85: read_uint32,  # 32-bit file signature
    163: read_uint32, # 32-bit file signature
}

class NPKFile:
    """Main class for handling NPK files."""

    def __init__(self, file_path: str):
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
        self.decrypt_key: Optional[int] = None
        self.aes_key: Optional[bytes] = None

        # NXFN file information
        self.nxfn_files = None

        # Key generator for advanced decryption
        self.key_generator = KeyGenerator()

        self._open()

    def _open(self) -> bool:
        """Open an NPK file and read its header information.

        Args:
            file_path: Path to the NPK file

        Returns:
            bool: True if the file was successfully opened
        """
        self.file = open(self.file_path, 'rb')

        # Read NPK header
        magic = self.file.read(4)
        if magic == b'NXPK':
            self.file_type = NPKFileType.NXPK
        elif magic == b'EXPK':
            self.file_type = NPKFileType.EXPK
        else:
            self.file.close()
            raise ValueError(f"Not a valid NPK file: {self.file_path}")

        # Read basic header info
        self.file_count = read_uint32(self.file)
        _var1 = read_uint32(self.file)  # Unknown variable
        self.encrypt_mode = read_uint32(self.file)
        self.hash_mode = read_uint32(self.file)
        self.index_offset = read_uint32(self.file)

        # Determine index entry size
        self.info_size = self._determine_info_size()

        if self.hash_mode == 2:
            print("HASHING MODE 2 DETECTED, COMPATIBILITY IS NOT GURANTEED")
        elif self.hash_mode == 3:
            self.arc_key = ARC4(b'61ea476e-8201-11e5-864b-fcaa147137b7')
        elif self.encrypt_mode == 256:
            self.file.seek(self.index_offset + (self.file_count * self.info_size) + 16)
            self.nxfn_files = [x for x in (self.file.read()).split(b'\x00') if x != b'']

        # Read the indices but don't load data yet
        self._read_indices()

        return True

    def close(self) -> None:
        """Close the NPK file."""
        self.file.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _determine_info_size(self) -> int:
        """Determine the size of each index entry."""
        if self.encrypt_mode == 256:
            return 0x1C  # 28 bytes

        current_pos = self.file.tell()
        self.file.seek(self.index_offset)
        buf = self.file.read()
        self.file.seek(current_pos)

        # The total size of the index divided by number of files gives us the entry size
        return len(buf) // self.file_count

    def _read_indices(self) -> None:
        """Read all the index entries from the NPK file."""
        self.indices = []

        self.file.seek(self.index_offset)
        index_data = self.file.read(self.file_count * self.info_size)

        if self.file_type == NPKFileType.EXPK:
            index_data = self.key_generator.decrypt(index_data)
        if self.hash_mode == 3:
            index_data = self.arc_key.decrypt(index_data)

        with io.BytesIO(index_data) as buf:
            for i in range(self.file_count):
                index = NPKIndex()

                # Read file signature (depends on info_size)
                if self.info_size in INFO_SIZE_MAP:
                    index.file_sign = INFO_SIZE_MAP[self.info_size](buf)
                else:
                    index.file_sign = buf.seek(4)     # Temporary fix

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

                print(index.zip_flag, index.encrypt_flag)

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

        # Load the actual data
        self._load_entry_data(entry)

        # Generate a default filename if not set
        if not entry.filename:
            entry.filename = f"file_{index}{entry.extension}"

        # Store in the cache
        self.entries[index] = entry
        return entry

    def _load_entry_data(self, entry: NPKEntry) -> None:
        """Load the data for an entry from the NPK file."""
        # Position file pointer to the file data
        self.file.seek(entry.file_offset)

        # Read the file data
        entry.data = self.file.read(entry.file_length)

        print(entry.file_length, entry.file_original_length)

        # Decrypt EXPK data if needed
        if self.file_type == NPKFileType.EXPK:
            entry.data = self.key_generator.decrypt(entry.data)

        # Decrypt if needed
        if entry.encrypt_flag != DecryptionType.NONE:
            self._decrypt_entry(entry)

        # Decompress if needed
        if entry.zip_flag != CompressionType.NONE:
            self._decompress_entry(entry)

        # todo: special decompression

        # Detect file extension if not already set
        if not entry.extension:
            entry.extension = self._detect_file_extension(entry.data)

    def _decrypt_entry(self, entry: NPKEntry) -> None:
        """Decrypt an NPK entry."""
        # Convert data to bytearray for in-place modifications
        entry.data = bytearray(entry.data)

        if entry.encrypt_flag == DecryptionType.BASIC_XOR:  # Basic XOR
            if self.decrypt_key is None:
                raise ValueError("Decryption key is required for this file")

            size = entry.file_length
            if size > 0x80:
                size = 0x80

            # Generate key array
            key_array = [(self.decrypt_key + x) & 0xFF for x in range(0, 0x100)]

            # Apply XOR decryption
            for j in range(size):
                entry.data[j] ^= key_array[j % 0xff]

        elif entry.encrypt_flag == DecryptionType.ADVANCED_XOR:  # Advanced XOR variants
            b = entry.crc ^ entry.file_original_length

            start = 0
            size = entry.file_length

            if size > 0x80:
                start = (entry.crc >> 1) % (size - 0x80)
                size = 2 * entry.file_original_length % 0x60 + 0x20

            # Generate key array
            key_array = [(x + b) & 0xFF for x in range(0, 0x81)]

            # Apply XOR decryption
            for j in range(size):
                entry.data[start + j] ^= key_array[j % 0x80]

        elif entry.encrypt_flag == DecryptionType.INCREMENTAL_XOR:  # Incremental XOR
            v3 = int(entry.file_original_length)
            v4 = int(entry.crc)

            crc_key = (v3 ^ v4) & 0xff
            offset = 0
            length = 0

            if entry.file_length <= 0x80:
                length = entry.file_length
            else:
                offset = (v3 >> 1) % (entry.file_length - 0x80)
                length = ((v4 << 1) & 0xffffffff) % 0x60 + 0x20

            # Apply incremental XOR decryption
            for xx in range(offset, offset + length):
                entry.data[xx] ^= crc_key
                crc_key = (crc_key + 1) & 0xff

        # Convert back to bytes
        entry.data = bytes(entry.data)

    def _decompress_entry(self, entry: NPKEntry) -> None:
        """Decompress an NPK entry."""

        if entry.zip_flag == CompressionType.ZLIB:
            entry.data = zlib.decompress(entry.data, bufsize=entry.file_original_length)
        elif entry.zip_flag == CompressionType.LZ4:
            entry.data = lz4.block.decompress(entry.data,
                                              uncompressed_size=entry.file_original_length)
        elif entry.zip_flag == CompressionType.ZSTANDARD:
            entry.data = zstandard.ZstdDecompressor().decompress(entry.data)

    def extract_all(self, output_dir: str, use_subfolders: bool = True) -> List[str]:
        """Extract all files from the NPK archive.

        Args:
            output_dir: Directory where files will be extracted
            use_subfolders: If True, create subfolders based on NPK filename

        Returns:
            List[str]: List of extracted file paths
        """
        os.makedirs(output_dir, exist_ok=True)

        extracted_files = []
        npk_name = os.path.splitext(os.path.basename(self.file_path))[0]

        for i in range(self.file_count):
            entry = self.get_entry(i)

            # Determine the output path
            if use_subfolders:
                out_path = os.path.join(output_dir, npk_name, entry.filename)
            else:
                out_path = os.path.join(output_dir, entry.filename)

            # Save the file
            entry.save_to_file(out_path)
            extracted_files.append(out_path)

        return extracted_files

    def _detect_file_extension(self, data: bytes) -> str:
        """Attempt to detect the file type and return an appropriate extension.

        Uses the original detection logic from the project.
        """
        ext = get_ext(data)
        return f".{ext}"
