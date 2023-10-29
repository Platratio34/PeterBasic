class BasicCompileError(Exception):
    """ Generic Basic compiler error """
    def __init__(self, error: str, lineN: int = -1, eType: str = 'Compile'):
        self.error = error
        self.lineN = lineN
        self.line: str|None = None
        self.eType = eType
        super().__init__(error)
    
    def setLine(self, lineN: int, line: str):
        self.lineN = lineN
        self.line = line
    
    def toString(self, lineN: int, line: str):
        if lineN == -1:
            lineN = self.lineN
        if lineN == -1:
            return f'{self.eType} Error: {self.error}'
        return f'{self.eType} Error at line {lineN+1}: {self.error}; Line: "{line}"'
    
    def __str__(self):
        if self.lineN and self.line:
            return self.toString(self.lineN, self.line)
        return f'{self.eType} Error: {self.error}'

# Could not parse line
class BasicParseError(BasicCompileError):
    """ Basic compiler error on parse failure """
    def __init__(self, error: str, lineN: int = -1):
        super().__init__(error, lineN, 'Parse')

# Value type mismatch
class BasicValueError(BasicCompileError):
    """ Basic compiler error on value mismatch """
    def __init__(self, error: str, lineN: int = -1):
        super().__init__(error, lineN, 'Value')

# No free register
class BasicRegisterFullError(BasicCompileError):
    """ Basic compiler error on registers full """
    def __init__(self, src: str, lineN: int = -1):
        super().__init__(f'Could not load {src} into register, none free', lineN, 'Register')

# Can not resolve jump
class BasicJumpResolveError(BasicCompileError):
    """ Basic compiler error on failure to resolve jump point """
    def __init__(self, jp: str, lineN: int = -1):
        super().__init__(f'Could not resolve jump point "{jp}"', lineN, 'Jump')