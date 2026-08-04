#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Shared test helper functions for clients test suite."""

import os

from tests.constants import K8S_CONTENT
from tests.constants import OPENRC_CONTENT
from tests.constants import OPENRC_CONTENT_KEYSTONE


def create_rc_file(directory, filename, keystone=False):
    """Create a mock OpenRC file for testing.

    Args:
        directory: Directory to create the file in.
        filename: Name of the RC file.
        keystone: If True, use keystone auth URL.

    Returns:
        str: Absolute path to the created RC file.
    """
    path = os.path.join(directory, filename)
    content = (
        OPENRC_CONTENT_KEYSTONE if keystone
        else OPENRC_CONTENT
    )
    with open(path, 'w', encoding='utf-8') as fobj:
        fobj.write(content)
    return path


def create_k8s_file(directory, filename):
    """Create a mock kubeconfig file for testing.

    Args:
        directory: Directory to create the file in.
        filename: Name of the kubeconfig file.

    Returns:
        str: Absolute path to the created file.
    """
    path = os.path.join(directory, filename)
    with open(path, 'w', encoding='utf-8') as fobj:
        fobj.write(K8S_CONTENT)
    return path
