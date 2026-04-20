#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Coverage-focused tests for shell scripts in remote_cli."""

import os
import sys
import unittest

sys.path.insert(
    0, os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)
from base_test import ConfigureClientTestCase  # noqa: E402
from base_test import ShellScriptTestCase  # noqa: E402
from tests.test_helpers import create_rc_file  # noqa: E402


class TestClientWrapperSyntax(ShellScriptTestCase):
    """Test client_wrapper.sh syntax and structure."""

    script_name = 'client_wrapper.sh'

    EXPECTED_VARS = [
        'KUBE_CFG_PATH=', 'HELM_CONFIG_PATH=', 'HELM_CACHE_PATH=',
        'VOLUME_LIST=', 'OS_ENDPOINT_TYPE=publicURL',
        'REQUESTS_CA_BUNDLE', 'CLI_CONFIRMATIONS',
    ]
    EXPECTED_LOGIC = [
        'SHELL_TYPE=$(uname -s)', 'CONFIG_TYPE', 'CYGWIN',
        'docker', 'FORCE_SHELL', 'FORCE_NO_SHELL',
        'cannot set both FORCE_SHELL',
    ]
    EXPECTED_OS_VARS = ['OS_PASSWORD', 'OS_AUTH_URL', 'OS_USERNAME']

    def test_bash_syntax_check(self):
        """Verify client_wrapper.sh has valid bash syntax."""
        self.assert_valid_bash_syntax()

    def test_shebang_line(self):
        """Verify script starts with bash shebang."""
        self.assert_shebang()

    def test_contains_expected_variables(self):
        """Verify all expected variables are defined."""
        self.assert_script_contains(*self.EXPECTED_VARS)

    def test_contains_expected_logic(self):
        """Verify all expected logic patterns are present."""
        self.assert_script_contains(*self.EXPECTED_LOGIC)

    def test_exports_list_contains_os_vars(self):
        """Verify environment variable exports list."""
        self.assert_script_contains(*self.EXPECTED_OS_VARS)


class TestConfigureClientSyntax(ShellScriptTestCase):
    """Test configure_client.sh syntax and structure."""

    script_name = 'configure_client.sh'

    EXPECTED_DEFAULTS = [
        'RC_FILE="admin-openrc.sh"',
        'CONF_FILE=remote_client_config.sh',
        'K8S_FILE="temp-kubeconfig"',
    ]
    EXPECTED_CONTENT = [
        'usage()', 'getopts',
        'remote_client_platform.sh', 'remote_client_openstack.sh',
        'does NOT exist', 'PATH_TO_SCRIPT=',
        'ALIAS_FILE=config_aliases.sh',
        'TAG_FILE=docker_image_version.sh',
        'override_platform_image', 'override_application_image',
    ]

    def test_bash_syntax_check(self):
        """Verify configure_client.sh has valid bash syntax."""
        self.assert_valid_bash_syntax()

    def test_shebang_line(self):
        """Verify script starts with bash shebang."""
        self.assert_shebang()

    def test_contains_defaults(self):
        """Verify default variable values."""
        self.assert_script_contains(*self.EXPECTED_DEFAULTS)

    def test_contains_expected_content(self):
        """Verify expected content patterns."""
        self.assert_script_contains(*self.EXPECTED_CONTENT)


class TestConfigureClientExecution(ConfigureClientTestCase):
    """Test configure_client.sh execution paths."""

    def test_usage_output(self):
        """Verify usage output with -h flag."""
        result = self.run_configure(['-h'])
        self.assertIn('Usage:', result.stdout)

    def test_invalid_option(self):
        """Verify error on invalid option."""
        result = self.run_configure(['-z'])
        self.assertNotEqual(result.returncode, 0)

    def test_missing_rc_file_error(self):
        """Verify error when RC file does not exist."""
        result = self.run_configure(['-r', '/nonexistent/file.sh'])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('does NOT exist', result.stderr + result.stdout)

    def test_invalid_client_type(self):
        """Verify error on invalid client type."""
        rc_file = create_rc_file(self.tmpdir, 'test-openrc.sh')
        result = self.run_configure(['-t', 'invalid', '-r', rc_file])
        self.assertNotEqual(result.returncode, 0)

    def test_platform_type_missing_k8s_file(self):
        """Verify error when k8s file missing."""
        rc_file = create_rc_file(self.tmpdir, 'plat-openrc.sh')
        result = self.run_configure(
            ['-t', 'platform', '-r', rc_file,
             '-k', '/nonexistent/kubeconfig']
        )
        self.assertNotEqual(result.returncode, 0)

    def test_openstack_type_generates_config(self):
        """Verify openstack type generates config file."""
        result, content = self.run_configure_workflow(
            'openstack', 'openrc.sh', 'output.sh'
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn('CONFIG_TYPE=application', content)
        self.assertIn('OSC_WORKDIR=', content)

    def test_platform_type_generates_config(self):
        """Verify platform type generates config."""
        result, content = self.run_configure_workflow(
            'platform', 'openrc3.sh', 'output3.sh',
            k8s_name='kubeconfig'
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn('CONFIG_TYPE=platform', content)
        self.assertIn('K8S_CONFIG_FILE=', content)

    def test_platform_image_override(self):
        """Verify platform image override."""
        result, content = self.run_configure_workflow(
            'platform', 'openrc4.sh', 'output4.sh',
            k8s_name='kubeconfig2',
            extra_args=['-p', 'my-registry/platform:v1']
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn('PLATFORM_DOCKER_IMAGE=', content)

    def test_application_image_override(self):
        """Verify application image override."""
        result, content = self.run_configure_workflow(
            'openstack', 'openrc5.sh', 'output5.sh',
            extra_args=['-a', 'my-registry/app:v1']
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn('APPLICATION_DOCKER_IMAGE=', content)


class TestConfigAliasesSyntax(ShellScriptTestCase):
    """Test config_aliases.sh syntax and structure."""

    script_name = 'config_aliases.sh'

    PLATFORM_SERVICES = ['system', 'fm', 'dcmanager', 'kubectl', 'helm',
                         'software', 'sw-manager', 'oidc-auth']
    APPLICATION_SERVICES = ['openstack', 'nova', 'cinder', 'glance', 'heat']
    EXPECTED_CONTENT = [
        'CONFIG_TYPE', 'client_wrapper.sh', 'platform_shell',
        'application_shell', 'PATH_TO_SCRIPT=',
    ]

    def test_bash_syntax_check(self):
        """Verify config_aliases.sh has valid bash syntax."""
        self.assert_valid_bash_syntax()

    def test_contains_platform_services(self):
        """Verify platform services list."""
        self.assert_script_contains(*self.PLATFORM_SERVICES)

    def test_contains_application_services(self):
        """Verify application services list."""
        self.assert_script_contains(*self.APPLICATION_SERVICES)

    def test_contains_expected_content(self):
        """Verify expected content patterns."""
        self.assert_script_contains(*self.EXPECTED_CONTENT)


class TestDockerImageVersionSyntax(ShellScriptTestCase):
    """Test docker_image_version.sh syntax and content."""

    script_name = 'docker_image_version.sh'

    EXPECTED_CONTENT = [
        'PLATFORM_DOCKER_IMAGE=', 'APPLICATION_DOCKER_IMAGE=',
        'docker.io/starlingx/',
        'export PLATFORM_DOCKER_IMAGE',
        'export APPLICATION_DOCKER_IMAGE',
    ]

    def test_bash_syntax_check(self):
        """Verify docker_image_version.sh has valid bash syntax."""
        self.assert_valid_bash_syntax()

    def test_contains_expected_content(self):
        """Verify expected image definitions and exports."""
        self.assert_script_contains(*self.EXPECTED_CONTENT)


if __name__ == '__main__':
    unittest.main()
