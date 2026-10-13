#!/usr/bin/env python3
"""
Module: /io/pipe-emit
Stream-oriented output formatter for UNIX pipeline composition.
Modules emit structured data as line-delimited records.
"""

import sys
import json
from typing import Any, Dict, Optional
from datetime import datetime


class PipeEmitter:
    """Emit structured data as plain-text streams for pipeline processing."""
    
    def __init__(self, format: str = "tsv", stream=sys.stdout):
        self.format = format.lower()
        self.stream = stream
        self.field_order: Optional[list] = None
    
    def emit(self, data: Dict[str, Any], timestamp: bool = True) -> None:
        """Emit a single record to the pipeline."""
        if timestamp and "ts" not in data:
            data["ts"] = datetime.utcnow().isoformat()
        
        if self.format == "json":
            self.stream.write(json.dumps(data) + "\n")
        elif self.format == "tsv":
            self._emit_tsv(data)
        elif self.format == "csv":
            self._emit_csv(data)
        else:
            # Simple key=value format (default UNIX style)
            self.stream.write(" ".join(f"{k}={v}" for k, v in data.items()) + "\n")
        
        self.stream.flush()
    
    def _emit_tsv(self, data: Dict[str, Any]) -> None:
        if self.field_order is None:
            self.field_order = list(data.keys())
            self.stream.write("\t".join(self.field_order) + "\n")
        values = [str(data.get(k, "")) for k in self.field_order]
        self.stream.write("\t".join(values) + "\n")
    
    def _emit_csv(self, data: Dict[str, Any]) -> None:
        if self.field_order is None:
            self.field_order = list(data.keys())
            self.stream.write(",".join(self.field_order) + "\n")
        values = [str(data.get(k, "")).replace(",", ";") for k in self.field_order]
        self.stream.write(",".join(values) + "\n")


def emit(data: Dict[str, Any], format: str = "tsv") -> None:
    """Convenience function for one-shot emission."""
    emitter = PipeEmitter(format=format)
    emitter.emit(data)


if __name__ == "__main__":
    # Example: orbital pass predictions as pipeline stream
    emitter = PipeEmitter(format="tsv")
    emitter.emit({"satellite": "ISS", "aos": "2024-01-15T14:32:00", "max_el": 45.2})
    emitter.emit({"satellite": "ISS", "aos": "2024-01-15T16:08:00", "max_el": 78.9})