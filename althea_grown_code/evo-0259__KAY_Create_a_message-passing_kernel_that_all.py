#!/usr/bin/env python3
"""
runtime_message_broker.py — Late-binding message dispatcher for live module replacement
"""
import asyncio
import importlib
import inspect
from typing import Any, Callable, Dict, Optional
from dataclasses import dataclass
from pathlib import Path
import sys

@dataclass
class Message:
    target: str
    method: str
    args: tuple
    kwargs: dict
    reply_to: Optional[asyncio.Queue] = None

class LiveModule:
    def __init__(self, module_path: str):
        self.module_path = module_path
        self.instance = None
        self.version = 0
        self.reload()
    
    def reload(self):
        """Hot-reload module implementation"""
        if self.module_path in sys.modules:
            mod = importlib.reload(sys.modules[self.module_path])
        else:
            mod = importlib.import_module(self.module_path)
        
        # Instantiate if class found
        for name, obj in inspect.getmembers(mod, inspect.isclass):
            if not name.startswith('_'):
                self.instance = obj()
                break
        self.version += 1
    
    async def handle(self, msg: Message) -> Any:
        method = getattr(self.instance, msg.method, None)
        if callable(method):
            result = method(*msg.args, **msg.kwargs)
            if asyncio.iscoroutine(result):
                return await result
            return result
        raise AttributeError(f"Method {msg.method} not found")

class MessageBroker:
    def __init__(self):
        self.modules: Dict[str, LiveModule] = {}
        self.queue = asyncio.Queue()
        self.running = False
    
    def register(self, name: str, module_path: str):
        self.modules[name] = LiveModule(module_path)
    
    def hot_swap(self, name: str):
        """Replace module implementation without stopping message flow"""
        if name in self.modules:
            self.modules[name].reload()
    
    async def send(self, target: str, method: str, *args, **kwargs) -> Any:
        reply_queue = asyncio.Queue()
        msg = Message(target, method, args, kwargs, reply_queue)
        await self.queue.put(msg)
        return await reply_queue.get()
    
    async def run(self):
        self.running = True
        while self.running:
            msg = await self.queue.get()
            if msg.target in self.modules:
                try:
                    result = await self.modules[msg.target].handle(msg)
                    if msg.reply_to:
                        await msg.reply_to.put(result)
                except Exception as e:
                    if msg.reply_to:
                        await msg.reply_to.put(e)

# Global broker instance
broker = MessageBroker()