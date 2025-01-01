import shutil, io, os, struct, tempfile, argparse, zipfile, time
from PyQt5.QtWidgets import QMessageBox
from decompression import zflag_decompress, special_decompress
from decryption import file_decrypt
from detection import get_ext, get_compression
from key import Keys
from math import ceil
from concurrent.futures import ProcessPoolExecutor

class npkfile:
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
    
    def __init__(self, filepath):
        self.path = filepath
        
    def clear(self):
        self.index_table.clear()
        self.nxfn_files.clear()
        
    
class npkfile_entry:
    ext = None
    special_decompress = None
    data = None
    has_ext = lambda ext: (type(ext) != None)
    
    def __init__(self, data):
        self.file_sign, self.file_offset, self.file_length, self.file_original_length, self.zcrc, self.crc, self.file_structure, self.zflag, self.fileflag = data

#determines the info size by basic math (from the start of the index pointer // EOF or until NXFN data 
def determine_info_size(self):
    if self.npk.encryption_mode == 256:
        return 0x1C
    indexbuf = self.npk_file.tell()
    buf = self.npk_file.seek(0, os.SEEK_END)
    self.npk_file.seek(indexbuf)
    return (buf - self.npk.index_offset) // self.npk.files

def split_chunks(lst, n):     
    k, m = divmod(len(lst), n)     
    for i in range(n):         
        yield lst[i*k+min(i, m):(i+1)*k+min(i+1, m)]

#reads an entry of the NPK index, if its 28 the file sign is 32 bits and if its 32 its 64 bits (NeoX 1.2 / 2 shienanigans)
def read_index_item(self, f, x):
    if self.npk.info_size == 28:
        file_sign = readuint32(f)
    elif self.npk.info_size == 32:
        file_sign = readuint64(f)
    else:
        file_sign = f.seek(4)     # Tempary fix 

    file_offset = readuint32(f)
    file_length = readuint32(f)
    file_original_length = readuint32(f)
    zcrc = readuint32(f)                #compressed crc
    crc = readuint32(f)                 #decompressed crc
    zip_flag = readuint16(f)
    file_flag = readuint16(f)
    file_structure = self.npk.nxfn_files[x] if self.npk.nxfn_files else None
    return (
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

#data readers
def readuint64(f):
    return struct.unpack('Q', f.read(8))[0]
def readuint32(f):
    return struct.unpack('I', f.read(4))[0]
def readuint16(f):
    return struct.unpack('H', f.read(2))[0]
def readuint8(f):
    return struct.unpack('B', f.read(1))[0]

def read_index(self, file_path):
    self.expkkeys = Keys()
    self.npk = npkfile(file_path)
    print(f"READING INDEX FROM NPK: {file_path}")

    data = self.npk_file.read(4)
    if data == b'NXPK':
        self.npk.pkg_type = 0
    elif data == b'EXPK':
        checked = QMessageBox.question(self, "Check Decryption Key!", "Your decryption key is {}, program may fail if the key is wrong!\nAre you sure you want to continue?".format(self.decryption_key))
        if checked == QMessageBox.No:
            return -1
        self.npk.pkg_type = 1
    else:
        raise Exception('NOT NXPK/EXPK FILE')
    print("FILE TYPE: {}".format(data.decode("utf-8")))
    #amount of files
    self.npk.files = readuint32(self.npk_file)
    if self.npk.files == 0:
        print(f"\nTHIS NPK ({file_path}) IS EMPTY\n")
        return None
        
    self.npk.var1 = readuint32(self.npk_file)
    print(f"UNKNOWN: {self.npk.var1}")
    self.npk.encryption_mode = readuint32(self.npk_file)
    print(f"ENCRYPTMODE: {self.npk.encryption_mode}")
    self.npk.hash_mode = readuint32(self.npk_file)
    print(f"HASHMODE: {self.npk.hash_mode}")
    self.npk.index_offset = readuint32(self.npk_file)
    print(f"INDEXOFFSET: {self.npk.index_offset}")
    self.npk.info_size = determine_info_size(self)
    
    #checks for the "hash mode"
    if self.npk.hash_mode == 2:
        print("HASHING MODE 2 DETECTED, COMPATIBILITY IS NOT GURANTEED")
    elif self.npk.hash_mode == 3:
        print("HASHING MODE 3 IS CURRENTLY NOT SUPPORTED!! EXPECT ERRORS!! PLEASE REPORT THEM IN GITHUB")
    
    elif self.npk.encryption_mode == 256:
        self.npk_file.seek(self.npk.index_offset + (self.npk.files * self.npk.info_size) + 16)
        self.npk.nxfn_files = [x for x in (self.npk_file.read()).split(b'\x00') if x != b'']
        
    
    self.npk_file.seek(self.npk.index_offset)
    
    data = self.npk_file.read(self.npk.files * self.npk.info_size)
    
    if self.npk.pkg_type:
        data = self.expkkeys.decrypt(data)
    with io.BytesIO(data) as f:
        f.seek(0)

        for x in range(self.npk.files):
            self.npk.index_table.append(read_index_item(self, f, x))

    #prints the end time
    print("READ {} INDEXES".format(self.npk.files))

def read_entry(self, fileindex):
    npkentry = npkfile_entry(self.npk.index_table[fileindex])
    npkentry.has_ext = bool(npkentry.file_structure)
    
    if npkentry.file_original_length == 0:
        return npkentry
    
    self.npk_file.seek(npkentry.file_offset)
    npkentry.data = self.npk_file.read(npkentry.file_length)
    
    if self.npk.pkg_type:
        npkentry.data = self.expkkeys.decrypt(npkentry.data)
    file_decrypt(npkentry, self.decryption_key)
    zflag_decompress(npkentry)
    npkentry.special_decompress = get_compression(npkentry.data)
    special_decompress(npkentry)
    
    npkentry.ext = get_ext(npkentry.data)
    
    return npkentry
    
