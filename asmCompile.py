import convert
import asmInstructions as asm
import re

asmInstructions = [
    "",
    "LOAD_MEM",
    "LOAD",
    "STORE",
    "MOVE",
    "ADD_S",
    "ADD_F",
    "OR",
    "AND",
    "XOR",
    "ROTATE",
    "JUMP",
    "HALT",
    "STORE_P",
    "LOAD_P",
    "JUMP_L"
]

def toMachine(asm):
    m = 0x0000
    op = 0
    for i in range(len(asmInstructions)):
        # print("{2}: '{0}' ?= '{1}'".format(asmInstructions[i], asm[0], i))
        if(asmInstructions[i] == asm[0]):
            op = i
            break
    
    m = op * 0x1000
    # print("'{0}' op:{1}".format(asm[0],op))

    if(op == 0x1 or op == 0x2 or op == 0x3 or op == 0xd or op == 0xe):
        m += int(asm[1],16) * 0x0100
        m += int(asm[2],16) * 0x0001
    elif(op == 0x4):
        m += int(asm[1],16) * 0x0010
        m += int(asm[2],16) * 0x0001
    elif(op >= 0x5 and op <= 9):
        m += int(asm[1],16) * 0x0100
        m += int(asm[2],16) * 0x0010
        m += int(asm[3],16) * 0x0001
    elif(op == 0xA):
        m += int(asm[1],16) * 0x0100
        m += int(asm[2],16) * 0x0001
    elif(op == 0xB or op == 0xF):
        m += int(asm[1],16) * 0x0100
        return m, asm[2]

    # if len(asm) >= 2:
    #     m += int(asm[1]) * 0x0100
    # if len(asm) >= 3:
    #     m += int(asm[2]) * 0x0010
    # if len(asm) >= 4:
    #     m += int(asm[3]) * 0x0001
    return m,None

def compile(filename):
    f = open(filename, "r")
    lines = f.read().split("\n")
    machine = []
    jp = []
    for i in range(len(lines)):
        line = lines[i].split(" ")
        if(len(line)) == 0:
            continue
        # if(len(line)) == 1:
        #     print("op:{0}".format(line[0]))
        #     continue
        # if(len(line)) == 2:
        #     print("op:{0} p0:{1}".format(line[0], line[1]))
        #     continue
        # if(len(line)) == 3:
        #     print("op:{0} p0:{1} p1:{2}".format(line[0], line[1] ,line[2]))
        #     continue
        # print("op:{0} p0:{1} p1:{2} p2:{3}".format(line[0], line[1], line[2], line[3]))
        if(":" in line[0]):
            jp.append([len(machine),line[0][1:]])
            # print("Recorded jp '{0}' at {1}".format(line[0][1:], len(machine)))
        else:
            m,adr = toMachine(line)
            # for j in range(len(jp)):
            #     if(adr == jp[j][1]):
            #         m += jp[j][0]
            # print("{0} => {1}".format(lines[i],convert.toHex(m,4)))
            if(adr == None):
                machine.append(m)
                # print("{0} => {1}".format(lines[i],convert.toHex(m,4)))
            else:
                machine.append([m,adr])
                # print("{0} => {1} to {1}".format(lines[i],convert.toHex(m,4),adr))
    
    for i in range(len(machine)):
        if isinstance(machine[i], list):
            m = machine[i][0]
            adr = machine[i][1]
            for j in range(len(jp)):
                if(adr == jp[j][1]):
                    m += jp[j][0]*2
            machine[i] = m
            # print("Updated jump for {0} to line {1}".format(adr,convert.toHex(m&0x00ff,2)))
    
    return machine

def asmCompile(filename: str):
    with open(filename) as f:
        lines = f.readlines()
        for i in range(len(lines)):
            lines[i] = lines[i].rstrip()
    
    machine: list[bytes] = []
     
    def add(by: tuple[bytes, bytes]):
        bh, bl = by
        # print(f'Adding {asm.strInstr(by)}')
        machine.append(bh)
        machine.append(bl)
    
    labels: dict[str, int] = {}
    jumps: list[tuple[str, int, int]] = []
    
    for i in range(len(lines)):
        line = lines[i]
        line = re.split(r';', line)[0]
        if (not line) or len(line) <= 0:
            continue
        
        parts = line.split(' ')
        
        op = parts[0]
        
        if line[0] == ':': # label
            labels[parts[0][1:]] = len(machine)
            # print(f'Found label {parts[0][1:]} at {convert.toHex(len(machine))}')
            continue
        
        if op == 'HALT':
            add(asm.halt())
        elif op == 'GOTO':
            if len(parts) != 2: return None, f'Invalid number of arguments for GOTO; Should be "GOTO :[label]"; Line {i}: "{lines[i]}"'
            if parts[1][0] == ':':
                parts[1] = parts[1][1:]
            jumps.append((parts[1], len(machine), i))
            add(asm.goto(0x00))
        elif op == 'JUMP' or op == 'JUMP_L':
            if len(parts) == 2 and op == 'JUMP':
                if parts[1][0] == ':':
                    parts[1] = parts[1][1:]
                jumps.append((parts[1], len(machine), i))
                add(asm.goto(0x00))
                continue
            if len(parts) < 3:return None, f'Invalid number of arguments for {op}; Should be "{op} r[reg] :[label]"; Line {i}: "{lines[i]}"'
            reg = parts[1]
            dest = parts[2]
            if dest[0] == ':':
                dest = dest[1:]
            
            if reg[0] == 'r':
                jumps.append((dest, len(machine), i))
                if op == 'JUMP_L':
                    add(asm.jumpLess(int(reg[1:],16), 0x00))
                else:
                    add(asm.jump(int(reg[1:],16), 0x00))
            else: return None, f'Must compare with register; Should be "{op} r[reg] :[label]"; Line {i}: "{lines[i]}"'
        elif op == 'LOAD_MEM':
            if len(parts) != 3: return None, f'Invalid number of arguments for {op}; Should be "{op} r[reg] m[mem]"; Line {i}: "{lines[i]}"'
            reg = parts[1]
            mem = parts[2]
            
            if reg[0] == 'r':
                reg = int(reg[1:], 16)
            else:
                return None, f'Must load to register; Should be "{op} r[reg] m[mem]"; Line {i}: "{lines[i]}"'
            
            if mem[0] == 'm':
                mem = int(mem[1:], 16)
            else: return None, f'Must load from memory; Should be "{op} r[reg] m[mem]"; Line {i}: "{lines[i]}"'
            
            add(asm.loadMem(reg, mem))
        elif op == 'LOAD':
            if len(parts) != 3: return None, f'Invalid number of arguments for {op}; Should be "{op} r[reg] [value]"; Line {i}: "{lines[i]}"'
            reg = parts[1]
            val = parts[2]
            
            if reg[0] == 'r':
                reg = int(reg[1:], 16)
            else:
                return None, f'Must load to register; Should be "{op} r[reg] [value]"; Line {i}: "{lines[i]}"'
            
            if val[0:2] == '0x':
                val = int(val, 16)
            else:
                return None, f'Value must be number; Should be "{op} r[reg] [value]"; Line {i}: "{lines[i]}"'
            
            add(asm.load(reg, val))
        elif op == 'STORE':
            if len(parts) != 3: return None, f'Invalid number of arguments for {op}; Should be "{op} r[reg] m[mem]"; Line {i}: "{lines[i]}"'
            reg = parts[1]
            mem = parts[2]
            
            if reg[0] == 'r':
                reg = int(reg[1:], 16)
            else:
                return None, f'Must store from register; Should be "{op} r[reg] m[mem]"; Line {i}: "{lines[i]}"'
            
            if mem[0] == 'm':
                mem = int(mem[1:], 16)
            else:
                return None, f'Must store to memory; Should be "{op} r[reg] m[mem]"; Line {i}: "{lines[i]}"'
            
            add(asm.store(reg, mem))
        elif op == 'MOVE':
            if len(parts) != 3: return None, f'Invalid number of arguments for {op}; Should be "{op} r[reg] m[mem]"; Line {i}: "{lines[i]}"'
            src = parts[1]
            dest = parts[2]
            
            opt = 0x0
            if src[0] == 'r':
                src = int(src[1:], 16)
            elif src[0:2] == 'R_':
                opt += 0x1
                if src == 'R_PGMI':
                    src = asm.R_PGMI
                elif src == 'R_STACK':
                    src = asm.R_STACK
                elif src == 'R_EXIT':
                    src = asm.R_EXIT
                else:
                    return None, f'Unknown register: "{dest}"; Line {i}: "{lines[i]}"'
            else:
                return None, f'Must move from register; Should be "{op} r[src] r[dest]"; Line {i}: "{lines[i]}"'
            
            if dest[0] == 'r':
                dest = int(dest[1:], 16)
            elif dest[0:1] == 'R_':
                opt += 0x2
                if dest == 'R_PGMI':
                    dest = asm.R_PGMI
                elif dest == 'R_STACK':
                    dest = asm.R_STACK
                elif dest == 'R_EXIT':
                    dest = asm.R_EXIT
                else:
                    return None, f'Unknown register: "{dest}"; Line {i}: "{lines[i]}"'
            else:
                return None, f'Must move to register; Should be "{op} r[src] r[dest]"; Line {i}: "{lines[i]}"'
            
            add(asm.move(src, dest, opt))
        elif op == 'ADD' or op == 'ADD_S' or op == 'OR' or op == 'AND' or op == "XOR":
            if len(parts) != 4: return None, f'Invalid number of arguments for {op}; Should be "{op} r[reg] r[op1] r[op2]"; Line {i}: "{lines[i]}"'
            reg = parts[1]
            op1 = parts[2]
            op2 = parts[3]
            
            if reg[0] == 'r':
                reg = int(reg[1:], 16)
            else: return None, f'Must store to register; Should be "{op} r[reg] r[op1] r[op2]"; Line {i}: "{lines[i]}"'
            
            if op1[0] == 'r':
                op1 = int(op1[1:], 16)
            else: return None, f'Must read from register; Should be "{op} r[reg] r[op1] r[op2]"; Line {i}: "{lines[i]}"'
            
            if op2[0] == 'r':
                op2 = int(op2[1:], 16)
            else: return None, f'Must read from register; Should be "{op} r[reg] r[op1] r[op2]"; Line {i}: "{lines[i]}"'
            
            if op == 'AND' or op == 'AND_S':
                add(asm.addS(reg, op1, op2))
            elif op == 'OR':
                add(asm.orB(reg, op1, op2))
            elif op == 'AND':
                add(asm.andB(reg, op1, op2))
            elif op == 'XOR':
                add(asm.xorB(reg, op1, op2))
        elif op == 'ROTATE':
            if len(parts) != 3: return None, f'Invalid number of arguments for {op}; Should be "{op} r[reg] [value]"; Line {i}: "{lines[i]}"'
            reg = parts[1]
            opr = parts[2]
            
            if reg[0] == 'r':
                reg = int(reg[1:], 16)
            else: return None, f'Must rotate register; Should be "{op} r[reg] [value]"; Line {i}: "{lines[i]}"'
            
            if opr[0:2] == '0x':
                opr = int(opr, 16)
            else: return None, f'Value must be number; Should be "{op} r[reg] [value]"; Line {i}: "{lines[i]}"'
            
            add(asm.rotate(reg, opr))
        elif op == 'LOAD_P':
            if len(parts) != 3: return None, f'Invalid number of arguments for {op}; Should be "{op} r[reg] p[per]"; Line {i}: "{lines[i]}"'
            reg = parts[1]
            per = parts[2]
            
            if reg[0] == 'r':
                reg = int(reg[1:], 16)
            else:
                return None, f'Must load to register; Should be "{op} r[reg] p[per]"; Line {i}: "{lines[i]}"'
            
            if per[0] == 'p':
                per = int(per[1:], 16)
            else:
                return None, f'Must load from peripheral; Should be "{op} r[reg] p[per]"; Line {i}: "{lines[i]}"'
            
            add(asm.loadPer(reg, per))
        elif op == 'STORE_P':
            if len(parts) != 3: return None, f'Invalid number of arguments for {op}; Should be "{op} r[reg] p[per]"; Line {i}: "{lines[i]}"'
            reg = parts[1]
            per = parts[2]
            
            if reg[0] == 'r':
                reg = int(reg[1:], 16)
            else: return None, f'Must store from register; Should be "{op} r[reg] p[per]"; Line {i}: "{lines[i]}"'
            
            if per[0] == 'p':
                per = int(per[1:], 16)
            else: return None, f'Must store to peripheral; Should be "{op} r[reg] p[per]"; Line {i}: "{lines[i]}"'
            
            add(asm.storePer(reg, per))
        else:
            return None, f'Unknown instruction "{op}"; Line {i}: "{lines[i]}"'
    for jump in jumps:
        name, index, lineN = jump
        if not name in labels: return None, f'Unknown jump point: "{name}"; Line {lineN}: "{lines[lineN]}"'
        # print(f'Resolving jump {name} to {convert.toHex(labels[name])}')
        machine[index+1] = bytes([labels[name]])
    return machine, None

def asmCompileToFile(srcFile: str, destFile: str):
    print(f'Compiling {srcFile} . . .')
    machine, error = asmCompile(srcFile)
    if not machine:
        print(f'Could not compile {srcFile}')
        print(error)
        return
    with open(destFile, 'wb') as f:
        for by in machine:
            f.write(by)
    print(f'Compiled {srcFile} to {destFile}')

if __name__ == '__main__':
    asmCompileToFile('asm/test.asm', 'bin/test.a.bin')

# compile("test.asm")