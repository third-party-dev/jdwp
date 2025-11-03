
from thirdparty.dalvik.dex.header import DexHeader

async def parse_dex_header(dbg, native, event):
    #print(event.location)
    this_class_obj = await dbg.deref(event.location.classID)
    #print(this_class_obj)
    dexCacheTValue = this_class_obj.field_value('Ljava/lang/Class;', 'dexCache')

    dexCache = await dbg.deref(dexCacheTValue.value)
    #print(dexCache)
    dexFileTValue = dexCache.field_value('Ljava/lang/DexCache;', 'dexFile')
    #print(dexFileTValue)

    headerRes = native.rpc.fetch_dex_header(dexFileTValue.value)
    
    #headerRes['addr']
    #headerRes['size']
    dexHeader = DexHeader(bytes(headerRes['headerData']))
    print(dexHeader)

async def parse_vregs(dbg, native, thread_info):
    # Get thread as ObjectInfo.
    breakpoint()
    thread_obj = await dbg.deref(thread_info.threadID)

    # Get nativePeer tagged value.
    nativePeerTValue = thread_obj.field_value('Ljava/lang/Thread;', 'nativePeer')
    
    # Get nativePeer pointer.
    nativePeer = nativePeerTValue.value
    
    # Using nativePeer, get the vregs (for Android 13)
    vregs = native.rpc.dump_vregs(nativePeer)
    
    # Dump results.
    print(f'dex_pc: {vregs['dex_pc']}')
    reg_names = [
        'raw_v0', 'raw_v1', 'raw_v2', 'raw_v3', 'raw_v4',
        'raw_v5', 'raw_v6', 'raw_v7', 'raw_v8',
        'ref_v0', 'ref_v1', 'ref_v2', 'ref_v3', 'ref_v4',
        'ref_v5', 'ref_v6', 'ref_v7', 'ref_v8',
    ]
    for reg in reg_names:
        print(f"{reg}: {vregs[reg]:8x}")