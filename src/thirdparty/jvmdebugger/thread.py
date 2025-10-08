import asyncio
from thirdparty.jdwp import (
    Jdwp, Byte, Boolean, Int, String, ReferenceTypeID, Location, 
    Long, ClassID, ObjectID, FrameID, MethodID)
from thirdparty.jvmdebugger.state import *
from thirdparty.jvmdebugger.object import ObjectInfo
from pydantic import BaseModel
from typing import Optional, List, Tuple


class SlotInfo():
    def __init__(self, frame, slot):
        self.frame = frame
        self.dbg = frame.dbg

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
    
    async def get_ref(self):
        return await self.dbg.object_ref(self.tagged_value.value)._update()


class FrameInfo():
    def __init__(self, frame, thread):
        self.thread = thread # ThreadInfo
        self.dbg = self.thread.dbg

        self.frameID = frame.frameID
        self.location = frame.location
        self.slots = None

        self.here = ""
    
    async def _update(self):
        # TODO: Consider caching?
        #print(f"UPDATING FRAME {self} {self.frameID}")

        vtable_req = self.dbg.jdwp.Method.VariableTableRequest()
        vtable_req.refType = ReferenceTypeID(ReferenceTypeID(self.location.classID))
        vtable_req.methodID = MethodID(self.location.methodID)
        vtable_reply, error_code = await self.dbg.jdwp.Method.VariableTable(vtable_req)
        if error_code != Jdwp.Error.NONE:
            print(f"ERROR: Failed to get method table: {Jdwp.Error.string[error_code]}")
            return
        
        # Using class/method variable table, fetch slot values.
        getvalues_req = self.dbg.jdwp.StackFrame.GetValuesRequest()
        getvalues_req.thread = ThreadID(self.thread.threadID)
        getvalues_req.frame = FrameID(self.frameID)

        # Prepare slot meta for value fetching.
        self.slots = {}
        for slot in vtable_reply.slots:
            slot_req = self.dbg.jdwp.StackFrame.GetValuesSlotEntry()
            slot_req.slot = Int(slot.slot)
            slot_req.sigbyte = Byte(ord(slot.signature[0]))
            self.slots[slot.slot] = SlotInfo(self, slot)
            getvalues_req.slots.append(slot_req)

        # Fetch values
        getvalues_reply, error_code = await self.dbg.jdwp.StackFrame.GetValues(getvalues_req)
        if error_code != Jdwp.Error.NONE:
            print(f"ERROR: Failed to get values in frame: {Jdwp.Error.string[error_code]}")
            return

        # Set the value.
        for idx, slot in enumerate(vtable_reply.slots):
            #print(f"UPDATING SLOT INFO {self.slots}")
            slot_info = self.slots[slot.slot]

            slot_info.tagged_value = getvalues_reply.values[idx]
            
            # TODO: This is where we can generate an object ref.
        
        return self
    

    def slot(self, idx):
        return self.slots[idx]


class ThreadInfo():

    def __init__(self, dbg, thread_id):
        self.dbg = dbg
        self.threadID = thread_id

        # Context set by std_break_event that are not valid
        # once the VM has been resumed.
        self._event = None
        self._frames = None


    # Run this on breakpoint.
    async def _update(self, event):
        self._event = event
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
            self._frames.append(await FrameInfo(frame, self)._update())


    def frames(self):
        return self._frames

    def frame(self, idx):
        return self._frames[idx]





