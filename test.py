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

# Utility imports
import multiprocessing
import pdb
from fuzzyfinder import fuzzyfinder
from pprint import pprint

db = {}
# TODO: This is not working.
#db = multiprocessing.Manager().dict()
db['class_by_generic'] = {}
db['class_by_signature'] = {}
db['class_by_typeid'] = {}
db['classpaths'] = {}
db['bootclasspaths'] = {}
db['threads'] = {}
db2 = db

jdwp = None

def handle_class_prepare(event, composite, wp):
    print(f"In event handler: {event}")

async def main():
    global db
    global jdwp

    print("Connecting to JDWP endpoint: localhost:8700")
    jdwp = await Jdwp('localhost', 8700).start()

    await jdwp.VirtualMachine.Suspend()
    
    print("VirtualMachine.IDSizes()")
    idsizes = await jdwp.VirtualMachine.IDSizes()
    db['idsizes'] = idsizes
    print(f"  fieldIDSize = {idsizes.fieldIDSize}")
    print(f"  methodIDSize = {idsizes.methodIDSize}")
    print(f"  objectIDSize = {idsizes.objectIDSize}")
    print(f"  referenceTypeIDSize = {idsizes.referenceTypeIDSize}")
    print(f"  frameIDSize = {idsizes.frameIDSize}")


    # Watch for new classes.
    print("EventRequest.Set(CLASS_PREPARE)")
    evt_req = jdwp.EventRequest.SetRequest()
    evt_req.eventKind = Byte(Jdwp.EventKind.CLASS_PREPARE)
    evt_req.suspendPolicy = Byte(Jdwp.SuspendPolicy.NONE)
    # No modifiers.
    class_prepare_reqid = await jdwp.EventRequest.Set(evt_req)
    print(f" RequestID = {class_prepare_reqid}")

    jdwp.register_event_handler(class_prepare_reqid, handle_class_prepare)


    # Watch for removed classes.
    print("EventRequest.Set(CLASS_UNLOAD)")
    evt_req = jdwp.EventRequest.SetRequest()
    evt_req.eventKind = Byte(Jdwp.EventKind.CLASS_UNLOAD)
    evt_req.suspendPolicy = Byte(Jdwp.SuspendPolicy.NONE)
    # No modifiers.
    class_unload_reqid = await jdwp.EventRequest.Set(evt_req)
    print(f" RequestID = {class_unload_reqid}")


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


    print("VirtualMachine.Version()")
    versions = await jdwp.VirtualMachine.Version()
    db['versions'] = versions
    print(f"  description = {versions.description}")
    print(f"  jdwpMajor = {versions.jdwpMajor}")
    print(f"  jdwpMinor = {versions.jdwpMinor}")
    print(f"  vmVersion = {versions.vmVersion}")
    print(f"  vmName = {versions.vmName}")

    
    # Get all the current classes.
    print("VirtualMachine.AllClassesWithGeneric()")
    all_classes_reply = await jdwp.VirtualMachine.AllClassesWithGeneric()
    db['all_classes_reply1'] = all_classes_reply
    i = 0
    for clazz in all_classes_reply.classes:
        db['class_by_typeid'][clazz.typeID] = clazz
        db['class_by_signature'][clazz.signature] = clazz
        db['class_by_generic'][clazz.genericString] = clazz

        if "playground" in clazz.signature:
          print(f"  {clazz.signature}")
          print(f"    refTypeTag = {clazz.refTypeTag}")
          print(f"    typeID = {clazz.typeID}")
          print(f"    signature = {clazz.signature}")
          print(f"    genericString = {clazz.genericString}")
          print(f"    status = {clazz.status}")
    print(f"  Classes returned: {len(all_classes_reply.classes)}")


    # print("EventRequest.Set(EXCEPTION)")
    # evt_req = jdwp.EventRequest.SetRequest()
    # evt_req.eventKind = Byte(Jdwp.EventKind.EXCEPTION)
    # evt_req.suspendPolicy = Byte(Jdwp.SuspendPolicy.ALL)
    # mod = jdwp.EventRequest.SetExceptionOnlyModifier()
    # # TODO: Get this value from AllClassesWithGeneric ?
    # mod.exceptionOrNull = ReferenceTypeID(0) #0x229
    # mod.caught = Boolean(0)
    # mod.uncaught = Boolean(0)
    # evt_req.modifiers.append(mod)
    # exception_reqid = await jdwp.EventRequest.Set(evt_req)

    # print("EventRequest.Clear()")
    # evt_req = jdwp.EventRequest.ClearRequest()
    # evt_req.eventKind = Byte(EventKind.EXCEPTION)
    # evt_req.requestID = exception_reqid
    # await jdwp.EventRequest.Clear(evt_req)


    # Watch for new threads.
    print("EventRequest.Set(THREAD_START)")
    evt_req = jdwp.EventRequest.SetRequest()
    evt_req.eventKind = Byte(Jdwp.EventKind.THREAD_START)
    #evt_req.suspendPolicy = Byte(Jdwp.SuspendPolicy.ALL)
    evt_req.suspendPolicy = Byte(Jdwp.SuspendPolicy.NONE)
    # No modifiers
    thread_start_reqid = await jdwp.EventRequest.Set(evt_req)
    print(f"  RequestID = {thread_start_reqid}")


    # Watch for removed threads.
    print("EventRequest.Set(THREAD_DEATH)")
    evt_req = jdwp.EventRequest.SetRequest()
    evt_req.eventKind = Byte(Jdwp.EventKind.THREAD_DEATH)
    evt_req.suspendPolicy = Byte(Jdwp.SuspendPolicy.ALL)
    # No modifiers
    thread_death_reqid = await jdwp.EventRequest.Set(evt_req)
    print(f"  RequestID = {thread_death_reqid}")


    # Get all current class paths.
    print("VirtualMachine.ClassPaths()")
    classpath_reply = await jdwp.VirtualMachine.ClassPaths()
    for p in classpath_reply.classpaths:
      db['classpaths'][p] = True
      #print(f"  {p}")
    print(f"  Classpaths: {len(db['classpaths'])}")
    for p in classpath_reply.bootclasspaths:
      db['bootclasspaths'][p] = True
      #print(f"  {p}")
    print(f"  BootClasspaths: {len(db['bootclasspaths'])}")


    # Get all the current threads.
    print("VirtualMachine.AllThreads()")
    thread_reply = await jdwp.VirtualMachine.AllThreads()
    print("Threads:")
    for t in thread_reply.threads:
      db['threads'][t] = True
    print(f"  Threads: {len(db['threads'])}")

    # print("VirtualMachine.Resume()")
    # await jdwp.VirtualMachine.Resume()

    try:
      print("Waiting for events... Ctrl-C to quit.")
      while True:
          await asyncio.sleep(1)
    except KeyboardInterrupt:
      exit(0)


async def main_with_sandbox():
    global db
    # Note: Need to send the globals() from this scope or we get the module's globals().
    sandbox_coro = __sandbox__.start_sandbox(
        repl_socket_path="/tmp/repl.sock", repl_namespace=globals(),
        exec_socket_path="/tmp/exec.sock", exec_namespace=globals(),
        dict_socket_path="/tmp/dict.sock", dict_shared_dict=db,
    )
    sandbox_task = asyncio.create_task(sandbox_coro)
    main_task = asyncio.create_task(main())
    await asyncio.gather(sandbox_task, main_task)


if __name__ == "__main__":
    asyncio.run(main_with_sandbox())



'''
async def dothing():
  await jdwp.VirtualMachine.Resume()
asyncio.get_event_loop().create_task(dothing())
'''