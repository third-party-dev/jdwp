
import struct

class DexHeader():
    def __init__(self, headerBytes: bytes):
        import struct
        self.magic, self.checksum, self.signature, \
        self.file_size, self.header_size, self.endian_tag, \
        self.link_size, self.link_off, self.map_off, \
        self.string_ids_size, self.string_ids_off, self.type_ids_size, \
        self.type_ids_off, self.proto_ids_size, self.proto_ids_off, \
        self.field_ids_size, self.field_ids_off, self.method_ids_size, \
        self.method_ids_off, self.class_defs_size, self.class_defs_off, \
        self.data_size, self.data_off, \
        = struct.unpack_from('<QI20sIIIIIIIIIIIIIIIIIIII', headerBytes)
    
    def __repr__(self):
        from pprint import pformat
        return pformat(self.__dict__)