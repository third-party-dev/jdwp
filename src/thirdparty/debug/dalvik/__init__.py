'''
Copyright (c) 2025 Vincent Agriesti

This file is part of the thirdparty JDWP project.
Licensed under the MIT License. See the LICENSE file in the project root
for full license text.
'''

import asyncio
from thirdparty.jdwp import (
    Jdwp, Byte, Boolean, Int, String, ReferenceTypeID, Location, 
    Long, ClassID, ObjectID, FrameID, MethodID)

from thirdparty.dalvik.dex import disassemble
from thirdparty.debug.dalvik.state import *
from thirdparty.debug.dalvik.breakpoint import BreakpointInfo
from thirdparty.debug.dalvik.thread import ThreadInfo
from thirdparty.debug.dalvik.object import ObjectInfo

import thirdparty.sandbox as __sandbox__
import typing

from pydantic import BaseModel
from typing import Optional, List, Tuple

import code

# Utility imports
import multiprocessing
import pdb
import threading
from fuzzyfinder import fuzzyfinder
from pprint import pprint


'''
    The TODO List:

    # Get list of ThreadInfo references
    await dbg.threads() -> List[ThreadInfo]

    # ThreadInfo - threadID, name?

    # Get number of stack frames (not cached).
    # Call this once and use "frames" as the local-only cache.
    # Store thread id in frameobject so you don't have to remember.
    frames = await dbg.frames(thread: ThreadInfo) -> FrameInfo

    # FrameInfo - threadID, frameID, location, values

    # Create ObjectInfo instance and gets fields and values.
    # Also has references to ClassInfo.MethodInfo for methods.

    objref = await dbg.deref(object_id) -> ObjectInfo

    # Used to show object fields and their values.
    # Note: If the value is an object, it'll be a 
    #       reference to another ObjectInfo
    await dbg.fields(obj: ObjectInfo)

    # ObjectInfo.getattr 
    await objref.field_one.field_two -> ObjectInfo

    # If we set an attribute, the types must match.
    # An object attribute can only be set to an ObjectInfo
    # Under the hood, its really being set to the objectID.
    # ObjectInfos should never be manually created. They are initialized
    #   by dbg.deref() and then subsequently filled out by getattr.
    # All ObjectInfo objects are referenced in a dict in dbg for
    # deduplication.

    # Used to list available methods.
    # Note: (Invoking isn't really a goal.)
    await dbg.methods(obj: ObjectInfo)
    # Consider: Call method by name plus sig as first param.
    # Example: objref.func("(L)V", objref)
'''



class JvmDebugger():

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
        self.objects_by_id = self.state.objects_by_id

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
        self.idsizes, _ = await self.jdwp.VirtualMachine.IDSizes()
        self.versions, _ = await self.jdwp.VirtualMachine.Version()

        # Always cache all prepared and unloaded classes
        await self.enable_class_prepare_events()
        await self.enable_class_unload_events()

        # Always cache all started and killed threads
        await self.enable_thread_start_events()
        await self.enable_thread_death_events()

        # Always get all current classes and threads
        print("Fetching all classes. This make take a moment.")
        await self.request_all_classes()
        await self.request_all_threads()
        print("Done fetching classes.")


    def object_info(self, object_id):
        if object_id in self.objects_by_id:
            return self.objects_by_id[object_id]
        return ObjectInfo(self, object_id)


    async def deref(self, obj):
        """Given an object_id or ObjectInfo, returns a dereferenced
           version in the form of a loaded ObjectInfo instance.

          Args:
            obj (int): Object ID.
            obj (ObjectInfo): ObjectInfo instance.

          Returns: Loaded ObjectInfo()
        """
        if not isinstance(obj, ObjectInfo):
            obj = self.object_info(obj)
        return await obj.load()


    


    async def enable_class_prepare_events(self):
        # Watch for new classes.
        #print("EventRequest.Set(CLASS_PREPARE / NO_SUSPEND)")
        evt_req = self.jdwp.EventRequest.SetRequest()
        evt_req.eventKind = Byte(Jdwp.EventKind.CLASS_PREPARE)
        evt_req.suspendPolicy = Byte(Jdwp.SuspendPolicy.NONE)
        # No modifiers.
        self.class_prepare_reqid, error_code = await self.jdwp.EventRequest.Set(evt_req)
        if error_code != Jdwp.Error.NONE:
            print(f"ERROR: Failed to enable class prepare events: {Jdwp.Error.string[error_code]}")
            return
        #print(f"enable_class_prepare_events RequestID = {self.class_prepare_reqid}")

        self.jdwp.register_event_handler(self.class_prepare_reqid, JvmDebugger.handle_class_prepare, self)


    async def enable_class_unload_events(self):
        # Watch for removed classes.
        #print("EventRequest.Set(CLASS_UNLOAD)")
        evt_req = self.jdwp.EventRequest.SetRequest()
        evt_req.eventKind = Byte(Jdwp.EventKind.CLASS_UNLOAD)
        evt_req.suspendPolicy = Byte(Jdwp.SuspendPolicy.NONE)
        # No modifiers.
        self.class_unload_reqid, error_code = await self.jdwp.EventRequest.Set(evt_req)
        if error_code != Jdwp.Error.NONE:
            print(f"ERROR: Failed to enable class unload events: {Jdwp.Error.string[error_code]}")
            return
        #print(f"enable_class_unload_events RequestID = {self.class_unload_reqid}")

        async def handle_class_unload(event, composite, wp):
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
        self.thread_start_reqid, error_code = await self.jdwp.EventRequest.Set(evt_req)
        if error_code != Jdwp.Error.NONE:
            print(f"ERROR: Failed to enable thread start events: {Jdwp.Error.string[error_code]}")
            return
        #print(f"enable_thread_start_events RequestID = {self.thread_start_reqid}")

        async def handle_thread_start(event, composite, wp):
            # TODO: Do we check if it already existed?
            threadInfo = ThreadInfo(self, event.thread)
            # TODO: Do we see if it already exists first?
            self.threads_by_id[threadInfo.threadID] = threadInfo
            #print(f"THREAD_START: {threadInfo.threadID}")

        self.jdwp.register_event_handler(self.thread_start_reqid, handle_thread_start)


    async def enable_thread_death_events(self):
        evt_req = self.jdwp.EventRequest.SetRequest()
        evt_req.eventKind = Byte(Jdwp.EventKind.THREAD_DEATH)
        evt_req.suspendPolicy = Byte(Jdwp.SuspendPolicy.NONE)
        self.thread_death_reqid, error_code = await self.jdwp.EventRequest.Set(evt_req)
        if error_code != Jdwp.Error.NONE:
            print(f"ERROR: Failed to enable thread death events: {Jdwp.Error.string[error_code]}")
            return
        #print(f"enable_thread_death_events RequestID = {self.thread_death_reqid}")

        async def handle_thread_death(event, composite, wp):

            # TODO: Do we check if it already existed?
            if event.thread in self.threads_by_id:
                threadInfo = self.threads_by_id[event.thread]
                self.threads_by_id.pop(threadInfo.threadID, None)
                self.dead_threads.append(threadInfo)
                # TODO: Implement way to show first A chars and last B chars in X width.
                #print(f"THREAD_DEATH: {threadInfo.threadID}")

        self.jdwp.register_event_handler(self.thread_death_reqid, handle_thread_death)


    async def disable_class_prepare_event(self, request_id):
        evt_req = self.jdwp.EventRequest.ClearRequest()
        evt_req.eventKind = Byte(Jdwp.EventKind.CLASS_PREPARE)
        evt_req.requestID = request_id
        await self.jdwp.EventRequest.Clear(evt_req)

    

    async def disable_breakpoint_event(self, request_id):
        evt_req = self.jdwp.EventRequest.ClearRequest()
        evt_req.eventKind = Byte(Jdwp.EventKind.BREAKPOINT)
        evt_req.requestID = request_id
        await self.jdwp.EventRequest.Clear(evt_req)

    async def disable_step_event(self, request_id):
        evt_req = self.jdwp.EventRequest.ClearRequest()
        evt_req.eventKind = Byte(Jdwp.EventKind.SINGLE_STEP)
        evt_req.requestID = request_id
        await self.jdwp.EventRequest.Clear(evt_req)


    


    async def load_method_bytecode(self, classID, methodID):

        if classID in self.classes_by_id:
            classInfo = self.classes_by_id[classID]
            if methodID in classInfo.methods_by_id:
                methodInfo = classInfo.methods_by_id[methodID]

                if not methodInfo.bytecode:
                    req = self.jdwp.Method.BytecodesRequest()
                    req.refType = ReferenceTypeID(classID)
                    req.methodID = methodID
                    reply, error_code = await self.jdwp.Method.Bytecodes(req)
                    if error_code != Jdwp.Error.NONE:
                        print(f"ERROR: Failed to fetch bytecode: {Jdwp.Error.string[error_code]}")
                        return
                    methodInfo.bytecode = reply.bytecodes
        
                return methodInfo.bytecode

        return None


    


    def create_breakpoint(self, **kwargs):
        """Create object to manage immediate and deferred breakpoint.

        Args:
            class_signature (str): JVM/JNI Class Signature
            method_name (str): Name of method to break within.
            method_signature (str): JVM/JNI of specific method to break within.
            callback: Awaited async callback on breakpoint event.
                      `async def callback(event, composite, args) -> None`
            bytecode_index (int): 16bit aligned offset into method to break at.
            count (int): Number of times to pass breakpoint without breaking.

        Returns:
            BreakpointInfo: Breakpoint Object. Run `await obj.set_breakpoint()` to activate!
        """

        if 'class_signature' not in kwargs or \
           'method_name' not in kwargs or \
           'method_signature' not in kwargs or \
           not kwargs['class_signature'] or \
           not kwargs['method_name'] or \
           not kwargs['method_signature']:
            raise RuntimeError("Must have class_signature, method_name, and method_signature set for breakpoint.")

        return BreakpointInfo(self, **kwargs)


    @staticmethod
    async def handle_class_prepare(event, composite, dbg):
        """Callback for JvmDebugger.enable_class_prepare_events()"""
        if event.typeID not in dbg.classes_by_id:

            # Unloaded until we think we'll deref.
            # TODO: Consider registering for generic event too.
            dbg.classes_by_id[event.typeID] = dbg.create_class_info(\
                event.typeID,
                typeTag=event.refTypeTag,
                signature=event.signature)

            # classInfo = ClassInfo()
            # classInfo.refTypeTag = event.refTypeTag
            # classInfo.typeID = event.typeID
            # classInfo.signature = event.signature
            # #classInfo.generic = # TODO: Is there an event with class prepare with generic?
            # # TODO: Do we see if it already exists first?
            # dbg.classes_by_id[classInfo.typeID] = classInfo
            # dbg.classes_by_signature[classInfo.signature] = classInfo
            # # TODO: Implement way to show first A chars and last B chars in X width.
            # #print(f"CLASS_PREPARE: {classInfo.signature[:60]}")


    async def request_all_classes(self):
        #print("VirtualMachine.AllClassesWithGeneric()")
        all_classes_reply, error_code = await self.jdwp.VirtualMachine.AllClassesWithGeneric()
        if error_code != Jdwp.Error.NONE:
            print(f"ERROR: Failed to fetch all classes: {Jdwp.Error.string[error_code]}")
            return

        #db['all_classes_reply1'] = all_classes_reply
        #i = 0
        for clazz in all_classes_reply.classes:

            # Unloaded until we think we'll deref.
            self.classes_by_id[clazz.typeID] = self.create_class_info(\
                clazz.typeID,
                typeTag=clazz.refTypeTag,
                signature=clazz.signature,
                generic=clazz.genericString)

            # classInfo = ClassInfo()
            # classInfo.refTypeTag = clazz.refTypeTag
            # classInfo.typeID = clazz.typeID
            # classInfo.signature = clazz.signature
            # classInfo.generic = clazz.genericString
            # # TODO: Do we see if it already exists first?
            # self.classes_by_id[classInfo.typeID] = classInfo
            # self.classes_by_signature[classInfo.signature] = classInfo        
        

    async def get_class_id(self, object_id):
        # Get the object type
        reftype_reply, error_code = await self.jdwp.ObjectReference.ReferenceType(ObjectID(object_id))
        if error_code != Jdwp.Error.NONE:
            print(f"ERROR: Failed to get object type: {Jdwp.Error.string[error_code]}")
            return None

        return reftype_reply.typeID


    async def get_super_id(self, class_id):
        # Is there a super class?
        super_class_id, error_code = await self.jdwp.ClassType.Superclass(ClassID(class_id))
        if error_code != Jdwp.Error.NONE:
            print(f"ERROR: Failed to get superclass: {Jdwp.Error.string[error_code]}")
            return None
        return super_class_id



    def create_class_info(self, typeID, typeTag=None, signature=None, generic=None):
        if typeID in self.classes_by_id:
            return

        class_info = ClassInfo(self, typeID)

        if typeTag:
            class_info.refTypeTag = typeTag

        if signature:
            class_info.signature = signature

        if generic:
            class_info.generic = generic

        return class_info


    async def class_info(self, clazz):
        clazz_orig = clazz
        if isinstance(clazz, int):
            clazz = self.classes_by_id[clazz]
        return await clazz.load()

    
    async def string(self, object_id):
        value, error_code = await self.jdwp.StringReference.IsCollected(ObjectID(object_id))
        if error_code != Jdwp.Error.NONE:
            print(f"ERROR: Failed to get string value: {Jdwp.Error.string[error_code]}")
            return None
        return value


    async def request_all_threads(self):
        thread_reply, error_code = await self.jdwp.VirtualMachine.AllThreads()
        if error_code != Jdwp.Error.NONE:
            print(f"ERROR: Failed to get all threads: {Jdwp.Error.string[error_code]}")
            return
        for thread_id in thread_reply.threads:
            # Caches itself in constructor.
            # Note: We don't load threads until we break.
            ThreadInfo(self, thread_id)


    async def resume_vm(self):
        """Resume VM"""
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


    async def thread(self, thread):
        # Only call when broke.
        if not isinstance(thread, ThreadInfo):
            try:
                thread = self.threads_by_id[thread]
            except KeyError:
                thread = ThreadInfo(self, thread)

        return await thread.load()


    async def frame(self, thread, frame=0):
        # Only call when broke.
        # thread can be ID or ThreadInfo
        if not isinstance(thread, ThreadInfo):
            thread = await self.thread(thread)
        return await thread.frame(frame)


    # Note: async def slot() is not useful at the moment.

    async def get_object_class_info(self, object_id):
        # Get the object type
        reftype_reply, error_code = await self.jdwp.ObjectReference.ReferenceType(ObjectID(object_id))
        if error_code != Jdwp.Error.NONE:
            print(f"ERROR: Failed to get object type: {Jdwp.Error.string[error_code]}")
            return

        # Get the class_info
        if reftype_reply.typeID not in self.classes_by_id:
            print(f"ERROR: Class id not found: {reftype_reply.typeID}")
            return

        return self.classes_by_id[reftype_reply.typeID]
    
