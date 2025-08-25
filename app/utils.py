import re
from typing import Any, List, Optional

def add_unique_line(lst: List[str], line: Optional[str]):
    if not line: return
    norm = re.sub(r"\s+", " ", line.strip().lower())
    if not norm: return
    for x in lst:
        if re.sub(r"\s+", " ", x.strip().lower()) == norm:
            return
    lst.append(line.strip())

def extend_unique(lst: List[str], lines: List[str]):
    for ln in lines or []:
        add_unique_line(lst, ln)

def unique_keep_order(items: List[str]) -> List[str]:
    seen = set(); out = []
    for it in items:
        key = re.sub(r"\s+", " ", it.strip().lower())
        if key and key not in seen:
            seen.add(key); out.append(it.strip())
    return out
