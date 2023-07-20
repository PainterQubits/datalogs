"""Function to get a filename for a logger directory or log file."""

import os
from datetime import datetime


def get_filename(
    directory: str, timestamp: datetime, description: str, ext: str = ""
) -> str:
    """
    Create a filename using the given timestamp, description, and extension, which does
    not already exist within the given directory.
    """
    formatted_timestamp = timestamp.strftime("%y-%m-%d-%H:%M")
    prefix = f"{formatted_timestamp}_{description}"
    name = f"{prefix}{ext}"
    version = 1
    while os.path.exists(os.path.join(directory, name)):
        name = f"{prefix}_{version}{ext}"
        version += 1
    return name
