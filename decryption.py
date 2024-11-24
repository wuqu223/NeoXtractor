#does the decryption algorithm
def file_decrypt(npkentry, key):
    npkentry.data = bytearray(npkentry.data)
    match npkentry.fileflag:
        case 1:
            if key == None:
                Exception("KEY FOR FILEFLAG 1 NOT SPECIFIED (check keys.txt)")

            size = npkentry.file_length

            if size > 0x80:
                size = 0x80

            usingkey = [(key + x) & 0xFF for x in range(0, 0x100)]
            #these keys are for different games, check the "keys.txt" file for more information
            #key1: 150 + x   (Onmyoji, Onmyoji RPG)
            #key2:  -250 + x (HPMA)
            for j in range(size):
                npkentry.data[j] = npkentry.data[j] ^ usingkey[j % 0xff]
            
            
        case 2:
            b = npkentry.crc ^ npkentry.file_original_length

            start = 0
            size = npkentry.file_length

            if size > 0x80:
                start = (npkentry.crc >> 1) % (size - 0x80)
                size = 2 * npkentry.file_original_length % 0x60 + 0x20

            usingkey = [(x + b) & 0xFF for x in range(0, 0x81, 1)]
            for j in range(size):
                npkentry.data[start + j] = npkentry.data[start + j] ^ usingkey[j % 0x80]
        case 3:
            b = npkentry.crc ^ npkentry.file_original_length

            start = 0
            size = npkentry.file_length
            if size > 0x80:
                start = (npkentry.crc >> 1) % (size - 0x80)
                size = 2 * npkentry.file_original_length % 0x60 + 0x20
            
            key = [(x + b) & 0xFF for x in range(0, 0x81, 1)]
            for j in range(size):
                npkentry.data[start + j] = npkentry.data[start + j] ^ key[j % 0x80]
        case 4:
            v3 = int(npkentry.file_original_length)
            v4 = int(npkentry.crc)

            crckey = (v3 ^ v4) & 0xff
            offset = 0
            length = 0

            if npkentry.file_length <= 0x80:
                length = npkentry.file_length
            elif npkentry.file_length > 0x80:
                offset = (v3 >> 1) % (npkentry.file_length - 0x80)
                length = (((v4 << 1) & 0xffffffff) % 0x60 + 0x20)

            for xx in range(offset, offset + length, 1):
                npkentry.data[xx] ^= crckey
                crckey = (crckey + 1) & 0xff
    npkentry.data = bytes(npkentry.data)
