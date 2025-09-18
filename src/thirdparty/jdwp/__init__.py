#!/usr/bin/env python3

'''
Copyright (c) 2025 Vincent Agriesti

This file is part of the thirdpart JDWP project.
Licensed under the MIT License. See the LICENSE file in the project root
for full license text.
'''

import asyncio
import struct


from typing import Optional, List, Tuple
from pydantic import BaseModel, with_config, ConfigDict
from pydantic_core import core_schema
import pdb
from thirdparty.jdwp import Jdwp

def strict_typedef(cls):
    '''
    Note: model_validate_json(data) allows coersion. This seemed preferable
    to fit the nature of JSON and its lack of types. The caller is expected
    to examine JSON with a JSON Schema before using model_validate_json(data).
    '''
    @classmethod
    def __get_pydantic_core_schema__(subcls, _source, _handler):
        def json_schema_for_base(cls):
            if isinstance(cls, int):
                return core_schema.int_schema()
            if isinstance(cls, str):
                return core_schema.str_schema()
            if isinstance(cls, float):
                return core_schema.float_schema()
            if isinstance(cls, bool):
                return core_schema.bool_schema()
            return core_schema.any_schema()

        return core_schema.json_or_python_schema(
            json_schema=json_schema_for_base(subcls),
            python_schema=core_schema.is_instance_schema(cls),
            serialization=core_schema.to_string_ser_schema(),    # optional, for JSON dumps
        )
        #return core_schema.is_instance_schema(subcls)

    cls.__get_pydantic_core_schema__ = __get_pydantic_core_schema__
    return cls


# @strict_typedef
# class A(int): pass

Byte = strict_typedef(type("Byte", (int,), {}))
Boolean = strict_typedef(type("Boolean", (int,), {}))
Int = strict_typedef(type("Int", (int,), {}))
Long = strict_typedef(type("Long", (int,), {}))
ObjectID = strict_typedef(type("ObjectID", (int,), {}))
ThreadID = strict_typedef(type("ThreadID", (int,), {}))
ThreadGroupID = strict_typedef(type("ThreadGroupID", (int,), {}))
StringID = strict_typedef(type("StringID", (int,), {}))
ClassLoaderID = strict_typedef(type("ClassLoaderID", (int,), {}))
ClassObjectID = strict_typedef(type("ClassObjectID", (int,), {}))
ArrayID = strict_typedef(type("ArrayID", (int,), {}))
ReferenceTypeID = strict_typedef(type("ReferenceTypeID", (int,), {}))
ClassID = strict_typedef(type("ClassID", (int,), {}))
InterfaceID = strict_typedef(type("InterfaceID", (int,), {}))
ArrayTypeID = strict_typedef(type("ArrayTypeID", (int,), {}))
MethodID = strict_typedef(type("MethodID", (int,), {}))
FieldID = strict_typedef(type("FieldID", (int,), {}))
FrameID = strict_typedef(type("FrameID", (int,), {}))
#Location = strict_typedef(type("A", (int,), {}))
String = strict_typedef(type("String", (str,), {}))
#Value = strict_typedef(type("A", (int,), {}))
#UntaggedValue = strict_typedef(type("A", (int,), {}))
#ArrayREgion = strict_typedef(type("A", (int,), {}))





class Jdwp():
    HANDSHAKE = b'JDWP-Handshake'

    def __init__(self, host: str = 'localhost', port: int = 8700):
        self.host
        self.port
        self.packet_id = 1

        self.VirtualMachine = VirtualMachineSet(self)

    async def start(self):
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
        self.writer.write(Jdwp.HANDSHAKE)
        await self.writer.drain()
        resp = await self.reader.readexactly(len(Jdwp.HANDSHAKE))
        if resp != Jdwp.HANDSHAKE:
            raise RuntimeError("Failed to receive JDWP handshake.")
        
        return self

    async def send(self, cmdset, cmd, data=b''):
        length = 11 + len(data)
        flags = 0x00
        pkt = self.packet_id
        self.packet_id += 1
        packet = struct.pack('>IIBBB', length, pkt, flags, cmdset, cmd) + data
        self.writer.write(packet)
        await self.writer.drain()
    
    async def recv(self):
        header = await self.reader.readexactly(11)
        length, pkt, flags, error_code = struct.unpack('>IIBH', header)
        data_length = length - 11
        data = await self.reader.readexactly(data_length)
        if error_code != 0:
            raise RuntimeError(f"JDWP error code {error_code}")
        return data, pkt, flags, error_code
    
    @staticmethod
    def parse_string(data, offset, cast=None):
        str_len = struct.unpack('>I', data[offset:offset+4])[0]
        offset += 4
        value = (data[offset:offset+str_len].decode('utf-8'), offset + str_len)
        return (cast(value[0]), value[1]) if cast else value
    
    @staticmethod
    def parse_long(data, offset, cast=None):
        value = struct.unpack('>Q', data[offset:offset+8])[0], offset + 8
        return (cast(value[0]), value[1]) if cast else value

    @staticmethod
    def parse_int(data, offset, cast=None):
        value = struct.unpack('>I', data[offset:offset+4])[0], offset + 4
        return (cast(value[0]), value[1]) if cast else value
    
    @staticmethod
    def parse_short(data, offset, cast=None):
        value = struct.unpack('>H', data[offset:offset+2])[0], offset + 2
        return (cast(value[0]), value[1]) if cast else value

    @staticmethod
    def parse_byte(data, offset, cast=None):
        value = data[offset], offset + 1
        return (cast(value[0]), value[1]) if cast else value
    
    @staticmethod
    def make_long(val: int) -> bytes:
        return struct.pack('>Q', val)

    @staticmethod
    def make_int(val: int) -> bytes:
        return struct.pack('>I', val)

    @staticmethod
    def make_byte(val: int) -> bytes:
        return bytes([val])

    @staticmethod
    def make_string(str_val: str) -> bytes:
        return Jdwp.make_int(len(str_Val)) + str_val.encode('utf-8')



#TaggedObjectID = strict_typedef(type("TaggedObjectID", (int,), {}))


'''
ARRAY 91 long
BYTE 66 byte
CHAR 67 short
OBJECT 76 long
FLOAT 70 int
DOUBLE 68 long
INT 73 int
LONG 74 long
SHORT 83 short
VOID 86 nothing
BOOLEAN 90 byte
STRING 115 long
THREAD 116 long
THREAD_GROUP 103 long
CLASS_LOADER 108 long
CLASS_OBJECT 99 long
'''
class Tag():
    ARRAY = 0x5b
    BYTE = 0x42
    CHAR = 0x43
    OBJECT = 0x4c
    FLOAT = 0x46
    DOUBLE = 0x44
    INT = 0x49
    LONG = 0x4a
    SHORT = 0x53
    VOID = 0x56
    BOOLEAN = 0x5a
    STRING = 0x73
    THREAD = 0x74
    THREAD_GROUP = 0x67
    CLASS_LOADER = 0x6c
    CLASS_OBJECT = 0x63

    u0 = [Tag.VOID]
    u8 = [Tag.BYTE, Tag.BOOLEAN, ]
    u16 = [Tag.CHAR, Tag.SHORT, ]
    u32 = [Tag.FLOAT, Tag.INT, ]
    u64 = [
        Tag.ARRAY,
        Tag.OBJECT,
        Tag.DOUBLE,
        Tag.LONG,
        Tag.STRING,
        Tag.THREAD,
        Tag.THREAD_GROUP,
        Tag.CLASS_LOADER,
        Tag.CLASS_OBJECT,
    ]


# !! Untested.
# !! This should only look at object IDs (in contrast to a Value object)
class TaggedObjectID(BaseModel):
    model_config = ConfigDict(validate_assignment=True)
    tag: Optional[Byte] = None
    # Note: Not really sure what to do here yet.
    objectID: Optional[Long] = None

    def from_bytes(self, data, offset=0) -> Tuple['TaggedObjectID', int]:
        self.tag, offset = Jdwp.parse_byte(data, offset, Byte)
        if tag in Tag.u0:
            return self, offset
        elif tag in Tag.u8:
            self.objectID, offset = Jdwp.parse_byte(data, offset, Long)
        elif tag in Tag.u16:
            self.objectID, offset = Jdwp.parse_short(data, offset, Long)
        elif tag in Tag.u32:
            self.objectID, offset = Jdwp.parse_int(data, offset, Long)
        elif tag in Tag.u64:
            self.objectID, offset = Jdwp.parse_long(data, offset, Long)
        return self, offset

# !! Untested.
class Value(BaseModel):
    model_config = ConfigDict(validate_assignment=True)
    tag: Optional[Byte] = None
    # Note: Not really sure what to do here yet.
    objectID: Optional[Long] = None

    def from_bytes(self, data, offset=0) -> Tuple['Value', int]:
        self.tag, offset = Jdwp.parse_byte(data, offset, Byte)
        if tag in Tag.u0:
            return self, offset
        elif tag in Tag.u8:
            self.objectID, offset = Jdwp.parse_byte(data, offset, Long)
        elif tag in Tag.u16:
            self.objectID, offset = Jdwp.parse_short(data, offset, Long)
        elif tag in Tag.u32:
            self.objectID, offset = Jdwp.parse_int(data, offset, Long)
        elif tag in Tag.u64:
            self.objectID, offset = Jdwp.parse_long(data, offset, Long)
        return self, offset


class VirtualMachineSet():

    def __init__(self, conn):
        self.conn = conn


    class VersionReply(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        description: Optional[String] = None
        jdwpMajor: Optional[Int] = None
        jdwpMinor: Optional[Int] = None
        vmVersion: Optional[String] = None
        vmName: Optional[String] = None

        def from_bytes(self, data, offset) -> Tuple['VersionReply', int]:
            self.description, offset = Jdwp.parse_string(data, offset, String)
            self.jdwpMajor, offset = Jdwp.parse_int(data, offset, Int)
            self.jdwpMinor, offset = Jdwp.parse_int(data, offset, Int)
            self.vmVersion, offset = Jdwp.parse_string(data, offset, String)
            self.vmName, offset = Jdwp.parse_string(data, offset, String)
            return self, offset


    async def Version(self) -> VersionReply:
        await self.conn.send(1, 1)
        data, _, _, _ = await self.conn.recv()
        return VersionReply().from_bytes(data)[0]


    class ClassesBySignatureEntry(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        refTypeTag: Optional[Byte] = None
        typeID: Optional[ReferenceTypeID] = None
        status: Optional[Int] = None

        def from_bytes(self, data, offset=0) -> Tuple['ClassesBySignatureEntry', int]:
            self.refTypeTag, offset = Jdwp.parse_byte(data, offset, Byte)
            self.typeID, offset = Jdwp.parse_long(data, offset, ReferenceTypeID)
            self.status, offset = Jdwp.parse_int(data, offset, Int)
            return self, offset


    class ClassesBySignatureReply(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        classes: List[ClassesBySignatureEntry] = []

        def from_bytes(self, data, offset=0) -> Tuple['ClassesBySignatureReply', int]:
            count, offset = Jdwp.parse_int(data, offset)
            for _ in range(count):
                value, offset = ClassesBySignatureEntry().from_bytes(data, offset)
                self.classes = [*self.classes, value]
            return self, offset


    async def ClassesBySignature(self, signature: String) -> ClassesBySignatureReply:
        await self.conn.send(1, 2, data=Jdwp.make_string(signature))
        data, _, _, _ = await self.conn.recv()
        return ClassesBySignatureReply().from_bytes(data)[0]


    class AllClassesEntry(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        refTypeTag: Optional[Byte] = None
        typeID: Optional[ReferenceTypeID] = None
        signature: Optional[String] = None
        status: Optional[Int] = None

        def from_bytes(self, data, offset) -> Tuple['AllClassesEntry', int]:
            self.refTypeTag, offset = Jdwp.parse_byte(data, offset, Byte)
            self.typeID, offset = Jdwp.parse_long(data, offset, ReferenceTypeID)
            self.signature, offset = Jdwp.parse_string(data, offset, String)
            self.status, offset = Jdwp.parse_int(data, offset, Int)
            return self, offset


    class AllClassesReply(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        classes: List[AllClassesEntry] = []

        def from_bytes(self, data, offset=0) -> Tuple['AllClassesReply', int]:
            count, offset = Jdwp.parse_int(data, offset)
            for _ in range(count):
                value, offset = AllClassesEntry().from_bytes(data, offset)
                self.classes = [*self.classes, value]
            return self, offset


    async def AllClasses(self) -> AllClassesReply:
        await self.conn.send(1, 3)
        data, _, _, _ = await self.conn.recv()
        return AllClassesReply().from_bytes(data)[0]
    

    class AllThreadsReply(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        threads: List[ThreadID] = []

        def from_bytes(self, data, offset=0) -> Tuple['AllThreadsReply', int]:
            count, offset = Jdwp.parse_int(data, offset)
            for _ in range(count):
                value, offset = Jdwp.parse_long(data, offset, ThreadID)
                self.threads = [*self.threads, value]
            return self, offset


    async def AllThreads(self) -> AllClassesReply:
        await self.conn.send(1, 4)
        data, _, _, _ = await self.conn.recv()
        return AllThreadsReply().from_bytes(data)[0]
    

    class TopLevelThreadGroupReply(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        groups: List[ThreadGroupID] = []

        def from_bytes(self, data, offset=0) -> Tuple['TopLevelThreadGroupReply', int]:
            count, offset = Jdwp.parse_int(data, offset)
            for _ in range(count):
                value, offset = Jdwp.parse_long(data, offset, ThreadGroupID)
                self.groups = [*self.groups, value]
            return self, offset


    async def TopLevelThreadGroup(self) -> TopLevelThreadGroupReply:
        await self.conn.send(1, 5)
        data, _, _, _ = await self.conn.recv()
        return TopLevelThreadGroupReply().from_bytes(data)
    

    async def Dispose(self) -> None:
        await self.conn.send(1, 6)
    

    class IDSizesReply(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        fieldIDSize: Optional[Int] = None
        methodIDSize: Optional[Int] = None
        objectIDSize: Optional[Int] = None
        referenceTypeIDSize: Optional[Int] = None
        frameIDSize: Optional[Int] = None

        def from_bytes(self, data, offset) -> Tuple['IDSizesReply', int]:
            self.fieldIDSize, offset = Jdwp.parse_int(data, offset, Int)
            self.methodIDSize, offset = Jdwp.parse_int(data, offset, Int)
            self.objectIDSize, offset = Jdwp.parse_int(data, offset, Int)
            self.referenceTypeIDSize, offset = Jdwp.parse_int(data, offset, Int)
            self.frameIDSize, offset = Jdwp.parse_int(data, offset, Int)
            return self, offset


    async def IDSizes(self) -> IDSizesReply:
        await self.conn.send(1, 7)
        data, _, _, _ = await self.conn.recv()
        return IDSizesReply().from_bytes(data)[0]
    

    async def Suspend(self) -> None:
        await self.conn.send(1, 8)
        #data, _, _, error_code = await self.conn.recv()
    

    async def Resume(self) -> None:
        await self.conn.send(1, 9)
    

    async def Exit(self, exit_code: Int) -> None:
        await self.conn.send(1, 10, data=Jdwp.make_int(exit_code))


    async def CreateString(self, utf: String) -> StringID:
        await self.conn.send(1, 11, data=Jdwp.make_string(utf))
        data, _, _, _ = await self.conn.recv()
        return Jdwp.parse_long(data, 0, String)[0]


    class CapabilitiesReply(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        canWatchFieldModification: Optional[Boolean] = None
        canWatchFieldAccess: Optional[Boolean] = None
        canGetBytecodes: Optional[Boolean] = None
        canGetSyntheticAttribute: Optional[Boolean] = None
        canGetOwnedMonitorInfo: Optional[Boolean] = None
        canGetCurrentContendedMonitor: Optional[Boolean] = None
        canGetMonitorInfo: Optional[Boolean] = None

        def from_bytes(self, data, offset) -> Tuple['CapabilitiesReply', int]:
            self.canWatchFieldModification, offset = Jdwp.parse_byte(data, offset, Boolean)
            self.canWatchFieldAccess, offset = Jdwp.parse_byte(data, offset, Boolean)
            self.canGetBytecodes, offset = Jdwp.parse_byte(data, offset, Boolean)
            self.canGetSyntheticAttribute, offset = Jdwp.parse_byte(data, offset, Boolean)
            self.canGetOwnedMonitorInfo, offset = Jdwp.parse_byte(data, offset, Boolean)
            self.canGetCurrentContendedMonitor, offset = Jdwp.parse_byte(data, offset, Boolean)
            self.canGetMonitorInfo, offset = Jdwp.parse_byte(data, offset, Boolean)
            return self, offset


    async def Capabilities(self) -> CapabilitiesReply:
        await self.conn.send(1, 12)
        data, _, _, _ = await self.conn.recv()
        return CapabilitiesReply().from_bytes(data)[0]


    class ClassPathsReply(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        classpaths: List[String] = []
        bootclasspaths: List[String] = []

        def from_bytes(self, data, offset=0) -> Tuple['ClassPathsReply', int]:
            count, offset = Jdwp.parse_int(data, offset)
            for _ in range(count):
                entry, offset = Jdwp.parse_string(data, offset, String)
                self.classpaths = [*self.classpaths, entry]
            
            count, offset = Jdwp.parse_int(data, offset)
            for _ in range(count):
                entry, offset = Jdwp.parse_string(data, offset, String)
                self.bootclasspaths = [*self.bootclasspaths, entry]
            return self, offset


    async def ClassPaths(self) -> ClassPathsReply:
        await self.conn.send(1, 13)
        data, _, _, _ = await self.conn.recv()
        return ClassPathsReply().from_bytes(data)
    

    class DisposeObjectsEntry(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        objectID: Optional[ObjectID] = None
        refCnt: Optional[Int] = None

        def to_bytes(self) -> bytes:
            return b''.join([
                Jdwp.make_long(self.objectID),
                Jdwp.make_int(self.refCnt)
            ])


    class DisposeObjectsRequest(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        requests: List[DisposeObjectsEntry] = []

        def to_bytes(self) -> bytes:
            out = [Jdwp.make_int(len(self.requests))]
            for request in self.requests:
                out.append(request.to_bytes())
            return b''.join(out)


    async def DisposeObjects(self, request: DisposeObjectsRequest) -> None:
        await self.conn.send(1, 14, data=request.to_bytes())


    async def HoldEvents(self) -> None:
        await self.conn.send(1, 15)


    async def ReleaseEvents(self) -> None:
        await self.conn.send(1, 16)
    

    class CapabilitiesNewReply(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        canWatchFieldModification: Optional[Boolean] = None
        canWatchFieldAccess: Optional[Boolean] = None
        canGetBytecodes: Optional[Boolean] = None
        canGetSyntheticAttribute: Optional[Boolean] = None
        canGetOwnedMonitorInfo: Optional[Boolean] = None
        canGetCurrentContendedMonitor: Optional[Boolean] = None
        canGetMonitorInfo: Optional[Boolean] = None
        # The new stuff
        canRedefineClasses: Optional[Boolean] = None
        canAddMethod: Optional[Boolean] = None
        canUnrestrictedlyRedefineClasses: Optional[Boolean] = None
        canPopFrames: Optional[Boolean] = None
        canUseInstanceFilters: Optional[Boolean] = None
        canGetSourceDebugExtension: Optional[Boolean] = None
        canRequestVMDeathEvent: Optional[Boolean] = None
        canSetDefaultStratum: Optional[Boolean] = None
        canGetInstanceInfo: Optional[Boolean] = None
        canRequestMonitorEvents: Optional[Boolean] = None
        canGetMonitorFrameInfo: Optional[Boolean] = None
        canUseSourceNameFilters: Optional[Boolean] = None
        canGetConstantPool: Optional[Boolean] = None
        canForceEarlyReturn: Optional[Boolean] = None
        reserved22: Optional[Boolean] = None
        reserved23: Optional[Boolean] = None
        reserved24: Optional[Boolean] = None
        reserved25: Optional[Boolean] = None
        reserved26: Optional[Boolean] = None
        reserved27: Optional[Boolean] = None
        reserved28: Optional[Boolean] = None
        reserved29: Optional[Boolean] = None
        reserved30: Optional[Boolean] = None
        reserved31: Optional[Boolean] = None
        reserved32: Optional[Boolean] = None

        def from_bytes(self, data, offset) -> Tuple['CapabilitiesNewReply', int]:
            self.canWatchFieldModification, offset = Jdwp.parse_byte(data, offset, Boolean)
            self.canWatchFieldAccess, offset = Jdwp.parse_byte(data, offset, Boolean)
            self.canGetBytecodes, offset = Jdwp.parse_byte(data, offset, Boolean)
            self.canGetSyntheticAttribute, offset = Jdwp.parse_byte(data, offset, Boolean)
            self.canGetOwnedMonitorInfo, offset = Jdwp.parse_byte(data, offset, Boolean)
            self.canGetCurrentContendedMonitor, offset = Jdwp.parse_byte(data, offset, Boolean)
            self.canGetMonitorInfo, offset = Jdwp.parse_byte(data, offset, Boolean)
            # The new stuff
            self.canRedefineClasses, offset = Jdwp.parse_byte(data, offset, Boolean)
            self.canAddMethod, offset = Jdwp.parse_byte(data, offset, Boolean)
            self.canUnrestrictedlyRedefineClasses, offset = Jdwp.parse_byte(data, offset, Boolean)
            self.canPopFrames, offset = Jdwp.parse_byte(data, offset, Boolean)
            self.canUseInstanceFilters, offset = Jdwp.parse_byte(data, offset, Boolean)
            self.canGetSourceDebugExtension, offset = Jdwp.parse_byte(data, offset, Boolean)
            self.canRequestVMDeathEvent, offset = Jdwp.parse_byte(data, offset, Boolean)
            self.canSetDefaultStratum, offset = Jdwp.parse_byte(data, offset, Boolean)
            self.canGetInstanceInfo, offset = Jdwp.parse_byte(data, offset, Boolean)
            self.canRequestMonitorEvents, offset = Jdwp.parse_byte(data, offset, Boolean)
            self.canGetMonitorFrameInfo, offset = Jdwp.parse_byte(data, offset, Boolean)
            self.canUseSourceNameFilters, offset = Jdwp.parse_byte(data, offset, Boolean)
            self.canGetConstantPool, offset = Jdwp.parse_byte(data, offset, Boolean)
            self.canForceEarlyReturn, offset = Jdwp.parse_byte(data, offset, Boolean)
            self.reserved22, offset = Jdwp.parse_byte(data, offset, Boolean)
            self.reserved23, offset = Jdwp.parse_byte(data, offset, Boolean)
            self.reserved24, offset = Jdwp.parse_byte(data, offset, Boolean)
            self.reserved25, offset = Jdwp.parse_byte(data, offset, Boolean)
            self.reserved26, offset = Jdwp.parse_byte(data, offset, Boolean)
            self.reserved27, offset = Jdwp.parse_byte(data, offset, Boolean)
            self.reserved28, offset = Jdwp.parse_byte(data, offset, Boolean)
            self.reserved29, offset = Jdwp.parse_byte(data, offset, Boolean)
            self.reserved30, offset = Jdwp.parse_byte(data, offset, Boolean)
            self.reserved31, offset = Jdwp.parse_byte(data, offset, Boolean)
            self.reserved32, offset = Jdwp.parse_byte(data, offset, Boolean)
            return self, offset


    async def CapabilitiesNew(self) -> CapabilitiesNewReply:
        await self.conn.send(1, 17)
        data, _, _, _ = await self.conn.recv()
        return CapabilitiesNewReply().from_bytes(data)


    class RedefineClassesRequest(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        refType: Optional[ReferenceTypeID] = None
        classfile: List[Byte] = []

        def to_bytes(self) -> bytes:
            out = [
                Jdwp.make_long(self.refType),
                Jdwp.make_int(len(self.classfile))
            ]
            out.extend([bytes([entry]) for entry in self.classfile])
            return b''.join(out)


    async def RedefineClasses(self, request: RedefineClassesRequest) -> None:
        await self.conn.send(1, 18, data=request.to_bytes())


    async def SetDefaultStratum(self, stratumID: String) -> None:
        await self.conn.send(1, 19, data=Jdwp.make_string(stratumID))


    class AllClassesWithGenericEntry(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        refTypeTag: Optional[Byte] = None
        typeID: Optional[ReferenceTypeID] = None
        signature: Optional[String] = None
        genericString: Optional[String] = None
        status: Optional[Int] = None

        def from_bytes(self, data, offset=0) -> Tuple['AllClassesWithGenericEntry', int]:
            self.refTypeTag, offset = Jdwp.parse_byte(data, offset, Byte)
            self.typeID, offset = Jdwp.parse_long(data, offset, ReferenceTypeID)
            self.signature, offset = Jdwp.parse_string(data, offset, String)
            self.genericString, offset = Jdwp.parse_string(data, offset, String)
            self.status, offset = Jdwp.parse_int(data, offset, Int)
            return self, offset


    class AllClassesWithGenericReply(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        classes: List[AllClassesWithGenericEntry] = []

        def from_bytes(self, data, offset=0) -> Tuple['AllClassesWithGenericReply', int]:
            count, offset = Jdwp.parse_int(data, offset)
            for _ in range(count):
                entry, offset = AllClassesWithGenericEntry().from_bytes(data, offset)
                self.classes = [*self.classes, entry]
            return self, offset


    async def AllClassesWithGeneric(self) -> AllClassesWithGenericReply:
        await self.conn.send(1, 20)
        data, _, _, _ = await self.conn.recv()
        return AllClassesWithGenericReply().from_bytes(data)


    class InstanceCountsRequest(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        refTypes: List[ReferenceTypeID] = []

        def to_bytes(self) -> bytes:
            out = [Jdwp.make_int(len(self.refTypes))]
            out.extend([Jdwp.make_long(refType) for refType in self.refTypes])
            return b''.join(out)


    class InstanceCountsReply(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        instanceCounts: List[Long] = []

        def from_bytes(self, data, offset=0) -> Tuple['InstanceCountsReply', int]:
            count, offset = Jdwp.parse_int(data, offset)
            for _ in range(count):
                value, offset = Jdwp.parse_long(data, offset, Long)
                self.instanceCounts = [*self.instanceCounts, value]
            return self, offset


    async def InstanceCounts(self, request: InstanceCountsRequest) -> InstanceCountsReply:
        await self.conn.send(1, 21, data=request.to_bytes())
        data, _, _, _ = await self.conn.recv()
        return InstanceCountsReply().from_bytes(data)


class ReferenceTypeSet():

    def __init__(self, conn):
        self.conn = conn
    

    async def Signature(self, refType: ReferenceTypeID) -> String:
        await self.conn.send(2, 1, data=Jdwp.make_long(refType))
        data, _, _, _ = await self.conn.recv()
        return Jdwp.parse_string(data, 0, String)[0]


    async def ClassLoader(self, refType: ReferenceTypeID) -> ClassLoaderID:
        await self.conn.send(2, 2, data=Jdwp.make_long(refType))
        data, _, _, _ = await self.conn.recv()
        return Jdwp.parse_long(data, 0, ClassLoaderID)[0]

    
    async def Modifiers(self, refType: ReferenceTypeID) -> Int:
        await self.conn.send(2, 3, data=Jdwp.make_long(refType))
        data, _, _, _ = await self.conn.recv()
        return Jdwp.parse_int(data, 0, Int)[0]


    class FieldsDeclaredEntry(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        fieldID: Optional[FieldID] = None
        name: Optional[String] = None
        signature: Optional[String] = None
        modBits: Optional[Int] = None

        def from_bytes(self, data, offset=0) -> Tuple['FieldsDeclaredEntry', int]:
            self.fieldID, offset = Jdwp.parse_long(data, offset, FieldID)
            self.name, offset = Jdwp.parse_string(data, offset, String)
            self.signature, offset = Jdwp.parse_string(data, offset, String)
            self.modBits, offset = Jdwp.parse_int(data, offset, Int)
            return self, offset


    class FieldsReply(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        declared: List[FieldsDeclaredEntry] = []

        def from_bytes(self, data, offset=0) -> Tuple['FieldsReply', int]:
            count, offset = Jdwp.parse_int(data, offset)
            for _ in range(count):
                entry, offset = FieldsDeclaredEntry().from_bytes(data, offset)
                self.declared = [*self.declared, entry]
            return self, offset

    
    async def Fields(self, refType: ReferenceTypeID) -> FieldsReply:
        await self.conn.send(2, 4, data=Jdwp.make_long(refType))
        data, _, _, _ = await self.conn.recv()
        return FieldsReply().from_bytes(data)[0]


    class MethodsDeclaredEntry(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        methodID: Optional[MethodID] = None
        name: Optional[String] = None
        signature: Optional[String] = None
        modBits: Optional[Int] = None

        def from_bytes(self, data, offset=0) -> Tuple['MethodsDeclaredEntry', int]:
            self.methodID, offset = Jdwp.parse_long(data, offset, MethodID)
            self.name, offset = Jdwp.parse_string(data, offset, String)
            self.signature, offset = Jdwp.parse_string(data, offset, String)
            self.modBits, offset = Jdwp.parse_int(data, offset, Int)
            return self, offset


    class MethodsReply(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        declared: List[MethodsDeclaredEntry] = []

        def from_bytes(self, data, offset=0) -> Tuple['MethodsReply', int]:
            count, offset = Jdwp.parse_int(data, offset)
            for _ in range(count):
                entry, offset = MethodsDeclaredEntry().from_bytes(data, offset)
                self.declared = [*self.declared, entry]
            return self, offset


    async def Methods(self, refType: ReferenceTypeID) -> MethodsReply:
        await self.conn.send(2, 5, data=Jdwp.make_long(refType))
        data, _, _, _ = await self.conn.recv()
        return MethodsReply().from_bytes(data)[0]

    
    # !! Need to implement TaggedValues
    # https://docs.oracle.com/javase/8/docs/platform/jpda/jdwp/jdwp-protocol.html#JDWP_Tag
    # class GetValuesRequest(BaseModel):
    #     model_config = ConfigDict(validate_assignment=True)
    #     refType: ReferenceTypeID
    #     fields: List[FieldID] = []

    #     def to_bytes(self) -> bytes:
    #         out = [Jdwp.make_long(self.refType), Jdwp.make_int(len(self.fields))]
    #         out.extend([Jdwp.make_long(fieldID) for fieldID in self.fields])
    #         return b''.join(out)


    # class GetValuesReply(BaseModel):
    #     model_config = ConfigDict(validate_assignment=True)
    #     values: List[Long] = []

    #     def from_bytes(self, data, offset=0) -> Tuple['InstanceCountsReply', int]:
    #         count, offset = Jdwp.parse_int(data, offset)
    #         for _ in range(count):
    #             value, offset = Jdwp.parse_long(data, offset)
    #             self.instanceCounts = [*self.instanceCounts, Long(value)]
    #         return self, offset


    # async def GetValues(self, *args):
    #     #await self.conn.send(1, 6)
    #     raise NotImplementedError("GetValues not implemented.")


    async def SourceFile(self, refType: ReferenceTypeID) -> String:
        await self.conn.send(2, 7, data=Jdwp.make_long(refType))
        data, _, _, _ = await self.conn.recv()
        return Jdwp.parse_string(data, 0, String)[0]


    class NestedTypesEntry(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        refTypeTag: Optional[Byte] = None
        typeID: Optional[ReferenceTypeID] = None

        def from_bytes(self, data, offset=0) -> Tuple['NestedTypesEntry', int]:
            self.refTypeTag, offset = Jdwp.parse_byte(data, offset, Byte)
            self.typeID, offset = Jdwp.parse_long(data, offset, ReferenceTypeID)
            return self, offset


    class NestedTypesReply(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        classes: List[NestedTypesEntry] = []

        def from_bytes(self, data, offset=0) -> Tuple['NestedTypesReply', int]:
            count, offset = Jdwp.parse_int(data, offset)
            for _ in range(count):
                value, offset = NestedTypesEntry().from_bytes(data)
                self.classes = [*self.classes, value]
            return self, offset

    
    async def NestedTypes(self, refType: ReferenceTypeID) -> NestedTypesReply:
        await self.conn.send(2, 8, data=Jdwp.make_long(refType))
        data, _, _, _ = await self.conn.recv()
        return NestedTypesReply().from_bytes(data)[0]
    

    async def Status(self, refType: ReferenceTypeID):
        await self.conn.send(2, 9, data=Jdwp.make_long(refType))
        data, _, _, _ = await self.conn.recv()
        return Jdwp.parse_int(data, 0, Int)[0]


    class InterfacesReply(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        interfaces: List[InterfaceID] = []

        def from_bytes(self, data, offset=0) -> Tuple['InterfacesReply', int]:
            count, offset = Jdwp.parse_int(data, offset)
            for _ in range(count):
                value, offset = Jdwp.parse_long(data, offset, InterfaceID)
                self.interfaces = [*self.interfaces, value]
            return self, offset

    
    async def Interfaces(self, refType: ReferenceTypeID) -> InterfacesReply:
        await self.conn.send(2, 10, data=Jdwp.make_long(refType))
        data, _, _, _ = await self.conn.recv()
        return InterfacesReply().from_bytes(data)[0]


    async def ClassObject(self, refType: ReferenceTypeID) -> ClassObjectID:
        await self.conn.send(2, 11, data=Jdwp.make_long(refType))
        data, _, _, _ = await self.conn.recv()
        return Jdwp.parse_long(data, 0, ClassObjectID)[0]
    

    async def SourceDebugExtension(self, refType: ReferenceTypeID) -> String:
        await self.conn.send(2, 12, data=Jdwp.make_long(refType))
        data, _, _, _ = await self.conn.recv()
        return Jdwp.parse_string(data, 0, String)[0]

    
    class SignatureWithGenericReply(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        signature: Optional[String] = None
        genericSignature: Optional[String] = None

        def from_bytes(self, data, offset=0) -> Tuple['SignatureWithGenericReply', int]:
            self.signature, offset = Jdwp.parse_byte(data, offset, String)
            self.genericSignature, offset = Jdwp.parse_long(data, offset, String)
            return self, offset


    async def SignatureWithGeneric(self, refType: ReferenceTypeID) -> SignatureWithGenericReply:
        await self.conn.send(2, 13, data=Jdwp.make_long(refType))
        data, _, _, _ = await self.conn.recv()
        return SignatureWithGenericReply().from_bytes(data)[0]
    

    class FieldsWithGenericEntry(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        fieldID: Optional[FieldID] = None
        name: Optional[String] = None
        signature: Optional[String] = None
        genericSignature: Optional[String] = None
        modBits: Optional[Int] = None

        def from_bytes(self, data, offset=0) -> Tuple['FieldsWithGenericEntry', int]:
            self.fieldID, offset = Jdwp.parse_long(data, offset, FieldID)
            self.name, offset = Jdwp.parse_string(data, offset, String)
            self.signature, offset = Jdwp.parse_string(data, offset, String)
            self.genericSignature, offset = Jdwp.parse_string(data, offset, String)
            self.modBits, offset = Jdwp.parse_int(data, offset, Int)
            return self, offset


    class FieldsWithGenericReply(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        declared: List[FieldsWithGenericEntry] = []

        def from_bytes(self, data, offset=0) -> Tuple['FieldsWithGenericReply', int]:
            count, offset = Jdwp.parse_int(data, offset)
            for _ in range(count):
                value, offset = FieldsWithGenericEntry().from_bytes(data)
                self.declared = [*self.declared, value]
            return self, offset


    async def FieldsWithGeneric(self, refType: ReferenceTypeID) -> FieldsWithGenericReply:
        await self.conn.send(2, 14, data=Jdwp.make_long(refType))
        data, _, _, _ = await self.conn.recv()
        return FieldsWithGenericReply().from_bytes(data)[0]


    class MethodsWithGenericEntry(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        methodID: Optional[MethodID] = None
        name: Optional[String] = None
        signature: Optional[String] = None
        genericSignature: Optional[String] = None
        modBits: Optional[Int] = None

        def from_bytes(self, data, offset=0) -> Tuple['MethodsWithGenericEntry', int]:
            self.fieldID, offset = Jdwp.parse_long(data, offset, FieldID)
            self.name, offset = Jdwp.parse_string(data, offset, String)
            self.signature, offset = Jdwp.parse_string(data, offset, String)
            self.genericSignature, offset = Jdwp.parse_string(data, offset, String)
            self.modBits, offset = Jdwp.parse_int(data, offset, Int)
            return self, offset


    class MethodsWithGenericReply(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        declared: List[MethodsWithGenericEntry] = []

        def from_bytes(self, data, offset=0) -> Tuple['MethodsWithGenericReply', int]:
            count, offset = Jdwp.parse_int(data, offset)
            for _ in range(count):
                value, offset = MethodsWithGenericEntry().from_bytes(data)
                self.declared = [*self.declared, value]
            return self, offset

    
    async def MethodsWithGeneric(self, refType: ReferenceTypeID) -> MethodsWithGenericReply:
        await self.conn.send(2, 15, data=Jdwp.make_long(refType))
        data, _, _, _ = await self.conn.recv()
        return MethodsWithGenericReply().from_bytes(data)[0]


    # !! Need to implement TaggedObjectID
    # class InstancesRequest(BaseModel):
    #     model_config = ConfigDict(validate_assignment=True)
    #     refType: Optional[ReferenceTypeID] = None
    #     maxInstances: Optional[Int] = None

    #     def to_bytes(self) -> bytes:
    #         return b''.join([Jdwp.make_long(self.refType), Jdwp.make_int(self.maxInstances)])


    # class InstancesReply(BaseModel):
    #     model_config = ConfigDict(validate_assignment=True)
    #     instances: List[TaggedObjectID] = []

    #     def from_bytes(self, data, offset=0) -> Tuple['InstancesReply', int]:
    #         count, offset = Jdwp.parse_int(data, offset)
    #         for _ in range(count):
    #             value, offset = Jdwp.parse_long(data, offset, Long)
    #             self.instanceCounts = [*self.instanceCounts, value]
    #         return self, offset

    
    # async def Instances(self, request: InstancesRequest) -> InstancesReply:
    #     await self.conn.send(1, 16, data=request.to_bytes())
    #     data, _, _, _ = await self.conn.recv()
    #     return InstancesReply().from_bytes(data)[0]
        
    
    class ClassFileVersionReply(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        majorVersion: Optional[Int] = None
        minorVersion: Optional[Int] = None

        def from_bytes(self, data, offset=0) -> Tuple['ClassFileVersionReply', int]:
            self.majorVersion, offset = Jdwp.parse_int(data, offset, Int)
            self.minorVersion, offset = Jdwp.parse_string(data, offset, Int)
            return self, offset

    
    async def ClassFileVersion(self, refType: ReferenceTypeID) -> ClassFileVersionReply:
        await self.conn.send(2, 17, data=Jdwp.make_long(refType))
        data, _, _, _ = await self.conn.recv()
        return ClassFileVersionReply().from_bytes(data)[0]


    class ConstantPoolReply(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        count: Optional[Int] = None
        cpbytes: List[Byte] = []

        def from_bytes(self, data, offset=0) -> Tuple['ConstantPoolReply', int]:
            self.count, offset = Jdwp.parse_int(data, offset, Int)
            count, offset = Jdwp.parse_int(data, offset)
            for _ in range(count):
                value, offset = Jdwp.parse_byte(data, offset, Byte)
                self.cpbytes = [*self.cpbytes, value]
            return self, offset

    
    async def ConstantPool(self, refType: ReferenceTypeID) -> ConstantPoolReply:
        await self.conn.send(2, 18, data=Jdwp.make_long(refType))
        data, _, _, _ = await self.conn.recv()
        return ConstantPoolReply().from_bytes(data)[0]

    
class ClassTypeSet():

    def __init__(self, conn):
        self.conn = conn


    async def Superclass(self, clazz: ClassID) -> ClassID:
        await self.conn.send(3, 1, data=Jdwp.make_long(clazz))
        data, _, _, _ = await self.conn.recv()
        return Jdwp.parse_long(data, 0, ClassID)[0]

    
    # !! Need to implement untagged value
    # !! I have no idea what is happening here... do we call GetValues to track value size?
    # class SetValuesEntry(BaseModel):
    #     model_config = ConfigDict(validate_assignment=True)
    #     fieldID: Optional[FieldID] = None
    #     value:  Optional[UntaggedValue] = None

    #     def to_bytes(self) -> bytes:
    #         out = [Jdwp.make_long(self.refType), Jdwp.make_int(len(self.fields))]
    #         out.extend([Jdwp.make_long(fieldID) for fieldID in self.fields])
    #         return b''.join(out)


    # class SetValuesRequest(BaseModel):
    #     model_config = ConfigDict(validate_assignment=True)
    #     clazz: ClassID
    #     values: List[SetValuesEntry] = []

    #     def to_bytes(self) -> bytes:
    #         out = [Jdwp.make_long(self.refType), Jdwp.make_int(len(self.fields))]
    #         out.extend([Jdwp.make_long(fieldID) for fieldID in self.fields])
    #         return b''.join(out)


    # async def SetValues(self, *args):
    #     raise NotImplementedError("SetValues not implemented.")
    #     # await self.conn.send(3, 2, data=Jdwp.make_long(clazz))


    # !! Implement taggedobject
    # async def InvokeMethod(self, *args):
    #     raise NotImplementedError("InvokeMethod not implemented.")
    #     # await self.conn.send(3, 3, data=Jdwp.make_long(clazz))
    

    # !! Implement taggedobject
    # async def NewInstance(self, *args):
    #     raise NotImplementedError("NewInstance not implemented.")
    #     # await self.conn.send(3, 4, data=Jdwp.make_long(clazz))


class ArrayTypeSet():

    def __init__(self, conn):
        self.conn = conn


    # !! Implement taggedobject
    async def NewInstance(self, arrType, length):
        out = Jdwp.make_long(arrType) + Jdwp.make_int(length)
        await self.conn.send(3, 1, data=out)
        data, _, _, _ = await self.conn.recv()

        offset = 0
        result = {}
        # tagged-objectID? ... for now I'm splitting into two fields.
        result['newArrayTag'], offset = Jdwp.parse_byte(data, offset)
        result['newArrayID'], offset = Jdwp.parse_objectid(data, offset)
        return result

class InterfaceTypeSet():

    def __init__(self, conn):
        self.conn = conn

    async def InvokeMethod(self, *args):
        raise NotImplementedError("InvokeMethod not implemented.")
        # await self.conn.send(5, 1, data=Jdwp.make_long(clazz))

class MethodSet():

    def __init__(self, conn):
        self.conn = conn

    async def LineTable(self, refType: ReferenceTypeID, methodID: MethodID):
        out = Jdwp.make_long(refType) + Jdwp.make_long(methodID)
        await self.conn.send(6, 1, data=out)
        data, _, _, _ = await self.conn.recv()

        offset = 0
        result = {'lines': []}
        result['start'], offset = Jdwp.parse_long(data, offset)
        result['end'], offset = Jdwp.parse_long(data, offset)
        count, offset = Jdwp.parse_int(data, offset)
        for _ in range(count):
            entry = {}
            entry['lineCodeIndex'], offset = Jdwp.parse_long(data, offset)
            entry['lineNumber'], offset = Jdwp.parse_int(data, offset)
            result['lines'].append(entry)
        return result
    
    async def VariableTable(self, refType: ReferenceTypeID, methodID: MethodID):
        out = Jdwp.make_long(refType) + Jdwp.make_long(methodID)
        await self.conn.send(6, 2, data=out)
        data, _, _, _ = await self.conn.recv()

        offset = 0
        result = {'slots': []}
        result['argCnt'], offset = Jdwp.parse_int(data, offset)
        count, offset = Jdwp.parse_int(data, offset)
        for _ in range(count):
            entry = {}
            entry['codeIndex'], offset = Jdwp.parse_long(data, offset)
            entry['name'], offset = Jdwp.parse_string(data, offset)
            entry['signature'], offset = Jdwp.parse_string(data, offset)
            entry['length'], offset = Jdwp.parse_int(data, offset)
            entry['slot'], offset = Jdwp.parse_int(data, offset)
            result['slots'].append(entry)
        return result
    
    async def Bytecodes(self, refType: ReferenceTypeID, methodID: MethodID):
        out = Jdwp.make_long(refType) + Jdwp.make_long(methodID)
        await self.conn.send(6, 3, data=out)
        data, _, _, _ = await self.conn.recv()

        offset = 0
        byte_count, offset = Jdwp.parse_int(data, offset)
        return {'bytes': data[offset:offset+byte_count]}
        
    async def IsObsolete(self, refType: ReferenceTypeID, methodID: MethodID):
        out = Jdwp.make_long(refType) + Jdwp.make_long(methodID)
        await self.conn.send(6, 4, data=out)
        data, _, _, _ = await self.conn.recv()

        offset = 0
        obsolete, offset = Jdwp.parse_byte(data, offset)
        return {'isObsolete': obsolete}
    
    async def VariableTableWithGeneric(self, refType: ReferenceTypeID, methodID: MethodID):
        out = Jdwp.make_long(refType) + Jdwp.make_long(methodID)
        await self.conn.send(6, 2, data=out)
        data, _, _, _ = await self.conn.recv()

        offset = 0
        result = {'slots': []}
        result['argCnt'], offset = Jdwp.parse_int(data, offset)
        count, offset = Jdwp.parse_int(data, offset)
        for _ in range(count):
            entry = {}
            entry['codeIndex'], offset = Jdwp.parse_long(data, offset)
            entry['name'], offset = Jdwp.parse_string(data, offset)
            entry['signature'], offset = Jdwp.parse_string(data, offset)
            entry['genericSignature'], offset = Jdwp.parse_string(data, offset)
            entry['length'], offset = Jdwp.parse_int(data, offset)
            entry['slot'], offset = Jdwp.parse_int(data, offset)
            result['slots'].append(entry)
        return result

# class FieldSet():

#     def __init__(self, conn):
#         self.conn = conn

class ObjectReferenceSet():

    def __init__(self, conn):
        self.conn = conn
    
    async def ReferenceType(self, objectid: ObjectID):
        await self.conn.send(9, 1, data=Jdwp.make_long(objectid))
        data, _, _, _ = await self.conn.recv()

        offset = 0
        result = {}
        # tagged-objectID? ... for now I'm splitting into two fields.
        result['refTypeTag'], offset = Jdwp.parse_byte(data, offset)
        result['typeID'], offset = Jdwp.parse_objectid(data, offset)
        return result
    
    async def GetValues(self, *args):
        raise NotImplementedError("GetValues not implemented.")
        # await self.conn.send(9, 2, data=Jdwp.make_long(clazz))
    
    async def SetValues(self, *args):
        raise NotImplementedError("SetValues not implemented.")
        # await self.conn.send(9, 3, data=Jdwp.make_long(clazz))
    
    async def MonitorInfo(self, objectid: ObjectID):
        await self.conn.send(9, 5, data=Jdwp.make_long(objectid))
        data, _, _, _ = await self.conn.recv()

        offset = 0
        result = {'waiters': []}
        # tagged-objectID? ... for now I'm splitting into two fields.
        result['owner'], offset = Jdwp.parse_objectid(data, offset)
        result['entryCount'], offset = Jdwp.parse_int(data, offset)
        count, offset = Jdwp.parse_int(data, offset)
        for _ in range(count):
            entry = {}
            entry['thread'], offset = Jdwp.parse_objectid(data, offset)
            result['waiters'].append(entry)
        return result

    async def InvokeMethod(self, *args):
        raise NotImplementedError("InvokeMethod not implemented.")
        # await self.conn.send(9, 6, data=Jdwp.make_long(clazz))
    
    async def DisableCollection(self, objectid: ObjectID):
        await self.conn.send(9, 7, data=Jdwp.make_long(objectid))
        #data, _, _, _ = await self.conn.recv()
    
    async def EnableCollection(self, objectid: ObjectID):
        await self.conn.send(9, 8, data=Jdwp.make_long(objectid))
        #data, _, _, _ = await self.conn.recv()
    
    async def IsCollected(self, objectid: ObjectID):
        await self.conn.send(9, 9, data=Jdwp.make_long(objectid))
        data, _, _, _ = await self.conn.recv()

        offset = 0
        result = {}
        result['isCollected'], offset = Jdwp.parse_byte(data, offset)
        return result
    
    async def ReferringObjects(self, objectid: ObjectID, maxReferrers: Int):
        out = Jdwp.make_long(objectid) + Jdwp.make_int(maxReferrers)
        await self.conn.send(9, 10, data=out)
        data, _, _, _ = await self.conn.recv()

        offset = 0
        result = {'referringObjects': []}
        count, offset = Jdwp.parse_int(data, offset)
        for _ in range(count):
            entry = {}
            # tagged-objectID? ... for now I'm splitting into two fields.
            entry['instanceTag'], offset = Jdwp.parse_byte(data, offset)
            entry['instanceID'], offset = Jdwp.parse_objectid(data, offset)
            result['referringObjects'].append(entry)
        return result

class StringReferenceSet():

    def __init__(self, conn):
        self.conn = conn

    async def IsCollected(self, stringObject: ObjectID):
        await self.conn.send(10, 1, data=Jdwp.make_long(stringObject))
        data, _, _, _ = await self.conn.recv()

        offset = 0
        result = {}
        result['stringValue'], offset = Jdwp.parse_string(data, offset)
        return result

class ThreadReferenceSet():

    def __init__(self, conn):
        self.conn = conn

    async def Name(self, thread: ThreadID):
        await self.conn.send(11, 1, data=Jdwp.make_long(thread))
        data, _, _, _ = await self.conn.recv()

        offset = 0
        result = {}
        result['threadName'], offset = Jdwp.parse_string(data, offset)
        return result
    
    async def Suspend(self, thread: ThreadID):
        await self.conn.send(11, 2, data=Jdwp.make_long(thread))
        #data, _, _, _ = await self.conn.recv()

    async def Resume(self, thread: ThreadID):
        await self.conn.send(11, 3, data=Jdwp.make_long(thread))
        #data, _, _, _ = await self.conn.recv()
    
    async def Status(self, thread: ThreadID):
        await self.conn.send(11, 4, data=Jdwp.make_long(thread))
        data, _, _, _ = await self.conn.recv()

        offset = 0
        result = {}
        result['threadStatus'], offset = Jdwp.parse_int(data, offset)
        result['suspendStatus'], offset = Jdwp.parse_int(data, offset)
        return result
    
    async def ThreadGroup(self, thread: ThreadID):
        await self.conn.send(11, 4, data=Jdwp.make_long(thread))
        data, _, _, _ = await self.conn.recv()

        offset = 0
        result = {}
        result['threadGroupID'], offset = Jdwp.parse_objectid(data, offset)
        return result
