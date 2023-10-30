import re
from convert import toHex

from BasicCompileError import *
from basicFunctions import basicFunctions
import asmInstructions as asm
import traceback

from basicClasses import *

class BasicProgram:
    def print(self, *msg):
        if self.debug:
            print(*msg)
            
    def __init__(self):
        self.debug = False
        self._reset()
    
    def _reset(self):
        self.variables: dict[str, Variable] = {}
        self.compiled = False
        self.error = Exception('How did you get this?')
        self.compileError = ''
        self.machine: list[bytes] = []
        self.chunks: list[Chunk] = []
        self.jumpPoints: dict[str, int] = {}
        self.jumps: list[Jump] = []
        # self.regUsed = [None] * 0x10
        self.regUsed: dict[int, Variable] = {}
        self.nextMem = 0xff
        self.codeBlockN = 0
        self.codeBlocks: list[CodeBlock] = []
        self.cFunc: Function|None = None
        self.functions: dict[str, Function] = {}
        self.__nextJump = 0
    
    def getNextJump(self):
        self.__nextJump += 1
        return f'jump_{self.__nextJump}'
    
    def getMachine(self):
        if not self.compiled:
            raise Exception('Program must be compiled to get machine code')
        # m = [bytes(1)] * len(self.machine)
        # for i in range(len(self.machine)):
            # m[i] = int.to_bytes(self.machine[i], "big")
        # return m
        m = [bytes(1)] * len(self.machine)
        for i in range(len(self.machine)):
            # print(toHex(i))
            m[i] = self.machine[i]
        return m
    
    def addVar(self, name:str, mAdr:int, rAdr=-1):
        if self.cFunc:
            if name in self.cFunc.variables:
                raise BasicCompileError(f'Variable with name {name} already exists in function scope')
        else:
            if name in self.variables:
                raise BasicCompileError(f'Variable with name {name} already exists in global scope')
        
        var = Variable(self, name, mAdr, rAdr)
        if self.cFunc:
            self.cFunc.variables[name] = var
            var.scope = self.cFunc.name
        else:
            self.variables[name] = var
            var.scope = 'global'
        # var.storeToMem()
        return var
    def isVar(self, name:str):
        if self.cFunc:
            if name in self.cFunc.variables: return True
        return name in self.functions
    def getVar(self, name: str):
        if self.cFunc:
            if name in self.cFunc.variables: return self.cFunc.variables[name]
        if name in self.variables:
            return self.variables[name]
        return None
    
    def _add(self, instruction:int, reg=0x0, op1=0x0, op2: int|None=None):
        if op2 != None:
            op1 = op1*0x10 + op2
        
        self.machine.append((instruction*0x10 + reg).to_bytes(1, "big"))
        self.machine.append(op1.to_bytes(1, "big"))
        return len(self.machine)
    def _addB(self, bh: bytes|tuple[bytes, bytes], bl=bytes(1)):
        if isinstance(bh, tuple):
            bh, bl = bh
        self.machine.append(bh)
        self.machine.append(bl)
        return len(self.machine)
    
    def addChunk(self, chunk: Chunk|tuple[bytes, bytes]):
        if isinstance(chunk, tuple):
            # self.chunks.append(chunk)
            chunk = AsmChunk(chunk)
        if self.cFunc:
            self.cFunc.addChunk(chunk)
        else:
            self.chunks.append(chunk)
    
    def nextReg(self, start=0x1):
        for i in range(start, 0x10):
            if not (i in self.regUsed):
                return i
        for i in range(start, 0x10):
            if i in self.regUsed and isinstance(self.regUsed[i], Variable):
                var = self.regUsed[i]
                if var.clearable:
                    var.removeReg(i)
                    return i
        return -1
    
    def compile(self, filename: str):
        self._reset()
        
        lines: list[str] = []
        with open(filename, "r") as f:
            for line in f:
                lines.append(line.rstrip('\n'))
        
        self.print('Parsing lines')
        for lineN in range(len(lines)):
            line = lines[lineN]
        
            if len(line) <= 0:
                continue
            
            try:
                self._parseLine(line, lineN)
            except BasicCompileError as e:
                e.setLine(lineN, line)
                self.compileError = str(e)
                self.error = e
                return None
            except Exception as e:
                self.error = e
                self.compileError = 'Internal error'
                return None
        
        if len(self.codeBlocks) > 0:
            block = self.codeBlocks.pop()
            error = BasicParseError(f'Un-ended {block.type}')
            error.setLine(block.lineN, lines[block.lineN])
            self.compileError = str(error)
            self.error = error
            return None

        # print(self.machine)
        # print(self.jumpPoints)
        # print(self.regUsed)
        # for r, var in self.regUsed.items():
        #     self.print(r, var)
        # for _, var in self.variables.items():
        #     self.print(var)
        self.print('Compiling Chunks')
        for chunk in self.chunks:
            self.print(toHex(len(self.machine)), chunk)
            chunk.compile(self)
        for name, func in self.functions.items():
            self.print(f'Func: {name}()')
            func.compileChunks()
        
        try:
            self.resolveJumps()
        except BasicCompileError as e:
            e.setLine(e.lineN, lines[e.lineN])
            self.compileError = str(e)
            self.error = e
            return None
        except Exception as e:
            self.error = e
            self.compileError = 'Internal error'
            return None
        
        self.compiled = True
    
    def _parseLine(self, line: str, lineN: int):
        line = line.lstrip()
        line = split(r'\s*--\s*', line)[0] # Remove comment starting with '--'
        line = split(r'\s*//\s*', line)[0] # Remove comment starting with '//'
        line = split(r'\s*##\s*', line)[0] # Remove comment starting with '##'
        line = split(r'\s*\Z', line)[0] # Remove trailing whitespace

        self.print(f'"{line}"')
        
        if len(line) <= 0: # Blank line
            return
        
        if line[0] == ':': # Jump point
            if not self._addJP(line[1:]):
                raise BasicCompileError(f'Jump point "{line[1:]}" was already defined')
            return
        
        if line == 'HALT': # Halt
            # self.add(asm.HALT)
            self.addChunk(HaltChunk())
            return
        if re.search(r'^exit\s+\d+', line):
            mtc = re.match(r'^exit\s*(\d+)', line)
            if not mtc:
                raise BasicParseError('Could not parse exit')
            code = mtc.groups()[0]
            try:
                self.addChunk(asm.load(0x0, int(code)))
            except ValueError:
                raise BasicValueError('Exit code must be a number')
            self.addChunk(asm.moveToSpec(0x0, asm.R_EXIT))
            self.addChunk(HaltChunk())
            return
        
        if line == 'else': # Else for if
            if len(self.codeBlocks) <= 0:
                raise BasicCompileError('Else statement found outside of if')
            
            block = self.codeBlocks[-1]
            if not isinstance(block, IfStatement):
                raise BasicCompileError('Else statement can only be used with if')
            block.gotoEnd()
            block.addElse()
            return
        elif line == 'end': # End for code block
            if len(self.codeBlocks) <= 0:
                raise BasicCompileError('End statement found outside of if, loop or function')
            block = self.codeBlocks.pop()
            if isinstance(block, Loop):
                block.gotoCheck()
            block.addEnd()
            if isinstance(block, Function):
                self.cFunc = None
            return
        elif line == 'return':
            if not self.cFunc:
                raise BasicCompileError('Return statement found outside of function')
            self.cFunc.addExit()
            return

        if re.search(r'^goto\s+', line): # Goto
            mtc = split(r'^goto\s+', line)[1]
            if not mtc or mtc=='':
                raise BasicParseError(f'Could not parse goto')
            dest = mtc
            self._addGoto(dest, lineN)
            return
        
        if re.search(r'^var\s+\w+', line): # Defining a new variable
            mtc = re.match(r'^var\s*(\w+)', line)
            if not mtc:
                raise BasicParseError('Could not parse variable definition')
            name = mtc.groups()[0]
            if self.nextMem <= len(self.machine):
                raise BasicCompileError(f'Out of memory addresses for variable {name}')
            var = self.addVar(name, self.nextMem)
            self.print('adding', var)
            self.nextMem -= 1
            
            if re.search(r'^var\s+\S*\s*=\s*\S+', line): # Initialize the value of the variable
                mtc = re.match(r'^var\s+\S*\s*=\s*(\S+)', line)
                if not mtc:
                    raise BasicParseError('Could not parse variable definition')
                val = mtc.groups()[0]
                if val in self.variables: # copy value
                    v2 = self.variables[val]
                    if v2.inReg():
                        # var.storeToMem(v2.rAdr, False)
                        return
                    else:
                        r = self.nextReg()
                        if r == -1:
                            raise BasicRegisterFullError(f'variable {val}')
                        v2.loadToReg(r, False)
                        # var.storeToMem(r)
                        v2.modified = True
                        v2.markReg(r, True)
                        return
                elif val[0] == 'm': # from mem
                    try:
                        m = int(val[1:], 16)
                        r = self.nextReg()
                        if r == -1:
                            raise BasicRegisterFullError(f'm{toHex(m)}')
                        self.addChunk(asm.loadMem(r, m))
                        var.modified = True
                        var.markReg(r, True)
                        return
                    except ValueError:
                        raise BasicCompileError(f'Could not read memory address "{val}"')
                elif val[0] == 'p': # from per
                    try:
                        p = int(val[1:], 16)
                        r = self.nextReg()
                        if r == -1:
                            raise BasicRegisterFullError(f'p{toHex(p)}')
                        self.addChunk(asm.loadPer(r, p))
                        var.modified = True
                        var.markReg(r, True)
                        return
                    except ValueError:
                        raise BasicCompileError(f'Could not read peripheral address "{val}"')
                elif val[0] == '"': # from char ASCII
                    v = ord(val[1])
                    r = self.nextReg()
                    if r == -1:
                        raise BasicRegisterFullError(f'"{val[1]}"')
                    self.addChunk(asm.load(r, v))
                    var.modified = True
                    var.markReg(r, True)
                    return
                elif val[0:2] == '0x': # from hex
                    try:
                        v = int(val, 16)
                        r = self.nextReg()
                        if r == -1:
                            raise BasicRegisterFullError(f'0x{toHex(v)}')
                        self.addChunk(asm.load(r, v))
                        var.modified = True
                        var.markReg(r, True)
                        return
                    except ValueError:
                        raise BasicCompileError(f'Could not read hex value "{val}"')
                else: # probably in base 10
                    try:
                        v = int(val)
                        r = self.nextReg()
                        if r == -1:
                            raise BasicRegisterFullError(f'{v}')
                        self.addChunk(asm.load(r, v))
                        var.modified = True
                        var.markReg(r, True)
                        return
                    except ValueError:
                        raise BasicCompileError(f'Unknown value "{val}"')
        
        if re.search(r'^if\s+', line): # If statement
            self._parseIf(lineN, line)
            return
        
        if re.search(r'^while\s+', line): # While loop
            self._parseWhile(lineN, line)
            return
        
        if re.search(r'^function\s+', line): # Custom function
            if self.cFunc: raise BasicCompileError('Functions can not be defined inside functions')
            self._parseFunction(lineN, line)
            return
        
        fMtc = re.match(r'([^\(]+)\((.*)\)', line) # Check for function
        if fMtc:
            fName, params = fMtc.groups()
            if fName in basicFunctions: # if it is a basic function
                basicFunctions[fName](self, params)
                return
            elif fName in self.functions:
                func = self.functions[fName]
                func.gotoMain()
                return
            else: 
                # TODO custom user defined function check here
                raise BasicCompileError(f'Unknown function "{fName}"', lineN, "Name")
        
        if re.search(r'\w+\s*[+]?=', line): # Assignment and math
            self._parseAssignment(line)
            return
        
        raise BasicCompileError(f'Unknown operation')
    
    def _addJP(self, name: str):
        if name in self.jumpPoints:
            return False
        self.jumpPoints[name] = len(self.machine)
        return True
    
    def _addJump(self, t: int, reg: int, name: str, lineN: int=-1):
        self.jumps.append(Jump(len(self.machine), name, lineN))
        self._add(t, reg)
    def _addGoto(self, name: str, lineN: int=-1):
        self._addJump(asm.JUMP, 0, name, lineN)
    
    def parseParam(self, param: str, reg = -1):
        var = self.getVar(param)
        if(var):
            # var = self.variables[param]
            # reg = var.getOrLoad()
            if not var.inReg():
                if reg == -1:
                    reg = self.nextReg(0)
                    if reg == -1:
                        raise BasicRegisterFullError(f'{param}')
                var.loadToReg(reg)
                self.print(f'Loading {param} to r{toHex(reg,1)}')
                return reg, var
            else:
                return var.rAdr, var
        elif(param[0] == '"'):
            char = param[1]
            if(char == '\\'):
                if(param[2] == '\\'):
                    char = '\\'
                elif(param[2] == '"'):
                    char = '"'
                elif(param[2] == '\''):
                    char = '\''
                elif(param[2] == 'n'):
                    char = '\n'
                elif(param[2] == 't'):
                    char = '\t'
                else:
                    raise BasicCompileError(f'Unknown escape sequence: \\{param[2]}')
                if(param[3] != '"'):
                    raise BasicValueError('String can only be 1 character')
            else:
                if(param[2] != '"'):
                    raise BasicValueError('String can only be 1 character')
            
            if reg == -1:
                reg = self.nextReg(0)
            self.addChunk(asm.load( reg, ord(char)))
            return reg, None
        elif(param[0:2] == '0x'):
            try:
                if reg == -1:
                    reg = self.nextReg(0)
                    if reg == -1:
                        raise BasicRegisterFullError(f'{param}')
                # self.add(asm.LOAD, reg, int(param,16))
                self.addChunk(asm.load(reg, int(param,16)))
                return reg, None
            except ValueError:
                raise BasicValueError(f'Could not parse hex "{param}"')
        else:
            try:
                if reg == -1:
                    reg = self.nextReg(0)
                    if reg == -1:
                        raise BasicRegisterFullError(f'{param}')
                # self.add(asm.LOAD, reg, int(param))
                self.addChunk(asm.load(reg, int(param)))
                return reg, None
            except ValueError:
                raise BasicValueError(f'Could not parse number "{param}"')

    def _parseIf(self, lineN: int, line: str):
        mtc = re.match(r'^if\s+(\S+)\s*(==|<=|<|>=|>|!=|=)\s*([^\s:]+)\s*(:)?\s*(\S+)?', line)
        if not mtc:
            raise BasicParseError('Could not parse if statement')
        p0, cmp, p1, c, j = mtc.groups()
        if c and not j:
            raise BasicParseError('If statement missing goto')
        if j and not c:
            raise BasicParseError(f'Could not parse if statement, unknown control: "{j}"')
        ifStatement = None
        if not j or j == '':
            ifn = self.codeBlockN
            self.codeBlockN += 1
            ifStatement = IfStatement(self, f'if{ifn}', lineN)
            # j = ifStatement.getMain()
            self.codeBlocks.append(ifStatement)
        if(cmp == '='):
            raise BasicCompileError('Can not assign in comparison')
        r0 = None
        v0 = None
        r1 = None
        v1 = None
        r0v = False
        if(p0 in self.variables):
            # r0 = alias[p0]
            var = self.variables[p0]
            if not var.inReg():
                # r1 = self.nextReg(0)
                r0 = 0x0
                var.loadToReg(r0, False)
            else:
                r0 = var.rAdr
                var.markReg()
            v0 = var
        elif(p0[0] == 'r'):
            r0 = int(p0[1:], 16)
        elif(p0[0] == 'm'):
            raise BasicCompileError(f'Can not compare with memory')
        elif(p0[0] == 'p'):
            raise BasicCompileError(f'Can not compare with peripheral')
        elif(p0[0:2] == '0x'):
            try:
                r0 = 0x0
                r0v = True
                # self.add(asm.LOAD, r0, int(p0,16))
                self.addChunk(asm.load(r0, int(p0,16)))
            except ValueError:
                raise BasicCompileError(f'Could not parse hex "{p0}"')
        else:
            try:
                r0 = 0x0
                r0v = True
                # self.add(asm.LOAD, r0, int(p0))
                self.addChunk(asm.load(r0, int(p0)))
            except ValueError:
                raise BasicCompileError(f'Could not parse number "{p0}"')
        
        if(p1 in self.variables):
            # r1 = alias[p1]
            var = self.variables[p1]
            if not var.inReg():
                r1 = self.nextReg(0)
                if r1 == -1:
                    raise BasicRegisterFullError(f'{p1}')
                var.loadToReg(r1)
            else:
                r1 = var.rAdr
                var.markReg()
            v1 = var
        elif(p1[0] == 'r'):
            r1 = int(p1[1:], 16) 
        elif(p1[0] == 'm'):
            r1 = 0x0
            if(r0 == 0):
                r1 = 0xf
            # self.add(asm.LOAD_MEM, r1, int(p1[1:], 16))
            self.addChunk(asm.loadMem(r1, int(p1[1:], 16)))
        elif(p1[0] == 'p'):
            r1 = 0x0
            if(r0 == 0):
                r1 = 0xf
            # self.add(asm.LOAD_P, r1, int(p1[1:], 16))
            self.addChunk(asm.loadPer(r1, int(p1[1:], 16)))
        elif(p1[0:2] == '0x'):
            if(r0v):
                raise BasicCompileError(f'Can not compare two numbers')
            r1 = 0x0
            if(r0 == 0):
                r1 = 0xf
            try:
                # self.add(asm.LOAD, r1, int(p1,16))
                self.addChunk(asm.load(r1, int(p1, 16)))
            except ValueError:
                raise BasicCompileError(f'Can not parse hex "{p1}"')
        else:
            if(r0v):
                raise BasicCompileError(f'Can not compare two numbers')
            r1 = 0x0
            if(r0 == 0):
                r1 = 0xf
            try:
                # self.add(asm.LOAD, r1, int(p1))
                self.addChunk(asm.load(r1, int(p1)))
            except ValueError:
                raise BasicCompileError(f'Can not parse number "{p1}"')
        
        if(r0 != 0x0 and r1 != 0x0):
            # self.add(asm.MOVE, 0x0, r0, 0x0)
            self.addChunk(asm.move(r0, 0x0))
            r0 = 0
        
        actions = []
        r = r1
        if(r1 == 0):
            r = r0
            if(cmp == '=='): # r0 == rn 
                actions = [ [asm.JUMP, False] ]
            elif(cmp == '!='): # not r0 == rn
                actions = [ [asm.JUMP, True] ]
            elif(cmp == '<'): # r0 > rn
                actions = [ [asm.JUMP_L, False] ]
            elif(cmp == '<='): # r0 > rn or r0 == rn
                actions = [ [asm.JUMP_L, False], False, [asm.JUMP, False] ]
            elif(cmp == '>'): # not r0 > rn and not r0 == r1
                actions = [ [asm.JUMP_L, True], True, [asm.JUMP, True] ]
            elif(cmp == '>='): # not r0 > rn
                actions = [ [asm.JUMP_L, True] ]
            else:
                raise BasicCompileError(f'Unknown comparison "{cmp}"')
        else:
            if(cmp == '=='): # r0 == rn
                actions = [ [asm.JUMP, False] ]
            elif(cmp == '!='): # not r0 == rn
                actions = [ [asm.JUMP, True] ]
            elif(cmp == '<'): # not r0 > rn and not r0 == rn
                actions = [ [asm.JUMP_L, True], True, [asm.JUMP, True] ]
            elif(cmp == '<='): # not r0 > rn
                actions = [ [asm.JUMP_L, True] ]
            elif(cmp == '>'): # r0 > rn
                actions = [ [asm.JUMP_L, False] ]
            elif(cmp == '>='): # r0 > rn or r0 == rn
                actions = [ [asm.JUMP_L, False], False, [asm.JUMP, False] ]
            else:
                raise BasicCompileError(f'Unknown comparison "{cmp}"')
        
        # self.addChunk(IfChunk(r, cmp, ))
        eL = LabelChunk(self.getNextJump())
        if len(actions) == 1:
            if actions[0][1]: # not
                if ifStatement:
                    ifStatement.jumpElse(actions[0][0], r)
                else:
                    # self.add(actions[0][0], r, len(self.machine)+4)
                    self.addChunk(JumpChunk(actions[0][0], r, eL))
                    # self._addGoto(j, lineN)
                    self.addChunk(GotoChunk(j))
            else:
                if ifStatement:
                    ifStatement.jumpMain(actions[0][0], r)
                    ifStatement.gotoElse()
                else:
                    # self._addJump(actions[0][0], r, j, lineN)
                    self.addChunk(JumpChunk(actions[0][0], r, j))
        else:
            if actions[1]: # not and not
                if ifStatement:
                    ifStatement.jumpElse(actions[0][0], r)

                    ifStatement.jumpElse(actions[2][0], r)
                else:
                    # self.add(actions[0][0], r, len(self.machine)+6)
                    self.addChunk(JumpChunk(actions[0][0], r, eL))
                    
                    # self.add(actions[2][0], r, len(self.machine)+4)
                    self.addChunk(JumpChunk(actions[2][0], r, eL))
                    # self._addGoto(j, lineN)
                    self.addChunk(GotoChunk(j))
            else: # or
                if actions[0][1]: # not
                    if ifStatement:
                        ifStatement.jumpElse(actions[0][0], r)
                    else:
                        # self.add(actions[0][0], r, len(self.machine)+4)
                        self.addChunk(JumpChunk(actions[0][0], r, eL))
                        # self._addGoto(j, lineN)
                        self.addChunk(GotoChunk(j))
                else:
                    if ifStatement:
                        ifStatement.jumpMain(actions[0][0], r)
                    else:
                        # self._addJump(actions[0][0], r, j, lineN)
                        self.addChunk(JumpChunk(actions[0][0], r, j))
                
                if actions[2][1]: # not
                    if ifStatement:
                        ifStatement.jumpElse(actions[2][0], r)
                    else:
                        # self.add(actions[2][0], r, len(self.machine)+4)
                        self.addChunk(JumpChunk(actions[2][0], r, eL))
                        # self._addGoto(j, lineN)
                        self.addChunk(GotoChunk(j))
                else:
                    if ifStatement:
                        ifStatement.jumpMain(actions[2][0], r)
                        ifStatement.gotoElse()
                    else:
                        # self._addJump(actions[2][0], r, j, lineN)
                        self.addChunk(JumpChunk(actions[2][0], r, j))
        self.addChunk(eL)
        if ifStatement != None:
            # ifStatement.gotoElse(lineN)
            ifStatement.addMain()
            # self._addGoto(f'if{ifn}:else', lineN)
            # self._addJP(j)
        if v0: v0.clearFromReg()
        if v1: v1.clearFromReg()
    
    def _parseAssignment(self, line: str):
        mtc = re.match(r'^(\w+)\s*([+]?=)\s*(".+"|\w+)\s*([+\^&|])?\s*(\w+)?', line)
        if not mtc:
            raise BasicParseError('Could not parse assignment')
        # print(mtc.groups())
        dest, asg, src1, op, src2 = mtc.groups()
        
        mth = asg != '=' or op # if this is math
        
        dr = -1
        dv = self.getVar(dest)
        dm = -1
        dp = -1
        if dv:
            # if mth:
            if not dv.inReg():
                dr = self.nextReg()
                if dr == -1:
                    raise BasicRegisterFullError(f'variable {dest}')
                dv.markReg(dr, True)
            else:
                dr = dv.rAdr
                dv.markReg()
            # else:
            #     dm = dv.mAdr
        elif dest[0] == 'm':
            dm = int(dest[1:],16)
            if mth:
                dr = self.nextReg()
                if dr == -1:
                    raise BasicRegisterFullError(f'm{toHex(dm,2)}')
                self.regUsed[dr] = Variable(self, 'tmp', -1, dr)
        elif dest[0] == 'p':
            dp = int(dest[1:],16)
            if mth:
                dr = self.nextReg()
                if dr == -1:
                    raise BasicRegisterFullError(f'p{toHex(dp,2)}')
                self.regUsed[dr] = Variable(self, 'tmp', -1, dr)
        else:
            raise BasicValueError(f'Unknown destination for assignment: "{dest}"')
        
        sr = -1
        sv = self.getVar(src1)
        if sv:
            if not sv.inReg():
                if not mth and dv:
                    # self.add(asm.LOAD_MEM, dv.rAdr, sv.mAdr)
                    sv.loadToReg(dv.rAdr, False)
                    dv.modified = True
                    return
                sr = self.nextReg()
                if sr == -1:
                    raise BasicRegisterFullError(f'variable {src1}')
                sv.loadToReg(sr)
            else:
                sr = sv.rAdr
                sv.markReg()
        elif src1[0] == 'm':
            sm = int(src1[1:],16)
            if not mth and dv:
                # self.add(asm.LOAD_MEM, dv.rAdr, sm)
                self.addChunk(asm.loadMem(dv.rAdr, sm))
                dv.modified = True
                return
            sr = self.nextReg()
            if sr == -1:
                raise BasicRegisterFullError(f'm{toHex(sm,2)}')
            self.regUsed[sr] = Variable(self, 'tmp', -1, dr)
            # self.add(asm.LOAD_MEM, sr, sm)
            self.addChunk(asm.loadMem(sr, sm))
        elif src1[0] == 'p':
            sp = int(src1[1:],16)
            if not mth and dv:
                # self.add(asm.LOAD_P, dv.rAdr, sp)
                self.addChunk(asm.loadPer(dv.rAdr, sp))
                dv.modified = True
                return
            sr = self.nextReg()
            if sr == -1:
                raise BasicRegisterFullError(f'p{toHex(sp,2)}')
            self.regUsed[sr] = Variable(self, 'tmp', -1, dr)
            # self.add(asm.LOAD_P, sr, sp)
            self.addChunk(asm.loadPer(sr, sp))
        elif src1[0] == '"': # from char ASCII
            val = ord(src1[1])
            if not mth and dv:
                # self.add(asm.LOAD, dv.rAdr, val)
                self.addChunk(asm.load(dv.rAdr, val))
                dv.modified = True
                return
            sr = self.nextReg()
            if sr == -1:
                raise BasicRegisterFullError(f'"{src1[1]}"')
            self.regUsed[sr] = Variable(self, 'tmp', -1, dr)
            # self.add(asm.LOAD, sr, val)
            self.addChunk(asm.load(sr, val))
        elif src1[0:2] == '0x':
            try:
                val = int(src1, 16)
            except ValueError:
                raise BasicCompileError(f'Could not parse hex "{src1}"')
            if not mth and dv:
                # self.add(asm.LOAD, dv.rAdr, val)
                self.addChunk(asm.load(dv.rAdr, val))
                dv.modified = True
                return
            sr = self.nextReg()
            if sr == -1:
                raise BasicRegisterFullError(f'0x{toHex(val,2)}')
            self.regUsed[sr] = Variable(self, 'tmp', -1, dr)
            # self.add(asm.LOAD, sr, val)
            self.addChunk(asm.load(sr, val))
        else:
            try:
                val = int(src1)
            except ValueError:
                raise BasicCompileError(f'Unknown source for assignment: "{src1}"')
            if not mth and dv:
                # self.add(asm.LOAD, dv.rAdr, val)
                self.addChunk(asm.load(dv.rAdr, val))
                dv.modified = True
                return
            sr = self.nextReg()
            if sr == -1:
                raise BasicRegisterFullError(f'{toHex(val,2)}')
            self.regUsed[sr] = Variable(self, '__tmp', -1, dr)
            # self.add(asm.LOAD, sr, val)
            self.addChunk(asm.load(sr, val))
        
        if mth: # this is math
            sr2 = -1
            sv2 = None
            
            if asg != '=':
                op = asg[0]
                sr2 = sr
                sv2 = sv
                sr = dr
                sv = dv
                # raise BasicCompileError(f'Self assignment statements are not available yet')
            else:
                sv2 = self.getVar(src2)
                if sv2:
                    if not sv2.inReg():
                        sr2 = self.nextReg()
                        if sr2 == -1:
                            raise BasicRegisterFullError(f'variable {src2}')
                        sv2.markReg(sr, True)
                    else:
                        sr2 = sv2.rAdr
                        sv2.markReg()
                elif src2[0] == 'm':
                    sm = int(src2[1:],16)
                    sr2 = self.nextReg()
                    if sr2 == -1:
                        raise BasicRegisterFullError(f'm{toHex(sm,2)}')
                    self.regUsed[sr2] = Variable(self, 'tmp', -1, dr)
                    # self.add(asm.LOAD_MEM, sr2, sm)
                    self.addChunk(asm.loadMem(sr2, sm))
                elif src2[0] == 'p':
                    sp = int(src2[1:],16)
                    sr2 = self.nextReg()
                    if sr2 == -1:
                        raise BasicRegisterFullError(f'p{toHex(sp,2)}')
                    self.regUsed[sr2] = Variable(self, 'tmp', -1, dr)
                    # self.add(asm.LOAD_P, sr2, sp)
                    self.addChunk(asm.loadPer(sr2, sp))
                elif src2[0:2] == '0x':
                    val = int(src2, 16)
                    sr2 = self.nextReg()
                    if sr2 == -1:
                        raise BasicRegisterFullError(f'0x{toHex(val,2)}')
                    self.regUsed[sr2] = Variable(self, 'tmp', -1, dr)
                    # self.add(asm.LOAD, sr2, val)
                    self.addChunk(asm.load(sr2, val))
                else:
                    val = int(src2)
                    sr2 = self.nextReg()
                    if sr2 == -1:
                        raise BasicRegisterFullError(f'{toHex(val,2)}')
                    self.regUsed[sr2] = Variable(self, 'tmp', -1, dr)
                    # self.add(asm.LOAD, sr2, val)
                    self.addChunk(asm.load(sr2, val))
                    # raise BasicValueError(f'Unknown source for math: "{src1}"')
            
            if op == '+':
                # self.add(asm.ADD_S, dr, sr, sr2)
                self.addChunk(asm.addS(dr, sr, sr2))
            elif op == '&':
                # self.add(asm.AND, dr, sr, sr2)
                self.addChunk(asm.andB(dr, sr, sr2))
            elif op == '|':
                # self.add(asm.OR, dr, sr, sr2)
                self.addChunk(asm.orB(dr, sr, sr2))
            elif op == '^':
                # self.add(asm.XOR, dr, sr, sr2)
                self.addChunk(asm.xorB(dr, sr, sr2))
            else:
                raise BasicCompileError(f'Unknown operator: "{op}"')
            
            if dv:
                # dv.storeToMem(dr)
                dv.modified = True
            elif dm >= 0:
                # self.add(asm.STORE, dr, dm)
                self.addChunk(asm.store(dr, dm))
            elif dp >= 0:
                # self.add(asm.STORE_P, dr, dp)
                self.addChunk(asm.storePer(dr, dp))
            
            if sv: sv.clearFromReg()
            if sv2: sv2.clearFromReg()
            return
        
        if dv:
            dv.modified = True
        elif dm >= 0:
            # self.add(asm.STORE, sr, dm)
            self.addChunk(asm.store(sr, dm))
        elif dp >= 0:
            # self.add(asm.STORE_P, sr, dp)
            self.addChunk(asm.storePer(sr, dp))
        else:
            raise Exception('How did we get here?')
            # self.add(asm.MOVE, 0x0, sr, dr)
            # dv.storeToMem(dr)
            
        if dv: dv.clearFromReg()
        if sv: sv.clearFromReg()
    
    def _parseWhile(self, lineN: int, line:str):
        mtc = re.match(r'^while\s+(\S+)\s*(==|<=|<|>=|>|!=|=)\s*(\S+)', line)
        if not mtc: raise BasicParseError('Could not parse while statement')
        p0, cmp, p1 = mtc.groups()

        if(cmp == '='): raise BasicCompileError('Can not assign in comparison')
        
        ifn = self.codeBlockN
        self.codeBlockN += 1
        loop = Loop(self, f'while{ifn}', lineN)
        # j = ifStatement.getMain()
        self.codeBlocks.append(loop)
        loop.addCheck()
        
        r0, v0 = self.parseParam(p0, 0x0)

        r1 = -1
        if r0 != 0: r1 = 0
        r1, v1 = self.parseParam(p1, r1)

        if r0 != 0 and r1 != 0:
            self.addChunk(asm.move(r0, 0x0))
            if v0:
                v0.markReg(0, False)
    
        r = r1
        if(r1 == 0):
            r = r0
            if(cmp == '=='): # r0 == rn 
                actions = [ [asm.JUMP, False] ]
            elif(cmp == '!='): # not r0 == rn
                actions = [ [asm.JUMP, True] ]
            elif(cmp == '<'): # r0 > rn
                actions = [ [asm.JUMP_L, False] ]
            elif(cmp == '<='): # r0 > rn or r0 == rn
                actions = [ [asm.JUMP_L, False], False, [asm.JUMP, False] ]
            elif(cmp == '>'): # not r0 > rn and not r0 == r1
                actions = [ [asm.JUMP_L, True], True, [asm.JUMP, True] ]
            elif(cmp == '>='): # not r0 > rn
                actions = [ [asm.JUMP_L, True] ]
            else:
                raise BasicCompileError(f'Unknown comparison "{cmp}"')
        else:
            if(cmp == '=='): # r0 == rn
                actions = [ [asm.JUMP, False] ]
            elif(cmp == '!='): # not r0 == rn
                actions = [ [asm.JUMP, True] ]
            elif(cmp == '<'): # not r0 > rn and not r0 == rn
                actions = [ [asm.JUMP_L, True], True, [asm.JUMP, True] ]
            elif(cmp == '<='): # not r0 > rn
                actions = [ [asm.JUMP_L, True] ]
            elif(cmp == '>'): # r0 > rn
                actions = [ [asm.JUMP_L, False] ]
            elif(cmp == '>='): # r0 > rn or r0 == rn
                actions = [ [asm.JUMP_L, False], False, [asm.JUMP, False] ]
            else:
                raise BasicCompileError(f'Unknown comparison "{cmp}"')
        
        if len(actions) == 1:
            if actions[0][1]: # not
                loop.jumpEnd(actions[0][0], r)
            else:
                loop.jumpMain(actions[0][0], r)
                loop.gotoEnd()
        else:
            if actions[1]: # not and not
                loop.jumpEnd(actions[0][0], r)

                loop.jumpEnd(actions[2][0], r)
            else: # or
                if actions[0][1]: # not
                    loop.jumpEnd(actions[0][0], r)
                else:
                    loop.jumpMain(actions[0][0], r)
                
                if actions[2][1]: # not
                    loop.jumpEnd(actions[2][0], r)
                else:
                    loop.jumpMain(actions[2][0], r)
                    loop.gotoEnd()

        loop.addMain()
        
        if v0: v0.clearFromReg()
        if v1: v1.clearFromReg()
    
    def _parseFunction(self, lineN: int, line: str):
        mtc = re.match(r'^function\s+(\S+)\(\)', line)
        if not mtc: raise BasicParseError('Could not parse while statement')
        name = mtc.groups()[0]
        if name in self.functions or name in basicFunctions:
            raise BasicCompileError('There is already a function named "{name}"', lineN, 'Name')
        
        func = Function(self, name, lineN)
        self.functions[name] = func
        self.codeBlocks.append(func)
        self.cFunc = func
        
        func.addMain()
    
    def resolveJumps(self):
        for jump in self.jumps:
            jump.resolve(self)
    
    def storeBinToFile(self, filename: str):
        if not self.compiled:
            raise Exception('Compile program before writing to file')
        
        with open(filename, "wb") as binary_file:
            for i in range(len(self.machine)):
                binary_file.write(self.machine[i])

def split(regex: str, string: str):
    s = re.search(regex, string)
    if s is not None:
        sp = s.span()
        return [string[:sp[0]], string[sp[1]:]]
    else:
        return [string, ""]

def storeToFile(filename: str, m: list[bytes]):
    with open(filename, "wb") as binary_file:
        for i in range(len(m)):
            # print(toHex(i), toHex(int.from_bytes(m[i],"big")))
            binary_file.write(m[i])

###############
###         ### 
###   GUI   ###
###         ###
###############

import tkinter as tk

def showGui():
    root = tk.Tk()
    root.title('Basic Compile')
    
    fileFrame = tk.LabelFrame(root, text='Files')
    fileFrame.pack()
    
    srcFrame = tk.Frame(fileFrame)
    srcFrame.pack()
    srcLabel = tk.Label(srcFrame, text='Source', anchor=tk.E, width=10)
    srcLabel.pack(side=tk.LEFT)
    srcFile = tk.Entry(srcFrame, width = 50)
    srcFile.insert(0, 'basic/func.basic')
    srcFile.pack(side=tk.LEFT)
    
    destFrame = tk.Frame(fileFrame)
    destFrame.pack()
    destLabel = tk.Label(destFrame, text='Destination', anchor=tk.E, width=10)
    destLabel.pack(side=tk.LEFT)
    destFile = tk.Entry(destFrame, width = 50)
    destFile.insert(0, 'bin/func.b.bin')
    destFile.pack(side=tk.LEFT)
    
    
    outputFrame = tk.LabelFrame(root, text='Output')
    outputFrame.pack()
    
    outputLabel = tk.Label(outputFrame, width = 50, wraplength=400, text='', anchor=tk.W, justify=tk.LEFT, font=('Consolas', 11))
    outputLabel.pack()
    
    program = BasicProgram()
    program.debug = True
    def compileAndOutput():
        file = srcFile.get()
        global machine
        try:
            program.compile(file)
        except FileNotFoundError:
            outputLabel.configure(text=f'File {file} does not exist')
            print('File not found')
            return
        except Exception as e:
            outputLabel.configure(text='An error occurred, check console for more details')
            print(e)
            traceback.print_tb(e.__traceback__)
            return
        text = ''
        if not program.compiled:
            if isinstance(program.error, BasicCompileError):
                text = program.compileError
                print(' - Basic Compiler Error:', program.compileError)
            else:
                text = str(program.error)
                print(type(program.error), program.error)
                # print(traceback.format_exc())
                traceback.print_tb(program.error.__traceback__)
        else:
            machine = program.getMachine()
            for i in range(int(len(machine)/2)):
                if(i > 0): text += '\n'
                instr = int.from_bytes(machine[i*2], "big") << 8
                instr += int.from_bytes(machine[i*2+1], "big")
                text += f'i{toHex(i*2)} │ 0x{toHex(instr,4)} │ {asm.strInstr(instr)}'
        # else:
        #     text = lastError
        outputLabel.configure(text=text)
    
    cmpButton = tk.Button(srcFrame, text='Compile', command=compileAndOutput, width=10)
    cmpButton.pack()
    
    def storeOutput():
        if not program.compiled:
            return
        file = destFile.get()
        program.storeBinToFile(file)
        storeToFile(file, program.getMachine())
    
    storeButton = tk.Button(destFrame, text='Store', command=storeOutput, width=10)
    storeButton.pack()
    
    root.mainloop()

if __name__ == '__main__':
    showGui()
    # pgm = Program()
    # pgm.compile('basic/test2.basic')
    # if not pgm.compiled:
    #     # print('Compile error: '+pgm.error)
    #     if isinstance(pgm.error, BasicCompileError):
    #         print(pgm.compileError)
    #     else:
    #         print(pgm.error)
    #         # print(traceback.format_exc())
    #         traceback.print_tb(pgm.error.__traceback__)
    #     print('Dump: ')
    #     print(f'Registers Used:')
    #     for r in range(len(pgm.regUsed)):
    #         u = pgm.regUsed[r]
    #         if u and u != True:
    #             print(f'\tr{toHex(r,1)} in use by {u.name}')
    #         elif u == True:
    #             print(f'\tr{toHex(r,1)} in use')
    #         else:
    #             print(f'\tr{toHex(r,1)} not in use {u}')
    # else:
    #     machine = pgm.getMachine()
    #     for i in range(len(machine)//2):
    #         instr = int.from_bytes(machine[i*2],"big") * 0x100
    #         instr += int.from_bytes(machine[i*2+1],"big")
    #         print(toHex(i*2), toHex(int.from_bytes(machine[i*2],"big")), toHex(int.from_bytes(machine[i*2+1],"big")), instName(instr))