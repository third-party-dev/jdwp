import asyncio
from thirdparty.jdwp import Jdwp, Byte, Boolean, Int, String, ReferenceTypeID

from thirdparty.jvmdebugger.state import *

import thirdparty.sandbox as __sandbox__

from pydantic import BaseModel
from typing import Optional, List, Tuple

# Utility imports
import multiprocessing
import pdb
from fuzzyfinder import fuzzyfinder
from pprint import pprint


class JvmDebugger():
  #threads_by_id = {}

  def __init__(self, state=None):
    if state:
      self.state = state
    else:
      self.state = JvmDebuggerState()

    self.jdwp = self.state.jdwp
    self.classes_by_id = self.state.classes_by_id
    self.classes_by_signature = self.state.classes_by_signature
    self.unloaded_classes = self.state.unloaded_classes
    self.threads_by_id = self.state.threads_by_id
    self.dead_threads = self.state.dead_threads

    # TODO: Consider the event handlers. We won't automatically hot reload them.


  async def start(self, host, port):
    # TODO: unwind this with JdmDebuggerState
    if self.state.jdwp is None:
        self.state.jdwp = Jdwp(host, port)
        self.jdwp = self.state.jdwp
    await self.jdwp.start()

    # Always immediately suspend VM
    await self.jdwp.VirtualMachine.Suspend()

    # Always need idsizes and version information
    # TODO: Implement actually using these ... assuming always 64bit atm.
    self.idsizes = await self.jdwp.VirtualMachine.IDSizes()
    self.versions = await self.jdwp.VirtualMachine.Version()
    
    # Always cache all prepared and unloaded classes
    await self.enable_class_prepare_events()
    await self.enable_class_unload_events()

    # Always cache all started and killed threads
    await self.enable_thread_start_events()
    await self.enable_thread_death_events()

    # Always get all current classes and threads
    await self.request_all_classes()
    await self.request_all_threads()


  async def enable_class_prepare_events(self):
    # Watch for new classes.
    #print("EventRequest.Set(CLASS_PREPARE / NO_SUSPEND)")
    evt_req = self.jdwp.EventRequest.SetRequest()
    evt_req.eventKind = Byte(Jdwp.EventKind.CLASS_PREPARE)
    evt_req.suspendPolicy = Byte(Jdwp.SuspendPolicy.NONE)
    # No modifiers.
    self.class_prepare_reqid = await self.jdwp.EventRequest.Set(evt_req)
    #print(f" RequestID = {class_prepare_reqid}")

    def handle_class_prepare(event, composite, wp):
      #print(f"In handle_class_prepare: {event}")
      # TODO: Do we check if it already existed?
      
      classInfo = ClassInfo()
      classInfo.refTypeTag = event.refTypeTag
      classInfo.typeID = event.typeID
      classInfo.signature = event.signature
      #classInfo.generic = # TODO: Is there an event with class prepare with generic?
      # TODO: Do we see if it already exists first?
      self.classes_by_id[classInfo.typeID] = classInfo
      self.classes_by_signature[classInfo.signature] = classInfo
      # TODO: Implement way to show first A chars and last B chars in X width.
      print(f"CLASS_PREPARE: {classInfo.signature[:60]}")

    self.jdwp.register_event_handler(self.class_prepare_reqid, handle_class_prepare)


  async def request_all_classes(self):
    #print("VirtualMachine.AllClassesWithGeneric()")
    all_classes_reply = await self.jdwp.VirtualMachine.AllClassesWithGeneric()

    #db['all_classes_reply1'] = all_classes_reply
    #i = 0
    for clazz in all_classes_reply.classes:
        classInfo = ClassInfo()
        classInfo.refTypeTag = clazz.refTypeTag
        classInfo.typeID = clazz.typeID
        classInfo.signature = clazz.signature
        classInfo.generic = clazz.genericString
        # TODO: Do we see if it already exists first?
        self.classes_by_id[classInfo.typeID] = classInfo
        self.classes_by_signature[classInfo.signature] = classInfo        
    #print(f"  Classes returned: {len(dbg.classes_by_id)}")


  async def enable_class_unload_events(self):
    # Watch for removed classes.
    #print("EventRequest.Set(CLASS_UNLOAD)")
    evt_req = self.jdwp.EventRequest.SetRequest()
    evt_req.eventKind = Byte(Jdwp.EventKind.CLASS_UNLOAD)
    evt_req.suspendPolicy = Byte(Jdwp.SuspendPolicy.NONE)
    # No modifiers.
    self.class_unload_reqid = await self.jdwp.EventRequest.Set(evt_req)
    #print(f" RequestID = {class_unload_reqid}")

    def handle_class_unload(event, composite, wp):
      #print(f"In handle_class_prepare: {event}")
      # TODO: Do we check if it already existed?
      
      if event.signature in self.classes_by_signature:
        classInfo = self.classes_by_signature[event.signature]
        self.classes_by_signature.pop(event.signature, None)
        self.classes_by_id.pop(classInfo.typeID, None)
        self.unloaded_classes.append(classInfo)
        # TODO: Implement way to show first A chars and last B chars in X width.
        print(f"CLASS_UNLOAD: {classInfo.signature[:60]}")

    self.jdwp.register_event_handler(self.class_unload_reqid, handle_class_unload)


  async def enable_thread_start_events(self):
    # Watch for removed classes.
    evt_req = self.jdwp.EventRequest.SetRequest()
    evt_req.eventKind = Byte(Jdwp.EventKind.THREAD_START)
    #evt_req.suspendPolicy = Byte(Jdwp.SuspendPolicy.ALL)
    evt_req.suspendPolicy = Byte(Jdwp.SuspendPolicy.NONE)
    # No modifiers.
    self.thread_start_reqid = await self.jdwp.EventRequest.Set(evt_req)
    #print(f" RequestID = {class_unload_reqid}")

    def handle_thread_start(event, composite, wp):
      #print(f"In handle_class_prepare: {event}")
      # TODO: Do we check if it already existed?
      threadInfo = ThreadInfo()
      threadInfo.threadID = event.thread
      # TODO: Do we see if it already exists first?
      self.threads_by_id[threadInfo.threadID] = threadInfo
      print(f"THREAD_START: {threadInfo.threadID}")

    self.jdwp.register_event_handler(self.thread_start_reqid, handle_thread_start)


  async def enable_thread_death_events(self):
    evt_req = self.jdwp.EventRequest.SetRequest()
    evt_req.eventKind = Byte(Jdwp.EventKind.THREAD_DEATH)
    evt_req.suspendPolicy = Byte(Jdwp.SuspendPolicy.NONE)
    self.thread_death_reqid = await self.jdwp.EventRequest.Set(evt_req)

    def handle_thread_death(event, composite, wp):
      #print(f"In handle_class_prepare: {event}")
      # TODO: Do we check if it already existed?
      
      if event.thread in self.threads_by_id:
        threadInfo = self.threads_by_id[event.thread]
        self.threads_by_id.pop(threadInfo.threadID, None)
        self.dead_threads.append(threadInfo)
        # TODO: Implement way to show first A chars and last B chars in X width.
        print(f"THREAD_DEATH: {threadInfo.threadID}")

    self.jdwp.register_event_handler(self.thread_death_reqid, handle_thread_death)


  async def request_all_threads(self):
    thread_reply = await self.jdwp.VirtualMachine.AllThreads()
    for t in thread_reply.threads:
      threadInfo = ThreadInfo()
      threadInfo.threadID = t
      self.threads_by_id[threadInfo.threadID] = threadInfo


  async def resume_vm(self):
    await self.jdwp.VirtualMachine.Resume()


  def print_summary(self):
    print("")
    print("-- VM Info --")  
    print(f"Description: {self.versions.description}")
    print(f"JDWP Version: {self.versions.jdwpMajor}.{self.versions.jdwpMinor}")
    print(f"VM Version: {self.versions.vmVersion}")
    print(f"VM Name: {self.versions.vmName}")
    print("")
    print("-- Cache Info --")
    print(f"Class Count: {len(self.classes_by_id)}")
    print(f"Thread Count: {len(self.classes_by_id)}")
