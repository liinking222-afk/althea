#!/usr/bin/env python3
import ast
import sys
import re

class WozCompressor(ast.NodeTransformer):
    def visit_Expr(self, node):
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            return None
        return node
    
    def visit_FunctionDef(self, node):
        node.body = [stmt for stmt in node.body if not (
            isinstance(stmt, ast.Expr) and 
            isinstance(stmt.value, ast.Constant)
        )]
        if not node.body:
            node.body = [ast.Pass()]
        return self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node):
        return self.visit_FunctionDef(node)

def compress_module(source_code):
    tree = ast.parse(source_code)
    tree = WozCompressor().visit(tree)
    ast.fix_missing_locations(tree)
    compressed = ast.unparse(tree)
    
    compressed = re.sub(r'\n\s*\n+', '\n', compressed)
    compressed = re.sub(r'(?m)^\s+$', '', compressed)
    lines = [line.rstrip() for line in compressed.split('\n') if line.strip()]
    
    return '\n'.join(lines)

def analyze_compression(original, compressed):
    orig_tokens = len(re.findall(r'\S+', original))
    comp_tokens = len(re.findall(r'\S+', compressed))
    orig_bytes = len(original.encode('utf-8'))
    comp_bytes = len(compressed.encode('utf-8'))
    
    return {
        'token_reduction': (1 - comp_tokens / orig_tokens) * 100,
        'byte_reduction': (1 - comp_bytes / orig_bytes) * 100,
        'original_bytes': orig_bytes,
        'compressed_bytes': comp_bytes
    }

if __name__ == '__main__':
    source = sys.stdin.read()
    compressed = compress_module(source)
    stats = analyze_compression(source, compressed)
    
    print(f"# WOZ_COMPRESSION_RATIO: {stats['byte_reduction']:.1f}%")
    print(f"# BYTES: {stats['original_bytes']} → {stats['compressed_bytes']}")
    print(compressed)