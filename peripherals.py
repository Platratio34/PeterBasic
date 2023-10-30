from __future__ import annotations
from typing import TYPE_CHECKING
from abc import ABC, abstractmethod

import tkinter as tk
import scrollableFrame as sF

if TYPE_CHECKING:
    from simpleMachine import CPU

class Peripheral(ABC):
    """ Generic CPU peripheral """
    def __init__(self, addr: int):
        self.cpu: CPU|None = None
        self.addr = addr
    
    @abstractmethod
    def preUpdate(self):
        pass
    @abstractmethod
    def update(self):
        pass
    @abstractmethod
    def clear(self):
        pass

class PerConsole(Peripheral):
    """ Peripheral Console """
    def __init__(self, addr: int):
        super().__init__(addr)
        self.text = ''
    
    def setGUI(self, frame: tk.Misc):
        self.frame = sF.VerticalScrolledFrame(frame, width=50, height=10)
        self.textLabel = tk.Label(frame, text='', font=("Consolas", 10), width=50, height=10, anchor=tk.NW, justify=tk.LEFT)
        self.textLabel.pack()
    
    def preUpdate(self):
        if not self.cpu: raise Exception('Must set CPU before pre-updating peripheral')
        self.cpu.peripheral[self.addr] = bytes(0x00)
    
    def update(self):
        if not self.cpu: raise Exception('Must set CPU before updating peripheral')
        v = int.from_bytes(self.cpu.peripheral[self.addr], "big")
        if(v > 0x00):
            self.text += chr(v)
            if(self.textLabel):
                self.textLabel.configure(text=self.text)
    
    def clear(self):
        self.text = ''
        if(self.textLabel):
            self.textLabel.configure(text=self.text)