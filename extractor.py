import shutil
import os, struct, tempfile, argparse, zipfile
import time
from decompression import zflag_decompress, special_decompress, decompression_algorithm
from decryption import file_decrypt, decryption_algorithm
from detection import get_ext, get_compression
from key import Keys
from timeit import default_timer as timer

#determines the info size by basic math (from the start of the index pointer // EOF or until NXFN data 
def determine_info_size(f, var1, hashmode, encryptmode, index_offset, files):
    if encryptmode == 256 or hashmode == 2:
        return 0x1C
    indexbuf = f.tell()
    f.seek(index_offset)
    buf = f.read()
    f.seek(indexbuf)
    return len(buf) // files

#reads an entry of the NPK index, if its 28 the file sign is 32 bits and if its 32 its 64 bits (NeoX 1.2 / 2 shienanigans)
def read_index(f, info_size, x, nxfn_files, index_offset):
    if info_size == 28:
        file_sign = [readuint32(f), f.tell() + index_offset]
    elif info_size == 32:
        file_sign = [readuint64(f), f.tell() + index_offset]
    file_offset = readuint32(f)
    file_length = readuint32(f)
    file_original_length = readuint32(f)
    zcrc = readuint32(f)                #compressed crc
    crc = readuint32(f)                 #decompressed crc
    zip_flag = readuint16(f)
    file_flag = readuint16(f)
    file_structure = nxfn_files[x] if nxfn_files else None
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

#formatted way to print data
def print_data(verblevel, minimumlevel, text, data, typeofdata, pointer=0):
    pointer = hex(pointer)
    match verblevel:
        case 1:
            if verblevel >= minimumlevel:
                print("{} {}".format(text, data))
        case 2:
            if verblevel >= minimumlevel:
                print("{} {}".format(text, data))
        case 3:
            if verblevel >= minimumlevel:
                print("{:10} {} {}".format(pointer, text, data))
        case 4:
            if verblevel >= minimumlevel:
                print("{:10} {} {}".format(pointer, text, data))
        case 5:
            if verblevel >= minimumlevel:
                print("{:10} {} {}   DATA TYPE:{}".format(pointer, text, data, typeofdata))

#main code
def unpack(args, statusBar=None):
    # Use specified output folder if provided, otherwise, create a folder based on the file name
    output_folder = args.output if args.output else os.path.splitext(args.path)[0]
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    allfiles = []
    if args.selectfile:
        args.selectfile = args.selectfile - 1
    if args.info == None:
        args.info = 0
    try:
        # Determines the files the reader will operate on
        if args.path is None:
            allfiles = ["./" + x for x in os.listdir(args.path) if x.endswith(".npk")]
        elif os.path.isdir(args.path):
            allfiles = [args.path + "/" + x for x in os.listdir(args.path) if x.endswith(".npk")]
        else:
            allfiles.append(args.path)
    except TypeError as e:
        print("NPK files not found")
    if not allfiles:
        print("No NPK files found in that folder")

    # Sets decryption keys for the custom XOR cipher
    keys = Keys()

    # Iterate through each file
    for path in allfiles:
        start = timer()  # Start timer for the unpacking duration
        print(f"UNPACKING: {path}")

        # Determine target folder based on the checkbox
        target_folder = os.path.join(output_folder, os.path.splitext(os.path.basename(path))[0]) if args.use_subfolders else output_folder
        if not os.path.exists(target_folder):
            os.makedirs(target_folder)

        with open(path, 'rb') as f:
            if not args.force:
                data = f.read(4)
                pkg_type = None
                if data == b'NXPK':
                    pkg_type = 0
                elif data == b'EXPK':
                    pkg_type = 1
                else:
                    raise Exception('NOT NXPK/EXPK FILE')
                print_data(args.info, 1, "FILE TYPE:", data, "NXPK", f.tell())

            files = readuint32(f)
            print_data(args.info, 1, "FILES:", files, "NXPK", f.tell())
            #print("")

            var1 = readuint32(f)
            print_data(args.info, 5, "UNKNOWN:", var1, "NXPK_DATA", f.tell())

            encryption_mode = readuint32(f)
            print_data(args.info, 2, "ENCRYPTMODE:", encryption_mode, "NXPK_DATA", f.tell())

            hash_mode = readuint32(f)
            print_data(args.info, 2, "HASHMODE:", hash_mode, "NXPK_DATA", f.tell())

            index_offset = readuint32(f)
            print_data(args.info, 2, "INDEXOFFSET:", index_offset, "NXPK_DATA", f.tell())

            info_size = determine_info_size(f, var1, hash_mode, encryption_mode, index_offset, files)
            print_data(args.info, 3, "INDEXSIZE", info_size, "NXPK_DATA", 0)
            #print("")

            index_table = []
            nxfn_files = []

            if hash_mode == 2:
                print("HASHING MODE 2 DETECTED, MAY OR MAY NOT WORK!")
                print("REPORT ERRORS ON GITHUB OR DISCORD <3")
            elif hash_mode == 3:
                raise Exception("HASHING MODE 3 IS CURRENTLY NOT SUPPORTED")

            if encryption_mode == 256 and args.nxfn_file:
                with open(os.path.join(target_folder, "NXFN_result.txt"), "w") as nxfn:
                    f.seek(index_offset + (files * info_size) + 16)
                    nxfn_files = [x for x in (f.read()).split(b'\x00') if x != b'']
                    for nxfnline in nxfn_files:
                        nxfn.write(nxfnline.decode() + "\n")
            elif encryption_mode == 256:
                f.seek(index_offset + (files * info_size) + 16)
                nxfn_files = [x for x in (f.read()).split(b'\x00') if x != b'']

            f.seek(index_offset)

            with tempfile.TemporaryFile() as tmp:
                data = f.read(files * info_size)
                if pkg_type:
                    data = keys.decrypt(data)
                tmp.write(data)
                tmp.seek(0)

                if args.do_one:
                    index_table.append(read_index(tmp, info_size, 0, nxfn_files, index_offset))
                else:
                    for x in range(files):
                        index_table.append(read_index(tmp, info_size, x, nxfn_files, index_offset))

            step = len(index_table) // 50 + 1

            for i, item in enumerate(index_table):
                if args.selectfile and (i != args.selectfile):
                    continue
                ext = None
                data2 = None
                if ((i % step == 0 or i + 1 == files) and args.info <= 2 and args.info != 0) or args.info > 2:
                    print(f'FILE: {i + 1}/{files}  ({((i + 1) / files) * 100:.2f}%)\n')

                file_sign, file_offset, file_length, file_original_length, zcrc, crc, file_structure, zflag, file_flag = item
                print_data(args.info, 4, "FILESIGN:", hex(file_sign[0]), "VERBOSE_FILE", file_sign[1])
                print_data(args.info, 3, "FILEOFFSET:", file_offset, "FILE", file_sign[1] + 4)
                print_data(args.info, 3, "FILELENGTH:", file_length, "FILE", file_sign[1] + 8)
                print_data(args.info, 4, "FILEORIGLENGTH:", file_original_length, "VERBOSE_FILE", file_sign[1] + 12)
                print_data(args.info, 4, "ZIPCRCFLAG:", zcrc, "VERBOSE_FILE", file_sign[1] + 16)
                print_data(args.info, 4, "CRCFLAG:", crc, "VERBOSE_FILE", file_sign[1] + 20)
                print_data(args.info, 3, "ZFLAG:", zflag, "VERBOSE_FILE", file_sign[1] + 22)
                print_data(args.info, 3, "FILEFLAG:", file_flag, "VERBOSE_FILE", file_sign[1] + 24)

                f.seek(file_offset)
                if file_original_length == 0 and not args.include_empty:
                    continue

                data = f.read(file_length)

                def check_file_structure():
                    if file_structure and not args.no_nxfn:
                        file_path = os.path.join(target_folder, file_structure.decode().replace("\\", "/"))
                        os.makedirs(os.path.dirname(file_path), exist_ok=True)
                        ext = file_path.split(".")[-1]
                    else:
                        file_path = os.path.join(target_folder, '{:08}.'.format(i))
                    return file_path

                file_path = check_file_structure()

                if pkg_type:
                    data = keys.decrypt(data)

                print_data(args.info, 5, "DECRYPTION:", decryption_algorithm(file_flag), "FILE", file_offset)
                data = file_decrypt(file_flag, data, args.key, crc, file_length, file_original_length)
                print_data(args.info, 5, "COMPRESSION0:", decompression_algorithm(zflag), "FILE", file_offset)
                data = zflag_decompress(zflag, data, file_original_length)

                compression = get_compression(data)
                print_data(args.info, 4, "COMPRESSION1:", compression.upper(), "FILE", file_offset)
                data = special_decompress(compression, data)

                if compression == 'zip':
                    file_path = check_file_structure() + "zip"
                    print_data(args.info, 5, "FILENAME_ZIP:", file_path, "FILE", file_offset)
                    with open(file_path, 'wb') as dat:
                        dat.write(data)
                    with zipfile.ZipFile(file_path, 'r') as zip:
                        zip.extractall(file_path[0:-4])
                    if args.delete_compressed:
                        os.remove(file_path)
                    continue

                if not file_structure:
                    ext = get_ext(data)
                    file_path += ext

                print_data(args.info, 3, "FILENAME:", file_path, "FILE", file_offset)
                with open(file_path, 'wb') as dat:
                    dat.write(data)

        end = timer()
        print(f"FINISHED - DECOMPRESSED {files} FILES IN {end - start} seconds")

#defines the parser arguments
def get_parser():
    parser = argparse.ArgumentParser(description='NXPK/EXPK Extractor made by MarcosVLl2 (@marcosvll2 on Discord or on GitHub https://github.com/MarcosVLl2/neox_tools)', add_help=False)
    parser.add_argument('-v', '--version', action='version', version='NXPK/EXPK Extractor  ---  Version: 1.9 --- Fixed CRC and other issues + added credits! (I kind of forgot what else)')
    parser.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS, help='Show this help message and exit')
    parser.add_argument('-p', '--path', help="Specify the path of the file or directory, if not specified will do all the files in the current directory",type=str)
    parser.add_argument('-d', '--delete-compressed', action="store_true",help="Delete compressed files (such as ZStandard or ZIP files) after decompression")
    parser.add_argument('-i', '--info', help="Print information about the npk file(s) 1 to 5 for least to most verbose",type=int)
    parser.add_argument('-k', '--key', help="Select the key to use in the CRC128 hash algorithm (check the keys.txt for information)",type=int)
    parser.add_argument('--credits', help="Shows credits and acknowledgements from people who helped me develop this!!", action="store_true")
    parser.add_argument('--force', help="Forces the NPK file to be extracted by ignoring the header",action="store_true")
    parser.add_argument('--selectfile', help="Only do the file selected", type=int)
    parser.add_argument('--nxfn-file', action="store_true",help="Writes a text file with the NXFN dump output (if applicable)")
    parser.add_argument('--no-nxfn',action="store_true",help="Disables NXFN file structure")
    parser.add_argument('--convert-images', help="Automatically converts KTX, PVR and ASTC to PNG files (WARNING, SUPER SLOW)",action="store_true")
    parser.add_argument('--include-empty', help="Prints empty files", action="store_false")
    parser.add_argument('--do-one', action='store_true', help='Only do the first file (TESTING PURPOSES)')
    opt = parser.parse_args()
    return opt

#main entry point
def main():
    #defines the parser argument
    opt = get_parser()

    # credits screen
    if opt.credits:
        print("\nThank you to everyone who helped me develop this tool and to all of the effort from other tool creators.\n")
        print("zhouhang95:    https://github.com/zhouhang95/neox_tools")  
        print("hax0r313373:   https://github.com/hax0r31337/denpk2")
        print("xforce:        https://github.com/xforce/neox-tools")
        print("yuanbi:        https://github.com/yuanbi/NeteaseUnpackTools\n")
        print("Also a big thank you to everyone in the unofficial Discord (https://discord.gg/eedXVqzmfn) who is helping me with reporting errors and new NPK files to detect!\n")
        print("Special thanks to: aocosmic, victornewspaper, danisis397, yumpyyingzi and _kingjulz")
        print("Please join the server above to help out!!\n")
    else:

        #runs the unpack script with the given arguments
        unpack(opt)

#entry point if ran as a standalone
if __name__ == '__main__':
    main()
