"""Utilities for file format detection in NPK files."""

from core.npk.enums import NPKEntryFileType

def get_ext(data):
    """Get the file extension based on file signature.

    Args:
        data: Raw file data

    Returns:
        str: File extension without leading dot
    """
    if not data:
        return 'empty'

    data_len = len(data)

    # Group signatures by length for more efficient checking
    signatures = {
        # 1-byte signatures
        1: {
            b'%': 'tpl',
        },
        # 2-byte signatures
        2: {
            b'BM': 'bmp',
            b'PK': 'zip',
        },
        # 3-byte signatures
        3: {
            b'PVR': 'pvr',
            b'DDS': 'dds',
            b'hit': 'hit',
            b'PKM': 'pkm',
        },
        # 4-byte signatures
        4: {
            b'NFXO': 'nfx',
            b'RGIS': 'gis',
            b'NTRK': 'trk',
            b'BKHD': 'bnk',
            b'RIFF': None,  # Special handling below
            b'OggS': 'ogg',
            b'VANT': 'vant',
            b'MDMP': 'mdmp',
            b'TZif': 'tzif',
            b'FSB5': 'fsb',
            bytes([0xFF, 0xD8, 0xFF, 0xE1]): 'jpg',
            bytes([0x34, 0x80, 0xC8, 0xBB]): 'mesh',
            bytes([0x13, 0xAB, 0xA1, 0x5C]): 'astc',
            bytes([0xC1, 0x59, 0x41, 0x0D]): 'unknown1',
        },
        # Special binary signatures for PYC files
        'pyc': [
            bytes([0xE3, 0x00, 0x00, 0x00]),
            bytes([0x63, 0x00, 0x00, 0x00]),
            bytes([0x4C, 0x0F, 0x00, 0x00])
        ],
        # Longer signatures
        'long': {
            b'SKELETON': 'skeleton',
            b'NEOXMESH': 'uimesh',
            b'NEOXBIN1': 'uiprefab',
            b'RAWANIMA': 'rawanimation',
            b'CompBlks': 'cbk',
            b'blastmesh': 'blastmesh',
            b'clothasset': 'clothasset',
            b'from typing import ': 'pyi',
            b'NVidia(r) GameWorks Blast(tm) v.1': 'blast',
            b'CocosStudio-UI': 'coc',
            b'-----BEING PUBLIC KEY-----': 'pem',
        },
        # Special foliage signature
        'foliage': bytes([0x01, 0x00, 0x05, 0x00, 0x00, 0x00]),
    }

    # Quick check for empty or very short data
    if data_len < 3:
        for length in range(1, min(data_len + 1, 3)):
            prefix = data[:length]
            if length in signatures and prefix in signatures[length]:
                return signatures[length][prefix]
        return 'dat'

    # PNG detection - efficient check
    if data_len >= 4 and data[1:4] == b'PNG':
        return 'png'

    # TGA detection at beginning
    if data_len >= 3 and (data[:3] == bytes([0x00, 0x00, 0x02]) or data[:3] == bytes([0x0D, 0x00, 0x02])):
        return 'tga'

    # TGA detection at end (only check if file is big enough)
    if data_len >= 18 and data[-18:-2] == b'TRUEVISION-XFILE':
        return 'tga'

    # Check for slpb signature at specific offset
    if data_len >= 0x3F and data[0x3B:0x3F] == bytes([0xC5, 0x00, 0x00, 0x80, 0x3F]):
        return 'slpb'

    # Check 3-byte signatures
    if data_len >= 3:
        prefix3 = data[:3]
        if 3 in signatures and prefix3 in signatures[3]:
            return signatures[3][prefix3]

    # Check 4-byte signatures and special cases
    if data_len >= 4:
        prefix4 = data[:4]
        if 4 in signatures and prefix4 in signatures[4]:
            result = signatures[4][prefix4]

            # Special case for RIFF files
            if prefix4 == b'RIFF':
                if b'FEV' in data:
                    return 'fev'
                elif b'WAVE' in data:
                    return 'wem'
            else:
                if result is not None:
                    return result

        # Check for PYC files
        if prefix4 in signatures['pyc']:
            return 'pyc'

        # Check for MP4 files
        if data_len >= 8 and data[4:8] == b'ftyp':
            return 'mp4'

    # Check 6-byte signatures
    if data_len >= 6:
        # Check for foliage files
        if data[:6] == signatures['foliage']:
            return 'foliage'

        # Check for JFIF files
        if data_len >= 10 and data[6:10] == b'JFIF':
            return 'jfif'

    # Check for longer signatures
    for sig, ext in signatures['long'].items():
        sig_len = len(sig)
        if data_len >= sig_len and data[:sig_len] == sig:
            return ext

    # Process XML-like files and other text formats if file is not too large
    if data_len < 100000000:  # ~100MB limit for text scanning
        # Special binary file cases to check first (faster)
        if b'SHEX' in data and b'OSGN' in data:
            return 'binary'

        # Dictionary of XML pattern to extension mappings
        xml_patterns = {
            b'<Material': 'mtl',
            b'<MaterialGroup': 'mtg',
            b'<MetaInfo': 'pvr.meta',
            b'<Section': 'sec',
            b'<SubMesh': 'gim',
            b'<FxGroup': 'sfx',
            b'<Track': 'trackgroup',
            b'<Instances': 'decal',
            b'<Physics': 'col',
            b'<LODPolicy': 'lod',
            b'<LODProfile': 'lod',
            b'<Scene': 'scn',
            b'<MainBody': 'nxcompute',
            b'<MapSkeletonToMeshBone': 'skeletonextra',
            b'<ShadingModel': 'nxshader',
            b'<BlastDynamic': 'blt',
            b'<AnimationConfig': 'animconfig',
            b'<AnimationGraph': 'animgraph',
            b'<Head Type="Timeline"': 'timeline',
            b'<Chain': 'physicalbone',
            b'<PostProcess': 'postprocess',
            b'<SceneConfig': 'scnex',
            b'<LocalPoints': 'localweather',
            b'<LocalFogParams': 'localfogparams',
            b'<Audios': 'prefabaudio',
            b'<AudioSource': 'prefabaudio',
            b'<Relationships': 'xml.rels',
            b'<Waterfall': 'waterfall',
            b'<ClothAsset': 'clt',
            b'<plist': 'plist',
            b'<ShaderCache': 'cache',
            b'<AllCaches': 'info',
            b'<AllPreloadCaches': 'list',
            b'<Remove_Files': 'map',
            b'<HLSL File="': 'md5',
            b'<EnvParticle': 'envp',
            b'<TextureGroup': 'txg',
            b'<SkeletonRig': 'skeletonrig',
        }

        # Special cases with multiple conditions - grouped by priority
        if b'?xml' in data:
            return 'xml'
        if b'Type="Animation"' in data:
            return 'animation'
        if b'DisableBakeLightProbe=' in data:
            return 'prefab'
        if b'<ShaderCompositor' in data or b'<ShaderFeature' in data or b"<ShaderIndexes" in data or b"<RenderTrigger" in data:
            return 'render'

        # BlendSpace checks - grouped
        if b'<BlendSpace' in data:
            if b'is2D="false"' in data:
                return 'blendspace1d'
            if b'is2D="true"' in data:
                return 'blendspace'

        # Other special cases
        if b'"ParticleSystemTemplate"' in data:
            return 'pse'
        if b'"ParticleAudio"' in data:
            return 'psemusic'
        if b'"mesh_import_options":{' in data:
            return 'nxmeta'
        if b'GeoBatchHint="0"' in data:
            return 'gimext'
        if b'"AssetType":"HapticsData"' in data:
            return 'haptic'
        if b'"ReferenceSkeleton' in data:
            return 'featureschema'
        if b'"ReferenceSkeletonPath"' in data:
            return 'mirrortable'
        if b'format: ' in data and b'filter: ' in data:
            return 'atlas'
        if b'char' in data and b'width=' in data and b'height=' in data:
            return 'fnt'

        # Optimized pattern matching for XML-like files
        # Use a slice of data to avoid scanning entire large files
        scan_data = data[:min(data_len, 8192)]  # Scan first 8KB for XML tags
        for pattern, ext in xml_patterns.items():
            if pattern in scan_data:
                return ext

    # Default fallback
    return 'dat'

def get_file_category(extension):
    """Categorize a file based on its extension.

    Args:
        extension: File extension

    Returns:
        str: Category name
    """
    extension = extension.lower()

    # Textures
    if extension in ["bmp", "gif", "jpg", "jpeg", "png", "pbm", "pgm", "ppm", "xbm",
                     "xpm", "tga", "ico", "tiff", "dds", "pvr", "astc", "ktx", "cbk"]:
        return NPKEntryFileType.TEXTURE

    # 3D Models
    if extension in ["mesh"]:
        return NPKEntryFileType.MESH

    # Text formats
    if extension in ["mtl", "json", "xml", "trackgroup", "nfx", "h", "shader", "animation"]:
        return NPKEntryFileType.TEXT

    return NPKEntryFileType.OTHER
