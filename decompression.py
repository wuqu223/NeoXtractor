import ctypes, zlib, zstandard, lz4.block, zipfile, os

def decompression_algorithm(zflag=0):
    match zflag:
        case 0:
            return "NONE"
        case 1:
            return "ZLIB"
        case 2:
            return "LZ4"
        case 3:
            return "ZSTANDARD"
        case 5:
            return "ZSTANDARD - NOT WORKING??"
    raise Exception("ERROR IN DECOMPRESSON ALGORITHM")

def init_rotor():
    asdf_dn = 'YkcuvaVgf0i#h'
             #'j2h56ogodh3se' 
    asdf_dt = 'g5/tqoU'
             #'=dziaq.'
    asdf_df = '%Hu"pvd,x36Pb'
             #'|os=5v7!"-234'                                    !     #                                 *     &
    asdf_tm = asdf_dn * 4 + (asdf_dt + asdf_dn + asdf_df) * 5 + '&' + '$' + asdf_dt * 7 + asdf_df * 2 + '@' + '*' + "'"
    import rotor
    rot = rotor.newrotor(asdf_tm)
    return rot
    
def init_rotor_2():
    asdf_dn = 'j2h56ogodh3se'
             #'' 
    asdf_dt = '=dziaq.'
             #''
    asdf_df = '|os=5v7!"-234'
             #''                                                 !     #                                 *     &
    asdf_tm = asdf_dn * 4 + (asdf_dt + asdf_dn + asdf_df) * 5 + '!' + '#' + asdf_dt * 7 + asdf_df * 2 + '*' + '&' + "'"
    import rotor
    rot = rotor.newrotor(asdf_tm)
    return rot

def _reverse_string(s):
    l = list(s)
    l = list(map(lambda x: x ^ 154, l[0:128])) + l[128:]
    l.reverse()
    return bytes(l)

def nxs_unpack(data):
    useless = """
    public_key_pem = '-----BEGIN RSA PUBLIC KEY-----\nMEgCQQCQaKEFJ3g1WM6WL0WHlosmgHZULxMyo2CbGHqHJQ/EWv3GJ1W2MfF9N9U2\n/hOs9k5ANj5DEQte7d3jPHuKvQ8xAgMBAAE=\n-----END RSA PUBLIC KEY-----'
    public_key = None
    import struct
    import hashlib
    import rsa
    import base64
    
    public_key = rsa.PublicKey.load_pkcs1(public_key_pem)
    
    md5_signature = base64.decodebytes(data[20:])
    valid_data = data[20:]
    
    myhash = hashlib.md5()
    myhash.update(valid_data)
    data_md5 = myhash.hexdigest()
    rsa.verify(data_md5.encode(), md5_signature, public_key)"""
    
    input_key = ctypes.create_string_buffer(b"-----BEGIN RSA PUBLIC KEY-----\nMIGJAoGBAOZAaZe2qB7dpT9Y8WfZIdDv+ooS1HsFEDW2hFnnvcuFJ4vIuPgKhISm\npY4/jT3aipwPNVTjM6yHbzOLhrnGJh7Ec3CQG/FZu6VKoCqVEtCeh15hjcu6QYtn\nYWIEf8qgkylqsOQ3IIn76udV6m0AWC2jDlmLeRcR04w9NNw7+9t9AgMBAAE=\n-----END RSA PUBLIC KEY-----\n")
    wrapped_key = ctypes.create_string_buffer(4)
    data_in = ctypes.create_string_buffer(data[20:])

    

    if os.name == "posix":
        liblinux = ctypes.CDLL("./dll/libpubdecrypt.so")
        returning = liblinux.public_decrypt(data_in, input_key, wrapped_key)
    elif os.name == "nt":
        libwindows = ctypes.CDLL("./dll/libpubdecrypt.dll")
        returning = libwindows.public_decrypt(data_in, input_key, wrapped_key)
        
    ephemeral_key = int.from_bytes(wrapped_key.raw, "little")

    decrypted = []

    for i, x in enumerate(data[20 + 128:]):
        val = x ^ ((ephemeral_key >> (i % 4 * 8)) & 0xff)
        if i % 4 == 3:
            ror = (ephemeral_key >> 19) | ((ephemeral_key << (32 - 19)) & 0xFFFFFFFF)
            ephemeral_key = (ror + ((ror << 2) & 0xFFFFFFFF) + 0xE6546B64) & 0xFFFFFFFF
        decrypted.append(val)

    decrypted = bytes(decrypted)
    return decrypted

def zflag_decompress(npkentry):
    match npkentry.zflag:
        case 1:
            npkentry.data = zlib.decompress(npkentry.data, bufsize=npkentry.file_original_length)
        case 2:
            npkentry.data = lz4.block.decompress(npkentry.data,uncompressed_size=npkentry.file_original_length)
        case 3:         
            npkentry.data = zstandard.ZstdDecompressor().decompress(npkentry.data)
        case 5:
            npkentry.data = lz4.block.decompress(npkentry.data,uncompressed_size=npkentry.file_original_length)

def special_decompress(npkentry):
    match npkentry.special_decompress:
        case "rot":
            rotor = init_rotor()
            npkentry.data = _reverse_string(zlib.decompress(rotor.decrypt(npkentry.data)))
            
        case "nxs3":
            buf = nxs_unpack(npkentry.data)
            npkentry.data = lz4.block.decompress(buf, int.from_bytes(npkentry.data[16:20], "little"))
            
    
