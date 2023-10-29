import convert
from peripherals import Peripheral
import asmInstructions as asm

# def dump():
#     dumpA(8,32)

# def dumpA(w,h):
#     print("-- Register and Memory Dump --")
#     for i in range(4):
#         string = ""
#         for j in range(4):
#             if j > 0:
#                 string += ", "
#             # str += convert.toHex(registers[j+(i*4)]&0xffff,2)
#             string += "r{0}={1}".format(convert.toHex(j+(i*4),1),convert.toHex(int.from_bytes(registers[j+(i*4)], "big"),2))
#         print(string)
#     print("")
#     for i in range(w):
#         string = ""
#         for j in range(h):
#             if j > 0:
#                 string += ", "
#             # str += convert.toHex(registers[j+(i*4)]&0xffff,2)
#             string += "m{0}={1}".format(convert.toHex(j+(i*h),2),convert.toHex(int.from_bytes(mem[j+(i*h)], "big"),2))
#         print(string)

def instName(inst, instL = None):
    if instL != None:
        inst = inst*0x100 + instL
    if isinstance(inst, bytes):
        inst = int.from_bytes(inst, "big")
    op = (inst&0xf000) >> 12
    reg = (inst&0x0f00) >> 8
    opr = (inst&0x00ff)
    opr1 = (inst&0x00f0) >> 4
    opr2 = (inst&0x000f)
    if(op == 0x1):
        return f'LOAD_MEM m{convert.toHex(opr,2)} --> r{convert.toHex(reg,1)}'
    elif(op == 0x2):
        return f'LOAD 0x{convert.toHex(opr,2)} --> r{convert.toHex(reg,1)}'
    elif(op == 0x3):
        return f"STORE r{convert.toHex(reg,1)} --> m{convert.toHex(opr,2)}"
    elif(op == 0x4):
        return f"MOVE r{convert.toHex(opr1,1)} --> r{convert.toHex(opr2,1)}"
    elif(op == 0x5):
        return f"ADD_S r{convert.toHex(opr1,1)} + r{convert.toHex(opr2,1)} --> r{convert.toHex(reg,1)}"
    elif(op == 0x6):
        return f"ADD_F r{convert.toHex(opr1,1)} + r{convert.toHex(opr2,1)} ->> r{convert.toHex(reg,1)}"
    elif(op == 0x7):
        return f"OR r{convert.toHex(opr1,1)} | r{convert.toHex(opr2,1)} --> r{convert.toHex(reg,1)}"
    elif(op == 0x8):
        return f"AND r{convert.toHex(opr1,1)} & r{convert.toHex(opr2,1)} --> r{convert.toHex(reg,1)}"
    elif(op == 0x9):
        return f"XOR r{convert.toHex(opr1,1)} ^ r{convert.toHex(opr2,1)} -- > r{convert.toHex(reg,1)}"
    elif(op == 0xa):
        return f"ROTATE r{convert.toHex(reg,1)} by 0x{convert.toHex(opr2,1)} --> r{convert.toHex(reg,1)}"
    elif(op == 0xb):
        return f"JUMP IF r{convert.toHex(reg,1)} = r0 TO i{convert.toHex(opr,2)}"
    elif(op == 0xc):
        return "HALT"
    elif(op == 0xd):
        return f"STORE_P r{convert.toHex(reg,1)} --> p{convert.toHex(opr,2)}"
    elif(op == 0xe):
        return f"LOAD_P p{convert.toHex(opr,2)} --> r{convert.toHex(reg,1)}"
    elif(op == 0xf):
        return f"JUMP IF r{convert.toHex(reg,1)} < r0 TO i{convert.toHex(opr,2)}"
    else:
        return "UNKNOWN"

class CPU:
    
    def __init__(self, pr=False):
        self.pr = pr
        self.mxEn = 0x10000
        self.peripherals: list[Peripheral] = []
        self.reset()
    
    def reset(self):
        self.register = [bytes(1)] * 0x10
        self.memory = [bytes(1)] * 0x100
        self.peripheral = [bytes(1)] * 0x100
        
        self.pgmi = 0x00
        self.en = 0

        self.stack = []
        self.exitCode = -1
        for per in self.peripherals:
            per.clear()
    
    def clear(self):
        self.pgmi = 0x00
        self.en = 0
        self.stack = []
        self.exitCode = -1
        for per in self.peripherals:
            per.clear()
    
    def step(self):
        for per in self.peripherals:
            per.preUpdate()
            
        self.en += 1
        rt = False
        if self.pgmi < 0xff and self.en < self.mxEn:
            cInst = int.from_bytes(b''.join([self.memory[self.pgmi],self.memory[self.pgmi+1]]), byteorder="big")
            self.pgmi += 2
            if self.pr: print("{0}| 0x{1} {2}".format(convert.toHex(self.pgmi,2),convert.toHex(cInst,4),instName(cInst)))
            rt = self._processInst(cInst)
        elif self.en >= self.mxEn:
            if self.pr: print("Max execute reached, terminating")
        else:
            if self.pr: print("End of memory reached without HALT")
        
        for per in self.peripherals:
            per.update()
        
        return rt
    
    def _processInst(self, inst: int):
        op = (inst&0xf000) >> 12
        reg = (inst&0x0f00) >> 8
        opr = (inst&0x00ff)
        opr1 = (inst&0x00f0) >> 4
        opr2 = (inst&0x000f)
        # print("{0}: {1},{2},{3}".format(op,reg,opr1,opr2))

        if(op == asm.LOAD_MEM): # LOAD_MEM
            self.register[reg] = self.memory[opr]
        elif(op == asm.LOAD): # LOAD
            self.register[reg] = bytes([opr])
        elif(op == asm.STORE): # STORE
            self.memory[opr] = self.register[reg]
        elif(op == asm.MOVE): # MOVE
            if reg == 0x0: # Standard registers
                self.register[opr2] = self.register[opr1]
            elif reg == 0x1: # From spec to normal
                if opr1 == asm.R_PGMI:
                    self.register[opr2] = bytes([self.pgmi])
                elif opr1 == asm.R_STACK:
                    if len(self.stack) > 0:
                        self.register[opr2] = self.stack.pop()
                    else:
                        self.register[opr2] = bytes([0x00])
                elif opr1 == asm.R_EXIT:
                    self.register[opr2] = bytes([self.exitCode])
            elif reg == 0x2: # From normal to spec
                val = int.from_bytes(self.register[opr1], "big")
                if opr2 == asm.R_PGMI:
                    self.pgmi = val
                elif opr2 == asm.R_STACK:
                    self.stack.append(self.register[opr1])
                elif opr2 == asm.R_EXIT:
                    self.exitCode = val
            elif reg == 0x3: # From spec to spec
                val = bytes([0x00])
                if opr1 == asm.R_PGMI:
                    val = bytes([self.pgmi])
                elif opr1 == asm.R_STACK:
                    if len(self.stack) > 0:
                        val = self.stack.pop()
                elif opr1 == asm.R_EXIT:
                    val = bytes([self.exitCode])
                if opr2 == asm.R_PGMI:
                    self.pgmi = int.from_bytes(val, "big")
                elif opr2 == asm.R_STACK:
                    if len(self.stack) <= 0xff:
                        self.stack.append(val)
                    else:
                        self.exitCode = 1
                        return False
                elif opr2 == asm.R_EXIT:
                    self.exitCode = int.from_bytes(val, "big")
        elif(op == asm.ADD_S): # ADD_S 2cp add
            b0 = self.register[opr1]
            b1 = self.register[opr2]
            ot = b0[0] + b1[0]
            self.register[reg] = bytes([ot&0xff])
        elif(op == asm.ADD_F): # ADD_F 8b float add
            # registers
            pass
        elif(op == asm.OR): # OR
            self.register[reg] = bytes([self.register[opr1][0] | self.register[opr2][0]])
        elif(op == asm.AND): # AND
            self.register[reg] = bytes([self.register[opr1][0] & self.register[opr2][0]])
        elif(op == asm.XOR): # XOR
            self.register[reg] = bytes([self.register[opr1][0] ^ self.register[opr2][0]])
        elif(op == asm.ROTATE): # ROTATE
            tmp = (int.from_bytes(self.register[reg], "big")&0x1) << 7
            out = (int.from_bytes(self.register[reg], "big") >> 0x1) + tmp
            self.register[reg] = bytes([out])
        elif(op == asm.JUMP): # JUMP
            if(self.register[0] == self.register[reg]):
                self.pgmi = opr
        elif(op == asm.HALT): # HALT
            return False
        elif(op == asm.STORE_P): # STORE_P
            self.peripheral[opr] = self.register[reg]
        elif(op == asm.LOAD_P): # LOAD_P
            self.register[reg] = self.peripheral[opr]
        elif(op == asm.JUMP_L): # JUMP_L
            if(self.register[reg] < self.register[0]):
                self.pgmi = opr
        return True
    
    def loadMemFromInstr(self, instructions: list[int]):
        for i in range(len(instructions)):
            mi = i*2
            self.memory[mi] = bytes([(instructions[i]&0xff00)>>8])
            self.memory[mi+1] = bytes([instructions[i]&0xff])
    
    def loadMemFromBytes(self, arr: list[bytes]):
        for i in range(len(arr)):
            self.memory[i] = arr[i]
    
    def loadMemFromBinFile(self, filename: str):
        with open(filename, 'rb') as file:
            i = 0
            while True:
                c = file.read(1)
                if(not c):
                    break
                # print(convert.toHex(int.from_bytes(c, "big"),2))
                self.memory[i] = c
                i += 1
    
    def addPeripheral(self, peripheral: Peripheral):
        peripheral.cpu = self
        self.peripherals.append(peripheral)