from __future__ import annotations
from typing import TYPE_CHECKING

from BasicCompileError import BasicCompileError, BasicParseError, BasicRegisterFullError, BasicValueError
from convert import toHex
import asmInstructions as asm
import re

if TYPE_CHECKING:
    from basicCompile import BasicProgram

basicFunctions = {}

def parseParams(paramStr: str, funcName: str, numParams: int):
    if len(paramStr) == 0:
        if numParams > 0:
            raise BasicCompileError(f'Function "{funcName}" must be passed {numParams} parameter(s)')
        return ['']
    
    if numParams == 1:
        return [paramStr]
    
    # mtc = re.match(r'(.+)', params)
    # if not mtc:
    #     raise BasicCompileError(f'Function "{funcName}" must be passed {numParams} parameter(s)')
    # param = mtc.groups()[0]

    # if len(param) != numParams:
    #     raise BasicCompileError()
    
    # if numParams == 1:
    #     return param
    
    params = re.split(r',\s*', paramStr)
    if not params:
        raise BasicParseError(f'Could not parse parameters for function')
    
    if len(params) != numParams:
        raise BasicCompileError(f'Function "{funcName}" must be passed {numParams} parameter(s)')
    
    return params

consoleAdr = 0x00
def write(pgm: BasicProgram, params: str):
    param = parseParams(params, 'write', 1)[0]
    
    if param[0] == '"': # Write from string literal
        if param[-1] != '"':
            raise BasicCompileError(f'Unterminated string literal: {param}')
        # print(param)
        r = pgm.nextReg()
        if r == -1:
            raise BasicRegisterFullError(f'"{param}"')
        
        i = 1
        while i < len(param)-1:
            c = param[i]
            # print(c)
            if c == '\\': # If the character is the start of an escape sequence
                if len(param) - 1 > i+1:
                    c2 = param[i+1]
                    if c2 == '\\': # backslash
                        c = '\\'
                        i += 1
                    elif c2 == 'n': # Newline
                        c = '\n'
                        i += 1
                    elif c2 == '\'': # Single quote
                        c = '\''
                        i += 1
                    elif c2 == '\"': # Double quote
                        c = '\"'
                        i += 1
                    else:
                        raise BasicCompileError(f'Unknown escape sequence: \\{c2}')
                else:
                    raise BasicCompileError(f'Unterminated string literal: {param}')
            
            # pgm.addB(asm.load( r, ord(c)))
            # pgm.addB(asm.storePer(r, consoleAdr))
            pgm.addChunk(asm.load( r, ord(c)))
            pgm.addChunk(asm.storePer(r, consoleAdr))
            i += 1
    elif param in pgm.variables: # Write from variable
        var = pgm.variables[param]
        if var.inReg():
            # pgm.addB(asm.storePer(var.rAdr, consoleAdr))
            pgm.addChunk(asm.storePer(var.rAdr, consoleAdr))
        else:
            r = pgm.nextReg()
            if r == -1:
                raise BasicRegisterFullError(f'variable {param}')
            var.loadToReg(r)
            # pgm.addB(asm.storePer(r, consoleAdr))
            pgm.addChunk(asm.storePer(r, consoleAdr))
            var.clearFromReg()
    elif param[0:2] == '0x': # Write from hex
        try:
            v = int(param, 16)
            r = pgm.nextReg()
            if r == -1:
                raise BasicRegisterFullError(f'0x{toHex(v)}')
            # pgm.addB(asm.load(r, v))
            # pgm.addB(asm.storePer(r, consoleAdr))
            pgm.addChunk(asm.load(r, v))
            pgm.addChunk(asm.storePer(r, consoleAdr))
        except ValueError:
            raise BasicValueError(f'Could not parse hex "{param}"')
    else: # Write from number
        try:
            v = int(param)
            r = pgm.nextReg()
            if r == -1:
                raise BasicRegisterFullError(f'{v}')
            # pgm.addB(asm.load(r, v))
            # pgm.addB(asm.storePer(r, consoleAdr))
            pgm.addChunk(asm.load(r, v))
            pgm.addChunk(asm.storePer(r, consoleAdr))
        except ValueError:
            raise BasicValueError(f'Unknown value "{param}"')
basicFunctions['write'] = write

def rotate(pgm: BasicProgram, paramStr: str):
    params = parseParams(paramStr, 'rotate', 2)
    
    if not (params[0] in pgm.variables):
        raise BasicValueError('First parameter of rotate() must be variable')
    
    var = pgm.variables[params[0]]
    
    ra = 0
    if params[1][0:2] == '0x':
        try:
            ra = int(params[1], 16)
        except ValueError:
            raise BasicValueError(f'Second parameter of rotate() must be a number')
    else:
        try:
            ra = int(params[1])
        except ValueError:
            raise BasicValueError(f'Second parameter of rotate() must be a number')
    
    if ra < 0 or ra >= 0x10:
        raise BasicCompileError(f'Rotation amount for rotate() must be between 0 and 15 (inclusive), was {ra}')
    
    vr = -1
    if not var.inReg():
        vr = pgm.nextReg()
        if vr == -1:
            raise BasicRegisterFullError(f'variable {params[0]}')
        var.loadToReg(vr)
    else:
        vr = var.rAdr
    
    # pgm.addB(asm.rotate(vr, ra))
    pgm.addChunk(asm.rotate(vr, ra))
    var.modified = True
basicFunctions['rotate'] = rotate

def toStack(pgm: BasicProgram, paramStr: str):
    params = parseParams(paramStr, 'toStack', 1)

    reg, var = pgm.parseParam(params[0])
    # pgm.addB(asm.moveToSpec(reg, asm.STACK))
    pgm.addChunk(asm.moveToSpec(reg, asm.R_STACK))
    if var:
        var.clearFromReg()
basicFunctions['toStack'] = toStack

def fromStack(pgm: BasicProgram, paramStr: str):
    params = parseParams(paramStr, 'fromStack', 1)

    reg, var = pgm.parseParam(params[0])
    # pgm.addB(asm.moveFromSpec(asm.STACK, reg))
    pgm.addChunk(asm.moveFromSpec(asm.R_STACK, reg))
    if var:
        var.modified = True
basicFunctions['fromStack'] = fromStack