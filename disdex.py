#!/usr/bin/env python3

import struct


from thirdparty.dalvik.dex import disassemble


example_bytecodes = [
    32, 128, 222, 30, 56, 0, 18, 0,7, 128, 31, 0, 222, 30, 82, 
    1,126, 54, 21, 2, 0, 128, 181, 33,56, 1, 8, 0, 82, 8, 126, 
    54,177,40,89,8,126,54,40,6,34,0,222,30,112,48,2,200,112,8,
    84,8,127,54,113,0,183,140,0,0,12,1,82,2,126,54,18,35,18,20,
    56,2,23,0,50,66,17,0,51,50,7,0,113,16,62,117,8,0,41,0,120,
    0,34,8,28,19,26,0,135,132,112,32,221,110,8,0,39,8,113,16,62,
    117,8,0,40,61,113,16,62,117,8,0,84,120,129,54,114,16,81,116,
    8,0,12,8,31,8,216,30,110,16,223,199,8,0,12,8,34,2,101,15,
    112,16,130,89,2,0,26,5,196,164,113,32,180,89,82,0,7,37,31,
    5,37,16,98,6,189,29,110,16,239,91,6,0,12,6,113,32,89,94,101,
    0,98,5,171,30,110,16,104,94,5,0,12,5,110,32,146,89,82,0,34,
    5,162,15,112,48,255,90,37,8,89,4,126,54,110,32,3,91,5,0,12,
    8,51,24,3,0,40,46,31,8,150,15,110,16,193,90,8,0,12,8,28,2,
    207,19,113,16,105,146,2,0,12,2,28,4,207,19,98,5,70,40,28,6,
    220,30,113,16,128,146,6,0,12,6,110,32,201,150,101,0,12,5,113,
    32,129,146,84,0,12,4,40,2,18,4,34,5,209,17,112,48,198,104,37,
    4,89,3,126,54,110,48,124,79,88,0,12,8,51,24,3,0,17,1,56,8,10,
    0,31,8,207,19,18,0,114,32,95,114,8,0,12,8,17,8,34,8,45,19,26,
    0,121,182,112,32,67,111,8,0,39,8,
]

offset = 0
prev_offset = -1
ins_idx = 0
while offset < len(example_bytecodes) and offset != prev_offset:
    prev_offset = offset
    ins, offset = disassemble(example_bytecodes, offset)
    ins_bytecode = bytes(example_bytecodes[prev_offset:offset]).hex()
    ins_bytecode_idx = f'{int(prev_offset/2):04x}'
    print(f'{ins_idx}: {ins_bytecode_idx}: {ins} [bytecode: {ins_bytecode}]')
    ins_idx += 1
    #breakpoint()


'''
#!/usr/bin/env python3

import sys
import logging
from androguard.core import dex
from androguard import util

util.set_log("CRITICAL")

with open(sys.argv[1], "rb") as f:
    data = f.read()

with open('method-table.txt', 'w') as fobj:
    print("Parsing dex.")
    d = dex.DEX(data)
    print("Dex parsing done.")

    print(d.get_methods()[0xc802].get_triple())
'''