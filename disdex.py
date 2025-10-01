#!/usr/bin/env python3

import struct

parser = {}

def p_10x(data: bytes, offset: int = 0):
    return { 'op': data[0+offset] }, offset + 2
parser['10x'] = p_10x

def p_12x(data: bytes, offset: int = 0):
    return {
        'op': data[0+offset],
        'b': (data[1+offset] >> 4) & 0xF,
        'a': data[1+offset] & 0xF
    }, offset + 2
parser['12x'] = p_12x
parser['11n'] = p_12x


def p_11x(data: bytes, offset: int = 0):
    return {
        'op': data[0+offset],
        'aa': data[1+offset],
    }, offset + 2
parser['11x'] = p_11x
parser['10t'] = p_11x


def p_20t(data: bytes, offset: int = 0):
    return {
        'op': data[0+offset],
        #'aaaa': bytes(data[2+offset:4+offset]),
        'aaaa': int.from_bytes(data[2+offset:4+offset], "little"),
    }, offset + 4
parser['20t'] = p_20t

def p_20bc(data: bytes, offset: int = 0):
    return {
        'op': data[0+offset],
        'aa': data[1+offset],
        #'bbbb': bytes(data[2+offset:4+offset]),
        'bbbb': int.from_bytes(data[2+offset:4+offset], "little"),
    }, offset + 4
parser['20bc'] = p_20bc

parser['22x'] = p_20bc
parser['21t'] = p_20bc
parser['21s'] = p_20bc
parser['21h'] = p_20bc
parser['21c'] = p_20bc

def p_23x(data: bytes, offset: int = 0):
    return {
        'op': data[0+offset],
        'aa': data[1+offset],
        'bb': data[2+offset],
        'cc': data[3+offset],
    }, offset + 4
parser['23x'] = p_23x
parser['22b'] = p_23x

def p_22t(data: bytes, offset: int = 0):
    return {
        'op': data[0+offset],
        'b': (data[1+offset] >> 4) & 0xF,
        'a': data[1+offset] & 0xF,
        #'cccc': bytes(data[2+offset:4+offset]),
        'cccc': int.from_bytes(data[2+offset:4+offset], "little"),
    }, offset + 4
parser['22t'] = p_22t
parser['22s'] = p_22t
parser['22c'] = p_22t
parser['22cs'] = p_22t


def p_30t(data: bytes, offset: int = 0):
    return {
        'op': data[0+offset],
        #'aaaahi': bytes(data[2+offset:4+offset]),
        'aaaahi': int.from_bytes(data[2+offset:4+offset], "little"),
        #'aaaalo': bytes(data[4+offset:6+offset]),
        'aaaalo': int.from_bytes(data[4+offset:6+offset], "little"),
    }, offset + 6
parser['30t'] = p_30t


def p_32x(data: bytes, offset: int = 0):
    return {
        'op': data[0+offset],
        #'aaaa': bytes(data[2+offset:4+offset]),
        'aaaa': int.from_bytes(data[2+offset:4+offset], "little"),
        #'bbbb': bytes(data[4+offset:6+offset]),
        'bbbb': int.from_bytes(data[4+offset:6+offset], "little"),
    }, offset + 6
parser['32x'] = p_32x

def p_31i(data: bytes, offset: int = 0):
    return {
        'op': data[0+offset],
        'aa': data[1+offset],
        #'bbbbhi': bytes(data[2+offset:4+offset]),
        'bbbbhi': int.from_bytes(data[2+offset:4+offset], "little"),
        #'bbbblo': bytes(data[4+offset:6+offset]),
        'bbbblo': int.from_bytes(data[4+offset:6+offset], "little"),
    }, offset + 6
parser['31i'] = p_31i
parser['31t'] = p_31i
parser['31c'] = p_31i

def p_35c(data: bytes, offset: int = 0):
    return {
        'op': data[0+offset],
        'a': (data[1+offset] >> 4) & 0xF,
        'g': data[1+offset] & 0xF,
        #'bbbb': bytes(data[2+offset:4+offset]),
        'bbbb': int.from_bytes(data[2+offset:4+offset], "little"),
        'f': (data[4+offset] >> 4) & 0xF,
        'e': data[4+offset] & 0xF,
        'd': (data[5+offset] >> 4) & 0xF,
        'c': data[5+offset] & 0xF,
    }, offset + 6
parser['35c'] = p_35c
parser['35ms'] = p_35c
parser['35mi'] = p_35c

def p_3rc(data: bytes, offset: int = 0):
    return {
        'op': data[0+offset],
        'aa': data[1+offset],
        #'bbbb': bytes(data[2+offset:4+offset]),
        'bbbb': int.from_bytes(data[2+offset:4+offset], "little"),
        #'cccc': bytes(data[4+offset:6+offset]),
        'cccc': int.from_bytes(data[4+offset:6+offset], "little"),
    }, offset + 6
parser['3rc'] = p_32x
parser['3rms'] = p_32x
parser['3rmi'] = p_32x

def p_45cc(data: bytes, offset: int = 0):
    return {
        'op': data[0+offset],
        'a': (data[1+offset] >> 4) & 0xF,
        'g': data[1+offset] & 0xF,
        #'bbbb': bytes(data[2+offset:4+offset]),
        'bbbb': int.from_bytes(data[2+offset:4+offset], "little"),
        'f': (data[4+offset] >> 4) & 0xF,
        'e': data[4+offset] & 0xF,
        'd': (data[5+offset] >> 4) & 0xF,
        'c': data[5+offset] & 0xF,
        #'hhhh': bytes(data[6+offset:8+offset]),
        'hhhh': int.from_bytes(data[6+offset:8+offset], "little"),
    }, offset + 8
parser['45cc'] = p_45cc


def p_4rcc(data: bytes, offset: int = 0):
    return {
        'op': data[0+offset],
        'aa': data[1+offset],
        #'bbbb': bytes(data[2+offset:4+offset]),
        'bbbb': int.from_bytes(data[2+offset:4+offset], "little"),
        #'cccc': bytes(data[4+offset:6+offset]),
        'cccc': int.from_bytes(data[4+offset:6+offset], "little"),
        #'hhhh': bytes(data[6+offset:8+offset]),
        'hhhh': int.from_bytes(data[6+offset:8+offset], "little"),
    }, offset + 8
parser['4rcc'] = p_4rcc


def p_51l(data: bytes, offset: int = 0):
    return {
        'op': data[0+offset],
        'aa': data[1+offset],
        #'bbbb4': bytes(data[2+offset:4+offset]),
        'bbbb4': int.from_bytes(data[2+offset:4+offset], "little"),
        #'bbbb3': bytes(data[4+offset:6+offset]),
        'bbbb3': int.from_bytes(data[4+offset:6+offset], "little"),
        #'bbbb2': bytes(data[6+offset:8+offset]),
        'bbbb2': int.from_bytes(data[6+offset:8+offset], "little"),
        #'bbbb1': bytes(data[8+offset:10+offset]),
        'bbbb1': int.from_bytes(data[8+offset:10+offset], "little"),
    }, offset + 10
parser['51l'] = p_51l



def op_00(data: bytes, offset: int = 0):
    params, offset = parser['10x'](data, offset)
    return f"nop", offset

def op_01(data: bytes, offset: int = 0):
    params, offset = parser['12x'](data, offset)
    return f"move v{params['a']}, v{params['b']}", offset

def op_02(data: bytes, offset: int = 0):
    params, offset = parser['22x'](data, offset)
    return f"move/from16 v{params['aa']}, v{params['bbbb']}", offset

def op_03(data: bytes, offset: int = 0):
    params, offset = parser['32x'](data, offset)
    return f"move/16 v{params['aaaa']}, v{params['bbbb']}", offset

def op_04(data: bytes, offset: int = 0):
    params, offset = parser['12x'](data, offset)
    return f"move-wide v{params['a']}, v{params['b']}", offset

def op_05(data: bytes, offset: int = 0):
    params, offset = parser['22x'](data, offset)
    return f"move-wide/from16 v{params['aa']}, v{params['bbbb']}", offset

def op_06(data: bytes, offset: int = 0):
    params, offset = parser['32x'](data, offset)
    return f"move-wide/16 v{params['aaaa']}, v{params['bbbb']}", offset

def op_07(data: bytes, offset: int = 0):
    params, offset = parser['12x'](data, offset)
    return f"move-object v{params['a']}, v{params['b']}", offset

def op_08(data: bytes, offset: int = 0):
    params, offset = parser['22x'](data, offset)
    return f"move-object/from16 v{params['aa']}, v{params['bbbb']}", offset

def op_09(data: bytes, offset: int = 0):
    params, offset = parser['32x'](data, offset)
    return f"move-object/16 v{params['aaaa']}, v{params['bbbb']}", offset

def op_0a(data: bytes, offset: int = 0):
    params, offset = parser['11x'](data, offset)
    return f"move-result v{params['aa']}", offset

def op_0b(data: bytes, offset: int = 0):
    params, offset = parser['11x'](data, offset)
    return f"move-result-wide v{params['aa']}", offset

def op_0c(data: bytes, offset: int = 0):
    params, offset = parser['11x'](data, offset)
    return f"move-result-object v{params['aa']}", offset

def op_0d(data: bytes, offset: int = 0):
    params, offset = parser['11x'](data, offset)
    return f"move-exception v{params['aa']}", offset

def op_0e(data: bytes, offset: int = 0):
    params, offset = parser['10x'](data, offset)
    return f"return-void", offset

def op_0f(data: bytes, offset: int = 0):
    params, offset = parser['11x'](data, offset)
    return f"return v{params['aa']}", offset

def op_10(data: bytes, offset: int = 0):
    params, offset = parser['11x'](data, offset)
    return f"return-wide v{params['aa']}", offset

def op_11(data: bytes, offset: int = 0):
    params, offset = parser['11x'](data, offset)
    return f"return-object v{params['aa']}", offset

def op_12(data: bytes, offset: int = 0):
    params, offset = parser['11n'](data, offset)
    return f"const/4 v{params['a']}, #+{params['b']}", offset

def op_13(data: bytes, offset: int = 0):
    params, offset = parser['21s'](data, offset)
    return f"const/16 v{params['aa']}, #+{params['bbbb']}", offset

def op_14(data: bytes, offset: int = 0):
    params, offset = parser['31i'](data, offset)
    return f"const/16 v{params['aa']}, #+{params['bbbb']:04x}", offset

def op_15(data: bytes, offset: int = 0):
    params, offset = parser['21h'](data, offset)
    return f"const/high16 v{params['aa']}, #+{params['bbbb']:04x}0000", offset

def op_16(data: bytes, offset: int = 0):
    params, offset = parser['21s'](data, offset)
    return f"const-wide/16 v{params['aa']}, #+{params['bbbb']:04x}", offset

def op_17(data: bytes, offset: int = 0):
    params, offset = parser['31i'](data, offset)
    return f"const-wide/32 v{params['aa']}, #+{params['bbbbhi']:04x}{params['bbbblo']:04x}", offset

def op_18(data: bytes, offset: int = 0):
    params, offset = parser['51l'](data, offset)
    return f"const-wide v{params['aa']}, #+{params['bbbb4']:04x}{params['bbbb3']:04x}{params['bbbb2']:04x}{params['bbbb1']:04x}", offset

def op_19(data: bytes, offset: int = 0):
    params, offset = parser['21h'](data, offset)
    return f"const-wide/high16 v{params['aa']}, #+{params['bbbb']:04x}000000000000", offset

def op_1a(data: bytes, offset: int = 0):
    params, offset = parser['21c'](data, offset)
    return f"const-string v{params['aa']}, string@{params['bbbb']:04x}", offset

def op_1b(data: bytes, offset: int = 0):
    params, offset = parser['31c'](data, offset)
    return f"const-string/jumbo v{params['aa']}, string@{params['bbbbhi']:04x}{params['bbbblo']:04x}", offset

def op_1c(data: bytes, offset: int = 0):
    params, offset = parser['21c'](data, offset)
    return f"const-class v{params['aa']}, type@{params['bbbb']:04x}", offset

def op_1d(data: bytes, offset: int = 0):
    params, offset = parser['11x'](data, offset)
    return f"monitor-enter v{params['aa']}", offset

def op_1e(data: bytes, offset: int = 0):
    params, offset = parser['11x'](data, offset)
    return f"monitor-exit v{params['aa']}", offset

def op_1f(data: bytes, offset: int = 0):
    params, offset = parser['21c'](data, offset)
    return f"check-cast v{params['aa']}, type@{params['bbbb']:04x}", offset

def op_20(data: bytes, offset: int = 0):
    params, offset = parser['22c'](data, offset)
    return f"instance-of v{params['a']}, v{params['b']} type@{params['cccc']:04x}", offset

def op_21(data: bytes, offset: int = 0):
    params, offset = parser['12x'](data, offset)
    return f"array-length v{params['a']}, v{params['b']}", offset

def op_22(data: bytes, offset: int = 0):
    params, offset = parser['21c'](data, offset)
    return f"new-instance v{params['aa']}, type@{params['bbbb']:04x}", offset

def op_23(data: bytes, offset: int = 0):
    params, offset = parser['22c'](data, offset)
    return f"new-array v{params['a']}, v{params['b']} type@{params['cccc']:04x}", offset

def op_24(data: bytes, offset: int = 0):
    params, offset = parser['35c'](data, offset)
    return f"filled-new-array v{params['c']}, v{params['d']}, v{params['e']}, v{params['f']}, v{params['g']}, type@{params['bbbb']:04x}", offset

# op_25

# op_26

def op_27(data: bytes, offset: int = 0):
    params, offset = parser['11x'](data, offset)
    return f"throw v{params['aa']}", offset

def op_28(data: bytes, offset: int = 0):
    params, offset = parser['10t'](data, offset)
    return f"goto +{params['aa']}", offset

# 29
def op_29(data: bytes, offset: int = 0):
    params, offset = parser['20t'](data, offset)
    return f"goto/16 +{params['aaaa']}", offset

# 2a
def op_2a(data: bytes, offset: int = 0):
    params, offset = parser['30t'](data, offset)
    return f"goto/32 +{params['aaaahi']}{params['aaaalo']}", offset

# 2b
def op_2b(data: bytes, offset: int = 0):
    params, offset = parser['31t'](data, offset)
    return f"packed-switch v{params['aa']}, +{params['bbbbhi']}{params['bbbblo']}", offset

# 2c
def op_2c(data: bytes, offset: int = 0):
    params, offset = parser['31t'](data, offset)
    return f"sparse-switch v{params['aa']}, +{params['bbbbhi']}{params['bbbblo']}", offset

###############################################################################
###############################################################################
###############################################################################



def op_2d(data: bytes, offset: int = 0):
    params, offset = parser['23x'](data, offset)
    return f"cmpl-float v{params['aa']}, v{params['bb']}, v{params['cc']}", offset

def op_2e(data: bytes, offset: int = 0):
    params, offset = parser['23x'](data, offset)
    return f"cmpg-float v{params['aa']}, v{params['bb']}, v{params['cc']}", offset

def op_2f(data: bytes, offset: int = 0):
    params, offset = parser['23x'](data, offset)
    return f"cmpl-double v{params['aa']}, v{params['bb']}, v{params['cc']}", offset

def op_30(data: bytes, offset: int = 0):
    params, offset = parser['23x'](data, offset)
    return f"cmpg-double v{params['aa']}, v{params['bb']}, v{params['cc']}", offset

def op_31(data: bytes, offset: int = 0):
    params, offset = parser['23x'](data, offset)
    return f"cmp-long v{params['aa']}, v{params['bb']}, v{params['cc']}", offset

###############################################################################
###############################################################################
###############################################################################

def op_32(data: bytes, offset: int = 0):
    params, offset = parser['22t'](data, offset)
    return f"if-eq v{params['a']}, v{params['b']}, +{params['cccc']:04x}", offset

def op_33(data: bytes, offset: int = 0):
    params, offset = parser['22t'](data, offset)
    return f"if-ne v{params['a']}, v{params['b']}, +{params['cccc']:04x}", offset

def op_34(data: bytes, offset: int = 0):
    params, offset = parser['22t'](data, offset)
    return f"if-lt v{params['a']}, v{params['b']}, +{params['cccc']:04x}", offset

def op_35(data: bytes, offset: int = 0):
    params, offset = parser['22t'](data, offset)
    return f"if-ge v{params['a']}, v{params['b']}, +{params['cccc']:04x}", offset

def op_36(data: bytes, offset: int = 0):
    params, offset = parser['22t'](data, offset)
    return f"if-gt v{params['a']}, v{params['b']}, +{params['cccc']:04x}", offset

def op_37(data: bytes, offset: int = 0):
    params, offset = parser['22t'](data, offset)
    return f"if-le v{params['a']}, v{params['b']}, +{params['cccc']:04x}", offset

###############################################################################
###############################################################################
###############################################################################

def op_38(data: bytes, offset: int = 0):
    params, offset = parser['21t'](data, offset)
    return f"if-eqz v{params['aa']}, +{params['bbbb']}", offset

def op_39(data: bytes, offset: int = 0):
    params, offset = parser['21t'](data, offset)
    return f"if-nez v{params['aa']}, +{params['bbbb']}", offset

def op_3a(data: bytes, offset: int = 0):
    params, offset = parser['21t'](data, offset)
    return f"if-ltz v{params['aa']}, +{params['bbbb']}", offset

def op_3b(data: bytes, offset: int = 0):
    params, offset = parser['21t'](data, offset)
    return f"if-gez v{params['aa']}, +{params['bbbb']}", offset

def op_3c(data: bytes, offset: int = 0):
    params, offset = parser['21t'](data, offset)
    return f"if-gtz v{params['aa']}, +{params['bbbb']}", offset

def op_3d(data: bytes, offset: int = 0):
    params, offset = parser['21t'](data, offset)
    return f"if-lez v{params['aa']}, +{params['bbbb']}", offset

###############################################################################
###############################################################################
###############################################################################

# 3e - 43 - unused

###############################################################################
###############################################################################
###############################################################################

def op_44(data: bytes, offset: int = 0):
    params, offset = parser['23x'](data, offset)
    return f"aget v{params['aa']}, v{params['bb']}, v{params['cc']}", offset

def op_45(data: bytes, offset: int = 0):
    params, offset = parser['23x'](data, offset)
    return f"aget-wide v{params['aa']}, v{params['bb']}, v{params['cc']}", offset

def op_46(data: bytes, offset: int = 0):
    params, offset = parser['23x'](data, offset)
    return f"aget-object v{params['aa']}, v{params['bb']}, v{params['cc']}", offset

def op_47(data: bytes, offset: int = 0):
    params, offset = parser['23x'](data, offset)
    return f"aget-boolean v{params['aa']}, v{params['bb']}, v{params['cc']}", offset

def op_48(data: bytes, offset: int = 0):
    params, offset = parser['23x'](data, offset)
    return f"aget-byte v{params['aa']}, v{params['bb']}, v{params['cc']}", offset

def op_49(data: bytes, offset: int = 0):
    params, offset = parser['23x'](data, offset)
    return f"aget-char v{params['aa']}, v{params['bb']}, v{params['cc']}", offset

def op_4a(data: bytes, offset: int = 0):
    params, offset = parser['23x'](data, offset)
    return f"aget-short v{params['aa']}, v{params['bb']}, v{params['cc']}", offset

def op_4b(data: bytes, offset: int = 0):
    params, offset = parser['23x'](data, offset)
    return f"aput v{params['aa']}, v{params['bb']}, v{params['cc']}", offset

def op_4c(data: bytes, offset: int = 0):
    params, offset = parser['23x'](data, offset)
    return f"aput-wide v{params['aa']}, v{params['bb']}, v{params['cc']}", offset

def op_4d(data: bytes, offset: int = 0):
    params, offset = parser['23x'](data, offset)
    return f"aput-object v{params['aa']}, v{params['bb']}, v{params['cc']}", offset

def op_4e(data: bytes, offset: int = 0):
    params, offset = parser['23x'](data, offset)
    return f"aput-boolean v{params['aa']}, v{params['bb']}, v{params['cc']}", offset

def op_4f(data: bytes, offset: int = 0):
    params, offset = parser['23x'](data, offset)
    return f"aput-byte v{params['aa']}, v{params['bb']}, v{params['cc']}", offset

def op_50(data: bytes, offset: int = 0):
    params, offset = parser['23x'](data, offset)
    return f"aput-char v{params['aa']}, v{params['bb']}, v{params['cc']}", offset

def op_51(data: bytes, offset: int = 0):
    params, offset = parser['23x'](data, offset)
    return f"aput-short v{params['aa']}, v{params['bb']}, v{params['cc']}", offset

###############################################################################
###############################################################################
###############################################################################

def op_52(data: bytes, offset: int = 0):
    params, offset = parser['22c'](data, offset)
    return f"iget v{params['a']}, v{params['b']}, field@{params['cccc']:04x}", offset

def op_53(data: bytes, offset: int = 0):
    params, offset = parser['22c'](data, offset)
    return f"iget-wide v{params['a']}, v{params['b']}, field@{params['cccc']:04x}", offset

def op_54(data: bytes, offset: int = 0):
    params, offset = parser['22c'](data, offset)
    return f"iget-object v{params['a']}, v{params['b']}, field@{params['cccc']:04x}", offset

def op_55(data: bytes, offset: int = 0):
    params, offset = parser['22c'](data, offset)
    return f"iget-boolean v{params['a']}, v{params['b']}, field@{params['cccc']:04x}", offset

def op_56(data: bytes, offset: int = 0):
    params, offset = parser['22c'](data, offset)
    return f"iget-byte v{params['a']}, v{params['b']}, field@{params['cccc']:04x}", offset

def op_57(data: bytes, offset: int = 0):
    params, offset = parser['22c'](data, offset)
    return f"iget-char v{params['a']}, v{params['b']}, field@{params['cccc']:04x}", offset

def op_58(data: bytes, offset: int = 0):
    params, offset = parser['22c'](data, offset)
    return f"iget-short v{params['a']}, v{params['b']}, field@{params['cccc']:04x}", offset

def op_59(data: bytes, offset: int = 0):
    params, offset = parser['22c'](data, offset)
    return f"iput v{params['a']}, v{params['b']}, field@{params['cccc']:04x}", offset

def op_5a(data: bytes, offset: int = 0):
    params, offset = parser['22c'](data, offset)
    return f"iput-wide v{params['a']}, v{params['b']}, field@{params['cccc']:04x}", offset

def op_5b(data: bytes, offset: int = 0):
    params, offset = parser['22c'](data, offset)
    return f"iput-object v{params['a']}, v{params['b']}, field@{params['cccc']:04x}", offset

def op_5c(data: bytes, offset: int = 0):
    params, offset = parser['22c'](data, offset)
    return f"iput-boolean v{params['a']}, v{params['b']}, field@{params['cccc']:04x}", offset

def op_5d(data: bytes, offset: int = 0):
    params, offset = parser['22c'](data, offset)
    return f"iput-byte v{params['a']}, v{params['b']}, field@{params['cccc']:04x}", offset

def op_5e(data: bytes, offset: int = 0):
    params, offset = parser['22c'](data, offset)
    return f"iput-char v{params['a']}, v{params['b']}, field@{params['cccc']:04x}", offset

def op_5f(data: bytes, offset: int = 0):
    params, offset = parser['22c'](data, offset)
    return f"iput-short v{params['a']}, v{params['b']}, field@{params['cccc']:04x}", offset

###############################################################################
###############################################################################
###############################################################################

def op_60(data: bytes, offset: int = 0):
    params, offset = parser['21c'](data, offset)
    return f"sget v{params['aa']}, field@{params['bbbb']:04x}", offset

def op_61(data: bytes, offset: int = 0):
    params, offset = parser['21c'](data, offset)
    return f"sget-wide v{params['aa']}, field@{params['bbbb']:04x}", offset

def op_62(data: bytes, offset: int = 0):
    params, offset = parser['21c'](data, offset)
    return f"sget-object v{params['aa']}, field@{params['bbbb']:04x}", offset

def op_63(data: bytes, offset: int = 0):
    params, offset = parser['21c'](data, offset)
    return f"sget-boolean v{params['aa']}, field@{params['bbbb']:04x}", offset

def op_64(data: bytes, offset: int = 0):
    params, offset = parser['21c'](data, offset)
    return f"sget-byte v{params['aa']}, field@{params['bbbb']:04x}", offset

def op_65(data: bytes, offset: int = 0):
    params, offset = parser['21c'](data, offset)
    return f"sget-char v{params['aa']}, field@{params['bbbb']:04x}", offset

def op_66(data: bytes, offset: int = 0):
    params, offset = parser['21c'](data, offset)
    return f"sget-short v{params['aa']}, field@{params['bbbb']:04x}", offset

def op_67(data: bytes, offset: int = 0):
    params, offset = parser['21c'](data, offset)
    return f"sput v{params['aa']}, field@{params['bbbb']:04x}", offset

def op_68(data: bytes, offset: int = 0):
    params, offset = parser['21c'](data, offset)
    return f"sput-wide v{params['aa']}, field@{params['bbbb']:04x}", offset

def op_69(data: bytes, offset: int = 0):
    params, offset = parser['21c'](data, offset)
    return f"sput-object v{params['aa']}, field@{params['bbbb']:04x}", offset

def op_6a(data: bytes, offset: int = 0):
    params, offset = parser['21c'](data, offset)
    return f"sput-boolean v{params['aa']}, field@{params['bbbb']:04x}", offset

def op_6b(data: bytes, offset: int = 0):
    params, offset = parser['21c'](data, offset)
    return f"sput-byte v{params['aa']}, field@{params['bbbb']:04x}", offset

def op_6c(data: bytes, offset: int = 0):
    params, offset = parser['21c'](data, offset)
    return f"sput-char v{params['aa']}, field@{params['bbbb']:04x}", offset

def op_6d(data: bytes, offset: int = 0):
    params, offset = parser['21c'](data, offset)
    return f"sput-short v{params['aa']}, field@{params['bbbb']:04x}", offset

###############################################################################
###############################################################################
###############################################################################

def op_6e(data: bytes, offset: int = 0):
    params, offset = parser['35c'](data, offset)
    return f"invoke-virtual v{params['c']}, v{params['d']}, v{params['e']}, v{params['f']}, v{params['g']}, meth@{params['bbbb']:04x}", offset

def op_6f(data: bytes, offset: int = 0):
    params, offset = parser['35c'](data, offset)
    return f"invoke-super v{params['c']}, v{params['d']}, v{params['e']}, v{params['f']}, v{params['g']}, meth@{params['bbbb']:04x}", offset

def op_70(data: bytes, offset: int = 0):
    params, offset = parser['35c'](data, offset)
    return f"invoke-direct v{params['c']}, v{params['d']}, v{params['e']}, v{params['f']}, v{params['g']}, meth@{params['bbbb']:04x}", offset

def op_71(data: bytes, offset: int = 0):
    params, offset = parser['35c'](data, offset)
    return f"invoke-static v{params['c']}, v{params['d']}, v{params['e']}, v{params['f']}, v{params['g']}, meth@{params['bbbb']:04x}", offset

def op_72(data: bytes, offset: int = 0):
    params, offset = parser['35c'](data, offset)
    return f"invoke-interface v{params['c']}, v{params['d']}, v{params['e']}, v{params['f']}, v{params['g']}, meth@{params['bbbb']:04x}", offset

###############################################################################
###############################################################################
###############################################################################

# 73 - unused

###############################################################################
###############################################################################
###############################################################################

#def op_74(data: bytes, offset: int = 0):
#    params, _ = parser['3rc'](data)
#    return f"invoke-virtual/range v{params['c']}, v{params['d']}, v{params['e']}, v{params['f']}, v{params['g']}, meth@{params['bbbb']:04x}"

# 75

# 76

# 77

# 78

###############################################################################
###############################################################################
###############################################################################

# 79-7a - unused

###############################################################################
###############################################################################
###############################################################################

def op_7b_8f(data: bytes, offset: int = 0):
    params, offset = parser['12x'](data, offset)
    ins = [
        'neg-int', 'not-int', 'neg-long', 'not-long',
        'neg-float', 'neg-double', 'int-to-long', 'int-to-float',
        'int-to-double', 'long-to-int', 'long-to-float', 
        'long-to-double', 'float-to-int', 'float-to-long',
        'float-to-double', 'double-to-int', 'double-to-long',
        'double-to-float', 'int-to-byte', 'int-to-char',
        'int-to-short',
    ]
    return f"{ins[params['op']-0x7b]} v{params['a']}, v{params['b']}", offset


def op_90_af(data: bytes, offset: int = 0):
    params, offset = parser['23x'](data, offset)
    ins = [
        'add-int', 'sub-int', 'mul-int', 'div-int',
        'rem-int', 'and-int', 'or-int', 'xor-int',
        'shl-int', 'shr-int', 'ushr-int', 'add-long',
        'sub-long', 'mul-long', 'div-long', 'rem-long',
        'and-long', 'or-long', 'xor-long', 'shl-long',
        'shr-long', 'ushr-long', 'add-float', 'sub-float',
        'mul-float', 'div-float', 'rem-float', 'add-double',
        'sub-double', 'mul-double', 'div-double', 'rme-double',
    ]
    return f"{ins[params['op']-0x90]} v{params['aa']}, v{params['bb']}, v{params['cc']}", offset


def op_b0_cf(data: bytes, offset: int = 0):
    params, offset = parser['12x'](data, offset)
    ins = [
        'add-int/2addr', 'sub-int/2addr', 'mul-int/2addr',
        'div-int/2addr', 'rem-int/2addr', 'and-int/2addr',
        'or-int/2addr', 'xor-int/2addr', 'shl-int/2addr',
        'shr-int/2addr', 'ushr-int/2addr', 'add-long/2addr',
        'sub-long/2addr', 'mul-long/2addr', 'div-long/2addr',
        'rem-long/2addr', 'and-long/2addr', 'or-long/2addr',
        'xor-long/2addr', 'shl-long/2addr', 'shr-long/2addr',
        'ushr-long/2addr', 'add-float/2addr', 'sub-float/2addr',
        'mul-float/2addr', 'div-float/2addr', 'rem-float/2addr',
        'add-double/2addr', 'sub-double/2addr', 'mul-double/2addr',
        'div-double/2addr', 'rem-double/2addr'
    ]
    return f"{ins[params['op']-0xb0]} v{params['a']}, v{params['b']}", offset

def op_d0_d7(data: bytes, offset: int = 0):
    params, offset = parser['22s'](data, offset)
    ins = [
        'add-int/lit16', 'rsub-int/lit16', 'mul-int/lit16',
        'div-int/lit16', 'rem-int/lit16', 'and-int/lit16',
        'or-int/lit16', 'xor-int/lit16'
    ]
    return f"{ins[params['op']-0xd0]} v{params['a']}, v{params['b']}, #+{params['cccc']:04x}", offset

def op_d8_e2(data: bytes, offset: int = 0):
    params, offset = parser['22b'](data, offset)
    ins = [
        'add-int/lit8', 'rsub-int/lit8', 'mul-int/lit8',
        'div-int/lit8', 'rem-int/lit8', 'and-int/lit8',
        'or-int/lit8', 'xor-int/lit8', 'shl-int/lit8',
        'shr-int/lit8', 'ushr-int/lit8'
    ]
    return f"{ins[params['op']-0xd8]} v{params['aa']}, v{params['bb']}, #+{params['cc']:04x}", offset

# e3-f9 - unused

def op_fa(data: bytes, offset: int = 0):
    params, offset = parser['45cc'](data, offset)
    return f"invoke-polymorphic v{params['c']}, v{params['d']}, v{params['e']}, v{params['f']}, v{params['g']}", offset

# fb

def op_fc(data: bytes, offset: int = 0):
    params, offset = parser['35c'](data, offset)
    return f"invoke-custom v{params['c']}, v{params['d']}, v{params['e']}, v{params['f']}, v{params['g']} call-site@{params['bbbb']}", offset

# fd

def op_fe(data: bytes, offset: int = 0):
    params, offset = parser['21c'](data, offset)
    return f"const-method-handle v{params['aa']}, method_handle@{params['bbbb']}", offset

def op_ff(data: bytes, offset: int = 0):
    params, offset = parser['21c'](data, offset)
    return f"const-method-type v{params['aa']}, proto@{params['bbbb']}", offset

def nop(data: bytes, offset: int = 0):
    raise RuntimeError("Nop Executed")

ops = [
    op_00, op_01, op_02, op_03, op_04, op_05, op_06, op_07,
    op_08, op_09, op_0a, op_0b, op_0c, op_0d, op_0e, op_0f,
    op_10, op_11, op_12, op_13, op_14, op_15, op_16, op_17,
    op_18, op_19, op_1a, op_1b, op_1c, op_1d, op_1e, op_1f,
    op_20, op_21, op_22, op_23, op_24,   nop,   nop, op_27,
    op_28, op_29, op_2a, op_2b, op_2c, op_2d, op_2e, op_2f,
    op_30, op_31, op_32, op_33, op_34, op_35, op_36, op_37,
    op_38, op_39, op_3a, op_3b, op_3c, op_3d,   nop,   nop,
      nop,   nop,   nop,   nop, op_44, op_45, op_46, op_47,
    op_48, op_49, op_4a, op_4b, op_4c, op_4d, op_4e, op_4f,
    op_50, op_51, op_52, op_53, op_54, op_55, op_56, op_57,
    op_58, op_59, op_5a, op_5b, op_5c, op_5d, op_5e, op_5f,
    op_60, op_61, op_62, op_63, op_64, op_65, op_66, op_67,
    op_68, op_69, op_6a, op_6b, op_6c, op_6d, op_6e, op_6f,
       op_70,    op_71,    op_72,      nop,      nop,      nop,      nop,      nop,
         nop,      nop,      nop, op_7b_8f, op_7b_8f, op_7b_8f, op_7b_8f, op_7b_8f,
    op_7b_8f, op_7b_8f, op_7b_8f, op_7b_8f, op_7b_8f, op_7b_8f, op_7b_8f, op_7b_8f,
    op_7b_8f, op_7b_8f, op_7b_8f, op_7b_8f, op_7b_8f, op_7b_8f, op_7b_8f, op_7b_8f,
    op_90_af, op_90_af, op_90_af, op_90_af, op_90_af, op_90_af, op_90_af, op_90_af,
    op_90_af, op_90_af, op_90_af, op_90_af, op_90_af, op_90_af, op_90_af, op_90_af,
    op_90_af, op_90_af, op_90_af, op_90_af, op_90_af, op_90_af, op_90_af, op_90_af,
    op_90_af, op_90_af, op_90_af, op_90_af, op_90_af, op_90_af, op_90_af, op_90_af,
    op_b0_cf, op_b0_cf, op_b0_cf, op_b0_cf, op_b0_cf, op_b0_cf, op_b0_cf, op_b0_cf,
    op_b0_cf, op_b0_cf, op_b0_cf, op_b0_cf, op_b0_cf, op_b0_cf, op_b0_cf, op_b0_cf,
    op_b0_cf, op_b0_cf, op_b0_cf, op_b0_cf, op_b0_cf, op_b0_cf, op_b0_cf, op_b0_cf,
    op_b0_cf, op_b0_cf, op_b0_cf, op_b0_cf, op_b0_cf, op_b0_cf, op_b0_cf, op_b0_cf,
    op_d0_d7, op_d0_d7, op_d0_d7, op_d0_d7, op_d0_d7, op_d0_d7, op_d0_d7, op_d0_d7,
    op_d8_e2, op_d8_e2, op_d8_e2, op_d8_e2, op_d8_e2, op_d8_e2, op_d8_e2, op_d8_e2,
    op_d8_e2, op_d8_e2, op_d8_e2,      nop,      nop,      nop,      nop,      nop,
      nop,   nop,   nop,   nop,   nop,   nop,   nop,   nop,
      nop,   nop,   nop,   nop,   nop,   nop,   nop,   nop,
      nop,   nop, op_fa,   nop, op_fc,   nop, op_fe, op_ff,
]



bytecodes = [
    32, 128, 222, 30, 56, 0, 18, 0,7, 128, 31, 0, 222, 30, 82, 1,126, 54, 21, 2, 0, 128, 181, 33,56, 1, 8, 0, 82, 8, 126, 54,177,40,89,8,126,54,40,6,34,0,222,30,112,48,2,200,112,8,84,8,127,54,113,0,183,140,0,0,12,1,82,2,126,54,18,35,18,20,56,2,23,0,50,66,17,0,51,50,7,0,113,16,62,117,8,0,41,0,120,0,34,8,28,19,26,0,135,132,112,32,221,110,8,0,39,8,113,16,62,117,8,0,40,61,113,16,62,117,8,0,84,120,129,54,114,16,81,116,8,0,12,8,31,8,216,30,110,16,223,199,8,0,12,8,34,2,101,15,112,16,130,89,2,0,26,5,196,164,113,32,180,89,82,0,7,37,31,5,37,16,98,6,189,29,110,16,239,91,6,0,12,6,113,32,89,94,101,0,98,5,171,30,110,16,104,94,5,0,12,5,110,32,146,89,82,0,34,5,162,15,112,48,255,90,37,8,89,4,126,54,110,32,3,91,5,0,12,8,51,24,3,0,40,46,31,8,150,15,110,16,193,90,8,0,12,8,28,2,207,19,113,16,105,146,2,0,12,2,28,4,207,19,98,5,70,40,28,6,220,30,113,16,128,146,6,0,12,6,110,32,201,150,101,0,12,5,113,32,129,146,84,0,12,4,40,2,18,4,34,5,209,17,112,48,198,104,37,4,89,3,126,54,110,48,124,79,88,0,12,8,51,24,3,0,17,1,56,8,10,0,31,8,207,19,18,0,114,32,95,114,8,0,12,8,17,8,34,8,45,19,26,0,121,182,112,32,67,111,8,0,39,8,
]

offset = 0
prev_offset = -1
ins_idx = 0
while offset < len(bytecodes) and offset != prev_offset:
    prev_offset = offset
    ins, offset = ops[bytecodes[offset]](bytecodes, offset)
    ins_bytecode = bytes(bytecodes[prev_offset:offset]).hex()
    ins_bytecode_idx = f'{int(prev_offset/2):04x}'
    print(f'{ins_idx}: {ins_bytecode_idx}: {ins} [bytecode: {ins_bytecode}]')
    ins_idx += 1
    #breakpoint()


'''
bytecode = [
32, 128, 222, 30, 56, 0, 18, 0,7, 128, 31, 0, 222, 30, 82, 1,126, 54, 21, 2, 0, 128, 181, 33,56, 1, 8, 0, 82, 8, 126, 54,177,40,89,8,126,54,40,6,34,0,222,30,112,48,2,200,112,8,84,8,127,54,113,0,183,140,0,0,12,1,82,2,126,54,18,35,18,20,56,2,23,0,50,66,17,0,51,50,7,0,113,16,62,117,8,0,41,0,120,0,34,8,28,19,26,0,135,132,112,32,221,110,8,0,39,8,113,16,62,117,8,0,40,61,113,16,62,117,8,0,84,120,129,54,114,16,81,116,8,0,12,8,31,8,216,30,110,16,223,199,8,0,12,8,34,2,101,15,112,16,130,89,2,0,26,5,196,164,113,32,180,89,82,0,7,37,31,5,37,16,98,6,189,29,110,16,239,91,6,0,12,6,113,32,89,94,101,0,98,5,171,30,110,16,104,94,5,0,12,5,110,32,146,89,82,0,34,5,162,15,112,48,255,90,37,8,89,4,126,54,110,32,3,91,5,0,12,8,51,24,3,0,40,46,31,8,150,15,110,16,193,90,8,0,12,8,28,2,207,19,113,16,105,146,2,0,12,2,28,4,207,19,98,5,70,40,28,6,220,30,113,16,128,146,6,0,12,6,110,32,201,150,101,0,12,5,113,32,129,146,84,0,12,4,40,2,18,4,34,5,209,17,112,48,198,104,37,4,89,3,126,54,110,48,124,79,88,0,12,8,51,24,3,0,17,1,56,8,10,0,31,8,207,19,18,0,114,32,95,114,8,0,12,8,17,8,34,8,45,19,26,0,121,182,112,32,67,111,8,0,39,8,
]

index is 16bit words

2080de1e
38001200
0780
1f00de1e
52017e36
15020080
b521
38010800
52087e36
b128
59087e36
2806
2200de1e
703002c87008
54087f36
7100b78c0000
0c01
52027e36
1223
1214
38021700
32421100
33320700
71103e750800
29007800
22081c13
1a008784
7020dd6e0800
2708
71103e750800
283d
71103e750800
54788136
721051740800
0c08
1f08d81e
6e10dfc70800
0c08
2202650f
701082590200
1a05c4a4
7120b4595200
0725
1f052510
6206bd1d
6e10ef5b0600
0c06
7120595e6500
6205ab1e
6e10685e0500
0c05
6e2092595200
2205a20f
7030ff5a2508
59047e36
6e20035b0500
0c08
33180300
282e
1f08960f
6e10c15a0800
0c08
1c02cf13
711069920200
0c02
1c04cf13
62054628
1c06dc1e
711080920600
0c06
6e20c9966500
0c05
712081925400
0c04
2802
1204
2205d111
7030c6682504
59037e36
6e307c4f5800
0c08
33180300
1101
38080a00
1f08cf13
1200
72205f720800
0c08
1108
22082d13
1a0079b6
7020436f0800
2708
'''

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