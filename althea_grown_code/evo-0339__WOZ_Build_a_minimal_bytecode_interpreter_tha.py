#!/usr/bin/env python3
import struct
from typing import Dict, Callable, Any, List
from dataclasses import dataclass

@dataclass
class OpCode:
    LOAD_CONST = 0x01
    STORE_VAR = 0x02
    CALL_OP = 0x03
    BIND_OP = 0x04
    JUMP_IF = 0x05
    RETURN = 0x06

class AltheaBytecodeVM:
    def __init__(self):
        self.constants: List[Any] = []
        self.variables: Dict[str, Any] = {}
        self.operations: Dict[str, Callable] = {}
        self.ip = 0
        self.stack: List[Any] = []
        
    def bind_operation(self, name: str, func: Callable):
        """Hot-swap operation implementations at runtime"""
        self.operations[name] = func
        
    def compile(self, ops: List[tuple]) -> bytes:
        """Compile operation tuples into bytecode stream"""
        bytecode = bytearray()
        for op in ops:
            bytecode.append(op[0])
            if len(op) > 1:
                bytecode.extend(struct.pack('<H', op[1]))
        return bytes(bytecode)
    
    def execute(self, bytecode: bytes):
        self.ip = 0
        while self.ip < len(bytecode):
            opcode = bytecode[self.ip]
            self.ip += 1
            
            if opcode == OpCode.LOAD_CONST:
                idx = struct.unpack('<H', bytecode[self.ip:self.ip+2])[0]
                self.ip += 2
                self.stack.append(self.constants[idx])
                
            elif opcode == OpCode.STORE_VAR:
                idx = struct.unpack('<H', bytecode[self.ip:self.ip+2])[0]
                self.ip += 2
                self.variables[self.constants[idx]] = self.stack.pop()
                
            elif opcode == OpCode.CALL_OP:
                idx = struct.unpack('<H', bytecode[self.ip:self.ip+2])[0]
                self.ip += 2
                op_name = self.constants[idx]
                arg = self.stack.pop()
                result = self.operations[op_name](arg)
                self.stack.append(result)
                
            elif opcode == OpCode.BIND_OP:
                idx = struct.unpack('<H', bytecode[self.ip:self.ip+2])[0]
                self.ip += 2
                op_name = self.constants[idx]
                func = self.stack.pop()
                self.bind_operation(op_name, func)
                
            elif opcode == OpCode.RETURN:
                return self.stack.pop() if self.stack else None

vm = AltheaBytecodeVM()