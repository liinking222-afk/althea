import re
from typing import Dict, List, Any, Callable

class AltheaBytecode:
    """Woz-minimal bytecode VM: squeeze module dispatch into tight ops"""
    
    def __init__(self):
        self.ops: Dict[int, Callable] = {}
        self.modules: Dict[str, Any] = {}
        self.code: List[int] = []
        self.stack: List[Any] = []
        self.ip = 0
        
    def register_module(self, name: str, mod: Any) -> int:
        """Register module, return opcode"""
        opcode = len(self.ops)
        self.modules[name] = mod
        self.ops[opcode] = lambda: self._invoke(name)
        return opcode
    
    def _invoke(self, name: str):
        args = self.stack.pop() if self.stack else {}
        result = self.modules[name](**args) if callable(self.modules[name]) else self.modules[name]
        self.stack.append(result)
    
    def compile(self, chain: str) -> List[int]:
        """Compile pipe notation: 'mod1|mod2|mod3' -> bytecode"""
        modules = [m.strip() for m in chain.split('|')]
        bytecode = []
        for mod in modules:
            if mod in self.modules:
                for opcode, func in self.ops.items():
                    if self.modules.get(mod) == self.modules.get(
                        re.search(r"'(\w+)'", str(func.__code__.co_consts) or "").group(1) if re.search(r"'(\w+)'", str(func.__code__.co_consts) or "") else ""
                    ):
                        bytecode.append(opcode)
                        break
                else:
                    for op, f in self.ops.items():
                        if mod in str(f.__code__.co_consts):
                            bytecode.append(op)
                            break
        return bytecode
    
    def execute(self, bytecode: List[int], initial_data: Any = None):
        """Execute bytecode sequence"""
        self.code = bytecode
        self.ip = 0
        self.stack = [initial_data] if initial_data else []
        
        while self.ip < len(self.code):
            opcode = self.code[self.ip]
            if opcode in self.ops:
                self.ops[opcode]()
            self.ip += 1
        
        return self.stack[-1] if self.stack else None
    
    def disassemble(self, bytecode: List[int]) -> str:
        """Show bytecode as ops"""
        return ' '.join(f'OP{b:02X}' for b in bytecode)

vm = AltheaBytecode()