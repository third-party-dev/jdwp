import asyncio
from thirdparty.jdwp import Jdwp, Byte, Boolean, Int, String, ReferenceTypeID, Location, Long, ClassID, ObjectID

from thirdparty.dalvik.dex import disassemble
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


    async def disable_class_prepare_event(self, request_id):
        evt_req = self.jdwp.EventRequest.ClearRequest()
        evt_req.eventKind = Byte(Jdwp.EventKind.CLASS_PREPARE)
        evt_req.requestID = request_id
        await self.jdwp.EventRequest.Clear(evt_req)
        print(f"Cleared {request_id} CLASS_PREPARE event.")


    @staticmethod
    async def handle_class_prepare(event, composite, dbg):
        if event.typeID not in dbg.classes_by_id:
            classInfo = ClassInfo()
            classInfo.refTypeTag = event.refTypeTag
            classInfo.typeID = event.typeID
            classInfo.signature = event.signature
            #classInfo.generic = # TODO: Is there an event with class prepare with generic?
            # TODO: Do we see if it already exists first?
            dbg.classes_by_id[classInfo.typeID] = classInfo
            dbg.classes_by_signature[classInfo.signature] = classInfo
            # TODO: Implement way to show first A chars and last B chars in X width.
            #print(f"CLASS_PREPARE: {classInfo.signature[:60]}")


    async def update_class_methods(self, classID: ReferenceTypeID):
        methods_reply, _ = await self.jdwp.ReferenceType.Methods(classID)
        
        # TODO: Potential KeyError
        classInfo = self.classes_by_id[classID]

        for method in methods_reply.declared:
            methodInfo = MethodInfo()
            methodInfo.methodID = method.methodID
            methodInfo.name = method.name
            methodInfo.signature = method.signature
            methodInfo.modBits = method.modBits

            print(f"METHOD SIGNATURE {methodInfo.methodID}:  {methodInfo.name}  {methodInfo.signature}")
        
            # TODO: Verify it doesn't already exist?
            classInfo.methods_by_id[methodInfo.methodID] = methodInfo
            # Note: method name or signature may be ambiguous.
            method_signature = (methodInfo.name, methodInfo.signature)
            print(f"Inserting method_signature {method_signature}")
            classInfo.methods_by_signature[method_signature] = methodInfo


    @staticmethod
    async def handle_breakpoint_event(event, composite, args):
        print(f"Breakpoint: {event}")
        dbg, = args
        # event.requestID
        # event.thread
        # event.location

        # req = dbg.jdwp.Method.BytecodesRequest()
        # req.refType = ReferenceTypeID(event.location.classID)
        # req.methodID = event.location.methodID
        # reply, _ = await dbg.jdwp.Method.Bytecodes(req)

        # TODO: Consider getting the bytecodes on CLASS_PREPARE.

        # offset = 0
        # prev_offset = -1
        # ins_idx = 0
        # while offset < len(example_bytecodes) and offset != prev_offset:
        #     prev_offset = offset
        #     ins, offset = disassemble(example_bytecodes, offset)
        #     ins_bytecode = bytes(example_bytecodes[prev_offset:offset]).hex()
        #     ins_bytecode_idx = f'{int(prev_offset/2):04x}'
        #     print(f'{ins_idx}: {ins_bytecode_idx}: {ins} [bytecode: {ins_bytecode}]')
        #     ins_idx += 1

        # Example: dbg.step_into(event.thread)
        await dbg.step_over(event.thread)
        #breakpoint()
        await dbg.resume_vm()
        # for byt in reply.bytecodes:
        #     print(byt)
        #     breakpoint()

    async def load_method_bytecode(self, classID, methodID):

        if classID in self.classes_by_id:
            classInfo = self.classes_by_id[classID]
            if methodID in classInfo.methods_by_id:
                methodInfo = classInfo.methods_by_id[methodID]

                if not methodInfo.bytecode:
                    req = self.jdwp.Method.BytecodesRequest()
                    req.refType = ReferenceTypeID(classID)
                    req.methodID = methodID
                    reply, _ = await self.jdwp.Method.Bytecodes(req)
                    methodInfo.bytecode = reply.bytecodes
        
                return methodInfo.bytecode

        return None

    async def load_class_fields(self, classID):
        if classID in self.classes_by_id:
            classInfo = self.classes_by_id[classID]

            if not classInfo.fields_loaded:
                fields_reply, error_code = await self.jdwp.ReferenceType.Fields(ReferenceTypeID(classID))
                if error_code != 0:
                    return
                for entry in fields_reply.declared:
                    field = FieldInfo()
                    field.fieldID = entry.fieldID
                    field.name = entry.name
                    field.signature = entry.signature
                    field.modBits = entry.modBits
                    classInfo.fields_by_id[field.fieldID] = field
                    classInfo.fields_by_signature[(field.name, field.signature)] = field
                    #print(f"CLASS({classID}) FIELD: {entry}")
                classInfo.fields_loaded = True


    @staticmethod
    async def handle_step_event(event, composite, args):
        print(f"Got step event: {event}")
        
        dbg, = args

        bytecode = await dbg.load_method_bytecode(
            event.location.classID, event.location.methodID)

        offset = event.location.index * 2
        prev_offset = offset
        ins, offset = disassemble(bytecode, offset)
        ins_bytecode = bytes(bytecode[prev_offset:offset]).hex()
        ins_bytecode_idx = f'{int(prev_offset/2):04x}'
        print(f'{ins_bytecode_idx}: {ins} [bytecode: {ins_bytecode}]')

        if event.location.index >= 0x4: #0x1e:
            await dbg.jdwp.VirtualMachine.Suspend()
            print("Doing frames analysis.")
            frame_count, _ = await dbg.jdwp.ThreadReference.FrameCount(event.thread)
            print(f"Frame Count: {frame_count}")

            frames_req = dbg.jdwp.ThreadReference.FramesRequest()
            frames_req.thread = ThreadID(event.thread)
            frames_req.startFrame = Int(0)
            frames_req.length = Int(-1) # -1 for everything

            frames_reply, frames_err = await dbg.jdwp.ThreadReference.Frames(frames_req)
            print(f"Frames Error: {frames_err}")
            
            # TODO: Get the Method.VariableTable (class, method)
            #       - Returns list of variables.
            # TODO: Get the StackFrame.GetValues with slot index and type.

            idx = -1
            for frame in frames_reply.frames:
                idx += 1

                

                print(f"-------------------- Frame[{idx}]: {frame}")

                # Filter all frames not in the current class/method.
                if frame.location.classID != event.location.classID \
                    or frame.location.methodID != event.location.methodID:
                    continue
                
                vtable_req = dbg.jdwp.Method.VariableTableRequest()
                vtable_req.refType = ReferenceTypeID(frame.location.classID)
                vtable_req.methodID = MethodID(frame.location.methodID)
                vtable_reply, vtable_err = await dbg.jdwp.Method.VariableTable(vtable_req)
                if vtable_err != 0:
                    print(f"  VTable Error: {vtable_err}")
                    continue

                print(f"  argCnt: {vtable_reply.argCnt}")
                getvalues_req = dbg.jdwp.StackFrame.GetValuesRequest()
                getvalues_req.thread = event.thread
                getvalues_req.frame = frame.frameID
                for slot in vtable_reply.slots:
                    slot_req = dbg.jdwp.StackFrame.GetValuesSlotEntry()
                    slot_req.slot = Int(slot.slot)
                    slot_req.sigbyte = Byte(ord(slot.signature[0]))
                    getvalues_req.slots.append(slot_req)
                    print(f"  Slot: {slot}")


                getvalues_reply, error_code = await dbg.jdwp.StackFrame.GetValues(getvalues_req)
                print(f"  SF GetValues = {getvalues_reply}")
                for entry in getvalues_reply.values:
                    print(f"  Attempting to fetch fields for ObjectID: {entry.value}")
                    reftype_reply = await dbg.jdwp.ObjectReference.ReferenceType(ObjectID(entry.value))
                    print(f"    Reftype Reply: {reftype_reply}")

                    # Make sure we know the fields
                    await dbg.load_class_fields(reftype_reply.typeID)
                    classInfo = dbg.classes_by_id[reftype_reply.typeID]

                    getvalues_req = dbg.jdwp.ObjectReference.GetValuesRequest()
                    getvalues_req.objectid = ObjectID(entry.value)
                    for fieldID in classInfo.fields_by_id:
                        print(f"    Requesting field: {classInfo.fields_by_id[fieldID].name}")
                        getvalues_req.fields.append(FieldID(fieldID))
                    getvalues_reply, error_code = await dbg.jdwp.ObjectReference.GetValues(getvalues_req)
                    if error_code != 0:
                        continue
                    print(f"    {getvalues_reply}")

                    
                    #fields_reply, error_code = await dbg.jdwp.ReferenceType.Fields(ReferenceTypeID(entry.value))
                    #if error_code != 0:
                    #    continue
                    #for declared in fields_reply.declared:
                    #    print(declared)
                    



            breakpoint()




        await dbg.step_over(event.thread)
        #breakpoint()
        await dbg.resume_vm()


    async def single_step(self, threadID, step_depth):
        evt_req = self.jdwp.EventRequest.SetRequest()
        evt_req.eventKind = Byte(Jdwp.EventKind.SINGLE_STEP)
        evt_req.suspendPolicy = Byte(Jdwp.SuspendPolicy.ALL)

        mod = self.jdwp.EventRequest.SetStepModifier()
        mod.thread = ThreadID(threadID)
        mod.size = Int(Jdwp.StepSize.MIN) # LINE is multiple bytecode lines
        mod.depth = Int(step_depth) #Jdwp.StepDepth.INTO
        evt_req.modifiers.append(mod)

        # TODO: The event supposidly only runs once anyway.
        #mod = dbg.jdwp.EventRequest.SetCountModifier()
        #mod.count = Int(1)
        #evt_req.modifiers.append(mod)

        reqid, _ = await self.jdwp.EventRequest.Set(evt_req)
        self.jdwp.register_event_handler(reqid, JvmDebugger.handle_step_event, (self,))


    async def step_into(self, threadID):
        await self.single_step(threadID, Jdwp.StepDepth.INTO)

    async def step_over(self, threadID):
        await self.single_step(threadID, Jdwp.StepDepth.OVER)
    
    async def step_out(self, threadID):
        await self.single_step(threadID, Jdwp.StepDepth.OUT)

        


    @staticmethod
    async def handle_deferred_breakpoint_class_prepare(event, composite, args):
        # Fetch arguments
        dbg, class_signature, method_signature, bytecode_index = args

        # Make sure the class is registered (in case this beats the general CLASS_PREPARE).
        await JvmDebugger.handle_class_prepare(event, composite, dbg)

        # Stop class prepare events.
        #print(f"Disable class prepare reqid {event.requestID}")
        await dbg.disable_class_prepare_event(event.requestID)

        # Get the methods for the target class.
        await dbg.update_class_methods(event.typeID)

        if class_signature in dbg.classes_by_signature:
            classInfo = dbg.classes_by_signature[class_signature]
            if method_signature in classInfo.methods_by_signature:
                methodInfo = classInfo.methods_by_signature[method_signature]
                print(f"BREAKPOINT: {classInfo.signature} [{classInfo.typeID}] {methodInfo.name}{methodInfo.signature} [{methodInfo.methodID}] bytecode index {bytecode_index}")
                # TODO: Event set breakpoint with class, method, and offset

                evt_req = dbg.jdwp.EventRequest.SetRequest()
                evt_req.eventKind = Byte(Jdwp.EventKind.BREAKPOINT)
                evt_req.suspendPolicy = Byte(Jdwp.SuspendPolicy.ALL)

                loc = Location()
                loc.tag = Byte(Jdwp.TypeTag.CLASS)
                loc.classID = ClassID(classInfo.typeID)
                loc.methodID = methodInfo.methodID
                loc.index = Long(0)

                mod = dbg.jdwp.EventRequest.SetLocationOnlyModifier()
                mod.loc = loc
                evt_req.modifiers.append(mod)
                mod = dbg.jdwp.EventRequest.SetCountModifier()
                mod.count = Int(1)
                evt_req.modifiers.append(mod)

                reqid, _ = await dbg.jdwp.EventRequest.Set(evt_req)
                dbg.jdwp.register_event_handler(reqid, JvmDebugger.handle_breakpoint_event, (dbg,))

                

    
    async def enable_deferred_breakpoint(self, class_signature, method_signature, bytecode_index=0):
        evt_req = self.jdwp.EventRequest.SetRequest()
        evt_req.eventKind = Byte(Jdwp.EventKind.CLASS_PREPARE)
        evt_req.suspendPolicy = Byte(Jdwp.SuspendPolicy.NONE)

        mod = self.jdwp.EventRequest.SetClassMatchModifier()
        #mod.classPattern = String(class_signature)
        mod.classPattern = String("sh.kau.playground.quoter.QuotesRepoImpl")
        evt_req.modifiers.append(mod)
        mod = self.jdwp.EventRequest.SetCountModifier()
        mod.count = Int(1)
        evt_req.modifiers.append(mod)

        # TODO: add a class matcher or something here?
        reqid, _ = await self.jdwp.EventRequest.Set(evt_req)

        print(f"Registered handle_deferred_breakpoint_class_prepare callback (reqid {reqid}).")
        self.jdwp.register_event_handler(reqid, JvmDebugger.handle_deferred_breakpoint_class_prepare, (self, class_signature, method_signature, bytecode_index))


    async def enable_class_prepare_events(self):
        # Watch for new classes.
        #print("EventRequest.Set(CLASS_PREPARE / NO_SUSPEND)")
        evt_req = self.jdwp.EventRequest.SetRequest()
        evt_req.eventKind = Byte(Jdwp.EventKind.CLASS_PREPARE)
        evt_req.suspendPolicy = Byte(Jdwp.SuspendPolicy.NONE)
        # No modifiers.
        self.class_prepare_reqid, _ = await self.jdwp.EventRequest.Set(evt_req)
        print(f"enable_class_prepare_events RequestID = {self.class_prepare_reqid}")

        self.jdwp.register_event_handler(self.class_prepare_reqid, JvmDebugger.handle_class_prepare, self)


    async def request_all_classes(self):
        #print("VirtualMachine.AllClassesWithGeneric()")
        all_classes_reply, _ = await self.jdwp.VirtualMachine.AllClassesWithGeneric()

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
        self.class_unload_reqid, _ = await self.jdwp.EventRequest.Set(evt_req)
        print(f"enable_class_unload_events RequestID = {self.class_unload_reqid}")

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
        self.thread_start_reqid, _ = await self.jdwp.EventRequest.Set(evt_req)
        print(f"enable_thread_start_events RequestID = {self.thread_start_reqid}")

        async def handle_thread_start(event, composite, wp):
            # TODO: Do we check if it already existed?
            threadInfo = ThreadInfo()
            threadInfo.threadID = event.thread
            # TODO: Do we see if it already exists first?
            self.threads_by_id[threadInfo.threadID] = threadInfo
            #print(f"THREAD_START: {threadInfo.threadID}")

        self.jdwp.register_event_handler(self.thread_start_reqid, handle_thread_start)


    async def enable_thread_death_events(self):
        evt_req = self.jdwp.EventRequest.SetRequest()
        evt_req.eventKind = Byte(Jdwp.EventKind.THREAD_DEATH)
        evt_req.suspendPolicy = Byte(Jdwp.SuspendPolicy.NONE)
        self.thread_death_reqid, _ = await self.jdwp.EventRequest.Set(evt_req)
        print(f"enable_thread_death_events RequestID = {self.thread_death_reqid}")

        async def handle_thread_death(event, composite, wp):

            # TODO: Do we check if it already existed?
            if event.thread in self.threads_by_id:
                threadInfo = self.threads_by_id[event.thread]
                self.threads_by_id.pop(threadInfo.threadID, None)
                self.dead_threads.append(threadInfo)
                # TODO: Implement way to show first A chars and last B chars in X width.
                print(f"THREAD_DEATH: {threadInfo.threadID}")

        self.jdwp.register_event_handler(self.thread_death_reqid, handle_thread_death)


    async def request_all_threads(self):
        thread_reply, _ = await self.jdwp.VirtualMachine.AllThreads()
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
