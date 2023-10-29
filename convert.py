def toHexD(num):
    if num >=0 and num < 10:
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
        raise ValueError(f'num must be between 0-15 (inclusive): was {num}')
        return "X"
def toHex(num, sz=2):
    if num < 0:
        raise ValueError(f'num must be positive: was {num}')
    if num >= 16**sz:
        raise ValueError(f'num must be less than 16^(sz) = 16^{sz} = {16**sz}: was {num}')
    hexStr = ""
    numT = num
    for i in reversed(range(0,sz)):
        cv = 0x10**i
        cn = numT // cv
        numT -= cn * cv
        hexStr += toHexD(cn)
        if i>0 and i%4 == 0:
            hexStr += " "
    return hexStr

def toBinStr(num, sz):
    numT = num
    binStr = ""
    for i in reversed(range(0,sz)):
        if(numT >= 2**i):
            numT -= 2**i
            binStr += "1"
        else:
            binStr += "0"
        
        if i>0 and i%8 == 0:
            binStr += " "
    return binStr

if __name__ == '__main__':
    print(toHex(0x1234, 4))