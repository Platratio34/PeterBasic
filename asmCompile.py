import convert

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

# compile("test.asm")