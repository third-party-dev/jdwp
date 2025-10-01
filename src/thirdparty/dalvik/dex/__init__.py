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

def op_25(data: bytes, offset: int = 0):
    params, offset = parser['3rc'](data, offset)
    return f"filled-new-array/range v{params['cccc']:04x} - v{(params['cccc']+params['aa']-1):04x} type@{params['bbbb']:04x}", offset

def op_26(data: bytes, offset: int = 0):
    params, offset = parser['31t'](data, offset)
    return f"fill-array-data v{params['aa']}, +{params['bbbbhi']}{params['bbbblo']}", offset

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

def op_2d_31(data: bytes, offset: int = 0):
    params, offset = parser['23x'](data, offset)
    ins = [
        'cmpl-float', 'cmpg-float', 'cmpl-double',
        'cmpg-double', 'cmp-long',
    ]
    return f"{ins[params['op']-0x2d]} v{params['aa']}, v{params['bb']}, v{params['cc']}", offset

###############################################################################
###############################################################################
###############################################################################

def op_32_37(data: bytes, offset: int = 0):
    params, offset = parser['22t'](data, offset)
    ins = [
        'if-eq', 'if-ne', 'if-lt', 'if-ge', 'if-gt', 'if-le'
    ]
    return f"{ins[params['op']-0x32]} v{params['a']}, v{params['b']}, +{params['cccc']:04x}", offset

###############################################################################
###############################################################################
###############################################################################

def op_38_3d(data: bytes, offset: int = 0):
    params, offset = parser['21t'](data, offset)
    ins = [
        'if-eqz', 'if-nez', 'if-ltz', 'if-gez', 'if-gtz', 'if-lez'
    ]
    return f"{ins[params['op']-0x38]} v{params['aa']}, +{params['bbbb']}", offset

###############################################################################
###############################################################################
###############################################################################

# 3e - 43 - unused

###############################################################################
###############################################################################
###############################################################################

def op_44_51(data: bytes, offset: int = 0):
    params, offset = parser['23x'](data, offset)
    ins = [
        'aget', 'aget-wide', 'aget-object', 'aget-boolean', 'aget-byte', 
        'aget-char', 'aget-short', 'aput', 'aput-wide', 'aput-object',
        'aput-boolean', 'aput-byte', 'aput-char', 'aput-short',
    ]
    return f"{ins[params['op']-0x44]} v{params['aa']}, v{params['bb']}, v{params['cc']}", offset

###############################################################################
###############################################################################
###############################################################################

def op_52_5f(data: bytes, offset: int = 0):
    params, offset = parser['22c'](data, offset)
    ins = [
        'iget', 'iget-wide', 'iget-object', 'iget-boolean', 'iget-byte',
        'iget-char', 'iget-short', 'iput', 'iput-wide', 'iput-object',
        'iput-boolean', 'iput-byte', 'iput-char', 'iput-short',
    ]
    return f"{ins[params['op']-0x52]} v{params['a']}, v{params['b']}, field@{params['cccc']:04x}", offset

###############################################################################
###############################################################################
###############################################################################

def op_60_6d(data: bytes, offset: int = 0):
    params, offset = parser['21c'](data, offset)
    ins = [
        'sget', 'sget-wide', 'sget-object', 'sget-byte', 'sget-char',
        'sget-short', 'sput', 'sput-wide', 'sput-object', 'sput-boolean',
        'sput-byte', 'sput-char', 'sput-short',
    ]
    return f"{ins[params['op']-0x60]} v{params['aa']}, field@{params['bbbb']:04x}", offset

###############################################################################
###############################################################################
###############################################################################

def op_6e_72(data: bytes, offset: int = 0):
    params, offset = parser['35c'](data, offset)
    ins = [
        'invoke-virtual', 'invoke-super', 'invoke-direct',
        'invoke-static', 'invoke-interface'
    ]
    return f"{ins[params['op']-0x6e]} v{params['c']}, v{params['d']}, v{params['e']}, v{params['f']}, v{params['g']}, meth@{params['bbbb']:04x}", offset

###############################################################################
###############################################################################
###############################################################################

# 73 - unused

###############################################################################
###############################################################################
###############################################################################

def op_74_78(data: bytes, offset: int = 0):
    params, offset = parser['3rc'](data, offset)
    ins = [
        'invoke-virtual/range', 'invoke-super/range', 'invoke-direct/range',
        'invoke-static/range', 'invoke-interface/range',
    ]
    return f"{ins[params['op']-0x74]} v{params['cccc']:04x} - v{(params['cccc']+params['aa']-1):04x} meth@{params['bbbb']:04x}", offset



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

def op_fb(data: bytes, offset: int = 0):
    params, offset = parser['4rcc'](data, offset)
    return f"invoke-polymorphic/range v{params['cccc']:04x} - v{(params['cccc']+params['aa']-1):04x} meth@{params['bbbb']:04x}, proto@{params['hhhh']:04x}", offset

def op_fc(data: bytes, offset: int = 0):
    params, offset = parser['35c'](data, offset)
    return f"invoke-custom v{params['c']}, v{params['d']}, v{params['e']}, v{params['f']}, v{params['g']} call-site@{params['bbbb']}", offset

def op_fd(data: bytes, offset: int = 0):
    params, offset = parser['3rc'](data, offset)
    return f"invoke-custom/range v{params['cccc']:04x} - v{(params['cccc']+params['aa']-1):04x} call_site@{params['bbbb']:04x}", offset

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
    op_20, op_21, op_22, op_23, op_24, op_25, op_26, op_27,

       op_28,    op_29,    op_2a,    op_2b,    op_2c, op_2d_31, op_2d_31, op_2d_31,
    op_2d_31, op_2d_31, op_32_37, op_32_37, op_32_37, op_32_37, op_32_37, op_32_37,
    op_38_3d, op_38_3d, op_38_3d, op_38_3d, op_38_3d, op_38_3d,      nop,      nop,
         nop,      nop,      nop,      nop, op_44_51, op_44_51, op_44_51, op_44_51,
    op_44_51, op_44_51, op_44_51, op_44_51, op_44_51, op_44_51, op_44_51, op_44_51,
    op_44_51, op_44_51, op_52_5f, op_52_5f, op_52_5f, op_52_5f, op_52_5f, op_52_5f,
    op_52_5f, op_52_5f, op_52_5f, op_52_5f, op_52_5f, op_52_5f, op_52_5f, op_52_5f,
    op_60_6d, op_60_6d, op_60_6d, op_60_6d, op_60_6d, op_60_6d, op_60_6d, op_60_6d,
    op_60_6d, op_60_6d, op_60_6d, op_60_6d, op_60_6d, op_60_6d, op_6e_72, op_6e_72,
    op_6e_72, op_6e_72, op_6e_72,      nop, op_74_78, op_74_78, op_74_78, op_74_78,
    op_74_78,      nop,      nop, op_7b_8f, op_7b_8f, op_7b_8f, op_7b_8f, op_7b_8f,
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
         nop,      nop,      nop,      nop,      nop,      nop,      nop,      nop,
         nop,      nop,      nop,      nop,      nop,      nop,      nop,      nop,
         nop,      nop,    op_fa,    op_fb,    op_fc,    op_fd,    op_fe,    op_ff,
]

def disassemble(data: bytes, offset: int=0):
    return ops[data[offset]](data, offset)

