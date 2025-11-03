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

import thirdparty.dalvik.dex
from thirdparty.debug.dalvik.state import *
from thirdparty.debug.dalvik.thread import ThreadInfo


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


def jvm_to_java(sig: str) -> str:
    if sig.startswith('L') and sig.endswith(';'):
        return sig[1:-1].replace('/', '.')
    else:
        raise ValueError(f"Invalid JVM signature: {sig}")


async def noop_break_event(event, composite, args):
    pass


async def instruction_str(dbg, event):
    bytecode = await dbg.load_method_bytecode(
        event.location.classID, event.location.methodID)

    try:
        offset = event.location.index * 2
        prev_offset = offset
        ins, offset = thirdparty.dalvik.dex.disassemble(bytecode, offset)
        ins_bytecode = bytes(bytecode[prev_offset:offset]).hex()
        ins_bytecode_idx = f'{int(prev_offset/2):04x}'
        return f'\n{ins_bytecode_idx}: {ins} [bytecode: {ins_bytecode}]'
    except TypeError:
        return f'\nERROR: Bytecode Instruction Not Available'


async def std_break_event(event, composite, args):
    bp, = args
    
    await bp.dbg.disable_breakpoint_event(event.requestID)
    thread = await bp.dbg.thread(event.thread)
    thread.event_args(event, composite, args)

    print(f"Bkpt@ {await bp.location_str(event)}")
    print(await instruction_str(bp.dbg, event))

    # DEBUG CODE

    # slot = bp.dbg.slot(event.thread)
    # print(f"SLOT: {slot}")
    # objref = await slot.get_ref()
    # print(f"OBJ: {objref}")
    # #pdb.set_trace()


    
async def std_step_event(event, composite, args):
    bp, = args

    await bp.dbg.disable_step_event(event.requestID)
    thread = await bp.dbg.thread(event.thread)
    thread.event_args(event, composite, args)
    
    print(f"Step@ {await bp.location_str(event)}")
    print(await instruction_str(bp.dbg, event))


async def break_location_str(dbg, event):
    # Ensure we have the methods for the target class.
    #await dbg.update_class_methods(event.location.classID)
    class_info = await dbg.class_info(event.location.classID)

    #class_info = dbg.classes_by_id[event.location.classID]
    class_name = jvm_to_java(class_info.signature)
    method_info = class_info.methods_by_id[event.location.methodID]
    method_name = method_info.name
    method_sig = method_info.signature
    class_pkg = '.'.join(class_name.split('.')[:-1])
    class_short_name = class_name.split('.')[-1]

    thread_and_pkg = f"Thread-{event.thread}:  {class_pkg}\n"
    call_str = f"  {class_short_name}.{method_name}(\n"
    param_str = f"  {method_sig}"

    #call_str = f"{jvm_to_java(class_name)}.{method_name}{method_sig}"
    return ''.join([thread_and_pkg, call_str, param_str])


class BreakpointInfo():

    def __init__(self, dbg, class_signature=None, method_name=None, method_signature=None, callback=None, bytecode_index=0, skip_count=0, userdata=None):
        self.dbg = dbg

        self.callback = callback
        if not self.callback:
            self.callback = std_break_event
        
        self.class_signature = class_signature
        self.class_info = None

        self.method_name = method_name
        self.method_signature = method_signature
        self.method_key = (self.method_name, self.method_signature)
        
        self.method_info = None
        self.bytecode_index = bytecode_index

        # How many times to skip the breakpoint.
        self.skip_count = skip_count + 1

        self.userdata = userdata

        ##### Experimental Things #####

        # An async event that can be awaited from the handler
        # and set from outside to progress execution. This gets
        # weird when you use stepping in combination with the
        # event, so its experiemental for now.

        self.aevent = asyncio.Event()

    
    def set_callback(self, callback):
        """Set the breakpoint callback.

        The callback is an async callable that includes
        the event, the event's composite, and args. args
        is a tuple with the sole value of the associated
        BreakpointInfo object. To pass user specific data
        see the BreakpointInfo.set_userdata() call.

        Example Callback Function:

        async def handle_breakpoint(event, composite, args):
            bp, = args
            print(f"{break_location_str(bp.dbg, event)}")

        """
        self.callback = callback
        return self
    

    def set_userdata(self, userdata):
        self.userdata = userdata
        return self


    async def set_breakpoint(self):

        if self.class_signature not in self.dbg.classes_by_signature:
            # This is a deferred breakpoint.
            await self._defer_breakpoint()
        else:
            # Class loaded, lets do it now.
            #await self.dbg.update_class_methods(self.class_info.typeID)
            self.class_info = await self.dbg.classes_by_signature[self.class_signature].load()
            if self.method_signature in self.class_info.methods_by_signature:
                self.method_info = self.class_info.methods_by_signature[self.method_signature]
                await self._enable_breakpoint()
        
        return None


    # callback = JvmDebugger.handle_breakpoint_event
    async def _enable_breakpoint(self):
        evt_req = self.dbg.jdwp.EventRequest.SetRequest()
        evt_req.eventKind = Byte(Jdwp.EventKind.BREAKPOINT)
        evt_req.suspendPolicy = Byte(Jdwp.SuspendPolicy.ALL)

        loc = Location()
        loc.tag = Byte(Jdwp.TypeTag.CLASS)
        loc.classID = ClassID(self.class_info.typeID)
        loc.methodID = self.method_info.methodID
        loc.index = Long(self.bytecode_index)

        mod = self.dbg.jdwp.EventRequest.SetLocationOnlyModifier()
        mod.loc = loc
        evt_req.modifiers.append(mod)
        if self.skip_count > 0:
            mod = self.dbg.jdwp.EventRequest.SetCountModifier()
            mod.count = Int(self.skip_count)
            evt_req.modifiers.append(mod)

        reqid, error_code = await self.dbg.jdwp.EventRequest.Set(evt_req)
        if error_code != Jdwp.Error.NONE:
            print(f"ERROR: Breakpoint not registered: {Jdwp.Error.string[error_code]}")
            return
        
        print(f"Setting breakpoint for: {jvm_to_java(self.class_signature)}.{self.method_name}{self.method_signature} (reqid {reqid}).")
        self.dbg.jdwp.register_event_handler(reqid, self.callback, (self,))


    @staticmethod
    async def _handle_class_prepare(event, composite, args):
        from thirdparty.debug.dalvik import JvmDebugger

        # Fetch arguments
        self, = args

        # Make sure the class is registered (in case this beats the general CLASS_PREPARE).
        await JvmDebugger.handle_class_prepare(event, composite, self.dbg)

        # Stop class prepare events.
        #print(f"Disable class prepare reqid {event.requestID}")
        await self.dbg.disable_class_prepare_event(event.requestID)

        # Get the methods for the target class.
        self.class_info = await self.dbg.class_info(event.typeID)
        #await self.dbg.update_class_methods(event.typeID)

        #if self.class_signature in self.dbg.classes_by_signature:
        #    self.class_info = self.dbg.classes_by_signature[self.class_signature]
        if (self.method_name, self.method_signature) in self.class_info.methods_by_signature:
            self.method_info = self.class_info.methods_by_signature[(self.method_name, self.method_signature)]
            
            await self._enable_breakpoint()


    async def _defer_breakpoint(self):
        evt_req = self.dbg.jdwp.EventRequest.SetRequest()
        evt_req.eventKind = Byte(Jdwp.EventKind.CLASS_PREPARE)
        evt_req.suspendPolicy = Byte(Jdwp.SuspendPolicy.NONE)

        mod = self.dbg.jdwp.EventRequest.SetClassMatchModifier()
        mod.classPattern = String(jvm_to_java(self.class_signature))
        evt_req.modifiers.append(mod)
        mod = self.dbg.jdwp.EventRequest.SetCountModifier()
        mod.count = Int(1)
        evt_req.modifiers.append(mod)

        reqid, error_code = await self.dbg.jdwp.EventRequest.Set(evt_req)
        if error_code != Jdwp.Error.NONE:
            print(f"ERROR: Deferred breakpoint not registered: {Jdwp.Error.string[error_code]}")
            return

        print(f"Deferring breakpoint for: {jvm_to_java(self.class_signature)}.{self.method_name}{self.method_signature} (reqid {reqid}).")
        self.dbg.jdwp.register_event_handler(reqid, BreakpointInfo._handle_class_prepare, (self, ))


    async def location_str(self, event):
        return await break_location_str(self.dbg, event)

    
    async def wait(self):
        await self.aevent.wait()
        # Reset event.
        self.aevent = asyncio.Event()
    

    def poke(self):
        self.aevent.set()


    async def single_step(self, thread, step_depth, step_handler=None):

        if isinstance(thread, ThreadInfo):
            thread = thread.threadID

        evt_req = self.dbg.jdwp.EventRequest.SetRequest()
        evt_req.eventKind = Byte(Jdwp.EventKind.SINGLE_STEP)
        evt_req.suspendPolicy = Byte(Jdwp.SuspendPolicy.ALL)

        mod = self.dbg.jdwp.EventRequest.SetStepModifier()
        mod.thread = ThreadID(thread)
        mod.size = Int(Jdwp.StepSize.MIN) # LINE is multiple bytecode lines
        mod.depth = Int(step_depth) #Jdwp.StepDepth.INTO
        evt_req.modifiers.append(mod)

        # TODO: Do we want to enable multi-step?
        #mod = dbg.jdwp.EventRequest.SetCountModifier()
        #mod.count = Int(1)
        #evt_req.modifiers.append(mod)

        reqid, error_code = await self.dbg.jdwp.EventRequest.Set(evt_req)
        if error_code != Jdwp.Error.NONE:
            print(f"ERROR: Failed to setup step: {Jdwp.Error.string[error_code]}")
            return
        handler = step_handler
        if not handler:
            handler = std_step_event
        self.dbg.jdwp.register_event_handler(reqid, handler, (self,))


    async def step_into(self, thread, step_handler=None):
        await self.single_step(thread, Jdwp.StepDepth.INTO, step_handler)
        await self.dbg.resume_vm()


    async def step_over(self, thread, step_handler=None):
        await self.single_step(thread, Jdwp.StepDepth.OVER, step_handler)
        await self.dbg.resume_vm()


    async def step_out(self, thread, step_handler=None):
        await self.single_step(thread, Jdwp.StepDepth.OUT, step_handler)
        await self.dbg.resume_vm()