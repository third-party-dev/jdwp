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
#TaggedObjectID = strict_typedef(type("TaggedObjectID", (int,), {}))
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

# rtt = Byte(34)
# tid = ReferenceTypeID(3545)
# status = Int(435)

# cbs = ClassesBySignatureEntry()
# cbs.refTypeTag = rtt
# cbs.typeID = tid
# cbs.status = status

# cbsr = ClassesBySignatureReply()
# cbsr.classes = [*cbsr.classes, cbs]


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


class AllThreadsReply(BaseModel):
    model_config = ConfigDict(validate_assignment=True)
    threads: List[ThreadID] = []

    def from_bytes(self, data, offset=0) -> Tuple['AllThreadsReply', int]:
        count, offset = Jdwp.parse_int(data, offset)
        for _ in range(count):
            value, offset = Jdwp.parse_long(data, offset, ThreadID)
            self.threads = [*self.threads, value]
        return self, offset


class TopLevelThreadGroupReply(BaseModel):
    model_config = ConfigDict(validate_assignment=True)
    groups: List[ThreadGroupID] = []

    def from_bytes(self, data, offset=0) -> Tuple['TopLevelThreadGroupReply', int]:
        count, offset = Jdwp.parse_int(data, offset)
        for _ in range(count):
            value, offset = Jdwp.parse_long(data, offset, ThreadGroupID)
            self.groups = [*self.groups, value]
        return self, offset


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

# d1 = DisposeObjectsEntry()
# d1.objectID = ObjectID(5235)
# d1.refCnt = Int(3)

# d2 = DisposeObjectsEntry()
# d2.objectID = ObjectID(6453)
# d2.refCnt = Int(8)

# dr = DisposeObjectsRequest()
# dr.requests = [*dr.requests, d1]
# dr.requests = [*dr.requests, d2]

# dr = DisposeObjectsRequest(requests=[
#     DisposeObjectsEntry(objectID=ObjectID(3425), refCnt=Int(5)),
#     DisposeObjectsEntry(objectID=ObjectID(543), refCnt=Int(7)),
# ])

# data = '''
# {
#   "requests": [
#     {"objectID": 657467, "refCnt": 1},
#     {"objectID": 43523, "refCnt": 2}
#   ]
# }
# '''
# dr = DisposeObjectsRequest.model_validate_json(data)

# print(dr.to_bytes())




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


# rcr = RedefineClassesRequest()
# rcr.refType = ReferenceTypeID(435)
# rcr.classfile = [*rcr.classfile, Byte(0x41), Byte(0x42), Byte(0x43)]
# print(rcr.to_bytes())

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
            value, offset = Jdwp.parse_long(data, offset)
            self.instanceCounts = [*self.instanceCounts, Long(value)]
        return self, offset


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


pdb.set_trace()