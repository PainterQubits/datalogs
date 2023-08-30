"""Tests for datalogger._get_filename."""

from __future__ import annotations
import os
from datetime import datetime
import pytest
from datalogger._get_filename import get_filename


def new_file(path: str) -> None:
    """Create a new blank file with the given path."""
    with open(path, "w", encoding="utf-8"):
        pass


@pytest.mark.usefixtures("cd_tempdir")
def test_empty_description() -> None:
    """If the description is empty, returns an empty filename."""
    assert get_filename("", "") == ""
    assert get_filename("dir", "") == ""


@pytest.mark.usefixtures("cd_tempdir")
def test_unique_filename() -> None:
    """
    If the given filename exists, a number will be appended to make it unique within the
    given directory.
    """
    dir_path = "dir"
    os.mkdir(dir_path)
    new_file(os.path.join(dir_path, "file"))
    for i in range(10):
        filename = get_filename(dir_path, "file")
        assert filename == f"file_{i + 1}"
        new_file(os.path.join(dir_path, filename))


@pytest.mark.usefixtures("cd_tempdir")
def test_current_directory() -> None:
    """Can generate unique file and directory names within the current directory."""
    assert get_filename("", "file") == "file"
    assert get_filename("", "dir") == "dir"
    assert get_filename(".", "file") == "file"
    new_file("file")
    os.mkdir("dir")
    assert get_filename("", "file") == "file_1"
    assert get_filename("", "dir") == "dir_1"
    assert get_filename(".", "file") == "file_1"


@pytest.mark.usefixtures("cd_tempdir")
def test_subdirectory() -> None:
    """Can generate unique file names within a subdirectory."""
    dir_path = "dir"
    subdir_path = os.path.join("dir", "subdir")
    os.mkdir(dir_path)
    os.mkdir(subdir_path)
    assert get_filename(dir_path, "file") == "file"
    assert get_filename(subdir_path, "file") == "file"
    new_file(os.path.join(dir_path, "file"))
    new_file(os.path.join(subdir_path, "file"))
    assert get_filename(dir_path, "file") == "file_1"
    assert get_filename(subdir_path, "file") == "file_1"


@pytest.mark.usefixtures("cd_tempdir")
def test_extension() -> None:
    """Can generate unique file names with extensions."""
    assert get_filename("", "file", ext=".txt") == "file.txt"
    new_file("file.txt")
    assert get_filename("", "file", ext=".txt") == "file_1.txt"


@pytest.mark.usefixtures("cd_tempdir")
def test_timestamp(timestamp: datetime, timestamp_str_short: str) -> None:
    """Can generate unique file names with a timestamp."""
    filename = f"{timestamp_str_short}_file"
    assert get_filename("", "file", timestamp=timestamp) == filename
    new_file(filename)
    assert get_filename("", "file", timestamp=timestamp) == f"{filename}_1"


@pytest.mark.usefixtures("cd_tempdir")
def test_timestamp_and_extension(timestamp: datetime, timestamp_str_short: str) -> None:
    """Can generate unique file names with an extension and timestamp."""
    filename = f"{timestamp_str_short}_file"
    filename_with_ext = get_filename("", "file", timestamp=timestamp, ext=".txt")
    assert filename_with_ext == f"{filename}.txt"
    new_file(filename_with_ext)
    assert (
        get_filename("", "file", timestamp=timestamp, ext=".txt") == f"{filename}_1.txt"
    )
