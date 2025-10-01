#!/usr/bin/env python3

import sys
import logging
from androguard.core import dex
from androguard import util

import struct

util.set_log("CRITICAL")

with open(sys.argv[1], "rb") as f:
    data = f.read()

with open('method-table.txt', 'w') as fobj:
    print("Parsing dex.")
    d = dex.DEX(data)
    print("Dex parsing done.")

    # Parse out the type table since its missing from Androguard v4?
    # EXample: d.get_strings()[type_ids[0x1ede]]
    type_ids_size = d.header.type_ids_size
    type_ids_off  = d.header.type_ids_off
    type_ids = []
    for i in range(type_ids_size):
        offset = type_ids_off + i * 4
        (descriptor_idx,) = struct.unpack_from("<I", data, offset)
        type_ids.append(descriptor_idx)

    breakpoint()

    # type@XXXX
    # d.get_strings()[type_ids[0x1ede]]

    # method@XXXX
    #print(d.get_methods()[0xc802].get_triple())
    
    # string@XXXX
    # d.get_strings()[0xb679]


