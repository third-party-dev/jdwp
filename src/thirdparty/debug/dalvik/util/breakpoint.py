
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
    return DexHeader(bytes(headerRes['headerData']))


async def parse_vregs(dbg, native, thread_info):
    # Get thread as ObjectInfo.
    thread_obj = await dbg.deref(thread_info.threadID)

    # Get nativePeer tagged value.
    nativePeerTValue = thread_obj.field_value('Ljava/lang/Thread;', 'nativePeer')
    
    # Get nativePeer pointer.
    nativePeer = nativePeerTValue.value
    
    # Using nativePeer, get the vregs (for Android 13)
    return native.rpc.dump_vregs(nativePeer)


def print_vregs(vregs):
    # Dump results.
    print(f'dex_pc: {vregs['dex_pc']}')
    for i in range(vregs['vreg_cnt']):
        reg = f'raw_v{i}'
        print(f"{reg}: {vregs[reg]:8x}")
    for i in range(vregs['vreg_cnt']):
        reg = f'ref_v{i}'
        print(f"{reg}: {vregs[reg]:8x}")