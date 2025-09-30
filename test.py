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
import thirdparty.jvmdebugger
from thirdparty.jvmdebugger.state import *

from pydantic import BaseModel
from typing import Optional, List, Tuple

# Utility imports
import multiprocessing
import pdb
from fuzzyfinder import fuzzyfinder
from pprint import pprint


# Keep these in global scope for remote REPL accessibility.
jdwp = None

# Create debugger instance.
dbg = thirdparty.jvmdebugger.JvmDebugger()
# Save reference to state for potential hot reload.
dbg_state = dbg.state
   

async def main():
  global dbg
  global jdwp

  print("Connecting debugger to localhost:8700")
  await dbg.start('127.0.0.1', 8700)
  dbg.print_summary()
  await dbg.resume_vm()

  try:
    print("Waiting for events... Ctrl-C to quit.")
    while True:
      await asyncio.sleep(1)
  except KeyboardInterrupt:
    exit(0)


async def main_with_sandbox():
  __sandbox__.hot_reload_module(thirdparty.jvmdebugger)
  # Note: Need to send the globals() from this scope or we get the module's globals().
  sandbox_coro = __sandbox__.start_sandbox(
    repl_socket_path="/tmp/repl.sock", repl_namespace=globals(),
    exec_socket_path="/tmp/exec.sock", exec_namespace=globals(),
    #dict_socket_path="/tmp/dict.sock", dict_shared_dict=db,
  )
  sandbox_task = asyncio.create_task(sandbox_coro)
  # TODO: Consider a event handler for when hot reload occurs to actually update references?!
  main_task = asyncio.create_task(main())
  await asyncio.gather(sandbox_task, main_task)


def reload_dbg():
  global dbg
  global dbg_state
  dbg = thirdparty.jvmdebugger.JvmDebugger(dbg_state)


if __name__ == "__main__":
  asyncio.run(main_with_sandbox())




'''

pprint(list(fuzzyfinder('playground', dbg.classes_by_signature)))


async def dothing():
  await jdwp.VirtualMachine.Resume()
asyncio.get_event_loop().create_task(dothing())


async def dothing():
  dbg = thirdparty.jvmdebugger.JvmDebugger(dbg_state)
  await dbg.resume_vm2()
asyncio.get_event_loop().create_task(dothing())
'''










    # # Watch for new Throwable classes.
    # print("EventRequest.Set(CLASS_PREPARE)")
    # evt_req = jdwp.EventRequest.SetRequest()
    # evt_req.eventKind = Byte(Jdwp.EventKind.CLASS_PREPARE)
    # evt_req.suspendPolicy = Byte(Jdwp.SuspendPolicy.ALL)
    # print("  ClassMatch = \"java.lang.Throwable\"")
    # mod = jdwp.EventRequest.SetClassMatchModifier()
    # mod.classPattern = String("java.lang.Throwable")
    # evt_req.modifiers.append(mod)
    # mod = jdwp.EventRequest.SetCountModifier()
    # mod.count = Int(1)
    # evt_req.modifiers.append(mod)
    # throwable_reqid = await jdwp.EventRequest.Set(evt_req)
    # print(f" RequestID = {throwable_reqid}")


    # # print("EventRequest.Set(EXCEPTION)")
    # # evt_req = jdwp.EventRequest.SetRequest()
    # # evt_req.eventKind = Byte(Jdwp.EventKind.EXCEPTION)
    # # evt_req.suspendPolicy = Byte(Jdwp.SuspendPolicy.ALL)
    # # mod = jdwp.EventRequest.SetExceptionOnlyModifier()
    # # # TODO: Get this value from AllClassesWithGeneric ?
    # # mod.exceptionOrNull = ReferenceTypeID(0) #0x229
    # # mod.caught = Boolean(0)
    # # mod.uncaught = Boolean(0)
    # # evt_req.modifiers.append(mod)
    # # exception_reqid = await jdwp.EventRequest.Set(evt_req)


    # # print("EventRequest.Clear()")
    # # evt_req = jdwp.EventRequest.ClearRequest()
    # # evt_req.eventKind = Byte(EventKind.EXCEPTION)
    # # evt_req.requestID = exception_reqid
    # # await jdwp.EventRequest.Clear(evt_req)


    # # Get all current class paths.
    # print("VirtualMachine.ClassPaths()")
    # classpath_reply = await jdwp.VirtualMachine.ClassPaths()
    # for p in classpath_reply.classpaths:
    #   db['classpaths'][p] = True
    #   #print(f"  {p}")
    # print(f"  Classpaths: {len(db['classpaths'])}")
    # for p in classpath_reply.bootclasspaths:
    #   db['bootclasspaths'][p] = True
    #   #print(f"  {p}")
    # print(f"  BootClasspaths: {len(db['bootclasspaths'])}")


    # # print("VirtualMachine.Resume()")
    # # await jdwp.VirtualMachine.Resume()


'''
class Capabilities():
    pass

class Version():
  # print("VirtualMachine.Version()")
  # db['versions'] = versions
  # print(f"  description = {versions.description}")
  # print(f"  jdwpMajor = {versions.jdwpMajor}")
  # print(f"  jdwpMinor = {versions.jdwpMinor}")
  # print(f"  vmVersion = {versions.vmVersion}")
  # print(f"  vmName = {versions.vmName}")
  pass



class ModuleInfo():
    pass

class InstanceInfo():
    pass

class InterfaceInfo():
    pass

class FieldInfo():
    # values? ... via GetValues()

    # FieldAccess ??
    # FieldModification ??
    pass

class MethodInfo():
    pass



class GroupInfo():
    pass

class ObjectInfo():
    pass

class EventRequest():
    pass

class Breakpoint():
    pass

# suspended threads with lists of frames

class FrameInfo():
    pass
'''