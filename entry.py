#!/usr/bin/env python3

'''
Consider:

pip install pure-python-adb-reborn
pip install androguard
pip install frida frida_tools
pip install pyaxml
pip install fuzzyfinder
'''

#"adb shell cat /proc/31778/maps | tr " " "\n" | grep "\.apk" | grep 'data\/app' | sort -u"

'''
Given PID, fetch APKs via the memory maps in /proc/PID/maps:



For each apk returned, get the sha1 of the apk. If we have the SHA1, load the cache.
  - If there is no matching sha1, pull APK and androguard process it into cache.
  - Is the APK package name always in the /data/app file path? Do all APKs have base.apk?
  - How does Androguard distinguish between dex files?
  - If path doesn't exist, skip it.
  - FINALLY, Once APKs are processed, try to load cache object again.
    - If cache object wasn't loaded, fail gracefully to untranslated labels.

Consider ... get *this* object, deref classID of *this* and get dexCache.
  - dexCache has pointers to resolvedFields, resolvedMethods, resolvedTypes and strings.



dexCache.dexFile points to:
  - internal data
  - DEX FILE DATA!!
    - u8 magic[8]
    - u32 adler32 CRC
  - DEX FILE SIZE!!

uint8_t  magic_[8];
    uint32_t checksum_;
    uint8_t  signature_[SHA1_DIGEST_LENGTH];  // 20 bytes
    uint32_t file_size_;
    uint32_t header_size_;
    uint32_t endian_tag_;
    uint32_t link_size_;
    uint32_t link_off_;
    uint32_t map_off_;
    uint32_t string_ids_size_;
    uint32_t string_ids_off_;
    uint32_t type_ids_size_;
    uint32_t type_ids_off_;
    uint32_t proto_ids_size_;
    uint32_t proto_ids_off_;
    uint32_t field_ids_size_;
    uint32_t field_ids_off_;
    uint32_t method_ids_size_;
    uint32_t method_ids_off_;
    uint32_t class_defs_size_;
    uint32_t class_defs_off_;
    uint32_t data_size_;
    uint32_t data_off_;

'''

'''
Test Use Case:

Setup JvmDebugger
Add breakpoint
On breakpoint:
  - Get the treadID
  - Dereference threadID to get nativePeer
  - Using nativePeer, fetch vregs from ShadowFrame (Given Android Version).
  - Using typeID of object in location from breakpoint:
  - Dereference class to fetch dexCache object
  - Using dexCache object, fetch location String (may lead to specific dex file)
  - CONSIDER: Can we read directly from the following in dexCache (via Frida):
    - resolvedFields, resolvedMethods, resolvedTypes, strings
  - Note: DexCache.java docs dexCache as "c array pointers as they become resolved."
      
'''

'''
adb shell am set-debug-app -w sh.kau.playground ; \
  frida -U -f sh.kau.playground ; \
  
  adb forward \
    tcp:8700 \
      jdwp:$(adb shell ps -A | grep sh.kau.playground | awk '{print $2}') ; \
  sleep 3 && ./test.py
'''

'''
await dbg.cli_frame(26092)
await dbg.cli_frame_values(26092, 131072)
await dbg.cli_object_values()
'''



import asyncio
from thirdparty.jdwp import Jdwp, Byte, Boolean, Int, String, ReferenceTypeID

from thirdparty.sandbox.repl import Repl
import thirdparty.jvmdebugger
from thirdparty.jvmdebugger.state import *
from ppadb.client import Client as AdbClient
import frida

# Utility imports
import pdb
from fuzzyfinder import fuzzyfinder
from pprint import pprint


class AdbObject():
    pass

class NativeObject():
    pass


# We're keeping jdwp, dbg, and dbg_state in global scope so
# they remain accessible to REPL mechanisms.
adb = AdbObject()
native = NativeObject()
jdwp = None
dbg = thirdparty.jvmdebugger.JvmDebugger()
dbg_state = dbg.state


'''
Areas Of Instrumentation:

- Emulator with Kernel Output (Android 13)
- Frida Server Pushed To /data and made executable.
- Frida Server verifiably running

- APK File Marked Debuggable
- (Optionally) APK Analyzed by Androguard with content cached for later usage.
- APK File Installed As App

1. App Configured For JDWP Debug
2. App Launched and waiting for Debugger
3. App PID fetched.
4. App JDWP port forwarded to 8700.
5. JvmDebugger attached to App via tcp:8700.
  - Standard JvmDebugger initialization started.
  - Setup initial breakpoints.
  - Once JVM is waiting for events, continue to 6.
6. Connect/inject Frida into app via PID.

# On Breakpoint:

1. (Via Single Call) Get the vregs via the nativePeer of target threadID (using Frida connection).
2. (Via Single Call) Get the dexCache for *this* object and resolve relevant thing. 


'''


async def main():
    global dbg
    global jdwp
    global native
    global adb

    # Start up the application in debug mode.
    setup_app('sh.kau.playground')

    # Connect to application native access.
    #native.device = frida.get_usb_device()
    #native.session = native.device.attach(adb.proc_pid)

    # Settle a bit.
    settle_timeout = 3
    print(f"Sleeping {settle_timeout} secs for system to settle.")
    await asyncio.sleep(settle_timeout)

    # Connect to application with our debugger.
    print("Connecting debugger to localhost:8700")
    await dbg.start('127.0.0.1', 8700)
    jdwp = dbg.jdwp
    dbg.print_summary()

    async def handle_breakpoint(event, composite, args):
        bp, = args
        print(f"{bp.location_str(event)}")
        
        await bp.wait()
        await bp.dbg.resume_vm()

    fetchQuote = dbg.create_breakpoint(**{
        'class_signature': 'Lsh/kau/playground/quoter/QuotesRepoImpl;',
        'method_name': 'fetchQuote',
        'method_signature': '(Lkotlin/coroutines/Continuation;)Ljava/lang/Object;',
    }, callback=None)
    await bp.fetchQuote.set_breakpoint()

    quoteForTheDay = dbg.create_breakpoint(**{
        'class_signature': 'Lsh/kau/playground/quoter/QuotesRepoImpl;',
        'method_name': 'quoteForTheDay',
        'method_signature': '(Lkotlin/coroutines/Continuation;)Ljava/lang/Object;',
    }, callback=None)
    #await bp.quoteForTheDay.set_breakpoint()

    await dbg.resume_vm()

    try:
        print("Waiting for events... Ctrl-C to quit.")
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        exit(0)


async def main_with_sandbox():
    socket_path = "/tmp/asyncrepl.sock"
    repl_coro = Repl(namespace=globals()).start_repl_server(socket_path=socket_path)
    repl_task = asyncio.create_task(repl_coro)
    main_task = asyncio.create_task(main())
    await asyncio.gather(repl_task, main_task)


def reload_dbg():
    global dbg
    global dbg_state
    dbg = thirdparty.jvmdebugger.JvmDebugger(dbg_state)


def setup_app(tgt_pkg, device_name='emulator-5554'):
    global adb
    
    adb.tgt_pkg = tgt_pkg
    adb.client = AdbClient(host="127.0.0.1", port=5037)
    # Connection sanity.
    print(f'ADB Client Version: {adb.client.version()}')
    adb.device = adb.client.device(device_name)

    # Configure the tgt_pkg to wait for debugger on start.
    cmd = f'am set-debug-app -w {adb.tgt_pkg}'
    print(cmd)
    print(adb.device.shell(cmd))

    # Get the main activity name. (Note: This is a bit wonky.)
    cmd = f'cmd package resolve-activity -c android.intent.category.LAUNCHER {adb.tgt_pkg}'
    pkg_act_info = adb.device.shell(cmd)

    import re
    # Get text following "name=" until end of line.
    pattern = re.compile(r'(?<=name=)\S+')
    matches = []
    for line in pkg_act_info.split('\n'):
        found = pattern.findall(line)
        matches.extend(found)
    print(matches)
    
    pkg_main_act = matches[0].replace(adb.tgt_pkg, f'{adb.tgt_pkg}/')
    print(pkg_main_act)

    # Start the tgt_pkg's main activity.
    adb.device.shell(f'am start -n {pkg_main_act}')

    import time
    time.sleep(0.5)

    # Get the process id (PID) of the running tgt_pkg.
    adb_procs = adb.device.shell(f'ps -A')
    adb.proc_pid = None
    for proc in adb_procs.split('\n'):
        if proc.find(adb.tgt_pkg) < 0:
            continue
        adb.proc_pid = int(proc.split()[1])
        break
    if not adb.proc_pid:
        print("Target process not found.")
        exit(1)
    
    # Port forward internal JDWP port (same as PID) to localhost:8700
    cmd = f'adb forward tcp:8700 jdwp:{adb.proc_pid}'
    #print(cmd)
    adb.device.shell(cmd)

    time.sleep(3)


if __name__ == "__main__":
    asyncio.run(main_with_sandbox())
    




