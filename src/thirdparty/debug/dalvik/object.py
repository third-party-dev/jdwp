
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
from thirdparty.debug.dalvik.state import *
from pydantic import BaseModel
from typing import Optional, List, Tuple
import pdb

'''
We have base classes and super classes. Since java is single inheritance
we should be able to have a sorted linear array of types in an array from
actual type up the class tree (i.e. super classes).

Field values are tied to the class they are defined in. A parent class and
a child class can have fields with the same name that are distinct in
memory. This can effectively "hide" a parent field from child field users.

To unhide these fields and their values, we need to not merge our fields
dictionary into a single flat structure. We need to associate each field
with its class_info type, but still be able to dump everything at once.
'''


class SubobjectInfo():
    def __init__(self, dbg, object_id: int, class_id: int):
        self.dbg = dbg
        self.object_id = object_id
        self.class_id = class_id

        self.class_info = None
        self.fields = {}


    async def load(self):

        # Get _loaded_ class_info.
        if not self.class_info:
            #class_id = await self.dbg.get_class_id(self.object_id)
            self.class_info = await self.dbg.class_info(self.class_id)
        
        # Get object values
        getvalues_req = self.dbg.jdwp.ObjectReference.GetValuesRequest()
        getvalues_req.objectid = ObjectID(self.object_id)
        
        field_ids = [*self.class_info.fields_by_id.keys()]
        for field_id in field_ids:
            getvalues_req.fields.append(FieldID(field_id))
        getvalues_reply, error_code = await self.dbg.jdwp.ObjectReference.GetValues(getvalues_req)
        if error_code != Jdwp.Error.NONE:
            print(f"ERROR: Failed to get object values: {Jdwp.Error.string[error_code]}")

        # Map object values to field names.
        for idx, field_id in enumerate(field_ids):
            field_info = self.class_info.fields_by_id[field_id]
            field_value = getvalues_reply.values[idx]
            field_tup = (field_info.fieldID, field_info.name)
            self.fields[field_tup] = field_value

        return self


    def __repr__(self):
        try:
            summary = [f'  {self.class_info.signature} (classID {self.class_info.typeID})']

            summary.append(f'\n    Methods: [skipped]')
            #for method_id, method in self.class_info.methods_by_id.items():
            #    summary.append(f'    - {method.name}{method.signature}')
            
            summary.append(f'\n    Fields:')

            for (field_id, field_name), field_value in self.fields.items():
                field_info = self.class_info.fields_by_id[field_id]
                summary.append(f'      - {field_info.signature} {field_name} = {Jdwp.Tag.type_str(field_value.tag)}({field_value.value})')
                #summary.append(f'      - {field_name} = {field_value}')

            return '\n'.join(summary)
        except Exception as e:
            return f"ObjectInfo(ERROR: {e})"


class ObjectInfo():
    def __init__(self, dbg, object_id: int):
        self.dbg = dbg
        self.object_id = object_id

        if self.object_id not in self.dbg.objects_by_id:
            self.dbg.objects_by_id[self.object_id] = self

        self.subobjects = []
        # Subobjects lookup by class id
        self.subobjects_by_id = {}
        # Subobjects lookup by class signature
        self.subobjects_by_signature = {}


    def field_value(self, as_class, field_name):
        subobject = self.subobjects_by_signature[as_class]

        for k,v in subobject.fields.items():
            if k[1] == field_name:
                return v

        return None


    async def load(self):
        self.subobjects = []
        self.subobjects_by_id = {}

        # Do the leaf class first.
        class_id = await self.dbg.get_class_id(self.object_id)
        #print(f"CLASS_ID: {class_id}  .. before loop")
        while class_id:
            # Now do all super classes
            self.subobjects_by_id[class_id] = await SubobjectInfo(self.dbg, self.object_id, class_id).load()
            self.subobjects.append(self.subobjects_by_id[class_id])
            class_signature = self.dbg.classes_by_id[class_id].signature
            self.subobjects_by_signature[class_signature] = self.subobjects_by_id[class_id]
            #print(f"CLASS_ID: {class_id}  .. before get_super_id")
            class_id = await self.dbg.get_super_id(class_id)
            #print(f"CLASS_ID: {class_id}  .. after get_super_id")
        #print(f"CLASS_ID: {class_id}  .. after loop")
        return self


    # Dereference a member of the object.
    async def deref(self, ref):
        if isinstance(ref, ObjectInfo) or isinstance(ref, int):
            return await self.dbg.deref(ref)

        if isinstance(ref, str):
            for (field_id, field_name), field_value in self.fields.items():
                if ref == field_name:
                    if field_value.tag == Jdwp.Tag.OBJECT:
                        return await self.dbg.deref(field_value.value)
                    
                    # TODO: We can handle other types like strings here too.
                    return field_value


    # Generate string output of object.
    def __repr__(self):
        
        try:
            if len(self.subobjects) == 0:
                return f'ObjectInfo(object_id {self.object_id} [unloaded])'

            # summary = [f'{self.class_info.signature} (classID {self.class_info.typeID})']

            # summary.append(f'\n  Methods: [skipped]')
            # #for method_id, method in self.class_info.methods_by_id.items():
            # #    summary.append(f'    - {method.name}{method.signature}')
            
            # summary.append(f'\n  Fields:')

            # for (field_id, field_name), field_value in self.fields.items():
            #     field_info = self.class_info.fields_by_id[field_id]
            #     summary.append(f'    - {field_info.signature} {field_name} = {Jdwp.Tag.type_str(field_value.tag)}({field_value.value})')
            #     #summary.append(f'    - {field_name} = {field_value}')

            # return '\n'.join(summary)

            summary = [f'ObjectInfo({self.object_id})']

            for subobj in reversed(self.subobjects):
                summary.append(f'{subobj}')
            return '\n'.join(summary)

        except Exception as e:
            return f"ObjectInfo(ERROR: {e})"


    # def __getattribute__(self, name):
    #     print(f"__getattribute__({name!r})")
    #     return super().__getattribute__(name)
    
    # def __getattr__(self, name):
    #     print(f"__getattr__({name!r})")
    #     return f"<no such attribute: {name}>"
    
    # def __setattr__(self, name, value):
    #     print(f"__setattr__({name!r}, {value!r})")
    #     super().__setattr__(name, value)
    
    # def __delattr__(self, name):
    #     print(f"__delattr__({name!r})")
    #     super().__delattr__(name)