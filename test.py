#!/usr/bin/env python3

'''
Consider:

pip install pure-python-adb
pip install androguard
pip install frida frida_tools
pip install pyaxml

'''

import asyncio
from thirdparty.jdwp import Jdwp, Byte, Boolean, Int, String, ReferenceTypeID
import thirdparty.sandbox as __sandbox__
from thirdparty.sandbox.repl import Repl
import thirdparty.debug.dalvik
from thirdparty.debug.dalvik.state import *
from pydantic import BaseModel
from typing import Optional, List, Tuple

# Utility imports
import multiprocessing
import pdb
from fuzzyfinder import fuzzyfinder
from pprint import pprint

'''
adb shell am set-debug-app -w sh.kau.playground ; \
  adb shell am start \
    -n $(adb shell cmd package resolve-activity \
      -c android.intent.category.LAUNCHER sh.kau.playground | \
        grep -oP 'name=\K\S+' | head -n 1 | \
          sed -s 's/sh.kau.playground/sh.kau.playground\//') ; \
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

class DumbObject():
    def __repr__(self):
        return '\n'.join(self.__dict__.keys())

async def __thirdparty_sandbox_async_def(): pass

# We're keeping jdwp, dbg, and dbg_state in global scope so
# they remain accessible to REPL mechanisms.
jdwp = None
dbg = thirdparty.debug.dalvik.Debugger()
dbg_state = dbg.state

bp = DumbObject()

async def main():
    global dbg
    global jdwp
    global bp

    print("Connecting debugger to localhost:8700")
    await dbg.start('127.0.0.1', 8700)
    jdwp = dbg.jdwp
    dbg.print_summary()

    async def handle_breakpoint(event, composite, args):
        bp, = args
        print(f"{bp.location_str(event)}")
        
        await bp.wait()
        await bp.dbg.resume_vm()

    bp.fetchQuote = dbg.create_breakpoint(**{
        'class_signature': 'Lsh/kau/playground/quoter/QuotesRepoImpl;',
        'method_name': 'fetchQuote',
        'method_signature': '(Lkotlin/coroutines/Continuation;)Ljava/lang/Object;',
    }, callback=None)
    await bp.fetchQuote.set_breakpoint()

    bp.quoteForTheDay = dbg.create_breakpoint(**{
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
    dbg = thirdparty.debug.dalvik.Debugger(dbg_state)


if __name__ == "__main__":
    asyncio.run(main_with_sandbox())


'''

    ##### Misc Notes #####


    pprint(list(fuzzyfinder('playground', dbg.classes_by_signature)))


    # Watch for new Throwable classes.
    print("EventRequest.Set(CLASS_PREPARE)")
    evt_req = jdwp.EventRequest.SetRequest()
    evt_req.eventKind = Byte(Jdwp.EventKind.CLASS_PREPARE)
    evt_req.suspendPolicy = Byte(Jdwp.SuspendPolicy.ALL)
    print("  ClassMatch = \"java.lang.Throwable\"")
    mod = jdwp.EventRequest.SetClassMatchModifier()
    mod.classPattern = String("java.lang.Throwable")
    evt_req.modifiers.append(mod)
    mod = jdwp.EventRequest.SetCountModifier()
    mod.count = Int(1)
    evt_req.modifiers.append(mod)
    throwable_reqid = await jdwp.EventRequest.Set(evt_req)
    print(f" RequestID = {throwable_reqid}")

'''


