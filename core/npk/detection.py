"""Utilities for file format detection in NPK files."""

from core.npk.enums import NPKEntryFileType


def get_ext(data):
    """Get the file extension based on file signature.

    Args:
        data: Raw file data

    Returns:
        str: File extension without leading dot
    """
    # todo: make this cleaner
    if len(data) == 0:
        return 'empty'
    #elif data[:4] != bytes([0x7A, 0x1C]):
     #   return 'not_data'
    elif data[:3] == b'PVR':
        return 'pvr'
    elif data[:4] == bytes([0x34, 0x80, 0xC8, 0xBB]):
        return 'mesh'
    elif data[:4] == b'RIFF':
        if b'FEV' in data:
            return 'fev'
        elif b'WAVE' in data:
            return 'wem'
    elif data[:8] == b'RAWANIMA':
        return 'rawanimation'
    elif data[:8] == b'NEOXBIN1':
        return 'uiprefab'
    elif data[:8] == b'SKELETON':
        return 'skeleton'
    #elif data[1:8] == bytes([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]):
    #    return 'blasttool'
    elif data[:6] == bytes([0x01, 0x00, 0x05, 0x00, 0x00, 0x00]):
        return 'foliage'
    elif data[:6] == bytes([0x01, 0x00, 0x05, 0x00, 0x00, 0x00]):
        return 'foliage'
    elif data[:8] == b'NEOXMESH':
        return 'uimesh'
    elif data[:33] == b'NVidia(r) GameWorks Blast(tm) v.1':
        return 'blast'
    elif data[:4] == bytes([0xE3, 0x00, 0x00, 0x00]) or data[:4] == bytes([0x63, 0x00, 0x00, 0x00]) or data[:4] == bytes([0x4C, 0x0F, 0x00, 0x00]):
        return 'pyc'
    elif data[:12] == b'CocosStudio-UI':
        return 'coc'
    elif data[:4] == bytes([0x13, 0xAB, 0xA1, 0x5C]):
        return 'astc'
    elif data[:3] == b'hit':
        return 'hit'
    elif data[:3] == b'PKM':
        return 'pkm'
    elif data[:3] == b'DDS':
        return 'dds'
    elif data[-18:-2] == b'TRUEVISION-XFILE' or data[:3] == bytes([0x00, 0x00, 0x02]) or data[:3] == bytes([0x0D, 0x00, 0x02]):
        return 'tga'
    elif data[:4] == b'NFXO':
        return 'nfx'
    elif data[:4] == bytes([0xC1, 0x59, 0x41, 0x0D]):
        return 'unknown1'
    elif data[:8] == b'CompBlks':
        return 'cbk'
    elif data [:2] == b'BM':
        return 'bmp'
    elif data[:18] == b'from typing import ':
        return 'pyi'
    elif data[1:4] == b'KTX':
        return 'ktx'
    elif data[:9] == b'blastmesh':
        return 'blastmesh'
    elif data[:10] == b'clothasset':
        return 'clothasset'
    elif data[1:4] == b'PNG':
        return 'png'
    elif data[:4] == b'FSB5':
        return 'fsb'
    elif data[:4] == b'VANT':
        return 'vant'
    elif data[:4] == b'MDMP':
        return 'mdmp'
    elif data[:4] == b'RGIS':
        return 'gis'
    elif data[:4] == b'NTRK':
        return 'trk'
    elif data[:4] == b'OggS':
        return 'ogg'
    elif data[:4] == bytes([0xFF,0xD8,0xFF,0xE1]):
        return 'jpg'
    elif data[:4] == b'BKHD':
        return 'bnk'
    elif data[:27] == b'-----BEING PUBLIC KEY-----':
        return 'pem'
    elif data[:1] == b'%':
        return 'tpl'
    elif data[:4] == b'TZif':
        return 'tzif'
    elif data[6:10] == b'JFIF':
        return 'jfif'
    elif data[4:8] == b'ftyp':
        return 'mp4'
    elif data[0x3B: 0x3F] == bytes([0xC5, 0x00, 0x00, 0x80, 0x3F]):
        return 'slpb'
    elif len(data) < 100000000:
        #NeoXML file detection
        if b'<Material' in data:
            return 'mtl'
        if b'<MaterialGroup' in data:
            return 'mtg'
        if b'<MetaInfo' in data:
            return 'pvr.meta'
        if b'SHEX' in data and b'OSGN' in data:
            return 'binary'
        if b'<Section' in data:
            return 'sec'
        if b'<SubMesh' in data:
            return 'gim'
        if b'<FxGroup' in data:
            return 'sfx'
        if b'<Track' in data:
            return 'trackgroup'
        if b'<Instances' in data:
            return 'decal'
        if b'<Physics' in data:
            return 'col'
        if b'<LODPolicy' in data or b'<LODProfile' in data:
            return 'lod'
        if b'Type="Animation"' in data:
            return 'animation'
        if b'DisableBakeLightProbe=' in data:
            return 'prefab'
        if b'<Scene' in data:
            return 'scn'
        if b'"ParticleSystemTemplate"' in data:
            return 'pse'
        if b'<MainBody' in data:
            return 'nxcompute'
        if b'?xml' in data:
            return 'xml'
        if b'<MapSkeletonToMeshBone' in data:
            return 'skeletonextra'
        if b'<ShadingModel' in data:
            return 'nxshader'
        if b'<BlastDynamic' in data:
            return 'blt'
        if b'"ParticleAudio"' in data:
            return 'psemusic'
        if b'<BlendSpace' in data and b'is2D="false"' in data:
            return 'blendspace1d'
        if b'<AnimationConfig' in data:
            return 'animconfig'
        if b'<AnimationGraph' in data:
            return 'animgraph'
        if b'<Head Type="Timeline"' in data:
            return 'timeline'
        if b'<Chain' in data:
            return 'physicalbone'
        if b'<BlendSpace' in data and b'is2D="true"' in data:
            return 'blendspace'
        if b'<PostProcess' in data:
            return 'postprocess'
        if b'"mesh_import_options":{' in data:
            return 'nxmeta'
        if b'<SceneConfig' in data:
            return 'scnex'
        if b'<LocalPoints' in data:
            return 'localweather'
        if b'GeoBatchHint="0"' in data:
            return 'gimext'
        if b'"AssetType":"HapticsData"' in data:
            return 'haptic'
        if b'<LocalFogParams' in data:
            return 'localfogparams'
        if b'<Audios' in data or b'<AudioSource' in data:
            return 'prefabaudio'
        if b'"ReferenceSkeleton' in data:
            return 'featureschema'
        if b'<Relationships' in data:
            return 'xml.rels'
        if b'<Waterfall' in data:
            return 'waterfall'
        if b'"ReferenceSkeletonPath"' in data:
            return 'mirrortable'
        if b'<ClothAsset' in data:
            return 'clt'
        if b'<plist' in data:
            return 'plist'
        if b'<ShaderCompositor' in data or b'<ShaderFeature' in data or b"<ShaderIndexes" in data or b"<RenderTrigger" in data:
            return 'render'
        if b'<SkeletonRig' in data:
            return 'skeletonrig'
        if b'format: ' in data and b'filter: ' in data:
            return 'atlas'
        if b'<ShaderCache' in data:
            return 'cache'
        if b'char' in data and b'width=' in data and b'height=' in data:
            return 'fnt'
        if b'<AllCaches' in data:
            return 'info'
        if b'<AllPreloadCaches' in data:
            return 'list'
        if b'<Remove_Files' in data:
            return 'map'
        if b'<HLSL File="' in data:
            return 'md5'
        if b'<EnvParticle' in data:
            return 'envp'
        if b'<TextureGroup' in data:
            return 'txg'

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
