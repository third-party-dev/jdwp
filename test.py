#!/usr/bin/env python3

'''
Consider:

pip install pure-python-adb
pip install androguard
pip install frida frida_tools
pip install pyaxml

'''

from thirdparty.jdwp import Jdwp, Byte, Boolean, Int, String, ReferenceTypeID
import asyncio
import pdb

db = {
    'class_by_generic': {},
    'class_by_signature': {},
    'class_by_typeid': {},
    'classpaths': {},
    'bootclasspaths': {},
    'threads': {},
}

async def main():
    global db

    jdwp = await Jdwp('localhost', 8700).start()

    await jdwp.VirtualMachine.Suspend()
    
    print("VirtualMachine.IDSizes()")
    idsizes = await jdwp.VirtualMachine.IDSizes()
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
    print(f"  description = {versions.description}")
    print(f"  jdwpMajor = {versions.jdwpMajor}")
    print(f"  jdwpMinor = {versions.jdwpMinor}")
    print(f"  vmVersion = {versions.vmVersion}")
    print(f"  vmName = {versions.vmName}")

    
    # Get all the current classes.
    print("VirtualMachine.AllClassesWithGeneric()")
    all_classes_reply = await jdwp.VirtualMachine.AllClassesWithGeneric()
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
    evt_req.suspendPolicy = Byte(Jdwp.SuspendPolicy.ALL)
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

    print("VirtualMachine.Resume()")
    await jdwp.VirtualMachine.Resume()

    try:
      print("Waiting for events... Ctrl-C to quit.")
      while True:
          await asyncio.sleep(1)
    except KeyboardInterrupt:
      exit(0)
        

asyncio.run(main())


'''
stop in sh.kau.playground.quoter.QuotesRepoImpl.quoteForTheDay
pkt 1 - 8

pkt 9 - 116 - actions

req
00000042 00001232 00 0f 01 08 02 00000002 
  - 05 00000027 73682e6b61752e706c617967726f756e642e71756f7465722e51756f7465735265706f496d706c
  - 01 00000001
EventRequest.Set(CLASS_PREPARE)

resp
0000000f 00001232 80 0000 0000000b - requestID

req
0000002b 00001234 00 0f 01 02 02 00000001 07 loc: 01 cls 00000000000055e1 meth 000072cbc9315488 off 0000000000000000
EventRequest.Set(BREAKPOINT)

req
00000010 00001236 00 0f 02 08 0000000b
EventRequest.Clear

req
00000013 000012d8 00 0b 07 00000000000065ec
ThreadReference.FrameCount

req
0000001b 000012da 00 0b 06 00000000000065ec0000000000000001
ThreadReference.Frames

req
00000013 000012dc 00 0b 01 00000000000065ec
ThreadReference.Name

req
0000000b 000012de 00 01 11
VirtualMachine.CapabilitiesNew

req
00000013 000012e0 00 02 0c 00000000000055e1
ReferenceType.SourceDebugExtension






resp 000012e0
tcp 000000000000000000000000080045000210fd11400040063dd47f0000017f00000121fcc2a480707ba298ac8e3780180200000500000101080a8b41fda58b41fda3 
data 000001dc000012e0800000000001cd534d41500a51756f7465735265706f496d706c2e6b740a4b6f746c696e0a2a53204b6f746c696e0a2a460a2b20312051756f7465735265706f496d706c2e6b740a73682f6b61752f706c617967726f756e642f71756f7465722f51756f7465735265706f496d706c0a2b2032206275696c646572732e6b740a696f2f6b746f722f636c69656e742f726571756573742f4275696c646572734b740a2b20332048747470436c69656e7443616c6c2e6b740a696f2f6b746f722f636c69656e742f63616c6c2f48747470436c69656e7443616c6c4b740a2b203420547970652e6b740a696f2f6b746f722f7574696c2f7265666c6563742f547970654b740a2a4c0a3123312c33333a310a33323923323a33340a32323223323a33350a393623322c323a33360a313923323a33380a31343223333a33390a353823342c31363a34300a2a53204b6f746c696e44656275670a2a460a2b20312051756f7465735265706f496d706c2e6b740a73682f6b61752f706c617967726f756e642f71756f7465722f51756f7465735265706f496d706c0a2a4c0a323723313a33340a323723313a33350a323723313a33362c320a323723313a33380a333023313a33390a333023313a34302c31360a2a450a

event
tcp 0000000000000000000000000800450002c4fd0c400040063d257f0000017f00000121fcc2a48070787f98ac8dd88018020000b900000101080a8b41fd8c8b41fd87 
data:

00000054 0000128d 00 40 64 00 00000001 08 

- 00000002 00000000000065ec 01 00000000000066db 00000026 4c696f2f6b746f722f687474702f436f6e74656e7454797065244170706c69636174696f6e3b 00000003

00000056 0000128e 00 40 64 00 00000001 08

- 00000002 00000000000065ec 01 00000000000066dc 00000028 4c696f2f6b746f722f687474702f48656164657256616c756557697468506172616d65746572733b 00000003

00000048 0000128f 00 40 64 00 00000001 08 

- 00000002 00000000000065ec 01 00000000000066dd 0000001a 4c696f2f6b746f722f687474702f436f6e74656e74547970653b 00000003

00000054 00001290 00 40 64 00 00000001 08

- 00000002 00000000000065ec 01 00000000000066de 00000026 4c696f2f6b746f722f687474702f487474704d65737361676550726f706572746965734b743b 00000003

00000047 00001291 00 40 64 00 00000001 08

- 00000002 00000000000065ec 01 00000000000066df 00000019 4c696f2f6b746f722f687474702f487474704d6574686f643b0000000300000051000012920040640000000001080000000200000000000065ec0100000000000066e0000000234c696f2f6b746f722f687474702f487474704d6574686f6424436f6d70616e696f6e3b0000000300000056000012930040640000000001080000000200000000000065ec0100000000000066e1000000284c696f2f6b746f722f636c69656e742f73746174656d656e742f4874747053746174656d656e743b000000030000005c000012940040640200000002020000000c00000000000065ec0100000000000055e1000072cbc93154880000000000000000020000000a00000000000065ec0100000000000055e1000072cbc93154880000000000000000










'''