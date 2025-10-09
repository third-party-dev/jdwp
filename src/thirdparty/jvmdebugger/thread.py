import asyncio
from thirdparty.jdwp import (
    Jdwp, Byte, Boolean, Int, String, ReferenceTypeID, Location, 
    Long, ClassID, ObjectID, FrameID, MethodID)
from thirdparty.jvmdebugger.state import *
from thirdparty.jvmdebugger.object import ObjectInfo
from pydantic import BaseModel
from typing import Optional, List, Tuple


class SlotInfo():
    def __init__(self, frame, slot=None):
        self.frame = frame
        self.dbg = frame.dbg

        if not slot:
            self.codeIndex = '[unloaded]'
            self.name = '[unloaded]'
            self.signature = '[unloaded]'
            self.length = '[unloaded]'
            self.slot = '[unloaded]'
        else:
            self.codeIndex = slot.codeIndex
            self.name = slot.name
            self.signature = slot.signature
            self.length = slot.length
            self.slot = slot.slot

        self.tagged_value = None

    def __repr__(self):
        try:
            tag_map = {
                Jdwp.Tag.ARRAY: 'Array',
                Jdwp.Tag.BYTE: 'Byte',
                Jdwp.Tag.CHAR: 'Char',
                Jdwp.Tag.OBJECT: 'Object',
                Jdwp.Tag.FLOAT: 'Float',
                Jdwp.Tag.DOUBLE: 'Double',
                Jdwp.Tag.INT: 'Int',
                Jdwp.Tag.LONG: 'Long',
                Jdwp.Tag.SHORT: 'Short',
                Jdwp.Tag.VOID: 'Void',
                Jdwp.Tag.BOOLEAN: 'Boolean',
                Jdwp.Tag.STRING: 'String',
                Jdwp.Tag.THREAD: 'Thread',
                Jdwp.Tag.THREAD_GROUP: 'ThreadGroup',
                Jdwp.Tag.CLASS_LOADER: 'ClassLoader',
                Jdwp.Tag.CLASS_OBJECT: 'ClassObject',
            }


            type_str = 'Unknown'
            if self.tagged_value.tag in tag_map:
                type_str = tag_map[self.tagged_value.tag]
            
            return f"{type_str}({self.tagged_value.value})"
        except:
            return "SlotInfo(ERROR)"
    

    async def deref(self):
        # TODO: Check if the slot is a OBJECT
        return await self.dbg.deref(self.tagged_value.value)


class FrameInfo():
    def __init__(self, frame, thread):
        self.thread = thread # ThreadInfo
        self.dbg = self.thread.dbg

        self.frameID = frame.frameID
        self.location = frame.location

        self.loc_class = '[unloaded]'
        self.loc_method = '[unloaded]'

        self.this_obj = '[unloaded]'

        self._slots = None
        self._given = None

        self.here = ""
    
    async def load(self):

        # TODO: Flesh out location?
        await self.dbg.update_class_methods(self.location.classID)

        class_info = self.dbg.classes_by_id[self.location.classID]
        method_info = class_info.methods_by_id[self.location.methodID]
        self.loc_class = class_info.signature
        self.loc_method = f'{method_info.name}{method_info.signature}'


        this_req = self.dbg.jdwp.StackFrame.ThisObjectRequest()
        this_req.thread = ThreadID(self.thread.threadID)
        this_req.frame = FrameID(self.frameID)
        this_reply, error_code = await self.dbg.jdwp.StackFrame.ThisObject(this_req)
        if error_code != Jdwp.Error.NONE:
            print(f"ERROR: Failed to get this information: {Jdwp.Error.string[error_code]}")
            return
        
        self.this_obj = this_reply
        if this_reply.tag == Jdwp.Tag.OBJECT:
            self.this_obj = self.dbg.object_info(this_reply.objectID)

        # TODO: Consider caching?
        #print(f"UPDATING FRAME {self} {self.frameID}")

        # NOTE: This is really silly, but if we use the VariableTable, we don't always get
        # all of the Dalvik slots that might exist. So instead, we brute force out the slots
        # that exist and their types. The get_given_slots() below can show the difference
        # between brute force and graceful fetch. The brute force clearly shows way more
        # registers/variables available! (Uncomment in __repr__ and below to see results.)
        async def get_given_slots(frame):

            
            vtable_req = self.dbg.jdwp.Method.VariableTableRequest()
            vtable_req.refType = ReferenceTypeID(ReferenceTypeID(frame.location.classID))
            vtable_req.methodID = MethodID(frame.location.methodID)
            vtable_reply, error_code = await frame.dbg.jdwp.Method.VariableTable(vtable_req)
            if error_code != Jdwp.Error.NONE:
                print(f"ERROR: Failed to get method table: {Jdwp.Error.string[error_code]}")
                return
            
            # Using class/method variable table, fetch slot values.
            getvalues_req = frame.dbg.jdwp.StackFrame.GetValuesRequest()
            getvalues_req.thread = ThreadID(frame.thread.threadID)
            getvalues_req.frame = FrameID(frame.frameID)

            # Prepare slot meta for value fetching.
            frame._given = {}
            for slot in vtable_reply.slots:
                slot_req = frame.dbg.jdwp.StackFrame.GetValuesSlotEntry()
                slot_req.slot = Int(slot.slot)
                slot_req.sigbyte = Byte(ord(slot.signature[0]))
                frame._given[slot.slot] = SlotInfo(frame, slot)
                getvalues_req.slots.append(slot_req)

            # Fetch values
            getvalues_reply, error_code = await frame.dbg.jdwp.StackFrame.GetValues(getvalues_req)
            if error_code != Jdwp.Error.NONE:
                print(f"ERROR: Failed to get values in frame: {Jdwp.Error.string[error_code]}")
                return

            # Set the value.
            for idx, slot in enumerate(vtable_reply.slots):
                #print(f"UPDATING SLOT INFO {self.slots}")
                slot_info = frame._given[slot.slot]

                slot_info.tagged_value = getvalues_reply.values[idx]
                
                # TODO: This is where we can generate an object ref.
        #await get_given_slots(self)

        # TODO: Consider using location to disassemble line?

        self._slots = {}

        async def guess_sigbyte(slot_idx):

            for sigbyte in ('L', '[', 's', 't', 'g', 'I', 'B', 'Z', 'S', 'J', 'C', 'D', 'F', 'l', 'c', 'V'):
                getvalues_req = self.dbg.jdwp.StackFrame.GetValuesRequest()
                getvalues_req.thread = ThreadID(self.thread.threadID)
                getvalues_req.frame = FrameID(self.frameID)

                slot_req = self.dbg.jdwp.StackFrame.GetValuesSlotEntry()
                slot_req.slot = Int(slot_idx)
                slot_req.sigbyte = Byte(ord(sigbyte)) # assuming everything is an object.
                getvalues_req.slots.append(slot_req)

                getvalues_reply, error_code = await self.dbg.jdwp.StackFrame.GetValues(getvalues_req)
                if error_code == Jdwp.Error.TYPE_MISMATCH:
                    continue
                if error_code != Jdwp.Error.NONE:
                    return getvalues_reply, error_code, None

                break

            return getvalues_reply, error_code, sigbyte

        
        for slot_idx in range(16):
            getvalues_reply, error_code, sigbyte = await guess_sigbyte(slot_idx)
            if error_code == Jdwp.Error.TYPE_MISMATCH:
                print(f"ERROR: Failed to guess slot type. (frame {self.frameID}) Skipping slot v{slot_idx}.")
                continue
            if error_code == Jdwp.Error.INVALID_SLOT:
                continue
            if error_code != Jdwp.Error.NONE:
                print(f"ERROR: Failed to get values in frame: {Jdwp.Error.string[error_code]}")
                
            #breakpoint()
            self._slots[slot_idx] = SlotInfo(self)
            self._slots[slot_idx].sigbyte = sigbyte
            self._slots[slot_idx].tagged_value = getvalues_reply.values[0]
            #print(getvalues_reply)


        
        return self


    def slots(self):
        return self._slots


    def slot(self, idx):
        return self._slots[idx]

    def __repr__(self):
        summary = [
            f'FrameID: {self.frameID}',
            f'ThisObj: {self.this_obj}',
            'Location:',
            f'  Class: {self.loc_class}',
            f'  Method: {self.loc_method}',
            f'Slots:'
        ]

        for slot_id, slot_value in self.slots().items():
            summary.append(f'  v{slot_id}: {slot_value}')

        # summary.append('Given Slots:')
        # for slot_id, slot_value in self._given.items():
        #     summary.append(f'  v{slot_id}: {slot_value}')

        
        return '\n'.join(summary)


class ThreadInfo():

    def __init__(self, dbg, thread_id):
        self.dbg = dbg
        self.threadID = thread_id

        if self.threadID in self.dbg.threads_by_id:
            raise RuntimeError(f"ThreadID {self.threadID} already exists!")
        self.dbg.threads_by_id[self.threadID] = self

        # Context set by std_break_event that are not valid
        # once the VM has been resumed.
        self._frames = None

        self.this_frame = None

        # Cached event arguments.
        self._event = None
        self._event_composite = None
        self._event_args = None


    def event_args(self, event, composite, args):
        self._event = event
        self._event_composite = composite
        self._event_args = args


    # Run this on breakpoint.
    async def load(self):
        self._frames = []

        frames_req = self.dbg.jdwp.ThreadReference.FramesRequest()
        frames_req.thread = ThreadID(self.threadID)
        frames_req.startFrame = Int(0)
        frames_req.length = Int(-1)

        frames_reply, error_code = await self.dbg.jdwp.ThreadReference.Frames(frames_req)
        if error_code != Jdwp.Error.NONE:
            print(f"ERROR: {Jdwp.Error.string[error_code]}")
            return

        for frame in frames_reply.frames:
            self._frames.append(await FrameInfo(frame, self).load())

        return self

    def frames(self):
        return self._frames


    async def frame(self, idx):
        return await self._frames[idx].load()


    def __repr__(self):
        summary = [f'ThreadID: {self.threadID}\nEvent: {self._event}']

        # TODO: Make this backwards
        for frame_idx, frame in enumerate(self._frames):
            summary.append(f'--- Frame[{frame_idx}] ---')
            summary.append(f'{frame}')
        
        return '\n'.join(summary)




