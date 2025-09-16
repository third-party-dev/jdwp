#!/usr/bin/env python3

'''
Copyright (c) 2025 Vincent Agriesti

This file is part of the thirdpart JDWP project.
Licensed under the MIT License. See the LICENSE file in the project root
for full license text.
'''

import asyncio
import struct

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
    def parse_string(data, offset):
        str_len = struct.unpack('>I', data[offset:offset+4])[0]
        offset += 4
        return data[offset:offset+str_len].decode('utf-8'), offset + str_len
    
    @staticmethod
    def parse_objectid(data, offset):
        return struct.unpack('>Q', data[offset:offset+8])[0], offset + 8
    
    @staticmethod
    def parse_long(data, offset):
        return struct.unpack('>Q', data[offset:offset+8])[0], offset + 8
    
    @staticmethod
    def parse_byte(data, offset):
        return data[offset], offset + 1

    @staticmethod
    def parse_int(data, offset):
        return struct.unpack('>I', data[offset:offset+4])[0], offset + 4
    
    @staticmethod
    def make_int(val: int):
        return struct.pack('>I', val)

    @staticmethod
    def make_int(val: int):
        return struct.pack('>Q', val)

    @staticmethod
    def make_string(str_val: str):
        return Jdwp.make_int(len(str_Val)) + str_val.encode('utf-8')

class VirtualMachineSet():

    def __init__(self, conn):
        self.conn = conn
    
    async def Version(self):
        await self.conn.send(1, 1)
        data, _, _, _ = await self.conn.recv()

        offset = 0
        result = {}
        result['description'], offset = Jdwp.parse_string(data, offset)
        result['jdwpMajor'], offset = Jdwp.parse_int(data, offset)
        result['jdwpMinor'], offset = Jdwp.parse_int(data, offset)
        result['vmVersion'], offset = Jdwp.parse_string(data, offset)
        result['vmName'], offset = Jdwp.parse_string(data, offset)
        return result
    
    async def ClassesBySignature(self, signature: str):
        await self.conn.send(1, 2, data=Jdwp.make_string(signature))
        data, _, _, _ = await self.conn.recv()

        offset = 0
        count, offset = Jdwp.parse_int(data, offset)
        classes = []
        for _ in range(count):
            result = {}
            result['refTYpeTag'], offset = Jdwp.parse_byte(data, offset)
            result['typeID'], offset = Jdwp.parse_objectid(data, offset)
            result['status'], offset = Jdwp.parse_int(data, offset)
            classes.append(result)
        return classes

    async def AllClasses(self):
        await self.conn.send(1, 3)
        data, _, _, _ = await self.conn.recv()

        offset = 0
        count, offset = Jdwp.parse_int(data, offset)
        classes = []
        for _ in range(count):
            result = {}
            result['refTYpeTag'], offset = Jdwp.parse_byte(data, offset)
            result['typeID'], offset = Jdwp.parse_objectid(data, offset)
            result['signature'], offset = Jdwp.parse_string(data, offset)
            result['status'], offset = Jdwp.parse_int(data, offset)
            classes.append(result)
        return classes
    
    async def AllThreads(self):
        await self.conn.send(1, 4)
        data, _, _, _ = await self.conn.recv()

        offset = 0
        count, offset = Jdwp.parse_int(data, offset)
        threads = []
        for _ in range(count):
            result = {}
            result['thread'], offset = Jdwp.parse_objectid(data, offset)
            threads.append(result)
        return threads
    
    async def TopLevelThreadGroup(self):
        await self.conn.send(1, 5)
        data, _, _, _ = await self.conn.recv()

        offset = 0
        count, offset = Jdwp.parse_int(data, offset)
        groups = []
        for _ in range(count):
            result = {}
            result['threadGroupID'], offset = Jdwp.parse_objectid(data, offset)
            groups.append(result)
        return groups
    
    async def Dispose(self):
        await self.conn.send(1, 6)
    
    async def IDSizes(self):
        await self.conn.send(1, 7)
        data, _, _, _ = await self.conn.recv()

        offset = 0
        result = {}
        result['fieldIDSize'], offset = Jdwp.parse_int(data, offset)
        result['methodIDSize'], offset = Jdwp.parse_int(data, offset)
        result['objectIDSize'], offset = Jdwp.parse_int(data, offset)
        result['referenceTypeIDSize'], offset = Jdwp.parse_int(data, offset)
        result['frameIDSize'], offset = Jdwp.parse_int(data, offset)
        return result
    
    async def Suspend(self):
        await self.conn.send(1, 8)
        #data, _, _, error_code = await self.conn.recv()
    
    async def Resume(self):
        await self.conn.send(1, 9)
    
    async def Exit(self, exit_code: int):
        await self.conn.send(1, 10, data=Jdwp.make_int(exit_code))

    async def CreateString(self, utf: str):
        await self.conn.send(1, 11, data=Jdwp.make_string(utf))
        data, _, _, _ = await self.conn.recv()

        offset = 0
        result = {}
        result['stringObject'], offset = Jdwp.parse_objectid(data, offset)
        return result
    
    async def Capabilities(self):
        await self.conn.send(1, 12, data=Jdwp.make_string(utf))
        data, _, _, _ = await self.conn.recv()

        offset = 0
        result = {}
        result['canWatchFieldModification'], offset = Jdwp.parse_byte(data, offset)
        result['canWatchFieldAccess'], offset = Jdwp.parse_byte(data, offset)
        result['canGetBytecodes'], offset = Jdwp.parse_byte(data, offset)
        result['canGetSyntheticAttribute'], offset = Jdwp.parse_byte(data, offset)
        result['canGetOwnedMonitorInfo'], offset = Jdwp.parse_byte(data, offset)
        result['canGetCurrentContendedMonitor'], offset = Jdwp.parse_byte(data, offset)
        result['canGetMonitorInfo'], offset = Jdwp.parse_byte(data, offset)
        return result

    async def ClassPaths(self):
        await self.conn.send(1, 13)
        data, _, _, _ = await self.conn.recv()

        offset = 0
        result = {'classpaths': [], 'bootclasspaths': []}
        result['baseDir'], offset = Jdwp.parse_string(data, offset)

        count, offset = Jdwp.parse_int(data, offset)
        for _ in range(count):
            entry = {}
            entry['path'], offset = Jdwp.parse_objectid(data, offset)
            result['classpaths'].append(entry)
        
        count, offset = Jdwp.parse_int(data, offset)
        for _ in range(count):
            entry = {}
            entry['path'], offset = Jdwp.parse_objectid(data, offset)
            result['bootclasspaths'].append(entry)
        
        return result
    
    async def DisposeObjects(self, requests):
        raise NotImplementedError("DisposeObjects not implemented.")

    async def HoldEvents(self):
        await self.conn.send(1, 15)

    async def ReleaseEvents(self):
        await self.conn.send(1, 16)
    
    async def CapabilitiesNew(self):
        await self.conn.send(1, 17)
        data, _, _, _ = await self.conn.recv()

        offset = 0
        result = {}

        result['canWatchFieldModification'], offset = Jdwp.parse_byte(data, offset)
        result['canWatchFieldAccess'], offset = Jdwp.parse_byte(data, offset)
        result['canGetBytecodes'], offset = Jdwp.parse_byte(data, offset)
        result['canGetSyntheticAttribute'], offset = Jdwp.parse_byte(data, offset)
        result['canGetOwnedMonitorInfo'], offset = Jdwp.parse_byte(data, offset)
        result['canGetCurrentContendedMonitor'], offset = Jdwp.parse_byte(data, offset)
        result['canGetMonitorInfo'], offset = Jdwp.parse_byte(data, offset)
        # The new stuff
        result['canRedefineClasses'], offset = Jdwp.parse_byte(data, offset)
        result['canAddMethod'], offset = Jdwp.parse_byte(data, offset)
        result['canUnrestrictedlyRedefineClasses'], offset = Jdwp.parse_byte(data, offset)
        result['canPopFrames'], offset = Jdwp.parse_byte(data, offset)
        result['canUseInstanceFilters'], offset = Jdwp.parse_byte(data, offset)
        result['canGetSourceDebugExtension'], offset = Jdwp.parse_byte(data, offset)
        result['canRequestVMDeathEvent'], offset = Jdwp.parse_byte(data, offset)
        result['canSetDefaultStratum'], offset = Jdwp.parse_byte(data, offset)
        result['canGetInstanceInfo'], offset = Jdwp.parse_byte(data, offset)
        result['canRequestMonitorEvents'], offset = Jdwp.parse_byte(data, offset)
        result['canGetMonitorFrameInfo'], offset = Jdwp.parse_byte(data, offset)
        result['canUseSourceNameFilters'], offset = Jdwp.parse_byte(data, offset)
        result['canGetConstantPool'], offset = Jdwp.parse_byte(data, offset)
        result['canForceEarlyReturn'], offset = Jdwp.parse_byte(data, offset)
        result['reserved22'], offset = Jdwp.parse_byte(data, offset)
        result['reserved23'], offset = Jdwp.parse_byte(data, offset)
        result['reserved24'], offset = Jdwp.parse_byte(data, offset)
        result['reserved25'], offset = Jdwp.parse_byte(data, offset)
        result['reserved26'], offset = Jdwp.parse_byte(data, offset)
        result['reserved27'], offset = Jdwp.parse_byte(data, offset)
        result['reserved28'], offset = Jdwp.parse_byte(data, offset)
        result['reserved29'], offset = Jdwp.parse_byte(data, offset)
        result['reserved30'], offset = Jdwp.parse_byte(data, offset)
        result['reserved31'], offset = Jdwp.parse_byte(data, offset)
        result['reserved32'], offset = Jdwp.parse_byte(data, offset)
        return result

    async def RedefineClasses(self, *args):
        #await self.conn.send(1, 18)
        raise NotImplementedError("RedefinedClasses not implemented.")

    async def SetDefaultStratum(self, *args):
        #await self.conn.send(1, 19)
        raise NotImplementedError("SetDefaultStratum not implemented.")
    
    async def AllClassesWithGeneric(self):
        await self.conn.send(1, 20)
        data, _, _, _ = await self.conn.recv()

        offset = 0
        count, offset = Jdwp.parse_int(data, offset)
        classes = []
        for _ in range(count):
            entry = {}
            entry['refTYpeTag'], offset = Jdwp.parse_byte(data, offset)
            entry['typeID'], offset = Jdwp.parse_objectid(data, offset)
            entry['signature'], offset = Jdwp.parse_string(data, offset)
            entry['genericSignature'], offset = Jdwp.parse_string(data, offset)
            entry['status'], offset = Jdwp.parse_int(data, offset)
            classes.append(entry)
        return classes

    async def InstanceCounts(self, *args):
        #await self.conn.send(1, 21)
        raise NotImplementedError("SetDefaultStratum not implemented.")

class ReferenceTypeSet():

    def __init__(self, conn):
        self.conn = conn
    
    async def Signature(self, refType):
        await self.conn.send(2, 1, data=Jdwp.make_objectid(refType))
        data, _, _, _ = await self.conn.recv()

        offset = 0
        result = {}
        result['signature'], offset = Jdwp.parse_string(data, offset)
        return result
    
    async def ClassLoader(self, refType):
        await self.conn.send(2, 2, data=Jdwp.make_objectid(refType))
        data, _, _, _ = await self.conn.recv()

        offset = 0
        result = {}
        result['classLoader'], offset = Jdwp.parse_objectid(data, offset)
        return result
    
    async def Modifiers(self, refType):
        await self.conn.send(2, 3, data=Jdwp.make_objectid(refType))
        data, _, _, _ = await self.conn.recv()

        offset = 0
        result = {}
        result['modBits'], offset = Jdwp.parse_int(data, offset)
        return result
    
    async def Fields(self, refType):
        await self.conn.send(2, 4, data=Jdwp.make_objectid(refType))
        data, _, _, _ = await self.conn.recv()

        offset = 0
        count, offset = Jdwp.parse_int(data, offset)
        declared = []
        for _ in range(count):
            entry = {}
            # Note: fieldID is VM-specific. Probably 4 bytes on 32 bit systems?
            entry['fieldID'], offset = Jdwp.parse_objectid(data, offset)
            entry['name'], offset = Jdwp.parse_string(data, offset)
            entry['signature'], offset = Jdwp.parse_string(data, offset)
            entry['modBits'], offset = Jdwp.parse_int(data, offset)
            declared.append(entry)
        return declared

    async def Methods(self, refType):
        await self.conn.send(2, 5, data=Jdwp.make_objectid(refType))
        data, _, _, _ = await self.conn.recv()

        offset = 0
        count, offset = Jdwp.parse_int(data, offset)
        declared = []
        for _ in range(count):
            entry = {}
            # Note: methodID is VM-specific. Probably 4 bytes on 32 bit systems?
            entry['methodID'], offset = Jdwp.parse_objectid(data, offset)
            entry['name'], offset = Jdwp.parse_string(data, offset)
            entry['signature'], offset = Jdwp.parse_string(data, offset)
            entry['modBits'], offset = Jdwp.parse_int(data, offset)
            declared.append(entry)
        return declared

    
    async def GetValues(self, *args):
        #await self.conn.send(1, 6)
        raise NotImplementedError("GetValues not implemented.")
    
    async def SourceFile(self, refType):
        await self.conn.send(2, 7, data=Jdwp.make_objectid(refType))
        data, _, _, _ = await self.conn.recv()

        result = {}
        result['sourceFile'], offset = Jdwp.parse_string(data, offset)
        return result
    
    async def NestedTypes(self, refType):
        await self.conn.send(2, 8, data=Jdwp.make_objectid(refType))
        data, _, _, _ = await self.conn.recv()

        offset = 0
        count, offset = Jdwp.parse_int(data, offset)
        classes = []
        for _ in range(count):
            entry = {}
            # Note: methodID is VM-specific. Probably 4 bytes on 32 bit systems?
            entry['refTagType'], offset = Jdwp.parse_byte(data, offset)
            entry['typeID'], offset = Jdwp.parse_objectid(data, offset)
            classes.append(entry)
        return classes
    
    async def Status(self, refType):
        await self.conn.send(2, 9, data=Jdwp.make_objectid(refType))
        data, _, _, _ = await self.conn.recv()

        offset = 0
        result = {}
        result['status'], offset = Jdwp.parse_int(data, offset)
        return result
    
    async def Interfaces(self, refType):
        await self.conn.send(2, 10, data=Jdwp.make_objectid(refType))
        data, _, _, _ = await self.conn.recv()

        offset = 0
        count, offset = Jdwp.parse_int(data, offset)
        ifaces = []
        for _ in range(count):
            entry = {}
            # Note: methodID is VM-specific. Probably 4 bytes on 32 bit systems?
            entry['interfaceType'], offset = Jdwp.parse_objectid(data, offset)
            ifaces.append(entry)
        return ifaces
    
    async def ClassObject(self, refType):
        await self.conn.send(2, 11, data=Jdwp.make_objectid(refType))
        data, _, _, _ = await self.conn.recv()

        offset = 0
        result = {}
        result['classObject'], offset = Jdwp.parse_objectid(data, offset)
        return result
    
    async def SourceDebugExtension(self, refType):
        await self.conn.send(2, 12, data=Jdwp.make_objectid(refType))
        data, _, _, _ = await self.conn.recv()

        offset = 0
        result = {}
        result['extension'], offset = Jdwp.parse_string(data, offset)
        return result
    
    async def SignatureWithGeneric(self, refType):
        await self.conn.send(2, 13, data=Jdwp.make_objectid(refType))
        data, _, _, _ = await self.conn.recv()

        offset = 0
        result = {}
        result['signature'], offset = Jdwp.parse_string(data, offset)
        result['genericSignature'], offset = Jdwp.parse_string(data, offset)
        return result
    
    async def FieldsWithGeneric(self, refType):
        await self.conn.send(2, 14, data=Jdwp.make_objectid(refType))
        data, _, _, _ = await self.conn.recv()

        offset = 0
        count, offset = Jdwp.parse_int(data, offset)
        declared = []
        for _ in range(count):
            entry = {}
            # Note: fieldID is VM-specific. Probably 4 bytes on 32 bit systems?
            entry['fieldID'], offset = Jdwp.parse_objectid(data, offset)
            entry['name'], offset = Jdwp.parse_string(data, offset)
            entry['signature'], offset = Jdwp.parse_string(data, offset)
            entry['genericSignature'], offset = Jdwp.parse_string(data, offset)
            entry['modBits'], offset = Jdwp.parse_int(data, offset)
            declared.append(entry)
        return declared
    
    async def MethodsWithGeneric(self, refType):
        await self.conn.send(2, 15, data=Jdwp.make_objectid(refType))
        data, _, _, _ = await self.conn.recv()

        offset = 0
        count, offset = Jdwp.parse_int(data, offset)
        declared = []
        for _ in range(count):
            entry = {}
            # Note: methodID is VM-specific. Probably 4 bytes on 32 bit systems?
            entry['methodID'], offset = Jdwp.parse_objectid(data, offset)
            entry['name'], offset = Jdwp.parse_string(data, offset)
            entry['signature'], offset = Jdwp.parse_string(data, offset)
            entry['genericSignature'], offset = Jdwp.parse_string(data, offset)
            entry['modBits'], offset = Jdwp.parse_int(data, offset)
            declared.append(entry)
        return declared
    
    async def Instances(self, *args):
        #await self.conn.send(1, 16)
        raise NotImplementedError("Instances not implemented.")
    
    async def ClassFileVersion(self, refType):
        await self.conn.send(2, 17, data=Jdwp.make_objectid(refType))
        data, _, _, _ = await self.conn.recv()

        offset = 0
        result = {}
        result['majorVersion'], offset = Jdwp.parse_int(data, offset)
        result['minorVersion'], offset = Jdwp.parse_int(data, offset)
        return result
    
    async def ConstantPool(self, refType):
        raise NotImplementedError("ConstantPool not implemented.")
        # await self.conn.send(2, 18, data=Jdwp.make_objectid(refType))
        # data, _, _, _ = await self.conn.recv()

        # offset = 0
        # result = {}
        # result['count'], offset = Jdwp.parse_int(data, offset)
        # bytes_count, offset = Jdwp.parse_int(data, offset)
        # result['bytes'] = data[offset:offset+bytes_count]
        
        # return result
    

class ClassTypeSet():

    def __init__(self, conn):
        self.conn = conn

    async def Superclass(self, clazz):
        await self.conn.send(3, 1, data=Jdwp.make_objectid(clazz))
        data, _, _, _ = await self.conn.recv()

        offset = 0
        result = {}
        result['superclass'], offset = Jdwp.parse_objectid(data, offset)
        return result
    
    async def SetValues(self, *args):
        raise NotImplementedError("SetValues not implemented.")
        # await self.conn.send(3, 2, data=Jdwp.make_objectid(clazz))

    async def InvokeMethod(self, *args):
        raise NotImplementedError("InvokeMethod not implemented.")
        # await self.conn.send(3, 3, data=Jdwp.make_objectid(clazz))
    
    async def NewInstance(self, *args):
        raise NotImplementedError("NewInstance not implemented.")
        # await self.conn.send(3, 4, data=Jdwp.make_objectid(clazz))
    
class ArrayTypeSet():

    def __init__(self, conn):
        self.conn = conn

    async def NewInstance(self, arrType, length):
        out = Jdwp.make_objectid(arrType) + Jdwp.make_int(length)
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
        # await self.conn.send(5, 1, data=Jdwp.make_objectid(clazz))

class MethodSet():

    def __init__(self, conn):
        self.conn = conn

    async def LineTable(self, refType, methodID):
        out = Jdwp.make_objectid(refType) + Jdwp.make_objectid(methodID)
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
    
    async def VariableTable(self, refType, methodID):
        out = Jdwp.make_objectid(refType) + Jdwp.make_objectid(methodID)
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
    
    async def Bytecodes(self, refType, methodID):
        out = Jdwp.make_objectid(refType) + Jdwp.make_objectid(methodID)
        await self.conn.send(6, 3, data=out)
        data, _, _, _ = await self.conn.recv()

        offset = 0
        byte_count, offset = Jdwp.parse_int(data, offset)
        return {'bytes': data[offset:offset+byte_count]}
        
    async def IsObsolete(self, refType, methodID):
        out = Jdwp.make_objectid(refType) + Jdwp.make_objectid(methodID)
        await self.conn.send(6, 4, data=out)
        data, _, _, _ = await self.conn.recv()

        offset = 0
        obsolete, offset = Jdwp.parse_byte(data, offset)
        return {'isObsolete': obsolete}
    
    async def VariableTableWithGeneric(self, refType, methodID):
        out = Jdwp.make_objectid(refType) + Jdwp.make_objectid(methodID)
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
    
    async def ReferenceType(self, objectid):
        await self.conn.send(9, 1, data=Jdwp.make_objectid(objectid))
        data, _, _, _ = await self.conn.recv()

        offset = 0
        result = {}
        # tagged-objectID? ... for now I'm splitting into two fields.
        result['refTypeTag'], offset = Jdwp.parse_byte(data, offset)
        result['typeID'], offset = Jdwp.parse_objectid(data, offset)
        return result
    
    async def GetValues(self, *args):
        raise NotImplementedError("GetValues not implemented.")
        # await self.conn.send(9, 2, data=Jdwp.make_objectid(clazz))
    
    async def SetValues(self, *args):
        raise NotImplementedError("SetValues not implemented.")
        # await self.conn.send(9, 3, data=Jdwp.make_objectid(clazz))
    
    async def MonitorInfo(self, objectid):
        await self.conn.send(9, 5, data=Jdwp.make_objectid(objectid))
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
        # await self.conn.send(9, 6, data=Jdwp.make_objectid(clazz))
    
    async def DisableCollection(self, objectid):
        await self.conn.send(9, 7, data=Jdwp.make_objectid(objectid))
        #data, _, _, _ = await self.conn.recv()
    
    async def EnableCollection(self, objectid):
        await self.conn.send(9, 8, data=Jdwp.make_objectid(objectid))
        #data, _, _, _ = await self.conn.recv()
    
    async def IsCollected(self, objectid):
        await self.conn.send(9, 9, data=Jdwp.make_objectid(objectid))
        data, _, _, _ = await self.conn.recv()

        offset = 0
        result = {}
        result['isCollected'], offset = Jdwp.parse_byte(data, offset)
        return result
    
    async def ReferringObjects(self, objectid, maxReferrers):
        out = Jdwp.make_objectid(objectid) + Jdwp.make_int(maxReferrers)
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

    async def IsCollected(self, stringObject):
        await self.conn.send(10, 1, data=Jdwp.make_objectid(stringObject))
        data, _, _, _ = await self.conn.recv()

        offset = 0
        result = {}
        result['stringValue'], offset = Jdwp.parse_string(data, offset)
        return result

class ThreadReferenceSet():

    def __init__(self, conn):
        self.conn = conn

    async def Name(self, thread):
        await self.conn.send(11, 1, data=Jdwp.make_objectid(thread))
        data, _, _, _ = await self.conn.recv()

        offset = 0
        result = {}
        result['threadName'], offset = Jdwp.parse_string(data, offset)
        return result
    
    async def Suspend(self, thread):
        await self.conn.send(11, 2, data=Jdwp.make_objectid(thread))
        #data, _, _, _ = await self.conn.recv()

    async def Resume(self, thread):
        await self.conn.send(11, 3, data=Jdwp.make_objectid(thread))
        #data, _, _, _ = await self.conn.recv()
    
    async def Status(self, thread):
        await self.conn.send(11, 4, data=Jdwp.make_objectid(thread))
        data, _, _, _ = await self.conn.recv()

        offset = 0
        result = {}
        result['threadStatus'], offset = Jdwp.parse_int(data, offset)
        result['suspendStatus'], offset = Jdwp.parse_int(data, offset)
        return result
    
    async def ThreadGroup(self, thread):
        await self.conn.send(11, 4, data=Jdwp.make_objectid(thread))
        data, _, _, _ = await self.conn.recv()

        offset = 0
        result = {}
        result['threadGroupID'], offset = Jdwp.parse_objectid(data, offset)
        return result
