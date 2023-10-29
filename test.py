size = 24
dec = 0

def toHex(num):
    if num < 10:
        return "{0}".format(num)
    elif num == 10:
        return "A"
    elif num == 11:
        return "B"
    elif num == 12:
        return "C"
    elif num == 13:
        return "D"
    elif num == 14:
        return "E"
    elif num == 15:
        return "F"
    else:
        return "X"
def convertToHex(num, sz):
    hexVal = ""
    numT = num
    for i in reversed(range(0,sz)):
        cv = 16**i
        cn = numT // cv
        numT -= cn * cv
        hexVal += toHex(cn)
        if i>0 and i%2 == 0:
            hexVal += " "
    return hexVal

def convertToBinStr(num, sz):
    numT = num
    binVal = ""
    for i in reversed(range(0,sz)):
        if(numT >= 2**i):
            numT -= 2**i
            binVal += "1"
        else:
            binVal += "0"
        
        if i>0 and i%8 == 0:
            binVal += " "
    return binVal

txt = "Hello World"
size = 8 * len(txt)

bout = ""
hout = ""

for i in range(len(txt)):
    m = len(txt) - i
    m *= 0x100
    v = ord(txt[i])
    dec += m*v
    print("{0}: b={3}, c='{1}', v={2}, d={4}, ba={5}".format(i,txt[i],convertToHex(v,2),m,dec,convertToBinStr(v,8)))
    if i > 0:
        bout += " "
        hout += " "
    bout += convertToBinStr(v,8)
    hout += convertToHex(v,2)

print('{0}_2'.format(bout))

print('0x{0}'.format(hout))

# print('{0}_2'.format(convertToBin(dec,size)))

# print('0x{0}'.format(convertToHex(dec, size//4)))