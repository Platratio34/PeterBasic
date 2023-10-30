from convert import toHex

# All instructions are split into 4 4bit sections: code, operand 1, operand 2, and operand 3
# If there are only 2 operands specified, the second is an 8 bit value
# x indicates un-used operand

NO_OP =     0x0 # NO_OP x x x
""" No operation. NO_OP x x x """
LOAD_MEM =  0x1 # LOAD_MEM destReg memAdr
""" Load memory to register. LOAD_MEM destReg memAdr """
LOAD =      0x2 # LOAD destReg value
""" Load value to register. LOAD destReg value """
STORE =     0x3 # STORE srcReg memAdr
""" Store register to memory. STORE srcReg memAdr """
MOVE =      0x4 # MOVE spec srcReg destReg
""" Move value between registers. MOVE spec srcReg destReg """
ADD_S =     0x5 # ADD_S destReg reg1 reg2
""" Add 2 registers into destination register. ADD_S destReg reg1 reg2 """
ADD_F =     0x6 # ADD_F destReg reg1 reg2
""" UNIMPLEMENTED. ADD_F destReg reg1 reg2 """
OR =        0x7 # OR destReg reg1 reg2
""" Binary or 2 registers into destination register. OR destReg reg1 reg2 """
AND =       0x8 # AND destReg reg1 reg2
""" Binary and 2 registers into destination register. AND destReg reg1 reg2 """
XOR =       0x9 # XOR destReg reg1 reg2
""" Binary xor 2 registers into destination register. XOR destReg reg1 reg2 """
ROTATE =    0xA # ROTATE reg x places
""" Rotate the value in register by given amount. ROTATE reg x places """
JUMP =      0xB # JUMP reg instruction
""" Jump to instruction if register is equal to r0. JUMP reg instruction """
HALT =      0xC # HALT x x x
""" Stop execution. HALT x x x """
STORE_P =   0xD # STORE_P srcReg perAdr
""" Store register to peripheral address. STORE_P srcReg perAdr """
LOAD_P =    0xE # LOAD_P destReg PerAdr
""" Load register from peripheral address. LOAD_P destReg PerAdr """
JUMP_L =    0xF # JUMP_L reg instruction
""" Jump to instruction if register is less than r0. JUMP_L reg instruction """

def toName(instr: int|bytes):
    """ Turn an instruction op-code into ASM name"""
    if isinstance(instr, bytes):
        instr = int.from_bytes(instr, 'big')
    if instr == NO_OP:
        return 'NO_OP'
    elif instr == LOAD_MEM:
        return 'LOAD_MEM'
    elif instr == LOAD:
        return 'LOAD'
    elif instr == STORE:
        return 'STORE'
    elif instr == MOVE:
        return 'MOVE'
    elif instr == ADD_S:
        return 'ADD_S'
    elif instr == ADD_F:
        return 'ADD_F'
    elif instr == OR:
        return 'OR'
    elif instr == AND:
        return 'AND'
    elif instr == XOR:
        return 'XOR'
    elif instr == ROTATE:
        return 'ROTATE'
    elif instr == JUMP:
        return 'JUMP'
    elif instr == HALT:
        return 'HALT'
    elif instr == STORE_P:
        return 'STORE_P'
    elif instr == LOAD_P:
        return 'LOAD_P'
    elif instr == JUMP_L:
        return 'JUMP_L'
    else:
        return 'UNKNOWN'

def strInstr(instr: int|tuple[bytes, bytes]):
    """ Turn an machine code instruction to ASM-Like string"""
    if isinstance(instr, tuple):
        bh, bl = instr
        instr = int.from_bytes(bh, "big") * 0x100
        instr += int.from_bytes(bl, "big")
    op = (instr & 0xf000) >> 12
    reg = (instr & 0x0f00) >> 8
    opr = (instr & 0x00ff)
    opr1 = (instr & 0x00f0) >> 4
    opr2 = (instr & 0x000f)
    if op == NO_OP:
        return 'NO_OP'
    if op == LOAD_MEM:
        return f'LOAD_MEM m{toHex(opr,2)} --> r{toHex(reg,1)}'
    elif op == LOAD:
        return f'LOAD 0x{toHex(opr,2)} --> r{toHex(reg,1)}'
    elif op == STORE:
        return f"STORE r{toHex(reg,1)} --> m{toHex(opr,2)}"
    elif op == MOVE:
        if reg == 0x0: return f"MOVE r{toHex(opr1,1)} --> r{toHex(opr2,1)}"
        elif reg == 0x1: return f"MOVE {specRegToName(opr1)} --> r{toHex(opr2,1)}"
        elif reg == 0x2: return f"MOVE r{toHex(opr1,1)} --> {specRegToName(opr2)}"
        elif reg == 0x3: return f"MOVE {specRegToName(opr1)} --> {specRegToName(opr2)}"
        return 'UNKNOWN MOVE'
    elif op == ADD_S:
        return f"ADD_S r{toHex(opr1,1)} + r{toHex(opr2,1)} --> r{toHex(reg,1)}"
    elif op == ADD_F:
        return f"ADD_F r{toHex(opr1,1)} + r{toHex(opr2,1)} ->> r{toHex(reg,1)}"
    elif op == OR:
        return f"OR r{toHex(opr1,1)} | r{toHex(opr2,1)} --> r{toHex(reg,1)}"
    elif op == AND:
        return f"AND r{toHex(opr1,1)} & r{toHex(opr2,1)} --> r{toHex(reg,1)}"
    elif op == XOR:
        return f"XOR r{toHex(opr1,1)} ^ r{toHex(opr2,1)} -- > r{toHex(reg,1)}"
    elif op == ROTATE:
        return f"ROTATE r{toHex(reg,1)} by 0x{toHex(opr2,1)} --> r{toHex(reg,1)}"
    elif op == JUMP:
        return f"JUMP IF r{toHex(reg,1)} = r0 TO i{toHex(opr,2)}"
    elif op == HALT:
        return "HALT"
    elif op == STORE_P:
        return f"STORE_P r{toHex(reg,1)} --> p{toHex(opr,2)}"
    elif op == LOAD_P:
        return f"LOAD_P p{toHex(opr,2)} --> r{toHex(reg,1)}"
    elif op == JUMP_L:
        return f"JUMP IF r{toHex(reg,1)} < r0 TO i{toHex(opr,2)}"
    else:
        return "UNKNOWN"

def toByte(ins: int, reg: int, op1: int, op2: int|None = None):
    bh = (ins << 4) + reg
    bl = op1
    if op2 != None:
        bl = (bl << 4) + op2
    return bytes([bh]), bytes([bl])

def noOp():
    """ No operation """
    return toByte(NO_OP, 0x0, 0x0, None)
def loadMem(reg: int, mem: int):
    """ Load from memory to register. m[mem] -> r[reg] """
    return toByte(LOAD_MEM, reg, mem, None)
def load(reg: int, val: int):
    """ Load value to register. r[reg] = val """
    return toByte(LOAD, reg, val, None)
def store(reg: int, mem: int):
    """ Store register to memory. r[reg] -> m[mem] """
    return toByte(STORE, reg, mem, None)
def move(src: int, dest: int, opt: int=0x0):
    """ Move value from register to register. r[src] -> r[dest] """
    return toByte(MOVE, opt, src, dest)
def addS(reg: int, op1: int, op2: int):
    """ Add (signed) values into register. r[op1] + r[op2] -> r[reg] """
    return toByte(ADD_S, reg, op1, op2)
def orB(reg: int, op1: int, op2: int):
    """ OR registers into register. r[op1] | r[op2] -> r[reg]"""
    return toByte(OR, reg, op1, op2)
def andB(reg: int, op1: int, op2: int):
    """ AND registers into register. r[op1] & r[op2] -> r[reg]"""
    return toByte(AND, reg, op1, op2)
def xorB(reg: int, op1: int, op2: int):
    """ XOR registers into register. r[op1] ^ r[op2] -> r[reg]"""
    return toByte(XOR, reg, op1, op2)
def rotate(reg: int, amt: int):
    """ Rotate register by value. r[reg] >> amt -> r[reg]"""
    return toByte(ROTATE, 0x0, reg, amt)
def jump(reg: int, instr: int):
    """ Jump to instruction IF register 0 equals register. Jump If r[reg] == r[0] TO i[instr] """
    return toByte(JUMP, reg, instr, None)
def halt():
    """ Stop execution """
    return toByte(HALT, 0x0, 0x0, None)
def storePer(reg: int, per: int):
    """ Store register into peripheral. r[reg] -> p[per] """
    return toByte(STORE_P, reg, per, None)
def loadPer(reg: int, per: int):
    """ Load register from peripheral. p[per] -> r[reg] """
    return toByte(LOAD_P, reg, per, None)
def jumpLess(reg: int, instr: int):
    """ Jump to instruction IF register 0 is less than register. Jump If r[reg] < r[0] TO i[instr] """
    return toByte(JUMP_L, reg, instr, None)

R_PGMI = 0x0
""" Program index register address """
R_STACK = 0x1
""" Stack register address """
R_EXIT = 0x2
""" Exit code register """

def specRegToName(reg: int):
    """ Special register index to name """
    if reg == R_PGMI:
        return 'R_PGMI'
    elif reg == R_STACK:
        return 'R_STACK'
    elif reg == R_EXIT:
        return 'R_EXIT'
    else:
        return f's{toHex(reg,1)}'

def moveFromSpec(src: int, dest: int):
    """ Move value from special register to normal register (r0-F) """
    return toByte(MOVE, 0x1, src, dest)
def moveToSpec(src: int, dest: int):
    """ Move value from normal register (r0-F) to special register """
    return toByte(MOVE, 0x2, src, dest)
def moveFromToSpec(src: int, dest: int):
    """ Move value from special register to special register """
    return toByte(MOVE, 0x3, src, dest)

def pgmiToStack():
    """ Move program index to stack """
    return moveFromToSpec(R_PGMI, R_STACK)
def stackToPgmi():
    """ Pop stack to program index """
    return moveFromToSpec(R_STACK, R_PGMI)

def goto(instr: int):
    """ Goto instruction """
    return jump(0x0, instr)