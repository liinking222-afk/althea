import re
import pandas as pd
from pathlib import Path
from typing import Union, Any
from io import StringIO
import urllib.request

def polymorphic_read(source: Any, **kwargs) -> pd.DataFrame:
    """
    Larry Wall style: accept anything that quacks like data.
    File path? URL? Raw CSV string? DataFrame already? We'll figure it out.
    """
    
    # Already a DataFrame? Pass through.
    if isinstance(source, pd.DataFrame):
        return source
    
    # Path-like object or string that looks like a file path
    if isinstance(source, (Path, str)):
        source_str = str(source)
        
        # URL pattern (http/https/ftp)
        if re.match(r'^(https?|ftp)://', source_str):
            with urllib.request.urlopen(source_str) as response:
                content = response.read().decode('utf-8')
            return _parse_content(content, **kwargs)
        
        # File path that exists
        if Path(source_str).exists():
            suffix = Path(source_str).suffix.lower()
            if suffix == '.csv':
                return pd.read_csv(source_str, **kwargs)
            elif suffix in ['.json', '.jsonl']:
                return pd.read_json(source_str, **kwargs)
            elif suffix in ['.xls', '.xlsx']:
                return pd.read_excel(source_str, **kwargs)
            elif suffix == '.parquet':
                return pd.read_parquet(source_str, **kwargs)
            else:
                # Try CSV as default
                return pd.read_csv(source_str, **kwargs)
        
        # Not a file, treat as raw content
        return _parse_content(source_str, **kwargs)
    
    # List of dicts? (JSON-style data)
    if isinstance(source, list) and source and isinstance(source[0], dict):
        return pd.DataFrame(source)
    
    # Dict? Try to construct DataFrame
    if isinstance(source, dict):
        return pd.DataFrame(source)
    
    raise ValueError(f"Cannot duck-type {type(source)} into tabular data")

def _parse_content(content: str, **kwargs) -> pd.DataFrame:
    """Parse raw string content, detecting format via regex."""
    
    # JSON array pattern
    if re.match(r'^\s*[\[{]', content.strip()):
        return pd.read_json(StringIO(content), **kwargs)
    
    # TSV pattern (tab-heavy)
    if content.count('\t') > content.count(','):
        return pd.read_csv(StringIO(content), sep='\t', **kwargs)
    
    # Default: CSV
    return pd.read_csv(StringIO(content), **kwargs)