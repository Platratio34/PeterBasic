from simpleMachine import CPU
import asmCompile as asm
from basicCompile import BasicProgram
import convert
from peripherals import PerConsole
from asmInstructions import strInstr
from BasicCompileError import BasicCompileError

import tkinter as tk
import re
import time
import traceback

cpu = CPU()

# cpu.instToMem([
#     0x1402,
#     0x3417,
#     0xc000
# ])
# cpu.instToMem([
#     0x2032,
#     0x2101,
#     0x2201,
#     0x5112,
#     0xb10c,
#     0xb006,
#     0xc000,
# ])
# cpu.instToMem([
#     0x2004,
#     0x2101,
#     0x4012,
#     0x5112,
#     0xb10c,
#     0xb006,
#     0xc000
# ])
# cpu.instToMem(asm.compile("asm/practice.asm"))
# cpu.instToMem(asm.compile("asm/memTest.asm"))
# cpu.instToMem(asm.compile("asm/test.asm"))
# cpu.instToMem(asm.compile("asm/peripheralTest.asm"))
# cpu.instToMem(asm.compile("asm/printAlpha.asm"))
# cpu.loadMemFromBinFile('bin/printAlpha2.b.bin')))
# cpu.loadMemFromBinFile('bin/test2.b.bin')

# while cpu.step():
#     cpu.dumpA(4,8)
#     # print("")
#     input("")
# cpu.dumpA(4,8)
memFont = ("Consolas", 12)

root = tk.Tk()
# root.geometry("1920x1080")
frame = tk.Frame(root)
frame.pack()

upperFrame = tk.Frame(root)
upperFrame.pack()

upperLeftFrame = tk.Frame(upperFrame)
upperLeftFrame.pack(side=tk.LEFT)

upperRightFrame = tk.Frame(upperFrame)
upperRightFrame.pack(side=tk.RIGHT)

cpuFrame = tk.LabelFrame(upperLeftFrame, text="CPU")
cpuFrame.pack()

instFrame = tk.Frame(cpuFrame)
instFrame.pack()

pgmCtrFrame = tk.LabelFrame(instFrame, text="Adr")
pgmCtrFrame.pack(side=tk.LEFT)
pgmCtrLabel = tk.Label(pgmCtrFrame, text="0x00", font=memFont)
pgmCtrLabel.pack()

cInstFrame = tk.LabelFrame(instFrame, text="Instruction")
cInstFrame.pack(side=tk.LEFT)
cInst = int.from_bytes(b''.join([cpu.memory[cpu.pgmi],cpu.memory[cpu.pgmi+1]]), byteorder="big")
cInstLabel = tk.Label(cInstFrame, text=f'0x{convert.toHex(cInst,4)}', font=memFont)
cInstLabel.pack(side=tk.LEFT)
cInstDLabel = tk.Label(cpuFrame, text=strInstr(cInst), font=memFont, width=40)
cInstDLabel.pack()

stackFrame = tk.LabelFrame(instFrame, text="Stack")
stackFrame.pack(side=tk.LEFT)
stackLabel = tk.Label(stackFrame, text="0x00@-", font=memFont)
stackLabel.pack()

exitCodeFrame = tk.LabelFrame(instFrame, text="Exit Code")
exitCodeFrame.pack(side=tk.LEFT)
exitCodeLabel = tk.Label(exitCodeFrame, text="0", font=memFont)
exitCodeLabel.pack()

cycleFrame = tk.LabelFrame(instFrame, text="Cycles")
cycleFrame.pack(side=tk.LEFT)
cycleLabel = tk.Label(cycleFrame, text="0", font=memFont)
cycleLabel.pack()

# cInst = Label(cpuFrame, text=f"{convert.toHex(cpu.pgmi,2)}| 0x{convert.toHex(cInst,4)} {strInstr(cInst)}")
# cInst.pack()

memPerFrame = tk.Frame(root)
memPerFrame.pack(side=tk.BOTTOM)

memFrame = tk.LabelFrame(memPerFrame, text="Memory")
memFrame.pack(side=tk.LEFT, padx = 5, pady = 5)

memLabels = {}
memR, memC = 16, 16
for i in range(-1,memR):
    f = tk.Frame(memFrame)
    f.pack()
    if i >= 0:
        for j in range(-1,memC):
            if j >= 0:
                mAdr = j + (i*memC)
                # print(f'Making mem {convert.toHex(mAdr,2)}')
                memLabels[mAdr] = tk.Label(f, text=convert.toHex(int.from_bytes(cpu.memory[mAdr], "big"),2), font=memFont)
                memLabels[mAdr].pack(side=tk.LEFT)
            else:
                l = tk.Label(f, text=f'{convert.toHex(i,1)}', font=memFont)
                l.pack(side=tk.LEFT)
    else:
        for j in range(-1,memC):
            if j >= 0:
                mAdr = j + (i*memR)
                l = tk.Label(f, text=f'{convert.toHex(j,1)} ', font=memFont)
                l.pack(side=tk.LEFT)
            else:
                l = tk.Label(f, text=' ', font=memFont)
                l.pack(side=tk.LEFT)

def updateMem():
    for i in range(0,memR):
        # print('i',i)
        for j in range(0,memC):
                # print('j',j)
                mAdr = j + (i*memC)
                # print(f'Updating mem {convert.toHex(mAdr,2)}')
                memLabels[mAdr].configure(text=convert.toHex(int.from_bytes(cpu.memory[mAdr], "big"),2))

perFrame = tk.LabelFrame(memPerFrame, text="Peripherals")
perFrame.pack(side=tk.RIGHT, padx = 5, pady = 5)

perLabels = {}
perR, perC = 16, 16
for i in range(-1,perR):
    f = tk.Frame(perFrame)
    f.pack()
    if i >= 0:
        for j in range(-1,perC):
            if j >= 0:
                mAdr = j + (i*perC)
                # print(f'Making mem {convert.toHex(mAdr,2)}')
                perLabels[mAdr] = tk.Label(f, text=convert.toHex(int.from_bytes(cpu.peripheral[mAdr], "big"),2), font=memFont)
                perLabels[mAdr].pack(side=tk.LEFT)
            else:
                l = tk.Label(f, text=f'{convert.toHex(i,1)}', font=memFont)
                l.pack(side=tk.LEFT)
    else:
        for j in range(-1,perC):
            if j >= 0:
                mAdr = j + (i*perR)
                l = tk.Label(f, text=f'{convert.toHex(j,1)} ', font=memFont)
                l.pack(side=tk.LEFT)
            else:
                l = tk.Label(f, text=' ', font=memFont)
                l.pack(side=tk.LEFT)

console = PerConsole(0x00)
cpu.addPeripheral(console)
consoleFrame = tk.LabelFrame(upperRightFrame, text='Console')
consoleFrame.pack(side=tk.BOTTOM)
console.setGUI(consoleFrame)

def updatePer():
    for i in range(0,perR):
        for j in range(0,perC):
                mAdr = j + (i*perC)
                perLabels[mAdr].configure(text=convert.toHex(int.from_bytes(cpu.peripheral[mAdr], "big"),2))

regFrame = tk.LabelFrame(cpuFrame, text='Registers')
regFrame.pack(side=tk.BOTTOM)
regLabels = {}
for i in range(0,0x10):
    l = tk.Label(regFrame, text=convert.toHex(int.from_bytes(cpu.register[i], "big"),2), font=memFont)
    l.pack(side=tk.LEFT)
    regLabels[i] = l

def updateReg():
    for i in range(0,0x10):
        regLabels[i].configure(text=convert.toHex(int.from_bytes(cpu.register[i], "big"),2))

def update():
    if cpu.pgmi < 0xff:
        cInst = int.from_bytes(b''.join([cpu.memory[cpu.pgmi],cpu.memory[cpu.pgmi+1]]), byteorder="big")
        pgmCtrLabel.configure(text=f'0x{convert.toHex(cpu.pgmi,2)}')
        cInstLabel.configure(text=f'0x{convert.toHex(cInst,4)}')
        cInstDLabel.configure(text=strInstr(cInst))
    
    if len(cpu.stack) > 0: stackLabel.configure(text=f'0x{convert.toHex(int.from_bytes(cpu.stack[-1],"big"))}@{len(cpu.stack)}')
    else: stackLabel.configure(text=f'0x00@-')
    exitCodeLabel.configure(text=str(cpu.exitCode))
    
    cycleLabel.configure(text=str(cpu.en))
    updateMem()
    updatePer()
    updateReg()

def step():
    c = cpu.step()
    # cInst.configure(text=f"{convert.toHex(cpu.pgmi,2)}| 0x{convert.toHex(cInst,4)} {strInstr(cInst)}")
    update()
    return c

run = False
speed = 0.5

lRun = time.time()
runAvg = [-1] * 5
runAvgI = 0
def runningAvg(new):
    global runAvgI
    runAvg[runAvgI] = new
    runAvgI += 1
    if runAvgI >= len(runAvg):
        runAvgI = 0
    return sum(runAvg)/len(runAvg)
def runLoop():
    global run
    global lRun
    if not run:
        print('Stopping run')
        return
    root.after(int((speed)*1000), runLoop)
    # cTime = time.time()
    # rt = cTime - lRun
    # lRun = cTime
    # ra = runningAvg(rt)
    # if ra > 0:
    #     print(f'{1/ra:.1f}/s')
    # print(f'from last: {rt*1000:.0f}ms')
    if not step():
        run = False
    # st = time.time() - cTime
    # print(f'stepTime: {st*1000:.0f}ms')
    # print(f'next: {(speed-st)*1000:.0f}ms')
    # root.after(int((speed-st)*1000), runLoop)

ctrlFrame = tk.LabelFrame(upperLeftFrame, text='Controls')
ctrlFrame.pack(side=tk.TOP)

runFrame = tk.Frame(ctrlFrame)
runFrame.pack()

def startRun():
    global run
    run = True
    global lRun
    lRun = time.time()
    runLoop()
    
def stopRun():
    global run
    run = False

stepButton = tk.Button(runFrame, text='Step', command=step)
stepButton.pack(side=tk.LEFT)

startButton = tk.Button(runFrame, text='Run', command=startRun)
startButton.pack(side=tk.LEFT)
stopButton = tk.Button(runFrame, text='Stop', command=stopRun)
stopButton.pack(side=tk.LEFT)

# speedFrame = tk.LabelFrame(runFrame, text='Speed')
# speedFrame.pack(side=tk.LEFT)
speedLabel = tk.Label(runFrame, text=f'{1/speed:.0f}/s')
speedLabel.pack(side=tk.LEFT, padx=5)

def runSlow():
    global speed
    speed = 1
    speedLabel.configure(text=f'{1/speed:.0f}/s')

def runMed():
    global speed
    speed = 0.5
    speedLabel.configure(text=f'{1/speed:.0f}/s')

def runFast():
    global speed
    speed = 0.1
    speedLabel.configure(text=f'~9/s')

def runVeryFast():
    global speed
    speed = 0.05
    speedLabel.configure(text=f'~17/s')

speedFrame = tk.Frame(ctrlFrame)
speedFrame.pack()
slowButton = tk.Button(speedFrame, text='Slow', command=runSlow)
slowButton.pack(side=tk.LEFT)
medButton = tk.Button(speedFrame, text='Medium', command=runMed)
medButton.pack(side=tk.LEFT)
fastButton = tk.Button(speedFrame, text='Fast', command=runFast)
fastButton.pack(side=tk.LEFT)
fastButton = tk.Button(speedFrame, text='Very Fast', command=runVeryFast)
fastButton.pack(side=tk.LEFT)

fileFrame = tk.LabelFrame(upperRightFrame, text='File')
fileFrame.pack()

fileInput = tk.Entry(fileFrame, width = 50)
fileInput.insert(0, 'basic/func.basic')
fileInput.pack(side=tk.LEFT)
def loadFile():
    file = fileInput.get()
    parts = re.split(r'\.', file)
    if len(parts) == 1:
        print('Could not get file type from file name')
        return
    fileType = parts[-1]
    if fileType == 'bin':
        print('Loading as binary')
        cpu.loadMemFromBinFile(file)
    elif fileType == 'asm':
        print('Loading as assembly')
        cpu.loadMemFromInstr(asm.compile(file))
    elif fileType == 'basic':
        print('Loading as basic')
        program = BasicProgram()
        program.compile(file)
        if not program.compiled:
            print(f'Could not compile basic program {file}')
            if isinstance(program.error, BasicCompileError):
                print(program.compileError)
            else:
                traceback.print_exception(program.error)
            return
        print('Compiled')
        cpu.loadMemFromBytes(program.getMachine())
    else:
        print('Unknown file type: '+fileType)
        return
    
    # cpu.pgmi = 0x0
    # cpu.en = 0
    # console.clear()
    cpu.clear()
    update()
loadButton = tk.Button(fileFrame, text='Load', command=loadFile)
loadButton.pack(side=tk.RIGHT)

root.title('Machine')
root.mainloop()