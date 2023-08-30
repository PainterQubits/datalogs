"""Function to get a filename for a logger directory or log file."""

from __future__ import annotations
import os
from datetime import datetime


def get_filename(
    directory: str,
    description: str,
    *,
    timestamp: datetime | None = None,
    ext: str = "",
) -> str:
    """
    Create a file or directory name using the description, timestamp, and extension,
    which does not already exist within the given directory.
    """
    formatted_timestamp = f"{timestamp.strftime('%y-%m-%d-%H%M')}_" if timestamp else ""
    prefix = f"{formatted_timestamp}{description}"
    name = f"{prefix}{ext}"
    version = 1
    while os.path.exists(os.path.join(directory, name)):
        name = f"{prefix}_{version}{ext}"
        version += 1
    return name
