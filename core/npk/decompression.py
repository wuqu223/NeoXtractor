"""Provides decompression functions."""

import zlib
import lz4.block
import zstandard

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5

from core.npk.enums import CompressionType
from core.npk.types import NPKEntry

def decompress_entry(entry: NPKEntry):
    """
    This function determines the compression type specified in the `zip_flag` attribute
    of the provided `entry` and applies the corresponding decompression algorithm.
    The decompressed data is returned as the output.


    Returns:
        bytes: The decompressed data.


        The decompressed data is returned as a new object and does not modify the original
        `data` attribute of the `entry` object.
    """

    if entry.zip_flag == CompressionType.ZLIB:
        return zlib.decompress(entry.data, bufsize=entry.file_original_length)

    if entry.zip_flag == CompressionType.LZ4:
        return lz4.block.decompress(entry.data,
                                          uncompressed_size=entry.file_original_length)

    if entry.zip_flag == CompressionType.ZSTANDARD:
        return zstandard.ZstdDecompressor().decompress(entry.data)

    # No matched compression.
    return entry.data

def check_nxs3(entry: NPKEntry) -> bool:
    """Check if the data is wrapped in NXS3 format."""
    if entry.data[0:8] == b"NXS3\x03\x00\x00\x01":
        return True
    return False

# todo: check if this works
def unpack_nxs3(data):
    """
    Decrypts and unpacks data encrypted with a custom algorithm using an RSA public key.
    This function extracts an encrypted key from the input data, decrypts it using
    an RSA public key, and uses the resulting ephemeral key to decrypt the remaining
    data. The decryption process involves XOR operations and bitwise manipulations.
    Args:
        data (bytes): The input data to be decrypted. The data must contain an
                      encrypted key starting at offset 20, followed by the encrypted payload.
    Returns:
        bytes: The decrypted data.
    Raises:
        ValueError: If the decryption of the encrypted key fails.
    """

    # Parse the RSA public key
    pem_key = """-----BEGIN RSA PUBLIC KEY-----
MIGJAoGBAOZAaZe2qB7dpT9Y8WfZIdDv+ooS1HsFEDW2hFnnvcuFJ4vIuPgKhISm
pY4/jT3aipwPNVTjM6yHbzOLhrnGJh7Ec3CQG/FZu6VKoCqVEtCeh15hjcu6QYtn
YWIEf8qgkylqsOQ3IIn76udV6m0AWC2jDlmLeRcR04w9NNw7+9t9AgMBAAE=
-----END RSA PUBLIC KEY-----"""

    key = RSA.import_key(pem_key)

    # Extract the encrypted data (starts at offset 20)
    encrypted_key_data = data[20:20+128]

    # Create a cipher object for decryption
    cipher = PKCS1_v1_5.new(key)

    # Decrypt the signature
    wrapped_key = cipher.decrypt(encrypted_key_data, None)

    if wrapped_key is None:
        raise ValueError("Decryption of the encrypted key failed.")

    # We only need the first 4 bytes
    wrapped_key = wrapped_key[:4]

    # Convert to int
    ephemeral_key = int.from_bytes(wrapped_key, "little")

    # Continue with the existing decryption logic
    decrypted = []

    for i, x in enumerate(data[20 + 128:]):
        val = x ^ ((ephemeral_key >> (i % 4 * 8)) & 0xff)
        if i % 4 == 3:
            ror = (ephemeral_key >> 19) | ((ephemeral_key << (32 - 19)) & 0xFFFFFFFF)
            ephemeral_key = (ror + ((ror << 2) & 0xFFFFFFFF) + 0xE6546B64) & 0xFFFFFFFF
        decrypted.append(val)

    decrypted = bytes(decrypted)
    return decrypted
