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
String = strict_typedef(type("String", (str,), {}))

#UntaggedValue = strict_typedef(type("A", (int,), {}))

class StepDepth():
    INTO = 0
    OVER = 1
    OUT = 2

class StepSize():
    MIN = 0
    LINE = 1

class SuspendPolicy():
    NONE = 0x0
    EVENT_THREAD = 0x1
    ALL = 0x2

class TypeTag():
    CLASS = 0x1
    INTERFACE = 0x2
    ARRAY = 0x3

class EventKind():
    SINGLE_STEP = 1
    BREAKPOINT = 2
    FRAME_POP = 3
    EXCEPTION = 4
    USER_DEFINED = 5
    THREAD_START = 6
    THREAD_DEATH = 7
    CLASS_PREPARE = 8
    CLASS_UNLOAD = 9
    CLASS_LOAD = 10
    FIELD_ACCESS = 20
    FIELD_MODIFICATION = 21
    EXCEPTION_CATCH = 30
    METHOD_ENTRY = 40
    METHOD_EXIT = 41
    METHOD_EXIT_WITH_RETURN_VALUE = 42
    MONITOR_CONTENDED_ENTER = 43
    MONITOR_CONTENDED_ENTERED = 44
    MONITOR_WAIT = 45
    MONITOR_WAITED = 46
    VM_START = 90
    VM_DEATH = 99
    VM_DISCONNECTED = 100 # unsent on JDWP

class Tag():
    ARRAY = 0x5b
    BYTE = 0x42
    CHAR = 0x43
    OBJECT = 0x4c  # 76
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

    u0 = [VOID]
    u8 = [BYTE, BOOLEAN]
    u16 = [CHAR, SHORT]
    u32 = [FLOAT, INT]
    u64 = [
        ARRAY,
        OBJECT,
        DOUBLE,
        LONG,
        STRING,
        THREAD,
        THREAD_GROUP,
        CLASS_LOADER,
        CLASS_OBJECT,
    ]
    objs = [
        OBJECT,
        STRING,
        ARRAY,
        THREAD,
        THREAD_GROUP,
        CLASS_LOADER,
        CLASS_OBJECT,
    ]

    @staticmethod
    def type_str(tag):
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


        _type_str = 'Unknown'
        if tag in tag_map:
            _type_str = tag_map[tag]

        return _type_str

class Error():
    NONE = 0

    string = {
        0: "NONE",
        10: "INVALID_THREAD",
        11: "INVALID_THREAD_GROUP",
        12: "INVALID_PRIORITY",
        13: "THREAD_NOT_SUSPENDED",
        14: "THREAD_SUSPENDED",
        15: "THREAD_NOT_ALIVE",
        20: "INVALID_OBJECT",
        21: "INVALID_CLASS",
        22: "CLASS_NOT_PREPARED",
        23: "INVALID_METHODID",
        24: "INVALID_LOCATION",
        25: "INVALID_FIELDID",
        30: "INVALID_FRAMEID",
        31: "NO_MORE_FRAMES",
        32: "OPAQUE_FRAME",
        33: "NOT_CURRENT_FRAME",
        34: "TYPE_MISMATCH",
        35: "INVALID_SLOT",
        40: "DUPLICATE",
        41: "NOT_FOUND",
        50: "INVALID_MONITOR",
        51: "NOT_MONITOR_OWNER",
        52: "INTERRUPT",
        60: "INVALID_CLASS_FORMAT",
        61: "CIRCULAR_CLASS_DEFINITION",
        62: "FAILS_VERIFICATION",
        63: "ADD_METHOD_NOT_IMPLEMENTED",
        64: "SCHEMA_CHANGE_NOT_IMPLEMENTED",
        65: "INVALID_TYPESTATE",
        66: "HIERARCHY_CHANGE_NOT_IMPLEMENTED",
        67: "DELETE_METHOD_NOT_IMPLEMENTED",
        68: "UNSUPPORTED_VERSION",
        69: "NAMES_DONT_MATCH",
        70: "CLASS_MODIFIERS_CHANGE_NOT_IMPLEMENTED",
        71: "METHOD_MODIFIERS_CHANGE_NOT_IMPLEMENTED",
        99: "NOT_IMPLEMENTED",
        100: "NULL_POINTER",
        101: "ABSENT_INFORMATION",
        102: "INVALID_EVENT_TYPE",
        103: "ILLEGAL_ARGUMENT",
        110: "OUT_OF_MEMORY",
        111: "ACCESS_DENIED",
        112: "VM_DEAD",
        113: "INTERNAL",
        115: "UNATTACHED_THREAD",
        500: "INVALID_TAG",
        502: "ALREADY_INVOKING",
        503: "INVALID_INDEX",
        504: "INVALID_LENGTH",
        506: "INVALID_STRING",
        507: "INVALID_CLASS_LOADER",
        508: "INVALID_ARRAY",
        509: "TRANSPORT_LOAD",
        510: "TRANSPORT_INIT",
        511: "NATIVE_METHOD",
        512: "INVALID_COUNT",
    }

class Jdwp():
    HANDSHAKE = b'JDWP-Handshake'
    REPLY_PACKET = 0x80

    Tag = Tag
    EventKind = EventKind
    TypeTag = TypeTag
    SuspendPolicy = SuspendPolicy
    StepDepth = StepDepth
    StepSize = StepSize
    Error = Error


    def __init__(self, host: str = 'localhost', port: int = 8700):
        self.host = host
        self.port = port
        self.started = False


    async def start(self):
        if not self.started:
            self.packet_id = 1
            self.pending_requests = {}
            self.event_loop = asyncio.get_running_loop()
            self.event_queue = asyncio.Queue()
            self.event_handler = {}

            self.VirtualMachine = VirtualMachineSet(self)
            self.ReferenceType = ReferenceTypeSet(self)
            self.ClassType = ClassTypeSet(self)
            self.ArrayType = ArrayTypeSet(self)
            self.InterfaceType = InterfaceTypeSet(self)
            self.Method = MethodSet(self)
            self.Field = FieldSet(self)
            self.ObjectReference = ObjectReferenceSet(self)
            self.StringReference = StringReferenceSet(self)
            self.ThreadReference = ThreadReferenceSet(self)
            self.ThreadGroupReference = ThreadGroupReferenceSet(self)
            self.ArrayReference = ArrayReferenceSet(self)
            self.ClassLoaderReference = ClassLoaderReferenceSet(self)
            self.EventRequest = EventRequestSet(self)
            self.StackFrame = StackFrameSet(self)
            self.ClassObjectReference = ClassObjectReferenceSet(self)
            self.Event = EventSet(self)

            self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
            self.writer.write(Jdwp.HANDSHAKE)
            await self.writer.drain()
            resp = await self.reader.readexactly(len(Jdwp.HANDSHAKE))
            if resp != Jdwp.HANDSHAKE:
                raise RuntimeError("Failed to receive JDWP handshake.")
            
            asyncio.create_task(self.reader_loop())
            asyncio.create_task(self.event_queue_consumer())

            self.started = True
        else:
            print("Already started. Restarting not implemented or supported.")

        return self


    async def reader_loop(self):
        while True:
            data, pkt, flags, error_code = await self.recv()

            if error_code != 0:
                print(f"JDWP error code {self.Error.string[error_code]} [{error_code}]\nData: {data.hex()}")

            if flags & Jdwp.REPLY_PACKET:
                fut = self.pending_requests.pop(pkt, None)
                if fut:
                    fut.set_result((data, pkt, flags, error_code))
            else:
                # Incoming event
                offset = 0
                cmdset, cmd = struct.unpack('>BB', data[offset:offset+2])
                offset += 2
                if cmdset != 64 or cmd != 100:
                    raise RuntimeError(f"Unsupported event received. cmdset {cmdset} cmd {cmd}")
                
                composite = self.Event.CompositeCommand().from_bytes(data, offset)[0]
                await self.event_queue.put(composite)


    # TODO: Make this a subscription based thing?
    def register_event_handler(self, requestID: Int, sync_handler, args=None):
        self.event_handler[requestID] = (sync_handler, args)

    
    async def event_queue_consumer(self):
        while True:
            composite = await self.event_queue.get()
            for event in composite.events:
                if event.requestID in self.event_handler:
                    # TODO: How do we handle the async nature of this?
                    # Note: Going to assume sync for now. Callee can convert to async if needed.
                    (handler, args) = self.event_handler[event.requestID]
                    await handler(event, composite, args)


    async def send(self, cmdset, cmd, data=b'', expect_reply=False):
        length = 11 + len(data)
        flags = 0x00
        pkt = self.packet_id
        self.packet_id += 1
        packet = struct.pack('>IIBBB', length, pkt, flags, cmdset, cmd) + data
        if expect_reply:
            self.pending_requests[pkt] = self.event_loop.create_future()
        self.writer.write(packet)
        await self.writer.drain()
        if expect_reply:
            return await self.pending_requests[pkt]

    
    async def send_and_recv(self, cmdset, cmd, data=b''):
        return await self.send(cmdset, cmd, data, True)


    async def recv(self):
        header = await self.reader.readexactly(9)
        length, pkt, flags = struct.unpack('>IIB', header)
        data_length = length - 9
        
        error_code = 0
        if flags == Jdwp.REPLY_PACKET:
            err_data = await self.reader.readexactly(2)
            error_code = struct.unpack('>H', err_data)[0]
            data_length -= 2
        
        data = await self.reader.readexactly(data_length)
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
        # TODO: Consider a uint version?
        return struct.pack('>i', val)


    @staticmethod
    def make_short(val: int) -> bytes:
        return struct.pack('>H', val)


    @staticmethod
    def make_byte(val: int) -> bytes:
        return bytes([val])


    @staticmethod
    def make_string(str_val: str) -> bytes:
        return Jdwp.make_int(len(str_val)) + str_val.encode('utf-8')


class TaggedObjectID(BaseModel):
    model_config = ConfigDict(validate_assignment=True)
    tag: Optional[Byte] = None
    # Note: Not really sure what to do here yet.
    objectID: Optional[Long] = None

    def from_bytes(self, data, offset=0) -> Tuple['TaggedObjectID', int]:
        self.tag, offset = Jdwp.parse_byte(data, offset, Byte)
        if tag not in Tag.objs:
            raise RuntimeError(f"TaggedObjectID tagged as non-object. (Tag: {tag})")
        # Note: Does this need to be some kind of union?
        self.objectID, offset = Jdwp.parse_long(data, offset, Long)
        return self, offset
        

class Value(BaseModel):
    model_config = ConfigDict(validate_assignment=True)
    tag: Optional[Byte] = None
    # Note: Not really sure what to do here yet.
    value: Optional[Long] = None

    def from_bytes(self, data, offset=0) -> Tuple['Value', int]:
        self.tag, offset = Jdwp.parse_byte(data, offset, Byte)
        if self.tag in Tag.u0:
            return self, offset
        elif self.tag in Tag.u8:
            self.value, offset = Jdwp.parse_byte(data, offset, Long)
        elif self.tag in Tag.u16:
            self.value, offset = Jdwp.parse_short(data, offset, Long)
        elif self.tag in Tag.u32:
            self.value, offset = Jdwp.parse_int(data, offset, Long)
        elif self.tag in Tag.u64:
            self.value, offset = Jdwp.parse_long(data, offset, Long)
        else:
            raise RuntimeError(f"Value tag not defined in from_bytes(). (Tag: {tag})")

        return self, offset
    
    def to_bytes(self) -> bytes:
        if self.tag in Tag.u0:
            return b''.join([Jdwp.make_byte(self.tag)])
        elif self.tag in Tag.u8:
            return b''.join([Jdwp.make_byte(self.tag), Jdwp.make_byte(self.value)])
        elif self.tag in Tag.u16:
            return b''.join([Jdwp.make_byte(self.tag), Jdwp.make_short(self.value)])
        elif self.tag in Tag.u32:
            return b''.join([Jdwp.make_byte(self.tag), Jdwp.make_int(self.value)])
        elif self.tag in Tag.u64:
            return b''.join([Jdwp.make_byte(self.tag), Jdwp.make_long(self.value)])
        
        raise RuntimeError(f"Value tag not defined in to_bytes(). (Tag: {tag})")


class Location(BaseModel):
    model_config = ConfigDict(validate_assignment=True)
    tag: Optional[Byte] = None
    classID: Optional[ClassID] = None
    methodID: Optional[MethodID] = None
    index: Optional[Long] = None

    def from_bytes(self, data, offset=0) -> Tuple['Location', int]:
        self.tag, offset = Jdwp.parse_byte(data, offset, Byte)
        self.classID, offset = Jdwp.parse_long(data, offset, ClassID)
        self.methodID, offset = Jdwp.parse_long(data, offset, MethodID)
        self.index, offset = Jdwp.parse_long(data, offset, Long)
        return self, offset
    
    def to_bytes(self) -> bytes:
        out = [
            Jdwp.make_byte(self.tag),
            Jdwp.make_long(self.classID),
            Jdwp.make_long(self.methodID),
            Jdwp.make_long(self.index),
        ]
        return b''.join(out)


class ArrayRegion(BaseModel):
    model_config = ConfigDict(validate_assignment=True)
    tag: Optional[Byte] = None
    values: List[Value] = []

    def from_bytes(self, data, offset=0) -> Tuple['ArrayRegion', int]:
        self.tag, offset = Jdwp.parse_byte(data, offset, Byte)
        count, offset = Jdwp.parse_int(data, offset)
        
        if self.tag in Tag.u0:
            raise RuntimeError("Void used in ArrayRegion.")

        elif self.tag in Tag.u8:
            for _ in range(count):
                value, offset = Jdwp.parse_byte(data, offset, Long)
                self.values = [*self.values, value]

        elif self.tag in Tag.u16:
            for _ in range(count):
                value, offset = Jdwp.parse_short(data, offset, Long)
                self.values = [*self.values, value]

        elif self.tag in Tag.u32:
            for _ in range(count):
                value, offset = Jdwp.parse_int(data, offset, Long)
                self.values = [*self.values, value]

        elif self.tag in Tag.u64:
            for _ in range(count):
                value, offset = Jdwp.parse_long(data, offset, Long)
                self.values = [*self.values, value]

        else:
            raise RuntimeError(f"Value tag not defined. (Tag: {tag})")

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

        def from_bytes(self, data, offset=0) -> Tuple['VersionReply', int]:
            self.description, offset = Jdwp.parse_string(data, offset, String)
            self.jdwpMajor, offset = Jdwp.parse_int(data, offset, Int)
            self.jdwpMinor, offset = Jdwp.parse_int(data, offset, Int)
            self.vmVersion, offset = Jdwp.parse_string(data, offset, String)
            self.vmName, offset = Jdwp.parse_string(data, offset, String)
            return self, offset


    async def Version(self) -> VersionReply:
        data, _, _, error_code = await self.conn.send_and_recv(1, 1)
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return self.VersionReply().from_bytes(data)[0], error_code


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
        classes: List['ClassesBySignatureEntry'] = []

        def from_bytes(self, data, offset=0) -> Tuple['ClassesBySignatureReply', int]:
            count, offset = Jdwp.parse_int(data, offset)
            for _ in range(count):
                value, offset = VirtualMachineSet.ClassesBySignatureEntry().from_bytes(data, offset)
                self.classes = [*self.classes, value]
            return self, offset


    async def ClassesBySignature(self, signature: String) -> Tuple[ClassesBySignatureReply, int]:
        data, _, _, error_code = await self.conn.send_and_recv(1, 2, data=Jdwp.make_string(signature))
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return self.ClassesBySignatureReply().from_bytes(data)[0], error_code


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
        classes: List['AllClassesEntry'] = []

        def from_bytes(self, data, offset=0) -> Tuple['AllClassesReply', int]:
            count, offset = Jdwp.parse_int(data, offset)
            for _ in range(count):
                value, offset = VirtualMachineSet.AllClassesEntry().from_bytes(data, offset)
                self.classes = [*self.classes, value]
            return self, offset


    async def AllClasses(self) -> Tuple[AllClassesReply, int]:
        data, _, _, error_code = await self.conn.send_and_recv(1, 3)
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return AllClassesReply().from_bytes(data)[0], error_code
    

    class AllThreadsReply(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        threads: List[ThreadID] = []

        def from_bytes(self, data, offset=0) -> Tuple['AllThreadsReply', int]:
            count, offset = Jdwp.parse_int(data, offset)
            for _ in range(count):
                value, offset = Jdwp.parse_long(data, offset, ThreadID)
                self.threads = [*self.threads, value]
            return self, offset


    async def AllThreads(self) -> Tuple[AllClassesReply, int]:
        data, _, _, error_code = await self.conn.send_and_recv(1, 4)
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return self.AllThreadsReply().from_bytes(data)[0], error_code
    

    class TopLevelThreadGroupReply(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        groups: List[ThreadGroupID] = []

        def from_bytes(self, data, offset=0) -> Tuple['TopLevelThreadGroupReply', int]:
            count, offset = Jdwp.parse_int(data, offset)
            for _ in range(count):
                value, offset = Jdwp.parse_long(data, offset, ThreadGroupID)
                self.groups = [*self.groups, value]
            return self, offset


    async def TopLevelThreadGroup(self) -> Tuple[TopLevelThreadGroupReply, int]:
        data, _, _, error_code = await self.conn.send_and_recv(1, 5)
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return self.TopLevelThreadGroupReply().from_bytes(data)[0], error_code
    

    async def Dispose(self) -> None:
        await self.conn.send(1, 6)
    

    class IDSizesReply(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        fieldIDSize: Optional[Int] = None
        methodIDSize: Optional[Int] = None
        objectIDSize: Optional[Int] = None
        referenceTypeIDSize: Optional[Int] = None
        frameIDSize: Optional[Int] = None

        def from_bytes(self, data, offset=0) -> Tuple['IDSizesReply', int]:
            self.fieldIDSize, offset = Jdwp.parse_int(data, offset, Int)
            self.methodIDSize, offset = Jdwp.parse_int(data, offset, Int)
            self.objectIDSize, offset = Jdwp.parse_int(data, offset, Int)
            self.referenceTypeIDSize, offset = Jdwp.parse_int(data, offset, Int)
            self.frameIDSize, offset = Jdwp.parse_int(data, offset, Int)
            return self, offset


    async def IDSizes(self) -> Tuple[IDSizesReply, int]:
        data, _, _, error_code = await self.conn.send_and_recv(1, 7)
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return self.IDSizesReply().from_bytes(data)[0], error_code
    

    async def Suspend(self) -> None:
        await self.conn.send(1, 8)
    

    async def Resume(self) -> None:
        await self.conn.send(1, 9)
    

    async def Exit(self, exit_code: Int) -> None:
        await self.conn.send(1, 10, data=Jdwp.make_int(exit_code))


    async def CreateString(self, utf: String) -> Tuple[StringID, int]:
        data, _, _, error_code = await self.conn.send_and_recv(1, 11, data=Jdwp.make_string(utf))
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return Jdwp.parse_long(data, 0, String)[0], error_code


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


    async def Capabilities(self) -> Tuple[CapabilitiesReply, int]:
        data, _, _, error_code = await self.conn.send_and_recv(1, 12)
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return self.CapabilitiesReply().from_bytes(data)[0], error_code


    class ClassPathsReply(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        baseDir: Optional[String] = None
        classpaths: List[String] = []
        bootclasspaths: List[String] = []

        def from_bytes(self, data, offset=0) -> Tuple['ClassPathsReply', int]:
            self.baseDir, offset = Jdwp.parse_string(data, offset, String)
            count, offset = Jdwp.parse_int(data, offset)
            for _ in range(count):
                entry, offset = Jdwp.parse_string(data, offset, String)
                self.classpaths = [*self.classpaths, entry]
            
            count, offset = Jdwp.parse_int(data, offset)
            for _ in range(count):
                entry, offset = Jdwp.parse_string(data, offset, String)
                self.bootclasspaths = [*self.bootclasspaths, entry]
            return self, offset


    async def ClassPaths(self) -> Tuple[ClassPathsReply, int]:
        data, _, _, error_code = await self.conn.send_and_recv(1, 13)
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return self.ClassPathsReply().from_bytes(data)[0], error_code
    

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
        requests: List['DisposeObjectsEntry'] = []

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


    async def CapabilitiesNew(self) -> Tuple[CapabilitiesNewReply, int]:
        data, _, _, error_code = await self.conn.send_and_recv(1, 17)
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return self.CapabilitiesNewReply().from_bytes(data)[0], error_code


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
        classes: List['AllClassesWithGenericEntry'] = []

        def from_bytes(self, data, offset=0) -> Tuple['AllClassesWithGenericReply', int]:
            count, offset = Jdwp.parse_int(data, offset)
            for _ in range(count):
                entry, offset = VirtualMachineSet.AllClassesWithGenericEntry().from_bytes(data, offset)
                self.classes = [*self.classes, entry]
            return self, offset


    async def AllClassesWithGeneric(self) -> Tuple[AllClassesWithGenericReply, int]:
        data, _, _, error_code = await self.conn.send_and_recv(1, 20)
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return self.AllClassesWithGenericReply().from_bytes(data)[0], error_code


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


    async def InstanceCounts(self, request: InstanceCountsRequest) -> Tuple[InstanceCountsReply, int]:
        data, _, _, error_code = await self.conn.send_and_recv(1, 21, data=request.to_bytes())
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return self.InstanceCountsReply().from_bytes(data)[0], error_code


class ReferenceTypeSet():

    def __init__(self, conn):
        self.conn = conn
    

    async def Signature(self, refType: ReferenceTypeID) -> Tuple[String, int]:
        data, _, _, error_code = await self.conn.send_and_recv(2, 1, data=Jdwp.make_long(refType))
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return Jdwp.parse_string(data, 0, String)[0], error_code


    async def ClassLoader(self, refType: ReferenceTypeID) -> Tuple[ClassLoaderID, int]:
        data, _, _, error_code = await self.conn.send_and_recv(2, 2, data=Jdwp.make_long(refType))
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return Jdwp.parse_long(data, 0, ClassLoaderID)[0], error_code

    
    async def Modifiers(self, refType: ReferenceTypeID) -> Tuple[Int, int]:
        data, _, _, error_code = await self.conn.send_and_recv(2, 3, data=Jdwp.make_long(refType))
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return Jdwp.parse_int(data, 0, Int)[0], error_code


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
        declared: List['FieldsDeclaredEntry'] = []

        def from_bytes(self, data, offset=0) -> Tuple['FieldsReply', int]:
            count, offset = Jdwp.parse_int(data, offset)
            for _ in range(count):
                entry, offset = ReferenceTypeSet.FieldsDeclaredEntry().from_bytes(data, offset)
                self.declared = [*self.declared, entry]
            return self, offset

    
    async def Fields(self, refType: ReferenceTypeID) -> Tuple[FieldsReply, int]:
        data, _, _, error_code = await self.conn.send_and_recv(2, 4, data=Jdwp.make_long(refType))
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return self.FieldsReply().from_bytes(data)[0], error_code


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
        declared: List['MethodsDeclaredEntry'] = []

        def from_bytes(self, data, offset=0) -> Tuple['MethodsReply', int]:
            count, offset = Jdwp.parse_int(data, offset)
            for _ in range(count):
                entry, offset = ReferenceTypeSet.MethodsDeclaredEntry().from_bytes(data, offset)
                self.declared = [*self.declared, entry]
            return self, offset


    async def Methods(self, refType: ReferenceTypeID) -> Tuple[MethodsReply, int]:
        data, _, _, error_code = await self.conn.send_and_recv(2, 5, data=Jdwp.make_long(refType))
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return self.MethodsReply().from_bytes(data)[0], error_code

    
    # !! Need to implement TaggedValues
    # https://docs.oracle.com/javase/8/docs/platform/jpda/jdwp/jdwp-protocol.html#JDWP_Tag
    class GetValuesRequest(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        refType: ReferenceTypeID
        fields: List[FieldID] = []

        def to_bytes(self) -> bytes:
            out = [Jdwp.make_long(self.refType), Jdwp.make_int(len(self.fields))]
            out.extend([Jdwp.make_long(fieldID) for fieldID in self.fields])
            return b''.join(out)


    class GetValuesReply(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        values: List[Value] = []

        def from_bytes(self, data, offset=0) -> Tuple['GetValuesReply', int]:
            count, offset = Jdwp.parse_int(data, offset)
            for _ in range(count):
                value, offset = Value().from_bytes(data, offset)
                self.values = [*self.values, value]
            return self, offset


    async def GetValues(self, request: GetValuesRequest) -> Tuple[GetValuesReply, int]:
        data, _, _, error_code = await self.conn.send_and_recv(1, 6, data=request.to_bytes())
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return self.GetValuesReply().from_bytes(data)[0], error_code


    async def SourceFile(self, refType: ReferenceTypeID) -> Tuple[String, int]:
        data, _, _, error_code = await self.conn.send_and_recv(2, 7, data=Jdwp.make_long(refType))
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return Jdwp.parse_string(data, 0, String)[0], error_code


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
        classes: List['NestedTypesEntry'] = []

        def from_bytes(self, data, offset=0) -> Tuple['NestedTypesReply', int]:
            count, offset = Jdwp.parse_int(data, offset)
            for _ in range(count):
                value, offset = ReferenceTypeSet.NestedTypesEntry().from_bytes(data)
                self.classes = [*self.classes, value]
            return self, offset

    
    async def NestedTypes(self, refType: ReferenceTypeID) -> Tuple[NestedTypesReply, int]:
        data, _, _, error_code = await self.conn.send_and_recv(2, 8, data=Jdwp.make_long(refType))
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return self.NestedTypesReply().from_bytes(data)[0], error_code
    

    async def Status(self, refType: ReferenceTypeID) -> Tuple[Int, int]:
        data, _, _, error_code = await self.conn.send_and_recv(2, 9, data=Jdwp.make_long(refType))
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return Jdwp.parse_int(data, 0, Int)[0], error_code


    class InterfacesReply(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        interfaces: List[InterfaceID] = []

        def from_bytes(self, data, offset=0) -> Tuple['InterfacesReply', int]:
            count, offset = Jdwp.parse_int(data, offset)
            for _ in range(count):
                value, offset = Jdwp.parse_long(data, offset, InterfaceID)
                self.interfaces = [*self.interfaces, value]
            return self, offset

    
    async def Interfaces(self, refType: ReferenceTypeID) -> Tuple[InterfacesReply, int]:
        data, _, _, error_code = await self.conn.send_and_recv(2, 10, data=Jdwp.make_long(refType))
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return self.InterfacesReply().from_bytes(data)[0], error_code


    async def ClassObject(self, refType: ReferenceTypeID) -> Tuple[ClassObjectID, int]:
        data, _, _, error_code = await self.conn.send_and_recv(2, 11, data=Jdwp.make_long(refType))
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return Jdwp.parse_long(data, 0, ClassObjectID)[0], error_code
    

    async def SourceDebugExtension(self, refType: ReferenceTypeID) -> Tuple[String, int]:
        data, _, _, error_code = await self.conn.send_and_recv(2, 12, data=Jdwp.make_long(refType))
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return Jdwp.parse_string(data, 0, String)[0], error_code

    
    class SignatureWithGenericReply(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        signature: Optional[String] = None
        genericSignature: Optional[String] = None

        def from_bytes(self, data, offset=0) -> Tuple['SignatureWithGenericReply', int]:
            self.signature, offset = Jdwp.parse_byte(data, offset, String)
            self.genericSignature, offset = Jdwp.parse_long(data, offset, String)
            return self, offset


    async def SignatureWithGeneric(self, refType: ReferenceTypeID) -> Tuple[SignatureWithGenericReply, int]:
        data, _, _, error_code = await self.conn.send_and_recv(2, 13, data=Jdwp.make_long(refType))
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return self.SignatureWithGenericReply().from_bytes(data)[0], error_code
    

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
        declared: List['FieldsWithGenericEntry'] = []

        def from_bytes(self, data, offset=0) -> Tuple['FieldsWithGenericReply', int]:
            count, offset = Jdwp.parse_int(data, offset)
            for _ in range(count):
                value, offset = ReferenceTypeSet.FieldsWithGenericEntry().from_bytes(data)
                self.declared = [*self.declared, value]
            return self, offset


    async def FieldsWithGeneric(self, refType: ReferenceTypeID) -> Tuple[FieldsWithGenericReply, int]:
        data, _, _, error_code = await self.conn.send_and_recv(2, 14, data=Jdwp.make_long(refType))
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return self.FieldsWithGenericReply().from_bytes(data)[0], error_code


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
        declared: List['MethodsWithGenericEntry'] = []

        def from_bytes(self, data, offset=0) -> Tuple['MethodsWithGenericReply', int]:
            count, offset = Jdwp.parse_int(data, offset)
            for _ in range(count):
                value, offset = ReferenceTypeSet.MethodsWithGenericEntry().from_bytes(data)
                self.declared = [*self.declared, value]
            return self, offset

    
    async def MethodsWithGeneric(self, refType: ReferenceTypeID) -> Tuple[MethodsWithGenericReply, int]:
        data, _, _, error_code = await self.conn.send_and_recv(2, 15, data=Jdwp.make_long(refType))
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return self.MethodsWithGenericReply().from_bytes(data)[0], error_code


    class InstancesRequest(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        refType: Optional[ReferenceTypeID] = None
        maxInstances: Optional[Int] = None

        def to_bytes(self) -> bytes:
            return b''.join([Jdwp.make_long(self.refType), Jdwp.make_int(self.maxInstances)])


    class InstancesReply(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        instances: List[TaggedObjectID] = []

        def from_bytes(self, data, offset=0) -> Tuple['InstancesReply', int]:
            count, offset = Jdwp.parse_int(data, offset)
            for _ in range(count):
                value, offset = TaggedObjectID().from_bytes(data, offset)
                self.instances = [*self.instances, value]
            return self, offset

    
    async def Instances(self, request: InstancesRequest) -> Tuple[InstancesReply, int]:
        data, _, _, error_code = await self.conn.send_and_recv(1, 16, data=request.to_bytes())
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return self.InstancesReply().from_bytes(data)[0], error_code
        
    
    class ClassFileVersionReply(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        majorVersion: Optional[Int] = None
        minorVersion: Optional[Int] = None

        def from_bytes(self, data, offset=0) -> Tuple['ClassFileVersionReply', int]:
            self.majorVersion, offset = Jdwp.parse_int(data, offset, Int)
            self.minorVersion, offset = Jdwp.parse_string(data, offset, Int)
            return self, offset

    
    async def ClassFileVersion(self, refType: ReferenceTypeID) -> Tuple[ClassFileVersionReply, int]:
        data, _, _, error_code = await self.conn.send_and_recv(2, 17, data=Jdwp.make_long(refType))
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return self.ClassFileVersionReply().from_bytes(data)[0], error_code


    class ConstantPoolReply(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        count: Optional[Int] = None
        cpbytes: List[Byte] = []

        def from_bytes(self, data, offset=0) -> Tuple['ConstantPoolReply', int]:
            self.count, offset = Jdwp.parse_int(data, offset, Int)
            cnt, offset = Jdwp.parse_int(data, offset)
            for _ in range(cnt):
                value, offset = Jdwp.parse_byte(data, offset, Byte)
                self.cpbytes = [*self.cpbytes, value]
            return self, offset

    
    async def ConstantPool(self, refType: ReferenceTypeID) -> Tuple[ConstantPoolReply, int]:
        data, _, _, error_code = await self.conn.send_and_recv(2, 18, data=Jdwp.make_long(refType))
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return self.ConstantPoolReply().from_bytes(data)[0], error_code

    
class ClassTypeSet():

    def __init__(self, conn):
        self.conn = conn


    async def Superclass(self, clazz: ClassID) -> Tuple[ClassID, int]:
        data, _, _, error_code = await self.conn.send_and_recv(3, 1, data=Jdwp.make_long(clazz))
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return Jdwp.parse_long(data, 0, ClassID)[0], error_code

    












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
    #     values: List['SetValuesEntry'] = []

    #     def to_bytes(self) -> bytes:
    #         out = [Jdwp.make_long(self.refType), Jdwp.make_int(len(self.fields))]
    #         out.extend([Jdwp.make_long(fieldID) for fieldID in self.fields])
    #         return b''.join(out)


    # async def SetValues(self, *args):
    #     raise NotImplementedError("SetValues not implemented.")
    #     # await self.conn.send(3, 2, data=Jdwp.make_long(clazz))
















    class InvokeMethodRequest(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        clazz: Optional[ClassID] = None
        thread: Optional[ThreadID] = None
        methodID: Optional[MethodID] = None
        arguments: List[Value] = []
        options: Optional[int] = None

        def to_bytes(self) -> bytes:
            out = [
                Jdwp.make_long(self.clazz),
                Jdwp.make_long(self.thred),
                Jdwp.make_lone(self.methodID),
                Jdwp.make_int(len(self.arguments))
            ]
            out.extend([argument.to_bytes() for argument in self.arguments])
            out.append(Jdwp.make_int(self.options))
            return b''.join(out)


    class InvokeMethodReply(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        returnValue: Optional[Value] = None
        exception: Optional[TaggedObjectID] = None

        def from_bytes(self, data, offset=0) -> Tuple['InvokeMethodReply', int]:
            self.returnValue, offset = Value().from_bytes(data, offset)
            self.exception, offset = TaggedObjectID().from_bytes(data, offset)
            return self, offset


    async def InvokeMethod(self, request: InvokeMethodRequest) -> Tuple[InvokeMethodReply, int]:
        data, _, _, error_code = await self.conn.send_and_recv(3, 3, data=request.to_bytes())
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return self.InvokeMethodReply().from_bytes(data)[0], error_code
    

    class NewInstanceRequest(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        clazz: Optional[ClassID] = None
        thread: Optional[ThreadID] = None
        methodID: Optional[MethodID] = None
        arguments: List[Value] = []
        options: Optional[int] = None

        def to_bytes(self) -> bytes:
            out = [
                Jdwp.make_long(self.clazz),
                Jdwp.make_long(self.thred),
                Jdwp.make_lone(self.methodID),
                Jdwp.make_int(len(self.arguments))
            ]
            out.extend([argument.to_bytes() for argument in self.arguments])
            out.append(Jdwp.make_int(self.options))
            return b''.join(out)


    class NewInstanceReply(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        newObject: Optional[TaggedObjectID] = None
        exception: Optional[TaggedObjectID] = None

        def from_bytes(self, data, offset=0) -> Tuple['NewInstanceReply', int]:
            self.newObject, offset = TaggedObjectID().from_bytes(data, offset)
            self.exception, offset = TaggedObjectID().from_bytes(data, offset)
            return self, offset


    async def NewInstance(self, request: NewInstanceRequest) -> Tuple[NewInstanceReply, int]:
        data, _, _, error_code = await self.conn.send_and_recv(3, 4, data=request.to_bytes())
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return self.NewInstanceReply().from_bytes(data)[0], error_code


class ArrayTypeSet():

    def __init__(self, conn):
        self.conn = conn


    class NewInstanceRequest(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        arrType: Optional[ArrayTypeID] = None
        length: Optional[Int] = None

        def to_bytes(self) -> bytes:
            return b''.join([Jdwp.make_long(self.arrType), Jdwp.make_int(self.length)])


    async def NewInstance(self, request: NewInstanceRequest) -> Tuple[TaggedObjectID, int]:
        data, _, _, error_code = await self.conn.send_and_recv(4, 1, data=request.to_bytes())
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return TaggedObjectID().from_bytes(data)[0], error_code


class InterfaceTypeSet():

    def __init__(self, conn):
        self.conn = conn


    class InvokeMethodRequest(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        clazz: Optional[ClassID] = None
        thread: Optional[ThreadID] = None
        methodID: Optional[MethodID] = None
        arguments: List[Value] = []
        options: Optional[int] = None

        def to_bytes(self) -> bytes:
            out = [
                Jdwp.make_long(self.clazz),
                Jdwp.make_long(self.thread),
                Jdwp.make_lone(self.methodID),
                Jdwp.make_int(len(self.arguments))
            ]
            out.extend([argument.to_bytes() for argument in self.arguments])
            out.append(Jdwp.make_int(self.options))
            return b''.join(out)


    class InvokeMethodReply(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        returnValue: Optional[Value] = None
        exception: Optional[TaggedObjectID] = None

        def from_bytes(self, data, offset=0) -> Tuple['InvokeMethodReply', int]:
            self.returnValue, offset = Value().from_bytes(data, offset)
            self.exception, offset = TaggedObjectID().from_bytes(data, offset)
            return self, offset


    async def InvokeMethod(self, request: InvokeMethodRequest) -> Tuple[InvokeMethodReply, int]:
        data, _, _, error_code = await self.conn.send_and_recv(5, 1, data=request.to_bytes())
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return self.InvokeMethodReply().from_bytes(data)[0], error_code


class MethodSet():

    def __init__(self, conn):
        self.conn = conn


    class LineTableRequest(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        refType: Optional[ReferenceTypeID] = None
        methodID: Optional[MethodID] = None

        def to_bytes(self) -> bytes:
            return b''.join([Jdwp.make_long(self.refType), Jdwp.make_long(self.methodID)])


    class LineTableEntry(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        lineCodeIndex: Optional[Long] = None
        lineNumber: Optional[Int] = None
        
        def from_bytes(self, data, offset=0) -> Tuple['LineTableReply', int]:
            self.lineCodeIndex, offset = Jdwp.parse_long(data, offset, Long)
            self.lineNumber, offset = Jdwp.parse_int(data, offset, Int)
            return self, offset


    class LineTableReply(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        start: Optional[Long] = None
        end: Optional[Long] = None
        lines: List['LineTableEntry'] = []

        def from_bytes(self, data, offset=0) -> Tuple['LineTableReply', int]:
            self.start, offset = Jdwp.parse_long(data, offset, Long)
            self.end, offset = Jdwp.parse_long(data, offset, Long)
            count, offset = Jdwp.parse_int(data, offset)
            for _ in range(count):
                value, offset = LineTableEntry().from_bytes(data, offset)
                lines.append(value)
            return self, offset


    async def LineTable(self, request: LineTableRequest) -> Tuple[LineTableReply, int]:
        out = Jdwp.make_long(refType) + Jdwp.make_long(methodID)
        data, _, _, error_code = await self.conn.send_and_recv(6, 1, data=out)
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return self.LineTableReply().from_bytes(data)[0], error_code
    

    class VariableTableRequest(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        refType: Optional[ReferenceTypeID] = None
        methodID: Optional[MethodID] = None

        def to_bytes(self) -> bytes:
            return b''.join([Jdwp.make_long(self.refType), Jdwp.make_long(self.methodID)])


    class VariableTableEntry(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        codeIndex: Optional[Long] = None
        name: Optional[String] = None
        signature: Optional[String] = None
        length: Optional[Int] = None
        slot: Optional[Int] = None
        
        def from_bytes(self, data, offset=0) -> Tuple['VariableTableEntry', int]:
            self.codeIndex, offset = Jdwp.parse_long(data, offset, Long)
            self.name, offset = Jdwp.parse_string(data, offset, String)
            self.signature, offset = Jdwp.parse_string(data, offset, String)
            self.length, offset = Jdwp.parse_int(data, offset, Int)
            self.slot, offset = Jdwp.parse_int(data, offset, Int)
            return self, offset


    class VariableTableReply(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        argCnt: Optional[Int] = None
        slots: List['VariableTableEntry'] = []

        def from_bytes(self, data, offset=0) -> Tuple['VariableTableReply', int]:
            self.argCnt, offset = Jdwp.parse_int(data, offset, Int)
            count, offset = Jdwp.parse_int(data, offset)
            for _ in range(count):
                value, offset = MethodSet.VariableTableEntry().from_bytes(data, offset)
                self.slots.append(value)
            return self, offset


    async def VariableTable(self, request: VariableTableRequest) -> Tuple[VariableTableReply, int]:
        data, _, _, error_code = await self.conn.send_and_recv(6, 2, data=request.to_bytes())
        if error_code != 0:
            return None, error_code
        return self.VariableTableReply().from_bytes(data)[0], error_code

    
    class BytecodesRequest(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        refType: Optional[ReferenceTypeID] = None
        methodID: Optional[MethodID] = None

        def to_bytes(self) -> bytes:
            return b''.join([Jdwp.make_long(self.refType), Jdwp.make_long(self.methodID)])
        
    
    class BytecodesReply(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        bytecodes: List[Byte] = []

        def from_bytes(self, data, offset=0) -> Tuple['BytecodesReply', int]:
            count, offset = Jdwp.parse_int(data, offset)
            for _ in range(count):
                bytecode, offset = Jdwp.parse_byte(data, offset, Byte)
                self.bytecodes.append(bytecode)
            return self, offset


    async def Bytecodes(self, request: BytecodesRequest) -> Tuple[BytecodesReply, int]:
        data, _, _, error_code = await self.conn.send_and_recv(6, 3, data=request.to_bytes())
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return self.BytecodesReply().from_bytes(data)[0], error_code

        
    class IsObsoleteRequest(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        refType: Optional[ReferenceTypeID] = None
        methodID: Optional[MethodID] = None

        def to_bytes(self) -> bytes:
            return b''.join([Jdwp.make_long(self.refType), Jdwp.make_long(self.methodID)])


    async def IsObsolete(self, request: IsObsoleteRequest) -> Tuple[Boolean, int]:
        data, _, _, error_code = await self.conn.send_and_recv(6, 4, data=request.to_bytes())
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return Jdwp.parse_byte(data, 0, Boolean)[0], error_code


    class VariableTableWithGenericRequest(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        refType: Optional[ReferenceTypeID] = None
        methodID: Optional[MethodID] = None

        def to_bytes(self) -> bytes:
            return b''.join([Jdwp.make_long(self.refType), Jdwp.make_long(self.methodID)])

    
    class VariableTableWithGenericEntry(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        codeIndex: Optional[Long] = None
        name: Optional[String] = None
        signature: Optional[String] = None
        genericSignature: Optional[String] = None
        length: Optional[Int] = None
        slot: Optional[Int] = None
        
        def from_bytes(self, data, offset=0) -> Tuple['VariableTableEntry', int]:
            self.codeIndex, offset = Jdwp.parse_long(data, offset, Long)
            self.name, offset = Jdwp.parse_string(data, offset, String)
            self.signature, offset = Jdwp.parse_string(data, offset, String)
            self.genericSignature, offset = Jdwp.parse_string(data, offset, String)
            self.length, offset = Jdwp.parse_int(data, offset, Int)
            self.slot, offset = Jdwp.parse_int(data, offset, Int)
            return self, offset


    class VariableTableWithGenericReply(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        argCnt: Optional[Long] = None
        slots: List['VariableTableWithGenericEntry'] = []

        def from_bytes(self, data, offset=0) -> Tuple['VariableTableWithGenericReply', int]:
            self.argCnt, offset = Jdwp.parse_int(data, offset, Int)
            count, offset = Jdwp.parse_int(data, offset)
            for _ in range(count):
                value, offset = MethodSet.VariableTableWithGenericEntry().from_bytes(data, offset)
                slots.append(value)
            return self, offset


    async def VariableTableWithGeneric(self, request: VariableTableWithGenericRequest) -> Tuple[VariableTableWithGenericReply, int]:
        data, _, _, error_code = await self.conn.send_and_recv(6, 5, data=request.to_bytes())
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return self.VariableTableWithGenericReply().from_bytes(data)[0], error_code


# Note: Empty set in specification.
class FieldSet():

    def __init__(self, conn):
        self.conn = conn


class ObjectReferenceSet():

    def __init__(self, conn):
        self.conn = conn
    

    class ReferenceTypeReply(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        refTypeTag: Optional[Byte] = None
        typeID: Optional[ReferenceTypeID] = None

        def from_bytes(self, data, offset=0) -> Tuple['ReferenceTypeReply', int]:
            self.refTypeTag, offset = Jdwp.parse_byte(data, offset, Byte)
            self.typeID, offset = Jdwp.parse_long(data, offset, ReferenceTypeID)
            return self, offset


    async def ReferenceType(self, objectid: ObjectID) -> Tuple[ReferenceTypeReply, int]:
        data, _, _, error_code = await self.conn.send_and_recv(9, 1, data=Jdwp.make_long(objectid))
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return self.ReferenceTypeReply().from_bytes(data)[0], error_code


    class GetValuesRequest(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        objectid: Optional[ObjectID] = None
        fields: List[FieldID] = []

        def to_bytes(self) -> bytes:
            out = [Jdwp.make_long(self.objectid), Jdwp.make_int(len(self.fields))]
            out.extend([Jdwp.make_long(fieldID) for fieldID in self.fields])
            return b''.join(out)


    class GetValuesReply(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        values: List[Value] = []

        def from_bytes(self, data, offset=0) -> Tuple['GetValuesReply', int]:
            count, offset = Jdwp.parse_int(data, offset)
            for _ in range(count):
                value, offset = Value().from_bytes(data, offset)
                self.values = [*self.values, value]
            return self, offset

    
    async def GetValues(self, request: GetValuesRequest) -> Tuple[GetValuesReply, int]:
        data, _, _, error_code = await self.conn.send_and_recv(9, 2, data=request.to_bytes())
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return self.GetValuesReply().from_bytes(data)[0], error_code

















    # !! Need to figure out untagged values.
    # async def SetValues(self, *args):
    #     raise NotImplementedError("SetValues not implemented.")
    #     # await self.conn.send(9, 3, data=Jdwp.make_long(clazz))
    











    class MonitorInfoReply(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        owner: Optional[ThreadID] = None
        entryCount: Optional[Int] = None
        waiters: List[ThreadID] = []

        def from_bytes(self, data, offset=0) -> Tuple['MonitorInfoReply', int]:
            self.owner, offset = Jdwp.parse_long(data, offset, ThreadID)
            self.entryCount, offset = Jdwp.parse_int(data, offset, Int)
            count, offset = Jdwp.parse_int(data, offset)
            for _ in range(count):
                value, offset = Jdwp.parse_long(data, offset, ThreadID)
                self.values = [*self.values, value]
            return self, offset


    async def MonitorInfo(self, objectid: ObjectID) -> MonitorInfoReply:
        data, _, _, error_code = await self.conn.send_and_recv(9, 5, data=Jdwp.make_long(objectid))
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return self.MonitorInfoReply().from_bytes(data)[0], error_code


    class InvokeMethodRequest(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        objectid: Optional[ObjectID] = None
        thread: Optional[ThreadID] = None
        clazz: Optional[ClassID] = None
        methodID: Optional[MethodID] = None
        arguments: List[Value] = []
        options: Optional[int] = None

        def to_bytes(self) -> bytes:
            out = [
                Jdwp.make_long(self.objectid),
                Jdwp.make_long(self.thread),
                Jdwp.make_long(self.clazz),
                Jdwp.make_lone(self.methodID),
                Jdwp.make_int(len(self.arguments))
            ]
            out.extend([argument.to_bytes() for argument in self.arguments])
            out.append(Jdwp.make_int(self.options))
            return b''.join(out)


    class InvokeMethodReply(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        returnValue: Optional[Value] = None
        exception: Optional[TaggedObjectID] = None

        def from_bytes(self, data, offset=0) -> Tuple['InvokeMethodReply', int]:
            self.returnValue, offset = Value().from_bytes(data, offset)
            self.exception, offset = TaggedObjectID().from_bytes(data, offset)
            return self, offset


    async def InvokeMethod(self, request: InvokeMethodRequest) -> Tuple[InvokeMethodReply, int]:
        data, _, _, error_code = await self.conn.send_and_recv(9, 6, data=request.to_bytes())
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return self.InvokeMethodReply().from_bytes(data)[0], error_code

    
    async def DisableCollection(self, objectid: ObjectID):
        await self.conn.send(9, 7, data=Jdwp.make_long(objectid))
        
    
    async def EnableCollection(self, objectid: ObjectID):
        await self.conn.send(9, 8, data=Jdwp.make_long(objectid))
        
    
    async def IsCollected(self, objectid: ObjectID) -> Tuple[Boolean, int]:
        data, _, _, error_code = await self.conn.send_and_recv(9, 9, data=Jdwp.make_long(objectid))
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return Jdwp.parse_byte(data, 0, Boolean)[0], error_code


    class ReferringObjectsRequest(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        objectid: Optional[ObjectID] = None
        maxReferrers: List[Int] = []

        def to_bytes(self) -> bytes:
            return b''.join([Jdwp.make_long(self.refType), Jdwp.make_int(self.maxReferrers)])


    class ReferringObjectsReply(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        referringObjects: List[TaggedObjectID] = []

        def from_bytes(self, data, offset=0) -> Tuple['ReferringObjectsReply', int]:
            count, offset = Jdwp.parse_int(data, offset)
            for _ in range(count):
                value, offset = TaggedObjectID().from_bytes(data, offset)
                self.referringObjects = [*self.referringObjects, value]
            return self, offset

    
    async def ReferringObjects(self, request: ReferringObjectsRequest) -> Tuple[ReferringObjectsReply, int]:
        data, _, _, error_code = await self.conn.send_and_recv(9, 10, data=request.to_bytes())
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return self.ReferringObjectsReply().from_bytes(data)[0], error_code


class StringReferenceSet():

    def __init__(self, conn):
        self.conn = conn

    async def IsCollected(self, stringObject: ObjectID) -> Tuple[String, int]:
        data, _, _, error_code = await self.conn.send_and_recv(10, 1, data=Jdwp.make_long(stringObject))
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return Jdwp.parse_string(data, 0, String)[0], error_code


class ThreadReferenceSet():

    def __init__(self, conn):
        self.conn = conn

    async def Name(self, thread: ThreadID) -> Tuple[String, int]:
        data, _, _, error_code = await self.conn.send_and_recv(11, 1, data=Jdwp.make_long(thread))
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return Jdwp.parse_string(data, 0, String)[0], error_code
    

    async def Suspend(self, thread: ThreadID) -> None:
        await self.conn.send(11, 2, data=Jdwp.make_long(thread))


    async def Resume(self, thread: ThreadID) -> None:
        await self.conn.send(11, 3, data=Jdwp.make_long(thread))

    
    class StatusReply(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        threadStatus: List[Int] = []
        suspendStatus: List[Int] = []

        def from_bytes(self, data, offset=0) -> Tuple['StatusReply', int]:
            self.threadStatus, offset = Jdwp.parse_int(data, offset, Int)
            self.suspendStatus, offset = Jdwp.parse_int(data, offset, Int)
            return self, offset


    async def Status(self, thread: ThreadID) -> Tuple[StatusReply, int]:
        data, _, _, error_code = await self.conn.send_and_recv(11, 4, data=Jdwp.make_long(thread))
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return self.StatusReply().from_bytes(data)[0], error_code
    

    async def ThreadGroup(self, thread: ThreadID) -> Tuple[ThreadGroupID, int]:
        data, _, _, error_code = await self.conn.send_and_recv(11, 5, data=Jdwp.make_long(thread))
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return Jdwp.parse_long(data, 0, ThreadGroupID)[0], error_code


    class FramesRequest(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        thread: Optional[ThreadID] = None
        startFrame: Optional[Int] = None
        length: Optional[Int] = None
        
        def to_bytes(self) -> bytes:
            return b''.join([
                Jdwp.make_long(self.thread),
                Jdwp.make_int(self.startFrame),
                Jdwp.make_int(self.length),
            ])


    class FramesEntry(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        frameID: Optional[FrameID] = None
        location: Optional[Location] = None
        
        def from_bytes(self, data, offset=0) -> Tuple['FramesEntry', int]:
            self.frameID, offset = Jdwp.parse_long(data, offset, FrameID)
            self.location, offset = Location().from_bytes(data, offset)
            return self, offset


    class FramesReply(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        frames: List['FramesEntry'] = []

        def from_bytes(self, data, offset=0) -> Tuple['FramesReply', int]:
            count, offset = Jdwp.parse_int(data, offset)
            for _ in range(count):
                value, offset = ThreadReferenceSet.FramesEntry().from_bytes(data, offset)
                self.frames = [*self.frames, value]
            return self, offset
    

    async def Frames(self, request: FramesRequest) -> Tuple[FramesReply, int]:
        data, _, _, error_code = await self.conn.send_and_recv(11, 6, data=request.to_bytes())
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return self.FramesReply().from_bytes(data)[0], error_code
    

    async def FrameCount(self, thread: ThreadID) -> Tuple[Int, int]:
        data, _, _, error_code = await self.conn.send_and_recv(11, 7, data=Jdwp.make_long(thread))
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return Jdwp.parse_int(data, 0, Int)[0], error_code
    

    class OwnedMonitorsReply(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        owned: List[TaggedObjectID] = []

        def from_bytes(self, data, offset=0) -> Tuple['OwnedMonitorsReply', int]:
            count, offset = Jdwp.parse_int(data, offset)
            for _ in range(count):
                value, offset = TaggedObjectID().from_bytes(data, offset)
                self.owned = [*self.owned, value]
            return self, offset


    async def OwnedMonitors(self, thread: ThreadID) -> Tuple[OwnedMonitorsReply, int]:
        data, _, _, error_code = await self.conn.send_and_recv(11, 8, data=Jdwp.make_long(thread))
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return self.OwnedMonitorsReply().from_bytes(data)[0], error_code

    
    async def CurrentContendedMonitor(self, thread: ThreadID) -> Tuple[TaggedObjectID, int]:
        data, _, _, error_code = await self.conn.send_and_recv(11, 8, data=Jdwp.make_long(thread))
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return TaggedObjectID().from_bytes(data)[0], error_code


    class StopRequest(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        thread: Optional[ThreadID] = None
        throwable: Optional[ObjectID] = None
        
        def to_bytes(self) -> bytes:
            return b''.join([
                Jdwp.make_long(self.thread),
                Jdwp.make_long(self.throwable),
            ])

    
    async def Stop(self, request: StopRequest) -> None:
        await self.conn.send(11, 10, data=request.to_bytes())
    

    async def Interrupt(self, thread: ThreadID) -> None:
        await self.conn.send(11, 11, data=Jdwp.make_long(thread))


    async def SuspendCount(self, thread: ThreadID) -> Tuple[Int, int]:
        data, _, _, error_code = await self.conn.send_and_recv(11, 8, data=Jdwp.make_long(thread))
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return Jdwp.parse_int(data, 0, Int)[0], error_code


    class OwnedMonitorsStackDepthInfoEntry(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        monitor: Optional[TaggedObjectID] = None
        stack_depth: Optional[Int] = None

        def from_bytes(self, data, offset=0) -> Tuple['OwnedMonitorsStackDepthInfoEntry', int]:
            self.monitor, offset = TaggedObjectID.from_bytes(data, offset)
            self.stack_depth, offset = Jdwp.parse_int(data, offset, Int)
            return self, offset


    class OwnedMonitorsStackDepthInfoReply(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        owned: List['OwnedMonitorsStackDepthInfoEntry'] = []

        def from_bytes(self, data, offset=0) -> Tuple['OwnedMonitorsStackDepthInfoReply', int]:
            count, offset = Jdwp.parse_int(data, offset)
            for _ in range(count):
                value, offset = ThreadReferenceSet.OwnedMonitorsStackDepthInfoEntry().from_bytes(data, offset)
                self.owned = [*self.owned, value]
            return self, offset

    
    async def OwnedMonitorsStackDepthInfo(self, thread: ThreadID) -> Tuple[OwnedMonitorsStackDepthInfoReply, int]:
        data, _, _, error_code = await self.conn.send_and_recv(11, 13, data=Jdwp.make_long(thread))
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return self.OwnedMonitorsStackDepthInfoReply().from_bytes(data)[0], error_code
    

    class ForceEarlyReturnRequest(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        thread: Optional[ThreadID] = None
        value: Optional[Value] = None
        
        def to_bytes(self) -> bytes:
            return b''.join([Jdwp.make_long(self.thread), value.to_bytes()])

    
    async def Stop(self, request: ForceEarlyReturnRequest) -> None:
        await self.conn.send(11, 14, data=request.to_bytes())
    

class ThreadGroupReferenceSet():

    def __init__(self, conn):
        self.conn = conn


    async def Name(self, group: ThreadGroupID) -> Tuple[String, int]:
        data, _, _, error_code = await self.conn.send_and_recv(12, 1, data=Jdwp.make_long(group))
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return Jdwp.parse_string(data, offset, String)[0], error_code

    
    async def Parent(self, group: ThreadGroupID) -> Tuple[String, int]:
        data, _, _, error_code = await self.conn.send_and_recv(12, 2, data=Jdwp.make_long(group))
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return Jdwp.parse_long(data, offset, ThreadGroupID)[0], error_code


    class ChildrenReply(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        childThreads: List[ThreadID] = []
        childGroups: List[ThreadGroupID] = []

        def from_bytes(self, data, offset=0) -> Tuple['ChildrenReply', int]:
            count, offset = Jdwp.parse_int(data, offset)
            for _ in range(count):
                value, offset = Jdwp.parse_long(data, offset, ThreadID)
                self.childThreads = [*self.childThreads, value]
            
            count, offset = Jdwp.parse_int(data, offset)
            for _ in range(count):
                value, offset = Jdwp.parse_long(data, offset, ThreadGroupID)
                self.childGroups = [*self.childGroups, value]
            return self, offset

    
    async def Children(self, group: ThreadGroupID) -> Tuple[ChildrenReply, int]:
        data, _, _, error_code = await self.conn.send_and_recv(12, 3, data=Jdwp.make_long(group))
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return self.ChildrenReply().from_bytes(data)[0], error_code
    

class ArrayReferenceSet():

    def __init__(self, conn):
        self.conn = conn
    

    async def Length(self, arrayObject: ArrayID) -> Tuple[Int, int]:
        data, _, _, error_code = await self.conn.send_and_recv(13, 1, data=Jdwp.make_long(arrayObject))
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return Jdwp.parse_int(data, offset, Int)[0], error_code


    class GetValuesRequest(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        arrayObject: Optional[ArrayID] = None
        firstIndex: Optional[Int] = None
        length: Optional[Int]
        
        def to_bytes(self) -> bytes:
            return b''.join([
                Jdwp.make_long(self.arrayObject),
                Jdwp.make_int(self.firstIndex),
                Jdwp.make_int(self.length),
            ])


    async def GetValues(self, request: GetValuesRequest) -> Tuple[ArrayRegion, int]:
        data, _, _, error_code = await self.conn.send_and_recv(13, 2, data=request.to_bytes())
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return self.ArrayRegion().from_bytes(data)[0], error_code


    # !! Need To Implement Untagged Values
    # class SetValuesRequest(BaseModel):
    #     model_config = ConfigDict(validate_assignment=True)
    #     arrayObject: Optional[ArrayID] = None
    #     firstIndex: Optional[Int] = None
    #     values: List[Value] = []
        
    #     def to_bytes(self) -> bytes:
    #         out = [Jdwp.make_long(self.arrayObject), Jdwp.make_int(self.firstIndex)]
    #         out.extend([value.to_bytes() for value in self.values])
    #         return b''.join(out)


    # async def SetValues(self, request: SetValuesRequest) -> None:
    #     await self.conn.send(13, 2, data=request.to_bytes())
    #     data, _, _, _ = await self.conn.recv()
    #     return ArrayRegion().from_bytes(data)[0]


class ClassLoaderReferenceSet():

    def __init__(self, conn):
        self.conn = conn


    class VisibleClassesEntry(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        refTypeTag: Optional[Byte] = None
        typeID: Optional[ReferenceTypeID] = None

        def from_bytes(self, data, offset=0) -> Tuple['VisibleClassesEntry', int]:
            self.refTypeTag, offset = Jdwp.parse_byte(data, offset, Byte)
            self.typeID, offset = Jdwp.parse_long(Data, offset, ReferenceTypeID)
            return self, offset

    
    class VisibleClassesReply(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        classes: List['VisibleClassesEntry'] = []

        def from_bytes(self, data, offset=0) -> Tuple['ChildrenReply', int]:
            count, offset = Jdwp.parse_int(data, offset)
            for _ in range(count):
                value, offset = ClassLoaderReferenceSet.VisibleClassesEntry().from_bytes(data, offset)
                self.classes = [*self.classes, value]
            return self, offset


    async def VisibleClasses(self, classLoaderObject: ClassLoaderID) -> Tuple[VisibleClassesReply, int]:
        data, _, _, error_code = await self.conn.send_and_recv(14, 1, data=request.to_bytes())
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return self.VisibleClassesReply().from_bytes(data)[0], error_code


class EventRequestSet():

    def __init__(self, conn):
        self.conn = conn


    class SetCountModifier(BaseModel): #1
        model_config = ConfigDict(validate_assignment=True)
        modKind: Optional[Int] = Int(1)
        count: Optional[Int] = None

        def to_bytes(self) -> bytes:
            return b''.join([
                Jdwp.make_byte(self.modKind),
                Jdwp.make_int(self.count),
            ])


    class SetConditionalModifier(BaseModel): #2
        model_config = ConfigDict(validate_assignment=True)
        modKind: Optional[Int] = Int(2)
        exprID: Optional[Int] = None

        def to_bytes(self) -> bytes:
            return b''.join([
                Jdwp.make_byte(self.modKind),
                Jdwp.make_int(self.exprID),
            ])
    

    class SetThreadOnlyModifier(BaseModel): #3
        model_config = ConfigDict(validate_assignment=True)
        modKind: Optional[Int] = Int(3)
        thread: Optional[ThreadID] = None

        def to_bytes(self) -> bytes:
            return b''.join([
                Jdwp.make_byte(self.modKind),
                Jdwp.make_long(self.thread),
            ])


    class SetClassOnlyModifier(BaseModel): #4
        model_config = ConfigDict(validate_assignment=True)
        modKind: Optional[Int] = Int(4)
        clazz: Optional[ReferenceTypeID] = None

        def to_bytes(self) -> bytes:
            return b''.join([
                Jdwp.make_byte(self.modKind),
                Jdwp.make_long(self.clazz),
            ])
    

    class SetClassMatchModifier(BaseModel): #5
        model_config = ConfigDict(validate_assignment=True)
        modKind: Optional[Int] = Int(5)
        classPattern: Optional[String] = None

        def to_bytes(self) -> bytes:
            return b''.join([
                Jdwp.make_byte(self.modKind),
                Jdwp.make_string(self.classPattern),
            ])
    

    class SetClassExcludeModifier(BaseModel): #6
        model_config = ConfigDict(validate_assignment=True)
        modKind: Optional[Int] = Int(6)
        classPattern: Optional[String] = None

        def to_bytes(self) -> bytes:
            return b''.join([
                Jdwp.make_byte(self.modKind),
                Jdwp.make_string(self.classPattern),
            ])
    

    class SetLocationOnlyModifier(BaseModel): #7
        model_config = ConfigDict(validate_assignment=True)
        modKind: Optional[Int] = Int(7)
        loc: Optional[Location] = None

        def to_bytes(self) -> bytes:
            return b''.join([
                Jdwp.make_byte(self.modKind),
                self.loc.to_bytes(),
            ])


    class SetExceptionOnlyModifier(BaseModel): #8
        model_config = ConfigDict(validate_assignment=True)
        modKind: Optional[Int] = Int(8)
        exceptionOrNull: Optional[ReferenceTypeID] = None
        caught: Optional[Boolean] = None
        uncaught: Optional[Boolean] = None

        def to_bytes(self) -> bytes:
            return b''.join([
                Jdwp.make_byte(self.modKind),
                Jdwp.make_long(self.exceptionOrNull),
                Jdwp.make_byte(self.caught),
                Jdwp.make_byte(self.uncaught),
            ])
        

    class SetFieldOnlyModifier(BaseModel): #9
        model_config = ConfigDict(validate_assignment=True)
        modKind: Optional[Int] = Int(9)
        declaring: Optional[ReferenceTypeID] = None
        fieldID: Optional[FieldID] = None

        def to_bytes(self) -> bytes:
            return b''.join([
                Jdwp.make_byte(self.modKind),
                Jdwp.make_long(self.declaring),
                Jdwp.make_long(self.fieldID),
            ])


    class SetStepModifier(BaseModel): #10
        model_config = ConfigDict(validate_assignment=True)
        modKind: Optional[Int] = Int(10)
        thread: Optional[ThreadID] = None
        size: Optional[Int] = None
        depth: Optional[Int] = None

        def to_bytes(self) -> bytes:
            return b''.join([
                Jdwp.make_byte(self.modKind),
                Jdwp.make_long(self.thread),
                Jdwp.make_int(self.size),
                Jdwp.make_int(self.depth),
            ])
    

    class SetInstanceOnlyModifier(BaseModel): #11
        model_config = ConfigDict(validate_assignment=True)
        modKind: Optional[Int] = Int(11)
        instance: Optional[ObjectID] = None

        def to_bytes(self) -> bytes:
            return b''.join([
                Jdwp.make_byte(self.modKind),
                Jdwp.make_long(self.instance),
            ])
    

    class SetSourceNameMatchModifier(BaseModel): #12
        model_config = ConfigDict(validate_assignment=True)
        modKind: Optional[Int] = Int(12)
        sourceNamePattern: Optional[String] = None

        def to_bytes(self) -> bytes:
            return b''.join([
                Jdwp.make_byte(self.modKind),
                Jdwp.make_string(self.sourceNamePattern),
            ])
    

    class SetPlatformThreadsOnlyModifier(BaseModel): #13
        model_config = ConfigDict(validate_assignment=True)
        modKind: Optional[Int] = Int(13)

        def to_bytes(self) -> bytes:
            return Jdwp.make_byte(self.modKind)


    SetModifier = {
        1: SetCountModifier,
        2: SetConditionalModifier,
        3: SetThreadOnlyModifier,
        4: SetClassOnlyModifier,
        5: SetClassMatchModifier,
        6: SetClassExcludeModifier,
        7: SetLocationOnlyModifier,
        8: SetExceptionOnlyModifier,
        9: SetFieldOnlyModifier,
        10: SetStepModifier,
        11: SetInstanceOnlyModifier,
        12: SetSourceNameMatchModifier,
        13: SetPlatformThreadsOnlyModifier,
    }


    # !! This is really sophisticated. Coming back later.
    class SetRequest(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        eventKind: Optional[Byte] = None
        suspendPolicy: Optional[Byte] = None

        # !! TODO: I'd like to put a base class here.
        # !! TODO: But we may not be able to if subclass
        # !! TODO: checked at runtime. Needs investigation.
        modifiers: List = []
        
        def to_bytes(self) -> bytes:
            out = [
                Jdwp.make_byte(self.eventKind),
                Jdwp.make_byte(self.suspendPolicy),
                Jdwp.make_int(len(self.modifiers)),
            ]
            for modifier in self.modifiers:
                out.append(modifier.to_bytes())
            return b''.join(out)
    

    async def Set(self, request: SetRequest) -> Tuple[Int, int]:
        data, _, _, error_code = await self.conn.send_and_recv(15, 1, data=request.to_bytes())
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return Jdwp.parse_int(data, 0)[0], error_code


    class ClearRequest(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        eventKind: Optional[Byte] = None
        requestID: Optional[Int] = None

        def to_bytes(self) -> bytes:
            return b''.join([Jdwp.make_byte(self.eventKind), Jdwp.make_int(self.requestID)])
    

    async def Clear(self, request: ClearRequest) -> None:
        await self.conn.send(15, 2, data=request.to_bytes())
    

    async def ClearAllBreakpoints(self) -> None:
        await self.conn.send(15, 3)


class StackFrameSet():

    def __init__(self, conn):
        self.conn = conn
    

    class GetValuesSlotEntry(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        slot: Optional[Int] = None
        sigbyte: Optional[Byte] = None

        def to_bytes(self) -> bytes:
            return b''.join([Jdwp.make_int(self.slot), Jdwp.make_byte(self.sigbyte)])
            

    class GetValuesRequest(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        thread: Optional[ThreadID] = None
        frame: Optional[FrameID] = None
        slots: List['GetValuesSlotEntry'] = []

        def to_bytes(self) -> bytes:
            out = [
                Jdwp.make_long(self.thread),
                Jdwp.make_long(self.frame),
                Jdwp.make_int(len(self.slots))
            ]
            out.extend([slot.to_bytes() for slot in self.slots])
            return b''.join(out)


    class GetValuesReply(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        values: List[Value] = []

        def from_bytes(self, data, offset=0) -> Tuple['GetValuesReply', int]:
            count, offset = Jdwp.parse_int(data, offset)
            for _ in range(count):
                value, offset = Value().from_bytes(data, offset)
                self.values = [*self.values, value]
            return self, offset

    
    async def GetValues(self, request: GetValuesRequest) -> Tuple[GetValuesReply, int]:
        data, _, _, error_code = await self.conn.send_and_recv(16, 1, data=request.to_bytes())
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return self.GetValuesReply().from_bytes(data)[0], error_code


    class SetValuesSlotEntry(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        slot: Optional[Int] = None
        slotValue: Optional[Value] = None

        def to_bytes(self) -> bytes:
            return b''.join([Jdwp.make_int(self.slot), slotValue.to_bytes()])
            

    class SetValuesRequest(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        thread: Optional[ThreadID] = None
        frame: Optional[FrameID] = None
        slots: List['SetValuesSlotEntry'] = []

        def to_bytes(self) -> bytes:
            out = [
                Jdwp.make_long(self.thread),
                Jdwp.make_long(self.frame),
                Jdwp.make_int(len(self.slots))
            ]
            out.extend([value.to_bytes() for slot in self.slots])
            return b''.join(out)


    async def SetValues(self, request: SetValuesRequest) -> None:
        await self.conn.send(16, 2, data=request.to_bytes())


    class ThisObjectRequest(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        thread: Optional[ThreadID] = None
        frame: Optional[FrameID] = None

        def to_bytes(self) -> bytes:
            return b''.join([Jdwp.make_long(self.thread), Jdwp.make_long(self.frame)])

    
    async def ThisObject(self, request: ThisObjectRequest) -> Tuple[TaggedObjectID, int]:
        data, _, _, error_code = await self.conn.send_and_recv(16, 3, data=request.to_bytes())
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return TaggedObjectID().from_bytes(data)[0], error_code


    class PopFramesRequest(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        thread: Optional[ThreadID] = None
        frame: Optional[FrameID] = None

        def to_bytes(self) -> bytes:
            return b''.join([Jdwp.make_long(self.thread), Jdwp.make_long(self.frame)])

    
    async def PopFrames(self, request: PopFramesRequest) -> None:
        await self.conn.send(16, 4, data=request.to_bytes())


class ClassObjectReferenceSet():

    def __init__(self, conn):
        self.conn = conn
    

    class ReflectedTypeReply(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        refTypeTag: Optional[Byte] = None
        typeID: Optional[ReferenceTypeID] = None

        def from_bytes(self, data, offset=0) -> Tuple['ReflectedTypeReply', int]:
            self.refTypeTag, offset = Jdwp.parse_byte(data, offset, Byte)
            self.typeID, offset = Jdwp.parse_long(data, offset, ReferenceTypeID)
            return self, offset

    
    async def ReflectedType(self, classObject: ClassObjectID) -> Tuple[ReflectedTypeReply, int]:
        data, _, _, error_code = await self.conn.send_and_recv(17, 1, data=request.to_bytes())
        if error_code != Jdwp.Error.NONE:
            return None, error_code
        return self.ReflectedTypeReply().from_bytes(data)[0], error_code


class EventSet():

    def __init__(self, conn):
        self.conn = conn


    class EventVMStart(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        eventKind: Optional[Byte] = Byte(EventKind.VM_START)
        requestID: Optional[Int] = None
        thread: Optional[ThreadID] = None

        def from_bytes(self, data, offset=0) -> Tuple['EventVMStart', int]:
            self.requestID, offset = Jdwp.parse_int(data, offset, Int)
            self.thread, offset = Jdwp.parse_long(data, offset, ThreadID)
            return self, offset


    class EventSingleStep(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        eventKind: Optional[Byte] = Byte(EventKind.SINGLE_STEP)
        requestID: Optional[Int] = None
        thread: Optional[ThreadID] = None
        location: Optional[Location] = None

        def from_bytes(self, data, offset=0) -> Tuple['EventSingleStep', int]:
            self.requestID, offset = Jdwp.parse_int(data, offset, Int)
            self.thread, offset = Jdwp.parse_long(data, offset, ThreadID)
            self.location, offset = Location().from_bytes(data, offset)
            return self, offset


    class EventBreakpoint(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        eventKind: Optional[Byte] = Byte(EventKind.BREAKPOINT)
        requestID: Optional[Int] = None
        thread: Optional[ThreadID] = None
        location: Optional[Location] = None

        def from_bytes(self, data, offset=0) -> Tuple['EventBreakpoint', int]:
            self.requestID, offset = Jdwp.parse_int(data, offset, Int)
            self.thread, offset = Jdwp.parse_long(data, offset, ThreadID)
            self.location, offset = Location().from_bytes(data, offset)
            return self, offset


    class EventMethodEntry(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        eventKind: Optional[Byte] = Byte(EventKind.METHOD_ENTRY)
        requestID: Optional[Int] = None
        thread: Optional[ThreadID] = None
        location: Optional[Location] = None

        def from_bytes(self, data, offset=0) -> Tuple['EventMethodEntry', int]:
            self.requestID, offset = Jdwp.parse_int(data, offset, Int)
            self.thread, offset = Jdwp.parse_long(data, offset, ThreadID)
            self.location, offset = Location().from_bytes(data, offset)
            return self, offset


    class EventMethodExit(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        eventKind: Optional[Byte] = Byte(EventKind.METHOD_EXIT)
        requestID: Optional[Int] = None
        thread: Optional[ThreadID] = None
        location: Optional[Location] = None

        def from_bytes(self, data, offset=0) -> Tuple['EventMethodExit', int]:
            self.requestID, offset = Jdwp.parse_int(data, offset, Int)
            self.thread, offset = Jdwp.parse_long(data, offset, ThreadID)
            self.location, offset = Location().from_bytes(data, offset)
            return self, offset
    
    
    class EventMethodExitWithReturnValue(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        eventKind: Optional[Byte] = Byte(EventKind.METHOD_EXIT_WITH_RETURN_VALUE)
        requestID: Optional[Int] = None
        thread: Optional[ThreadID] = None
        location: Optional[Location] = None
        value: Optional[Value] = None

        def from_bytes(self, data, offset=0) -> Tuple['EventMethodExitWithReturnValue', int]:
            self.requestID, offset = Jdwp.parse_int(data, offset, Int)
            self.thread, offset = Jdwp.parse_long(data, offset, ThreadID)
            self.location, offset = Location().from_bytes(data, offset)
            self.value, offset = Value().from_bytes(data, offset)
            return self, offset
    

    class EventMonitorContendedEnter(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        eventKind: Optional[Byte] = Byte(EventKind.MONITOR_CONTENDED_ENTER)
        requestID: Optional[Int] = None
        thread: Optional[ThreadID] = None
        objectID: Optional[TaggedObjectID] = None
        location: Optional[Location] = None

        def from_bytes(self, data, offset=0) -> Tuple['EventMonitorContendedEnter', int]:
            self.requestID, offset = Jdwp.parse_int(data, offset, Int)
            self.thread, offset = Jdwp.parse_long(data, offset, ThreadID)
            self.objectID, offset = TaggedObjectID().from_bytes(data, offset)
            self.location, offset = Location().from_bytes(data, offset)
            return self, offset
        

    class EventMonitorContendedEntered(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        eventKind: Optional[Byte] = Byte(EventKind.MONITOR_CONTENDED_ENTERED)
        requestID: Optional[Int] = None
        thread: Optional[ThreadID] = None
        objectID: Optional[TaggedObjectID] = None
        location: Optional[Location] = None

        def from_bytes(self, data, offset=0) -> Tuple['EventMonitorContendedEntered', int]:
            self.requestID, offset = Jdwp.parse_int(data, offset, Int)
            self.thread, offset = Jdwp.parse_long(data, offset, ThreadID)
            self.objectID, offset = TaggedObjectID().from_bytes(data, offset)
            self.location, offset = Location().from_bytes(data, offset)
            return self, offset
    

    class EventMonitorWait(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        eventKind: Optional[Byte] = Byte(EventKind.MONITOR_WAIT)
        requestID: Optional[Int] = None
        thread: Optional[ThreadID] = None
        objectID: Optional[TaggedObjectID] = None
        location: Optional[Location] = None
        timeout: Optional[Long] = None


        def from_bytes(self, data, offset=0) -> Tuple['EventMonitorWait', int]:
            self.requestID, offset = Jdwp.parse_int(data, offset, Int)
            self.thread, offset = Jdwp.parse_long(data, offset, ThreadID)
            self.objectID, offset = TaggedObjectID().from_bytes(data, offset)
            self.location, offset = Location().from_bytes(data, offset)
            self.timeout, offset = Jdwp.parse_long(data, offset, Long)
            return self, offset
    

    class EventMonitorWaited(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        eventKind: Optional[Byte] = Byte(EventKind.MONITOR_WAITED)
        requestID: Optional[Int] = None
        thread: Optional[ThreadID] = None
        objectID: Optional[TaggedObjectID] = None
        location: Optional[Location] = None
        timed_out: Optional[Boolean] = None

        def from_bytes(self, data, offset=0) -> Tuple['EventMonitorWaited', int]:
            self.requestID, offset = Jdwp.parse_int(data, offset, Int)
            self.thread, offset = Jdwp.parse_long(data, offset, ThreadID)
            self.objectID, offset = TaggedObjectID().from_bytes(data, offset)
            self.location, offset = Location().from_bytes(data, offset)
            self.timed_out, offset = Jdwp.parse_byte(data, offset, Boolean)
            return self, offset


    class EventException(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        eventKind: Optional[Byte] = Byte(EventKind.EXCEPTION)
        requestID: Optional[Int] = None
        thread: Optional[ThreadID] = None
        location: Optional[Location] = None
        exception: Optional[TaggedObjectID] = None
        catchLocation: Optional[Location] = None

        def from_bytes(self, data, offset=0) -> Tuple['EventException', int]:
            self.requestID, offset = Jdwp.parse_int(data, offset, Int)
            self.thread, offset = Jdwp.parse_long(data, offset, ThreadID)
            self.location, offset = Location().from_bytes(data, offset)
            self.exception, offset = TaggedObjectID().from_bytes(data, offset)
            self.catchLocation, offset = Location().from_bytes(data, offset)
            return self, offset


    class EventThreadStart(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        eventKind: Optional[Byte] = Byte(EventKind.THREAD_START)
        requestID: Optional[Int] = None
        thread: Optional[ThreadID] = None

        def from_bytes(self, data, offset=0) -> Tuple['EventThreadStart', int]:
            self.requestID, offset = Jdwp.parse_int(data, offset, Int)
            self.thread, offset = Jdwp.parse_long(data, offset, ThreadID)
            return self, offset


    class EventThreadDeath(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        eventKind: Optional[Byte] = Byte(EventKind.THREAD_DEATH)
        requestID: Optional[Int] = None
        thread: Optional[ThreadID] = None

        def from_bytes(self, data, offset=0) -> Tuple['EventThreadDeath', int]:
            self.requestID, offset = Jdwp.parse_int(data, offset, Int)
            self.thread, offset = Jdwp.parse_long(data, offset, ThreadID)
            return self, offset


    class EventClassPrepare(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        eventKind: Optional[Byte] = Byte(EventKind.CLASS_PREPARE)
        requestID: Optional[Int] = None
        thread: Optional[ThreadID] = None
        refTypeTag: Optional[Byte] = None
        typeID: Optional[ReferenceTypeID] = None
        signature: Optional[String] = None
        status: Optional[Int] = None

        def from_bytes(self, data, offset=0) -> Tuple['EventClassPrepare', int]:
            self.requestID, offset = Jdwp.parse_int(data, offset, Int)
            self.thread, offset = Jdwp.parse_long(data, offset, ThreadID)
            self.refTypeTag, offset = Jdwp.parse_byte(data, offset, Byte)
            self.typeID, offset = Jdwp.parse_long(data, offset, ReferenceTypeID)
            self.signature, offet = Jdwp.parse_string(data, offset, String)
            self.status, offset = Jdwp.parse_int(data, offset, Int)
            return self, offset
        

    class EventClassUnload(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        eventKind: Optional[Byte] = Byte(EventKind.CLASS_UNLOAD)
        requestID: Optional[Int] = None
        signature: Optional[String] = None

        def from_bytes(self, data, offset=0) -> Tuple['EventClassUnload', int]:
            self.requestID, offset = Jdwp.parse_int(data, offset, Int)
            self.signature, offet = Jdwp.parse_string(data, offset, String)
            return self, offset


    class EventFieldAccess(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        eventKind: Optional[Byte] = Byte(EventKind.FIELD_ACCESS)
        requestID: Optional[Int] = None
        thread: Optional[ThreadID] = None
        location: Optional[Location] = None
        refTypeTag: Optional[Byte] = None
        typeID: Optional[ReferenceTypeID] = None
        fieldID: Optional[FieldID] = None
        objectID: Optional[TaggedObjectID] = None

        def from_bytes(self, data, offset=0) -> Tuple['EventFieldAccess', int]:
            self.requestID, offset = Jdwp.parse_int(data, offset, Int)
            self.thread, offset = Jdwp.parse_long(data, offset, ThreadID)
            self.location, offset = Location().from_bytes(data, offset)
            self.refTypeTag, offset = Jdwp.parse_byte(data, offset, Byte)
            self.typeID, offset = Jdwp.parse_long(data, offset, ReferenceTypeID)
            self.fieldID, offet = Jdwp.parse_long(data, offset, FieldID)
            self.objectID, offset = TaggedObjectID().from_bytes(data, offset)
            return self, offset
    

    class EventFieldModification(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        eventKind: Optional[Byte] = Byte(EventKind.FIELD_MODIFICATION)
        requestID: Optional[Int] = None
        thread: Optional[ThreadID] = None
        location: Optional[Location] = None
        refTypeTag: Optional[Byte] = None
        typeID: Optional[ReferenceTypeID] = None
        fieldID: Optional[FieldID] = None
        objectID: Optional[TaggedObjectID] = None
        valueToBe: Optional[Value] = None

        def from_bytes(self, data, offset=0) -> Tuple['EventFieldModification', int]:
            self.requestID, offset = Jdwp.parse_int(data, offset, Int)
            self.thread, offset = Jdwp.parse_long(data, offset, ThreadID)
            self.location, offset = Location().from_bytes(data, offset)
            self.refTypeTag, offset = Jdwp.parse_byte(data, offset, Byte)
            self.typeID, offset = Jdwp.parse_long(data, offset, ReferenceTypeID)
            self.fieldID, offet = Jdwp.parse_long(data, offset, FieldID)
            self.objectID, offset = TaggedObjectID().from_bytes(data, offset)
            self.valueToBe, offset = Value().from_bytes(data, offset)
            return self, offset


    class EventVMDeath(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        eventKind: Optional[Byte] = Byte(EventKind.VM_DEATH)
        requestID: Optional[Int] = None

        def from_bytes(self, data, offset=0) -> Tuple['EventVMDeath', int]:
            self.requestID, offset = Jdwp.parse_int(data, offset, Int)
            return self, offset


    Events = {
        EventKind.VM_START: EventVMStart,
        EventKind.SINGLE_STEP: EventSingleStep,
        EventKind.BREAKPOINT: EventBreakpoint,
        #EventKind.FRAME_POP: 3 # undefined,
        EventKind.EXCEPTION: EventException,
        #EventKind.USER_DEFINED: 5 # undefined,
        EventKind.THREAD_START: EventThreadStart,
        EventKind.THREAD_DEATH: EventThreadDeath,
        EventKind.CLASS_PREPARE: EventClassPrepare,
        EventKind.CLASS_UNLOAD: EventClassUnload,
        #EventKind.CLASS_LOAD: 10 # undefined,
        EventKind.FIELD_ACCESS: EventFieldAccess,
        EventKind.FIELD_MODIFICATION: EventFieldModification,
        #EventKind.EXCEPTION_CATCH: 30 # undefined,
        EventKind.METHOD_ENTRY: EventMethodEntry,
        EventKind.METHOD_EXIT: EventMethodExit,
        EventKind.METHOD_EXIT_WITH_RETURN_VALUE: EventMethodExitWithReturnValue,
        EventKind.MONITOR_CONTENDED_ENTER: EventMonitorContendedEnter,
        EventKind.MONITOR_CONTENDED_ENTERED: EventMonitorContendedEntered,
        EventKind.MONITOR_WAIT: EventMonitorWait,
        EventKind.MONITOR_WAITED: EventMonitorWaited,
        EventKind.VM_DEATH: EventVMDeath,
    }


    class CompositeCommand(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        suspendPolicy: Optional[Byte] = None
        # !! TODO: Would like to eventually use a type here.
        events: List = []

        def from_bytes(self, data, offset=0) -> Tuple['CompositeCommand', int]:
            self.suspendPolicy, offset = Jdwp.parse_byte(data, offset, Byte)
            count, offset = Jdwp.parse_int(data, offset)
            for _ in range(count):
                eventKind, offset = Jdwp.parse_byte(data, offset, Byte)
                #print(f"EventKind: {eventKind}")
                if eventKind not in EventSet.Events:
                    #print(f"UNKNOWN EVENT: Got {eventKind} as eventKind.")
                    #print(f"{data[offset:]}")
                    # TODO: Maybe throw here? Letting it pass for now.
                    break
                evt, offset = EventSet.Events[eventKind]().from_bytes(data, offset)
                self.events.append(evt)
            return self, offset


