"""Image conversion functions for various formats."""

# TODO: Code cleanup

import io
import math
import texture2ddecoder
from typing import Literal, cast
from PIL import Image, ImageFile
from bitstring import ConstBitStream

DDS_HEADER = b"DDS\x20\x7C\0\0\0\x07\x10\0\0"
DDS_PIXFORM_HEADER = b"\x20\0\0\0\x04\0\0\0"
QUAD_NULL_BYTES = b"\0\0\0\0"

def _r_uintle32(data: ConstBitStream):
    return data.read('uintle:32')
def _r_uintle64(data: ConstBitStream):
    return data.read('uintle:64')

#tga, ico, tiff, dds
def _pillow_image_conversion(data, fmt):
    return Image.open(io.BytesIO(data), "r", (fmt.upper(), "PNG"))

def image_to_png_data(img: Image.Image | ImageFile.ImageFile) -> bytes:
    """Convert an image to PNG data."""
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()

def _get_astc_file_size(width, height, block_x, block_y):
    return math.ceil(width/block_y) * math.ceil(height/block_x) * 16

#this code was derived from TeaEffTeu's works and he slightly guided me, thank you very much for sharing!!
def compblks_convert(data):
    """Convert CompBlks to Image."""
    def get_pitch(width):
        return int.to_bytes(max(1, ((int.from_bytes(width, "little")+3)//4) ) * 16, 4, "little")
    width = data[16:18] + b"\0\0"
    height = data[18:20] + b"\0\0"

    dds_data = DDS_HEADER + height + width + get_pitch(width) + (QUAD_NULL_BYTES * 13) + DDS_PIXFORM_HEADER + \
                b"DXT5" + (QUAD_NULL_BYTES * 5) + b"\0\x10\0\0" + (QUAD_NULL_BYTES * 4) + data[28:]
    return _pillow_image_conversion(dds_data, "dds")

def pvr_convert(data: bytes):
    """Convert PVR to Image."""
    
    def int_to_bytes(number: int):
        return int.to_bytes(number, 4, "little")
    def get_format_bits_per_pixel(form):
        match form:
            case 3:
                return (b"PVRTC", 4)
            case 7:
                return (b"DXT1", 4)
            case 11:
                return (b"DXT5", 8)
            case 27:
                return (b"ASTC", (4, 4))
            case 28:
                return (b"ASTC", (5, 4))
            case 29:
                return (b"ASTC", (5, 5))
            case 30:
                return (b"ASTC", (6, 5))
            case 31:
                return (b"ASTC", (6, 6))
            case 32:
                return (b"ASTC", (8, 5))
            case 33:
                return (b"ASTC", (8, 6))
            case 34:
                return (b"ASTC", (8, 8))
            case 35:
                return (b"ASTC", (10, 5))
            case 36:
                return (b"ASTC", (10, 6))
            case 37:
                return (b"ASTC", (10, 8))
            case 38:
                return (b"ASTC", (10, 10))
            case 39:
                return (b"ASTC", (12, 10))
            case 40:
                return (b"ASTC", (12, 12))
    def get_pitch(width, block_size):
        return int.to_bytes(max(1, ((width+3)//4) ) * (2 * block_size), 4, "little")

    f = ConstBitStream(io.BytesIO(data))
    #version = f.read('hex:32')  # 50565203 (endianness does NOT match)
    #flags = _r_uintle32(f)  # 0 (no flag)
    f.read("pad64")
    pixel_format = f.read("uintle64") #_r_uintle64(f)  # 34 (astc_8x8)
    #colour_space = _r_uintle32(f) # 0 (linear RGB)
    #channel_type = _r_uintle32(f) # 0 (unsigned byte normalised)
    f.read("pad64")
    height, width, depth = f.readlist("3*uintle32") #_r_uintle32(f) # 150
    #width = _r_uintle32(f) # 256
    #depth = _r_uintle32(f) # 1 (no depth)
    #num_surfaces = _r_uintle32(f) # 1
    #num_faces = _r_uintle32(f) # 1
    #mip_map_count = _r_uintle32(f) # 1
    f.read("pad96")
    meta_data_size = f.read("uintle32") #_r_uintle32(f) # 15
    f.pos += meta_data_size * 8
    p_format, bpp = get_format_bits_per_pixel(pixel_format) # 4

    if p_format == b"ASTC": #PVR with ASTC encoding
        x, y = bpp
        return Image.frombytes('RGBA', (width, height), texture2ddecoder.decode_astc(f.read(f"bytes"), width, height, x, y), 'raw', ("BGRA"))
    
    elif p_format == b"PVRTC": #PVR with PVRTC encoding
        return Image.frombytes("RGBA", (width, height), texture2ddecoder.decode_pvrtc(f.read(f"bytes{width*height*bpp // 8}"), width, height, False), "raw", ("BGRA"))
    
    else: #PVR with DXT1 or DXT5 encoding
        texture_data = f.read(f"bytes:{width*height*bpp // 8}")

    dds_data = DDS_HEADER + int_to_bytes(height) + int_to_bytes(width) + \
                get_pitch(width, bpp) + QUAD_NULL_BYTES + int_to_bytes(1) + \
                (QUAD_NULL_BYTES * 11) + DDS_PIXFORM_HEADER + p_format + (QUAD_NULL_BYTES * 10)

    return _pillow_image_conversion(dds_data + texture_data, "dds")

#https://registry.khronos.org/KTX/specs/1.0/ktxspec.v1.html
#https://docs.vulkan.org/spec/latest/chapters/formats.html
def ktx_convert(data: bytes):
    """Convert KTX to Image."""
    ## Useless code currently reserve in case different types of encodings are used in KTX images...
    
    #def get_glInternal_format(data):
    #    match data:
    #        case 37815:
    #            return "COMPRESSED_RGBA_ASTC_8x8_KHR"
    f = ConstBitStream(io.BytesIO(data))
    #identifier = f.read("bytes:12")
    #endianness = _r_uintle32(f)
    #glType = _r_uintle32(f)
    #glTypeSize = _r_uintle32(f)
    #glFormat = _r_uintle32(f)
    #glInternalFormat = get_glInternal_format(_r_uintle32(f))
    #glBaseInternalFormat = _r_uintle32(f)
    f.read("pad288")
    pixelWidth, pixelHeight= f.readlist("2*uintle32")
    #pixelDepth = _r_uintle32(f)
    #numberOfArrayElements = _r_uintle32(f)
    #numberOfFaces = _r_uintle32(f)
    #numberOfMipmapLevels = _r_uintle32(f)
    #bytesOfKeyValueData  = _r_uintle32(f)
    f.read("pad160")
    image_size = _r_uintle32(f)
    image_data = texture2ddecoder.decode_astc(f.read(f"bytes:{image_size}"), pixelWidth, pixelHeight, 8, 8)
    return Image.frombytes('RGBA', (pixelWidth, pixelHeight), image_data, 'raw', ("BGRA"))

def astc_convert(data: bytes):
    """Convert ASTC to Image."""
    f = ConstBitStream(io.BytesIO(data))
    block_x, block_y = f.readlist("pad32, 2*uintle8 , pad8")
    width, height = f.readlist("2*uintle24, pad24")
    return Image.frombytes('RGBA', (width, height), texture2ddecoder.decode_astc(f.read(f"bytes"), width, height, block_x, block_y), "raw", ("BGRA"))

def convert_image(data, extension):
    """Identify and convert image data to Image."""
    if extension == "dds":
        return _pillow_image_conversion(data, extension)
    if extension == "pvr":
        return pvr_convert(data)
    if extension == "ktx":
        return ktx_convert(data)
    if extension == "astc":
        return astc_convert(data)
    if extension == "cbk":
        return compblks_convert(data)
    return None
