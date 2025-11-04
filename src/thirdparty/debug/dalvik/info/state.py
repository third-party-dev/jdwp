'''
Copyright (c) 2025 Vincent Agriesti

This file is part of the thirdparty JDWP project.
Licensed under the MIT License. See the LICENSE file in the project root
for full license text.
'''

from thirdparty.jdwp import Jdwp, Byte, Boolean, Int, String, ReferenceTypeID, ThreadID, MethodID, ClassID, FieldID
from pydantic import BaseModel
from typing import Optional, List, Tuple






class FieldInfo():
    def __init__(self):
        self.fieldID: Optional[FieldID] = None
        self.name: Optional[String] = None
        self.signature: Optional[String] = None
        self.modBits: Optional[Int] = None

class MethodInfo():
    def __init__(self):
        self.methodID: Optional[MethodID] = None
        self.name: Optional[String] = None
        self.signature: Optional[String] = None
        self.modBits: Optional[Int] = None
        self.bytecode = None


class ClassInfo():

    def __init__(self, dbg, class_id):
        self.dbg = dbg
        self.typeID = class_id

        # Populated by self.dbg.create_class_info()
        self.refTypeTag: Optional[Byte] = None
        self.signature: Optional[String] = None
        self.generic: Optional[String] = None

        self.methods_loaded = False
        self.methods_by_id = {}
        self.methods_by_signature = {}

        self.fields_loaded = False
        self.fields_by_id = {}
        self.fields_by_signature = {}

        self.super_class = None

        # Dereference of these will cause crash.
        self.unsafe_fields_by_id = {}
        self.unsafe_fields_by_signature = {}


    def _is_unsafe_field(self, field):
        return "java/lang/Thread" in self.signature and \
            ("ExceptionHandler" in field.signature \
            or "java/lang/RuntimePermission" in field.signature)

    async def _update_class_fields(self):
        if self.fields_loaded:
            return

        fields_reply, error_code = await self.dbg.jdwp.ReferenceType.Fields(ReferenceTypeID(self.typeID))
        if error_code != Jdwp.Error.NONE:
            print(f"ERROR: Failed to get class fields: {Jdwp.Error.string[error_code]}")
            return

        for entry in fields_reply.declared:
            field = FieldInfo()
            field.fieldID = entry.fieldID
            field.name = entry.name
            field.signature = entry.signature
            field.modBits = entry.modBits

            if self._is_unsafe_field(field):
                self.unsafe_fields_by_id[field.fieldID] = field
                self.unsafe_fields_by_signature[(field.name, field.signature)] = field
            else:
                self.fields_by_id[field.fieldID] = field
                self.fields_by_signature[(field.name, field.signature)] = field
            
        self.fields_loaded = True


    async def _update_class_methods(self):
        if self.methods_loaded:
            return
        
        methods_reply, error_code = await self.dbg.jdwp.ReferenceType.Methods(self.typeID)
        if error_code != Jdwp.Error.NONE:
            print(f"ERROR: Failed to get class methods: {Jdwp.Error.string[error_code]}")
            return

        for entry in methods_reply.declared:
            method = MethodInfo()
            method.methodID = entry.methodID
            method.name = entry.name
            method.signature = entry.signature
            method.modBits = entry.modBits
            self.methods_by_id[method.methodID] = method
            method_signature = (method.name, method.signature)
            self.methods_by_signature[method_signature] = method

        self.methods_loaded = True


    async def _update_super_class(self):
        if self.super_class:
            return

        super_id = await self.dbg.get_super_id(self.typeID)
        if super_id:
            self.super_class = await self.dbg.class_info(super_id)


    async def load(self):
        await self._update_class_methods()
        await self._update_class_fields()

        # Note: Recursive.
        await self._update_super_class()
        return self


class DebuggerState():
  def __init__(self):
    self.jdwp = None

    self.classes_by_id = {}
    self.classes_by_signature = {}

    # TODO: What is the best way to store unloaded classes, consider recycled signatures and ids.
    self.unloaded_classes = []

    self.threads_by_id = {}
    #self.thread_by_name = {}
    self.dead_threads = []

    self.objects_by_id = {}