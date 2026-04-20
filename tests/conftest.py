#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Shared fixtures for clients test suite."""

import os
import pytest


@pytest.fixture
def project_root():
    """Return the absolute path to the project root.

    Returns:
        str: Absolute path to the project root directory.
    """
    return os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )


@pytest.fixture
def remote_cli_dir(project_root):
    """Return the path to the remote_cli directory.

    Args:
        project_root: Absolute path to project root.

    Returns:
        str: Absolute path to the remote_cli directory.
    """
    return os.path.join(project_root, 'remote_cli')


@pytest.fixture
def tmp_workdir(tmp_path):
    """Provide a temporary working directory.

    Args:
        tmp_path: Pytest built-in tmp_path fixture.

    Returns:
        str: Path to a temporary working directory.
    """
    return str(tmp_path)
