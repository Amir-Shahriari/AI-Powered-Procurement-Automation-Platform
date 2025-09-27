"""
Configuration and constants for the NSW Procurement Platform
"""
import os
from pathlib import Path
from typing import List


# Data directory
DATA_DIR = Path("data")

# Task management
TASKS = {}
TASKS_LOCK = None

# Model discovery
def discover_models() -> List[str]:
    """Discover available AI models."""
    models = [
        "gpt-4o",
        "gpt-4o-mini", 
        "gpt-4-turbo",
        "gpt-3.5-turbo",
        "claude-3-5-sonnet-20241022",
        "claude-3-5-haiku-20241022",
        "claude-3-opus-20240229"
    ]
    
    # Filter based on environment variables
    allowed_models = os.getenv("ALLOWED_MODELS", "").split(",")
    if allowed_models and allowed_models[0]:
        models = [m for m in models if m in allowed_models]
    
    return models


def _env_list(var: str, sep: str = ",") -> List[str]:
    """Get environment variable as list."""
    value = os.getenv(var, "")
    return [item.strip() for item in value.split(sep) if item.strip()]
