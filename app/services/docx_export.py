"""
Utility for exporting structured JSON documents to Word (DOCX).

This module provides helper functions to transform nested dictionaries and lists
into a Markdown representation and then convert that Markdown into a Word
document using pandoc. It is used by the API endpoints to allow tender
documents (RFT, TEPP and Returnable Schedules) to be downloaded as .docx
files on demand. Pandoc must be available in the runtime environment.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, List

def _escape_markdown(text: str) -> str:
    """Escape vertical bars and pipes within table cells."""
    return text.replace('|', '\\|').replace('\n', ' ')

def _json_to_markdown(obj: Any, level: int = 1) -> str:
    """
    Recursively convert a Python object (dict/list/primitive) into a Markdown string.

    - Dictionaries become sections with headings (#, ##, ###, etc.) for keys.
    - Lists of primitives become bulleted lists.
    - Lists of objects become Markdown tables with columns for all keys.
    - Primitive values are written inline.

    Args:
        obj: The JSON-like object to convert.
        level: The heading level (starts at 1).

    Returns:
        A Markdown string representing the object.
    """
    md_parts: List[str] = []
    # Dictionaries
    if isinstance(obj, dict):
        for key, value in obj.items():
            # Section header
            heading = '#' * level + f' {key}\n\n'
            md_parts.append(heading)
            md_parts.append(_json_to_markdown(value, level + 1))
    # Lists
    elif isinstance(obj, list):
        if not obj:
            return ''
        # Determine if this is a list of dictionaries
        first_nonnull = None
        for item in obj:
            if item is not None:
                first_nonnull = item
                break
        if isinstance(first_nonnull, dict):
            # Union of keys across all objects
            keys: List[str] = []
            for item in obj:
                if isinstance(item, dict):
                    for k in item.keys():
                        if k not in keys:
                            keys.append(k)
            # Build table header
            header = '| ' + ' | '.join(keys) + ' |\n'
            separator = '| ' + ' | '.join(['---'] * len(keys)) + ' |\n'
            rows = []
            for item in obj:
                if isinstance(item, dict):
                    row_cells = []
                    for k in keys:
                        v = item.get(k, '')
                        if isinstance(v, (dict, list)):
                            cell_text = json.dumps(v, ensure_ascii=False)
                        else:
                            cell_text = str(v) if v is not None else ''
                        row_cells.append(_escape_markdown(cell_text))
                    rows.append('| ' + ' | '.join(row_cells) + ' |')
                else:
                    # Non-dict items in list of objects, treat as single value
                    rows.append('| ' + ' | '.join([_escape_markdown(str(item)) for _ in keys]) + ' |')
            md_parts.append(header + separator + '\n'.join(rows) + '\n\n')
        else:
            # List of primitives
            for item in obj:
                md_parts.append(f'- {item}\n')
            md_parts.append('\n')
    else:
        # Primitive
        md_parts.append(f'{obj}\n\n')
    return ''.join(md_parts)

def export_json_to_docx(data: Dict[str, Any], title: str) -> str:
    """
    Generate a DOCX file from the given JSON data.

    The function first builds a Markdown representation of the JSON, prepending
    the supplied title as a level‑1 heading. It then writes the Markdown to a
    temporary file and invokes pandoc to convert it into a DOCX. The caller is
    responsible for deleting the returned file when no longer needed.

    Args:
        data: The structured JSON object to convert.
        title: The title to use as the first heading in the document.

    Returns:
        The path to the generated DOCX file.
    """
    # Build Markdown content
    markdown = f'# {title}\n\n' + _json_to_markdown(data, level=2)
    # Create a temporary Markdown file
    with tempfile.NamedTemporaryFile('w+', suffix='.md', delete=False) as md_file:
        md_file.write(markdown)
        md_file.flush()
        md_path = md_file.name
    # Prepare the output DOCX path
    docx_path = md_path[:-3] + '.docx'
    # Run pandoc to convert to DOCX
    try:
        subprocess.run(['pandoc', md_path, '-o', docx_path], check=True)
    except Exception as e:
        # If conversion fails, remove markdown file and re-raise
        Path(md_path).unlink(missing_ok=True)
        raise RuntimeError(f'Failed to convert to DOCX: {e}')
    # Clean up markdown file
    Path(md_path).unlink(missing_ok=True)
    return docx_path