
import asyncio
from thirdparty.jdwp import (
    Jdwp, Byte, Boolean, Int, String, ReferenceTypeID, Location, 
    Long, ClassID, ObjectID, FrameID, MethodID)

from thirdparty.dalvik.dex import disassemble
from thirdparty.jvmdebugger.state import *


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

async def noop(event, composite, args):
    pass

class BreakpointInfo():

    def __init__(self, dbg, class_signature=None, method_name=None, method_signature=None, callback=None, bytecode_index=0, count=1):
        self.dbg = dbg

        self.callback = callback
        if not self.callback:
            self.callback = noop
        
        self.class_signature = class_signature
        self.class_info = None

        self.method_name = method_name
        self.method_signature = method_signature
        self.method_key = (self.method_name, self.method_signature)
        
        self.method_info = None
        self.bytecode_index = bytecode_index

        # How many times to listen for breakpoint event
        self.count = count

    
    def set_callback(self, callback):
        self.callback = callback
        return self


    async def set_breakpoint(self):

        if self.class_signature not in self.dbg.classes_by_signature:
            # This is a deferred breakpoint.
            await self._defer_breakpoint()
        else:
            # Class loaded, lets do it now.
            await self.dbg.update_class_methods(self.class_info.typeID)
            self.class_info = self.dbg.classes_by_signature[self.class_signature]
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
        if self.count > 0:
            mod = self.dbg.jdwp.EventRequest.SetCountModifier()
            mod.count = Int(self.count)
            evt_req.modifiers.append(mod)

        reqid, error_code = await self.dbg.jdwp.EventRequest.Set(evt_req)
        if error_code != Jdwp.Error.NONE:
            print(f"ERROR: Breakpoint not registered: {Jdwp.Error.string[error_code]}")
            return
        
        print(f"Setting breakpoint for: {jvm_to_java(self.class_signature)}.{self.method_name}{self.method_signature} (reqid {reqid}).")
        self.dbg.jdwp.register_event_handler(reqid, self.callback, (self,))


    @staticmethod
    async def _handle_class_prepare(event, composite, args):
        from thirdparty.jvmdebugger import JvmDebugger

        # Fetch arguments
        self, = args

        # Make sure the class is registered (in case this beats the general CLASS_PREPARE).
        await JvmDebugger.handle_class_prepare(event, composite, self.dbg)

        # Stop class prepare events.
        #print(f"Disable class prepare reqid {event.requestID}")
        await self.dbg.disable_class_prepare_event(event.requestID)

        # Get the methods for the target class.
        await self.dbg.update_class_methods(event.typeID)

        if self.class_signature in self.dbg.classes_by_signature:
            self.class_info = self.dbg.classes_by_signature[self.class_signature]
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
