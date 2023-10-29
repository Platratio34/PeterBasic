from __future__ import annotations
from typing import TYPE_CHECKING
from abc import ABC, abstractmethod
import asmInstructions as asm
from BasicCompileError import *
from convert import toHex

if TYPE_CHECKING:
    from basicCompile import BasicProgram

class Variable:
    def __init__(self, program: BasicProgram, name:str, mAdr:int, rAdr=-1):
        self.pgm = program
        self.name = name
        if mAdr < 0 and name != '__tmp': raise ValueError(f'mAdr must be positive: was {rAdr}')
        self.mAdr = mAdr
        self.rAdr = rAdr
        self.clearable = False
        self.modified = False
        self.scope = 'global'
        if rAdr > -1:
            self.storeToMem()
    
    def __str__(self):
        if self.name == '__tmp': return 'Variable {' + f'temp , rAdr={self.rAdr}, clearable={self.clearable}, modified={self.modified}' + '}'
        return 'Variable {' + f'name="{self.name}", scope={self.scope}, mAdr={toHex(self.mAdr)}, rAdr={self.rAdr}, clearable={self.clearable}, modified={self.modified}' + '}'
    
    def loadToReg(self, reg:int, mark=True):
        if self.rAdr == reg: # already loaded here
            return
        if (reg in self.pgm.regUsed) and self.pgm.regUsed[reg] != self:
            raise BasicRegisterFullError(f'Register {reg} was already in use, could not load {self.name}')
        if self.modified:
            self.storeToMem()
        # self.pgm.add(asm.LOAD_MEM, reg, self.mAdr)
        self.pgm.addChunk(asm.loadMem(reg, self.mAdr))
        if mark:
            self.markReg(reg, True)
            self.clearable = False
            self.rAdr = reg
            self.pgm.print(self.name, 'setting reg', reg)
    
    def storeToMem(self, reg:int|None=None, clear=True):
        if reg == None: # reg not passed
            if self.rAdr == -1:
                self.pgm.print(self.name, 'Not in reg')
                return
            reg = self.rAdr
            self.pgm.print(self.name, reg)
        if reg == -1: # not in a register
            return
        if clear:
            self.clearable = True
            # self.pgm.regUsed[reg] = False # let the program know this register is free now and can be reassigned
            # self.rAdr = -1
        self.pgm.print(self.modified)
        if self.modified: # if we are not modified, then we don't need to store it
            # self.pgm.add(asm.STORE, reg, self.mAdr)
            self.pgm.addChunk(asm.store(reg, self.mAdr))
            self.modified = False
    
    def clearFromReg(self):
        # if reg == None:
        #     reg = self.rAdr
        # if reg == -1:
        #     return # not in any register
        # self.pgm.regUsed[self.rAdr] = False # let the program know this register is free now and can be reassigned
        self.clearable = True
    
    def markReg(self, reg:int|None=None, override=False):
        self.clearable = False
        if reg == None or reg == self.rAdr: return # If no register or same as current
        if override:
            if self.rAdr >= 0: del self.pgm.regUsed[self.rAdr] # Clear previous
            self.rAdr = reg
            self.pgm.print(self.name, 'setting reg', reg)
        self.pgm.regUsed[reg] = self
        self.pgm.print(self.name, 'marking reg', reg)
    
    def inReg(self):
        return self.rAdr != -1
    
    def removeReg(self, reg:int):
        if self.rAdr == reg:
            if self.modified:
                self.storeToMem()
            
            self.clearable = False
            self.rAdr = -1
            # self.pgm.regUsed[reg] = None
            del self.pgm.regUsed[reg]

class Jump:
    """ Jump to named location """
    def __init__(self, adr:int, name:str, lineN:int):
        self.adr = adr
        self.name = name
        self.lineN = lineN
    
    def resolve(self, pgm: BasicProgram):
        """ Resolve the jump. Throws BasicJumpResolveError if not jump point with name was found """
        if self.name not in pgm.jumpPoints:
            raise BasicJumpResolveError(self.name, self.lineN)
        pgm.machine[self.adr+1] = pgm.jumpPoints[self.name].to_bytes(1, "big")
        return True


class Chunk(ABC):
    """ Basic asm chunk """
    def __init__(self):
        pass

    def __str__(self):
        return 'Chunk'
    
    @abstractmethod
    def compile(self, pgm: BasicProgram):
        pass

class LabelChunk(Chunk):
    """ Jump label chunk """
    def __init__(self, name: str):
        super().__init__()
        self.name = name
    
    def __str__(self):
        return f'LabelChunk "{self.name}"'
    
    def compile(self, pgm: BasicProgram):
        pgm._addJP(self.name)

class JumpChunk(Chunk):
    def __init__(self, jump: int, reg: int, dest: str|LabelChunk):
        super().__init__()
        self.jump = jump
        self.reg = reg
        if isinstance(dest, str):
            self.dest = dest
        elif isinstance(dest, LabelChunk):
            self.dest = dest.name
    
    def __str__(self):
        if self.jump == asm.JUMP:
            return f'JumpChunk r[{toHex(self.reg,1)}] == r0 --> "{self.dest}"'
        elif self.jump == asm.JUMP_L:
            return f'JumpChunk r[{toHex(self.reg,1)}] < r0 --> "{self.dest}"'
        return f'JumpChunk {asm.toName(self.jump)} r[{toHex(self.reg,1)}] "{self.dest}"'
    
    def compile(self, pgm: BasicProgram):
        pgm._addJump(self.jump, self.reg, self.dest)

class IfChunk(Chunk):
    """ If chunk """
    def __init__(self, reg: int, comp: str, dest: str|LabelChunk):
        super().__init__()
        self.reg = reg
        self.comp = comp
        if isinstance(dest, str):
            self.dest = dest
        elif isinstance(dest, LabelChunk):
            self.dest = dest.name
    
    def compile(self, pgm: BasicProgram):
        if self.comp == '==':
            pgm._addJump(asm.JUMP, self.reg, self.dest)
        elif self.comp == '!=':
            d2 = pgm.getNextJump()
            pgm._addJump(asm.JUMP, self.reg, d2)
            pgm._addGoto(self.dest)
            pgm._addJP(d2)
        elif self.comp == '<':
            pgm._addJump(asm.JUMP_L, self.reg, self.dest)
        elif self.comp == '<=':
            pgm._addJump(asm.JUMP_L, self.reg, self.dest)
            pgm._addJump(asm.JUMP, self.reg, self.dest)
        elif self.comp == '>=':
            d2 = pgm.getNextJump()
            pgm._addJump(asm.JUMP_L, self.reg, d2)
            pgm._addGoto(self.dest)
            pgm._addJP(d2)
        elif self.comp == '>':
            d2 = pgm.getNextJump()
            pgm._addJump(asm.JUMP_L, self.reg, d2)
            pgm._addJump(asm.JUMP, self.reg, self.dest)
            pgm._addGoto(self.dest)
            pgm._addJP(d2)

class IfInvertChunk(IfChunk):
    def compile(self, pgm: BasicProgram):
        if self.comp == '!=':
            pgm._addJump(asm.JUMP, self.reg, self.dest)
        elif self.comp == '==':
            d2 = pgm.getNextJump()
            pgm._addJump(asm.JUMP, self.reg, d2)
            pgm._addGoto(self.dest)
            pgm._addJP(d2)
        elif self.comp == '>=':
            pgm._addJump(asm.JUMP_L, self.reg, self.dest)
        elif self.comp == '>':
            pgm._addJump(asm.JUMP_L, self.reg, self.dest)
            pgm._addJump(asm.JUMP, self.reg, self.dest)
        elif self.comp == '<=':
            d2 = pgm.getNextJump()
            pgm._addJump(asm.JUMP_L, self.reg, d2)
            pgm._addGoto(self.dest)
            pgm._addJP(d2)
        elif self.comp == '<':
            d2 = pgm.getNextJump()
            pgm._addJump(asm.JUMP_L, self.reg, d2)
            pgm._addJump(asm.JUMP, self.reg, self.dest)
            pgm._addGoto(self.dest)
            pgm._addJP(d2)

class GotoChunk(Chunk):
    def __init__(self, dest: str|LabelChunk):
        super().__init__()
        if isinstance(dest, str):
            self.dest = dest
        elif isinstance(dest, LabelChunk):
            self.dest = dest.name
    
    def __str__(self):
        return f'GotoChunk "{self.dest}"'

    def compile(self, pgm: BasicProgram):
        pgm._addGoto(self.dest)

class GotoFuncChunk(GotoChunk):
    def __str__(self):
        return f'GotoFuncChunk "{self.dest}"'
    
    def compile(self, pgm: BasicProgram):
        pgm._addB(asm.load(0x0, len(pgm.machine)+6))
        pgm._addB(asm.moveToSpec(0x0, asm.R_STACK))
        pgm._addGoto(self.dest)
class ExitFuncChunk(Chunk):
    def __str__(self):
        return f'ExitFuncChunk'
    def compile(self, pgm: BasicProgram):
        pgm._addB(asm.stackToPgmi())

class AsmChunk(Chunk):
    def __init__(self, by: tuple[bytes, bytes]):
        super().__init__()
        self.by = by
    
    def __str__(self):
        return f'AsmChunk: {asm.strInstr(self.by)}'
    
    def compile(self, pgm: BasicProgram):
        pgm._addB(self.by)

class HaltChunk(Chunk):
    def compile(self, pgm: BasicProgram):
        pgm._addB(asm.halt())
    
    def __str__(self):
        return f'HaltChunk'


class CodeBlock:
    """ Generic code block. Has main block and end """
    def __init__(self, pgm: BasicProgram, name:str, lineN: int):
        self.pgm = pgm
        self.name = name
        self.lineN = lineN
        self.hasMain = False
        self.mainLabel = LabelChunk(self.name+':main')
        self.ended = False
        self.endLabel = LabelChunk(self.name+':end')
        self.type = 'Code block'
    
    def addMain(self):
        if self.hasMain:
            raise BasicCompileError(f'{self.type} already had a main')
        # self.pgm._addJP(self.name+':main')
        self.pgm.addChunk(self.mainLabel)
        self.hasMain = True
    def gotoMain(self):
        # self.pgm._addGoto(self.name+':main', lineN)
        self.pgm.addChunk(GotoChunk(self.mainLabel))
    def jumpMain(self, jump:int, reg:int):
        # self.pgm._addJump(jump, reg, self.name+':main', lineN)
        self.pgm.addChunk(JumpChunk(jump, reg, self.mainLabel))

    def addEnd(self):
        if self.ended:
            raise BasicCompileError(f'{self.type} was already ended')
        self.ended = True
        # self.pgm._addJP(self.name+':end')
        self.pgm.addChunk(self.endLabel)
    def gotoEnd(self):
        # self.pgm._addGoto(self.name+':end', lineN)
        self.pgm.addChunk(GotoChunk(self.endLabel))
    def jumpEnd(self, jump:int, reg:int):
        # self.pgm._addJump(jump, reg, self.name+':end', lineN)
        self.pgm.addChunk(JumpChunk(jump, reg, self.endLabel))

class IfStatement(CodeBlock):
    """ Code block for if statement. Has else block """
    def __init__(self, pgm: BasicProgram, name:str, lineN: int):
        super().__init__(pgm, name, lineN)
        self.hasElse = False
        self.elseLabel = LabelChunk(self.name+':else')
        self.type = 'If statement'

    def addElse(self):
        if self.hasElse:
            raise BasicCompileError('If statement already had an else')
        # self.pgm._addJP(self.name+':else')
        self.pgm.addChunk(self.elseLabel)
        self.hasElse = True 
    def gotoElse(self):
        # self.pgm._addGoto(self.name+':else', lineN)
        self.pgm.addChunk(GotoChunk(self.elseLabel))
    def jumpElse(self, jump:int, reg:int):
        # self.pgm._addJump(jump, reg, self.name+':else', lineN)
        self.pgm.addChunk(JumpChunk(jump, reg, self.elseLabel))
    
    def addEnd(self): # Override so end is marked as else if no else block existed
        if self.ended:
            raise BasicCompileError('If statement was already ended')
        self.ended = True
        if self.hasElse:
            # self.pgm._addJP(self.name+':end')
            self.pgm.addChunk(self.endLabel)
        else:
            # self.pgm._addJP(self.name+':else')
            self.pgm.addChunk(self.elseLabel)

class Loop(CodeBlock):
    """ Code block for while or for loop. Has check block """
    def __init__(self, pgm: BasicProgram, name:str, lineN: int):
        super().__init__(pgm, name, lineN)
        self.checked = False
        self.checkLabel = LabelChunk(self.name+':check')
        self.type = 'Loop'
    
    def addCheck(self):
        if self.checked:
            raise BasicCompileError('Loop already had a check')
        self.checked = True
        # self.pgm._addJP(self.name+':check')
        self.pgm.addChunk(self.checkLabel)
    def gotoCheck(self):
        # self.pgm._addGoto(self.name+':check', lineN)
        self.pgm.addChunk(GotoChunk(self.checkLabel))

class Function(CodeBlock):
    
    def __init__(self, pgm: BasicProgram, name:str, lineN: int):
        super().__init__(pgm, 'func_'+name, lineN)
        self.chunks: list[Chunk] = []
        self.variables: dict[str, Variable] = {}
        self.regUsed: dict[str, Variable] = {}
    
    # def addMain(self):
    #     super().gotoEnd()
    #     super().addMain()
    
    def gotoMain(self):
        # self.pgm.addChunk(asm.pgmToStack())
        self.pgm.addChunk(GotoFuncChunk(self.mainLabel))
        # super().gotoMain()
    
    def addEnd(self):
        self.addExit()
        super().addEnd()
    
    def addExit(self):
        # self.pgm.addChunk(asm.stackToPgmi())
        self.pgm.addChunk(ExitFuncChunk())

    def addChunk(self, chunk: Chunk):
        self.chunks.append(chunk)
    def compileChunks(self):
        for chunk in self.chunks:
            self.pgm.print(toHex(len(self.pgm.machine)), chunk)
            chunk.compile(self.pgm)