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

Setup Debugger
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
await dbg.cli_frame(26092)
await dbg.cli_frame_values(26092, 131072)
await dbg.cli_object_values()
'''



import asyncio
from thirdparty.jdwp import Jdwp, Byte, Boolean, Int, String, ReferenceTypeID

from thirdparty.sandbox.repl import Repl
import thirdparty.debug.dalvik
from thirdparty.debug.dalvik.util.adb import AdbObject
from thirdparty.debug.dalvik.util.native import NativeObject
from thirdparty.debug.dalvik.util.breakpoint import parse_dex_header, parse_vregs
from thirdparty.debug.dalvik.info.breakpoint import instruction_str
from thirdparty.debug.dalvik.info.state import *

# Utility imports
import pdb
from fuzzyfinder import fuzzyfinder
from pprint import pprint


# We're keeping jdwp, dbg, and dbg_state in global scope so
# they remain accessible to REPL mechanisms.
adb = AdbObject()
native = NativeObject()
class BreakpointObject(): pass
bp = BreakpointObject()
jdwp = None
dbg = thirdparty.debug.dalvik.Debugger()
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
5. Debugger attached to App via tcp:8700.
  - Standard Debugger initialization started.
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
    global bp

    # Start up the application in debug mode.
    adb.target('sh.kau.playground')

    # Connect to application native access.
    native.connect(adb)

    # Settle a bit.
    settle_timeout = 3
    print(f"Sleeping {settle_timeout} secs for system to settle.")
    await asyncio.sleep(settle_timeout)

    # Connect to application with our debugger.
    print("Connecting debugger to localhost:8700")
    await dbg.start('127.0.0.1', 8700)
    jdwp = dbg.jdwp
    dbg.print_summary()

    fetchQuote = dbg.create_breakpoint(**{
        'class_signature': 'Lsh/kau/playground/quoter/QuotesRepoImpl;',
        'method_name': 'fetchQuote',
        'method_signature': '(Lkotlin/coroutines/Continuation;)Ljava/lang/Object;',
    }, callback=None)
    bp.fetchQuote = fetchQuote
    await fetchQuote.set_breakpoint()

    quoteForTheDay = dbg.create_breakpoint(**{
        'class_signature': 'Lsh/kau/playground/quoter/QuotesRepoImpl;',
        'method_name': 'quoteForTheDay',
        'method_signature': '(Lkotlin/coroutines/Continuation;)Ljava/lang/Object;',
    }, callback=None)
    bp.quoteForTheDay = quoteForTheDay
    #await quoteForTheDay.set_breakpoint()

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


if __name__ == "__main__":
    asyncio.run(main_with_sandbox())
    




