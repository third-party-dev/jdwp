
import asyncio
from thirdparty.jdwp import (
    Jdwp, Byte, Boolean, Int, String, ReferenceTypeID, Location, 
    Long, ClassID, ObjectID, FrameID, MethodID)
from thirdparty.jvmdebugger.state import *
from pydantic import BaseModel
from typing import Optional, List, Tuple



class ObjectInfo():
    def __init__(self, dbg, object_id: int):
        self.dbg = dbg
        self.object_id = object_id

        if self.object_id not in self.dbg.objects_by_id:
            self.dbg.objects_by_id[self.object_id] = self

        self.class_info = None

        self.fields = {}


    async def _update(self):
        print(f"ObjectInfo({self.object_id})._update()")

        # Get the object type
        reftype_reply, error_code = await self.dbg.jdwp.ObjectReference.ReferenceType(ObjectID(self.object_id))
        if error_code != Jdwp.Error.NONE:
            print(f"ERROR: Failed to get object type: {Jdwp.Error.string[error_code]}")
            return

        # Get the class_info
        if reftype_reply.typeID not in self.dbg.classes_by_id:
            print(f"ERROR: Class id not found: {reftype_reply.typeID}")
            return

        self.class_info = self.dbg.classes_by_id[reftype_reply.typeID]
        
        # Ensure class_info updated.
        await self.dbg.update_class_fields(reftype_reply.typeID)
        await self.dbg.update_class_methods(reftype_reply.typeID)

        # Get object values
        getvalues_req = self.dbg.jdwp.ObjectReference.GetValuesRequest()

        getvalues_req.objectid = ObjectID(self.object_id)
        
        field_ids = [*self.class_info.fields_by_id.keys()]
        for field_id in field_ids:
            getvalues_req.fields.append(FieldID(field_id))
        getvalues_reply, error_code = await self.dbg.jdwp.ObjectReference.GetValues(getvalues_req)
        if error_code != Jdwp.Error.NONE:
            print(f"ERROR: Failed to get object values: {Jdwp.Error.string[error_code]}")

        # !! This doesn't feel correct.

        # Map object values to field names.
        for idx, field_id in enumerate(field_ids):
            field_info = self.class_info.fields_by_id[field_id]
            field_value = getvalues_reply.values[idx]
            field_tup = (field_info.fieldID, field_info.name)
            self.fields[field_tup] = field_value
            
        return self


    async def deref(self, ref):
        if isinstance(ref, str):
            for (field_id, field_name), field_value in self.fields.items():
                if ref == field_name:
                    if field_value.tag == Jdwp.Tag.OBJECT:
                        return await self.dbg.object_ref(field_value.value)._update()
                    # TODO: We can handle other types like strings here too.
                    return field_value
        elif isinstance(ref, int):
            for (field_id, field_name), field_value in self.fields.items():
                if ref == field_id:
                    if field_value.tag == Jdwp.Tag.OBJECT:
                        return await self.dbg.object_ref(field_value.value)._update()
                    # TODO: We can handle other types like strings here too.
                    return field_value


    def __repr__(self):
        try:
            if not self.class_info:
                return f'ObjectInfo(object_id {self.object_id} [not updated])'

            #breakpoint()
            summary = [
                f'{self.class_info.signature} (classID {self.class_info.typeID})',
                f'  Methods:',
            ]

            for method_id, method in self.class_info.methods_by_id.items():
                summary.append(f'    - {method.name}{method.signature}')
            
            summary.append(f'\n  Fields:')

            for (field_id, field_name), field_value in self.fields.items():
                field_info = self.class_info.fields_by_id[field_id]
                summary.append(f'    - {field_info.signature} {field_name} = {Jdwp.Tag.type_str(field_value.tag)}({field_value.value})')
                #summary.append(f'    - {field_name} = {field_value}')

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