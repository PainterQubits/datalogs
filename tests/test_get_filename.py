"""Tests for datalogger._get_filename."""

import os
import pytest
from datalogger._get_filename import get_filename


@pytest.fixture(name="cd_tempdir")
def cd_tempdir(tmp_path) -> None:
    """Change to a temporary directory."""
    os.chdir(tmp_path)


@pytest.mark.usefixtures("cd_tempdir")
def test_empty_description() -> None:
    """If the description is empty, returns an empty filename."""
    assert get_filename("", "") == ""
    assert get_filename("dir", "") == ""


@pytest.mark.usefixtures("cd_tempdir")
def test_current_directory_existing() -> None:
    """Can handle an existing file name within the current directory."""

    dir_name = get_filename("", "dir")
    assert dir_name == "dir"
    os.mkdir(dir_name)
    dir_name_1 = get_filename("", "dir")
    assert dir_name_1 == "dir_1"
