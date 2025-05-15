import io, os, struct
from typing import Literal, cast
from decompression import zflag_decompress, special_decompress
from decryption import file_decrypt
from detection import get_ext, get_compression
from key import Keys
from arc4 import ARC4

from utils.config_manager import ConfigManager

#data readers
def readuint64(f):
    return struct.unpack('Q', f.read(8))[0]
def readuint32(f):
    return struct.unpack('I', f.read(4))[0]
def readuint16(f):
    return struct.unpack('H', f.read(2))[0]
def readuint8(f):
    return struct.unpack('B', f.read(1))[0]

# Map info_size values to their appropriate reader functions
INFO_SIZE_MAP = {
    28: readuint32,  # 32-bit file signature
    30: readuint32,  # 32-bit file signature
    32: readuint64,  # 64-bit file signature (NeoX 2.0)
    49: readuint32,  # 32-bit file signature
    65: readuint32,  # 32-bit file signature
    78: readuint32,  # 32-bit file signature
    85: readuint32,  # 32-bit file signature
    163: readuint32, # 32-bit file signature
}

class NPKEntry:
    ext: str | None = None
    special_decompress: Literal["nxs3"] | None = None
    data: bytes = bytes()
    filename = None
    has_ext = False
    
    def __init__(self, data):
        self.file_sign = data[0]         # Unique file signature/hash
        self.file_offset = data[1]       # File data offset in NPK
        self.file_length = data[2]       # Compressed size
        self.file_original_length = data[3] # Decompressed/original size
        self.zcrc = data[4]              # Compressed CRC
        self.crc = data[5]               # Decompressed CRC
        self.file_structure = cast(bytes, data[6])    # File path in archive (if available)
        self.zflag = data[7]             # Compression flag
        self.fileflag = data[8]          # File flag/type

class NPKFile:
    path = ""
    pkg_type = 0
    files = 0
    var1 = 0
    encryption_mode = 0
    hash_mode = 0
    index_offset = 0
    index_size = 0
    index_table = []
    nxfn_files = []
    
    _npk_entries: dict[int, NPKEntry] = {}
    
    def __init__(self, filepath: str, config: ConfigManager):
        self.path = filepath
        self.file = io.BytesIO(open(filepath, 'rb').read())
        
        data = self.file.read(4)
        if data == b'NXPK':
            self.pkg_type = 0
        elif data == b'EXPK':
            self.decryption_key = config.get("decryption_key")
            self.pkg_type = 1
        else:
            raise Exception('NOT NXPK/EXPK FILE')
        
    def clear(self):
        self.index_table.clear()
        self.nxfn_files.clear()
        self._npk_entries.clear()

    #determines the info size by basic math (from the start of the index pointer // EOF or until NXFN data 
    def determine_info_size(self):
        if self.encryption_mode == 256:
            return 0x1C
        indexbuf = self.file.tell()
        buf = self.file.seek(0, os.SEEK_END)
        self.file.seek(indexbuf)
        return (buf - self.index_offset) // self.files

    def read_index(self):
        self.expkkeys = Keys()
        print(f"READING INDEX FROM NPK: {self.path}")

        print("FILE TYPE: {}".format("NXPK" if self.pkg_type == 0 else "EXPK"))
        #amount of files
        self.files = readuint32(self.file)
        if self.files == 0:
            print(f"\nTHIS NPK ({self.path}) IS EMPTY\n")
            return None
            
        self.var1 = readuint32(self.file)
        print(f"UNKNOWN: {self.var1}")
        self.encryption_mode = readuint32(self.file)
        print(f"ENCRYPTMODE: {self.encryption_mode}")
        self.hash_mode = readuint32(self.file)
        print(f"HASHMODE: {self.hash_mode}")
        self.index_offset = readuint32(self.file)
        print(f"INDEXOFFSET: {self.index_offset}")
        self.info_size = self.determine_info_size()
        print(f"INFOSIZE: {self.info_size}")
        
        #checks for the "hash mode"
        if self.hash_mode == 2:
            print("HASHING MODE 2 DETECTED, COMPATIBILITY IS NOT GURANTEED")
        elif self.hash_mode == 3:
            self.arc_key = ARC4(b'61ea476e-8201-11e5-864b-fcaa147137b7')
        
        elif self.encryption_mode == 256:
            self.file.seek(self.index_offset + (self.files * self.info_size) + 16)
            self.nxfn_files = [x for x in (self.file.read()).split(b'\x00') if x != b'']
            
        
        self.file.seek(self.index_offset)
        
        data = self.file.read(self.files * self.info_size)
        
        if self.pkg_type:
            data = self.expkkeys.decrypt(data)
        if self.hash_mode == 3:
            data = self.arc_key.decrypt(data)
            
        with io.BytesIO(data) as f:
            f.seek(0)

            for x in range(self.files):                # Use the INFO_SIZE_MAP dictionary to get the appropriate reader function
                if self.info_size in INFO_SIZE_MAP:
                    file_sign = INFO_SIZE_MAP[self.info_size](f)
                else:
                    file_sign = f.seek(4)     # Temporary fix
                file_offset = readuint32(f)
                file_length = readuint32(f)
                file_original_length = readuint32(f)
                zcrc = readuint32(f)                #compressed crc
                crc = readuint32(f)                 #decompressed crc
                zip_flag = readuint16(f)
                file_flag = readuint16(f)
                file_structure = self.nxfn_files[x] if self.nxfn_files else None
                
                # Create a tuple with all the parsed data
                entry_data = (
                    file_sign,
                    file_offset, 
                    file_length,
                    file_original_length,
                    zcrc,
                    crc,
                    file_structure,
                    zip_flag,
                    file_flag,
                )
                
                # Add to the index table
                self.index_table.append(entry_data)

        print("READ {} INDEXES".format(self.files))

    def is_entry_valid(self, entry_index):
        return self._npk_entries.get(entry_index) != None
    
    def get_loaded_entries(self):
        return self._npk_entries
        
    def read_entry(self, entry_index):
        cached = self._npk_entries.get(entry_index)
        if cached:
            return cached

        npkentry = NPKEntry(self.index_table[entry_index])
        npkentry.has_ext = bool(npkentry.file_structure)
        
        if npkentry.file_original_length == 0:
            return npkentry
        
        self.file.seek(npkentry.file_offset)
        npkentry.data = self.file.read(npkentry.file_length)
        
        if self.pkg_type:
            npkentry.data = self.expkkeys.decrypt(npkentry.data)
        file_decrypt(npkentry, self.decryption_key)
        zflag_decompress(npkentry)
        npkentry.special_decompress = get_compression(npkentry.data)
        special_decompress(npkentry)
        npkentry.ext = get_ext(npkentry.data)

        self._npk_entries[entry_index] = npkentry
        
        return npkentry

def split_chunks(lst, n):    
    k, m = divmod(len(lst), n)     
    for i in range(n):         
        yield lst[i*k+min(i, m):(i+1)*k+min(i+1, m)]
