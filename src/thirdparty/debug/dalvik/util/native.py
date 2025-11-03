import frida

class NativeObject():

    RPC_SCRIPT = """
        rpc.exports = {
            ping: function () {
                return "pong";
            },
            read: function(addr, size) {
                return ptr(addr).readByteArray(size);
            },
            dumpVregs: function(threadAddr) {
                var artThreadShadowFrameOffset = 0xB8;
                var artShadowFrameVregOffset = 0x30;

                var frame = ptr(threadAddr + artThreadShadowFrameOffset).readPointer();
                var vreg_offset = artShadowFrameVregOffset;
                var vreg_count = frame.add(0x30).readU32();
                
                var result = {vreg_cnt: vreg_count};
                result.dex_pc = frame.add(vreg_offset + 0x4).readU32();

                for (var i = 0; i < vreg_count; ++i) {
                    var off = vreg_offset + 0x10 + (i * 4);
                    result[`raw_v${i}`] = frame.add(off).readU32();
                }
                for (var i = 0; i < vreg_count; ++i) {
                    var off = vreg_offset + 0x10 + (vreg_count * 4) + (i * 4);
                    result[`ref_v${i}`] = frame.add(off).readU32();
                }

                return result;
            },
            fetchDexHeader: function(addr) {
                var dataPtr = ptr(addr + 8).readPointer();
                var dataSz = ptr(addr + 16).readU32();
                //var dataPtr = ptr(dataAddr);
                var data = dataPtr.readByteArray(128); // actually 112
                //console.log(data);

                return {addr: dataPtr, size: dataSz, headerData: Array.from(new Uint8Array(data))};
            },

            // I don't see myself implementing this. I think I'm happy with mapping
            // package_name and checksum to lookup androguard generated cache.
            fetchDexType: function(dexAddr, typeOff, typeIdx) {
                var entryAddr = dexAddr + typeOff + (typeIdx * 4);
                return {
                    descriptorIdx: ptr(entryAddr).readU32(), // string_id
                };
            },
            fetchDexString: function(dexAddr, stringOff, stringIdx) {
                var entryAddr = dexAddr + stringOff + (stringIdx * 4);
                return {
                    stringOff: ptr(entryAddr).readU32(), // string_id
                };
            },
            fetchDexField: function(dexAddr, fieldOff, fieldIdx) {
                var entryAddr = dexAddr + fieldOff + (fieldIdx * 8);
                return {
                    classIdx: ptr(entryAddr + 0).readU16(), // type_id
                    typeIdx: ptr(entryAddr + 2).readU16(), // type_id
                    nameIdx: ptr(entryAddr + 4).readU32(), // string_id
                };
            },
            fetchDexProto: function(dexAddr, protoOff, protoIdx) {
                var entryAddr = dexAddr + protoOff + (protoIdx * 8);
                return {
                    shortyIdx: ptr(entryAddr + 0).readU32(), // string_id
                    returnTypeIdx: ptr(entryAddr + 4).readU32(), // type_id
                    paramsOff: ptr(entryAddr + 8).readU32(), // offset to type_list or 0 for none
                };
            },
            fetchDexMethod: function(dexAddr, methodOff, methodIdx) {
                var entryAddr = dexAddr + methodOff + (methodIdx * 8);
                return {
                    classIdx: ptr(entryAddr + 0).readU16(), // type_id
                    protoIdx: ptr(entryAddr + 2).readU16(), // proto_id
                    nameIdx: ptr(entryAddr + 4).readU32(), // string_id
                };
            },
            
        };
    """

    def connect(self, adb):
        self.device = frida.get_usb_device()
        self.session = self.device.attach(adb.proc_pid)
        if self.session:
            # Add utility function.
            self.script = self.session.create_script(NativeObject.RPC_SCRIPT)
            self.script.on("message", lambda msg, data: print("FRIDA MESSAGE:", msg, data))
            self.script.load()
            self.rpc = self.script.exports_sync

            #print("ping -> ", self.rpc.ping())