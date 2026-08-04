#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Shared test constants for clients test suite."""

TEST_AUTH_URL = "http://test:5000/v3"
TEST_AUTH_URL_KEYSTONE = "http://keystone:5000/v3"

OPENRC_LINE = (
    "export OS_AUTH_URL={auth_url}\n"
)
OPENRC_CONTENT = (
    "export OS_AUTH_URL=" + TEST_AUTH_URL + "\n"
)
OPENRC_CONTENT_KEYSTONE = (
    "export OS_AUTH_URL=" + TEST_AUTH_URL_KEYSTONE + "\n"
)

K8S_CONTENT = "apiVersion: v1\n"
K8S_CONTENT_FULL = "apiVersion: v1\nkind: Config\n"

PLATFORM_DOCKER_IMAGE = "test-platform:v1"
APPLICATION_DOCKER_IMAGE = "test-app:v1"
