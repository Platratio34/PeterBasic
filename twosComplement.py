dinp = int(input())

def toBinArr(num, sz):
    numT = num
    arr = [False]*sz
    for i in reversed(range(0,sz)):
        if(numT >= 2**i):
            numT -= 2**i
            arr[i] = True
        else:
            arr[i] = False
    return arr

def toBinStr(arr):
    bimStr = ""
    for i in reversed(range(len(arr))):
        bimStr += "1" if arr[i] else "0"
        if i > 0 and i%4 == 0:
            bimStr += " "
    return bimStr
def decToBin(num, sz):
    return toBinStr(toBinArr(num,sz))

def binAdd(b0, b1):
    carry = False
    o = [False] * len(b0)
    for i in range(len(b0)):
        c = False
        if b0[i] and b1[i]:
            c = True
            o[i] = carry
        elif (b0[i] or b1[i]) and carry:
            o[i] = False
            c = True
        else:
            o[i] = b0[i] or b1[i] or carry
        carry = c
    return o


def toTows(num,sz):
    if num >= 2**sz-1 or num < -(2**sz-1):
        return None
    if num < 0:
        u = toBinArr(abs(num),sz)
        for i in range(len(u)):
            u[i] = not u[i]
        s = binAdd(u,toBinArr(0x1,8))

        return s
    else:
        return toBinArr(num,sz)

print("{0}_10 = {1}_2s".format(dinp,toBinStr(toTows(dinp,8))))