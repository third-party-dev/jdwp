
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

        self.class_info = None


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
        
        await self.dbg.update_class_fields(reftype_reply.typeID)
        await self.dbg.update_class_methods(reftype_reply.typeID)

        # TODO: Get values

        return self


    def __repr__(self):
        try:
            #breakpoint()
            summary = [
                self.class_info.signature,
                f'  Methods:',
            ]

            for method_id, method in self.class_info.methods_by_id.items():
                summary.append(f'    - {method.name}{method.signature}')
            
            summary.append(f'\n  Fields:')

            for field_id, field in self.class_info.fields_by_id.items():
                summary.append(f'    - {field.signature} {field.name}')

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