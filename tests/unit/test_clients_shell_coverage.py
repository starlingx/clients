#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Shell script execution coverage tests using bash trace mode."""

import os
import subprocess
import sys
import unittest

sys.path.insert(
    0, os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)
from base_test import ConfigureClientTestCase  # noqa: E402
from base_test import TempDirTestCase  # noqa: E402
from tests.constants import APPLICATION_DOCKER_IMAGE  # noqa: E402
from tests.constants import PLATFORM_DOCKER_IMAGE  # noqa: E402
from tests.constants import TEST_AUTH_URL_KEYSTONE  # noqa: E402
from tests.test_helpers import create_k8s_file  # noqa: E402
from tests.test_helpers import create_rc_file  # noqa: E402


class ShellCoverageBase(TempDirTestCase):
    """Base class with helpers for shell coverage testing."""

    @classmethod
    def setUpClass(cls):
        """Set up paths and mock docker."""
        super().setUpClass()
        mock_docker = os.path.join(cls.tmpdir, 'docker')
        with open(mock_docker, 'w', encoding='utf-8') as fobj:
            fobj.write('#!/bin/bash\necho "MOCK_DOCKER $@"\n')
        os.chmod(mock_docker, 0o755)

    def _build_env(self, overrides=None):
        """Build environment dict with defaults.

        Args:
            overrides: Dict of env var overrides.

        Returns:
            dict: Environment for subprocess.
        """
        env = os.environ.copy()
        env['PATH'] = self.tmpdir + ':' + env.get('PATH', '')
        env['OSC_WORKDIR'] = self.tmpdir
        env['PLATFORM_DOCKER_IMAGE'] = PLATFORM_DOCKER_IMAGE
        env['APPLICATION_DOCKER_IMAGE'] = APPLICATION_DOCKER_IMAGE
        for key in ('OS_CACERT', 'FORCE_SHELL',
                    'FORCE_NO_SHELL', 'CONFIG_TYPE'):
            env.pop(key, None)
        if overrides:
            env.update(overrides)
        return env

    def _run_wrapper(self, env_overrides=None, args=None):
        """Run client_wrapper.sh with mocked docker and trace.

        Args:
            env_overrides: Dict of environment variable overrides.
            args: List of command-line arguments.

        Returns:
            subprocess.CompletedProcess: Result.
        """
        env = self._build_env(env_overrides)
        script = os.path.join(self.cli_dir, 'client_wrapper.sh')
        wrapper = (
            'function exec() { "$@"; return $?; }\n'
            'export -f exec\n'
            'source "$1" "${@:2}"\n'
        )
        cmd_args = args or ['test-cmd']
        return subprocess.run(
            ['bash', '-x', '-c', wrapper, '--', script] + cmd_args,
            capture_output=True, text=True, env=env, timeout=10
        )

    def _source_aliases(self, config_type, absolute=True):
        """Source config_aliases.sh and capture output.

        Args:
            config_type: Client type (platform/application).
            absolute: Use absolute BASH_SOURCE path.

        Returns:
            subprocess.CompletedProcess: Result with aliases.
        """
        script = os.path.join(self.cli_dir, 'config_aliases.sh')
        bash_src = (
            f'BASH_SOURCE=/{self.cli_dir}/config_aliases.sh'
            if absolute else 'BASH_SOURCE=config_aliases.sh'
        )
        cmd = (
            f'shopt -s expand_aliases; '
            f'export CONFIG_TYPE={config_type}; '
            f'{bash_src}; '
            f'source {script}; '
            f'alias'
        )
        return subprocess.run(
            ['bash', '-x', '-c', cmd],
            capture_output=True, text=True, timeout=10
        )


class TestClientWrapperPlatformLinux(ShellCoverageBase):
    """Test client_wrapper.sh platform path on Linux."""

    PLATFORM_ENV = {
        'CONFIG_TYPE': 'platform',
        'K8S_CONFIG_FILE': '/tmp/kubeconfig',
    }

    def test_platform_default(self):
        """Exercise platform + Linux + single arg."""
        result = self._run_wrapper(self.PLATFORM_ENV, ['system'])
        self.assertIn('MOCK_DOCKER', result.stdout)
        self.assertEqual(result.returncode, 0)

    def test_platform_with_two_args(self):
        """Exercise platform + Linux + two args."""
        result = self._run_wrapper(self.PLATFORM_ENV, ['system', 'host-list'])
        self.assertIn('MOCK_DOCKER', result.stdout)

    def test_platform_with_os_cacert(self):
        """Exercise REQUESTS_CA_BUNDLE path."""
        env = {**self.PLATFORM_ENV, 'OS_CACERT': '/tmp/ca.pem'}
        result = self._run_wrapper(env, ['system'])
        self.assertIn('REQUESTS_CA_BUNDLE', result.stderr)

    def test_platform_with_env_vars(self):
        """Exercise env var export loop."""
        env = {
            **self.PLATFORM_ENV,
            'OS_AUTH_URL': TEST_AUTH_URL_KEYSTONE,
            'OS_USERNAME': 'admin',
            'OS_PASSWORD': 'secret',
        }
        result = self._run_wrapper(env, ['system'])
        self.assertIn('OS_AUTH_URL', result.stderr)
        self.assertIn('OS_USERNAME', result.stderr)


class TestClientWrapperApplicationLinux(ShellCoverageBase):
    """Test client_wrapper.sh application path on Linux."""

    APP_ENV = {'CONFIG_TYPE': 'application'}

    def test_application_default(self):
        """Exercise application + Linux path."""
        result = self._run_wrapper(self.APP_ENV, ['openstack'])
        self.assertIn('MOCK_DOCKER', result.stdout)

    def test_application_two_args(self):
        """Exercise application + two args."""
        result = self._run_wrapper(
            self.APP_ENV, ['openstack', 'server', 'list']
        )
        self.assertIn('MOCK_DOCKER', result.stdout)


class TestClientWrapperForceFlags(ShellCoverageBase):
    """Test FORCE_SHELL and FORCE_NO_SHELL branches."""

    BASE_ENV = {
        'CONFIG_TYPE': 'platform',
        'K8S_CONFIG_FILE': '/tmp/kubeconfig',
    }

    def test_force_shell_true(self):
        """Exercise FORCE_SHELL=true branch."""
        env = {**self.BASE_ENV, 'FORCE_SHELL': 'true'}
        result = self._run_wrapper(env, ['system'])
        self.assertIn('MOCK_DOCKER', result.stdout)

    def test_force_no_shell_true(self):
        """Exercise FORCE_NO_SHELL=true branch."""
        env = {**self.BASE_ENV, 'FORCE_NO_SHELL': 'true'}
        result = self._run_wrapper(env, ['system', 'host-list'])
        self.assertIn('MOCK_DOCKER', result.stdout)

    def test_both_force_flags_error(self):
        """Exercise error when both FORCE flags set."""
        env = {**self.BASE_ENV, 'FORCE_SHELL': 'true',
               'FORCE_NO_SHELL': 'true'}
        result = self._run_wrapper(env, ['system'])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('cannot set both', result.stdout + result.stderr)

    def test_force_shell_invalid_value(self):
        """Exercise default FORCE_SHELL=false path."""
        env = {'CONFIG_TYPE': 'application', 'FORCE_SHELL': 'maybe'}
        result = self._run_wrapper(env, ['openstack'])
        self.assertEqual(result.returncode, 0)

    def test_force_no_shell_invalid_value(self):
        """Exercise default FORCE_NO_SHELL=false path."""
        env = {'CONFIG_TYPE': 'application', 'FORCE_NO_SHELL': 'maybe'}
        result = self._run_wrapper(env, ['openstack'])
        self.assertEqual(result.returncode, 0)


class TestConfigAliasesExecution(ShellCoverageBase):
    """Execute config_aliases.sh through both branches."""

    def test_platform_aliases(self):
        """Exercise platform branch — creates platform aliases."""
        result = self._source_aliases('platform')
        self.assertEqual(result.returncode, 0)
        for svc in ['system', 'fm', 'dcmanager', 'kubectl', 'helm']:
            self.assertIn(svc, result.stdout)

    def test_application_aliases(self):
        """Exercise application branch."""
        result = self._source_aliases('application')
        self.assertEqual(result.returncode, 0)
        for svc in ['openstack', 'nova', 'cinder', 'glance', 'heat']:
            self.assertIn(svc, result.stdout)

    def test_platform_shell_alias(self):
        """Verify platform_shell alias is created."""
        result = self._source_aliases('platform')
        self.assertIn('platform_shell', result.stdout)

    def test_application_shell_alias(self):
        """Verify application_shell alias is created."""
        result = self._source_aliases('application')
        self.assertIn('application_shell', result.stdout)

    def test_relative_path_branch(self):
        """Exercise relative BASH_SOURCE path branch."""
        result = self._source_aliases('platform', absolute=False)
        self.assertEqual(result.returncode, 0)


class TestDockerImageVersionExecution(ShellCoverageBase):
    """Execute docker_image_version.sh."""

    @classmethod
    def setUpClass(cls):
        """Set up script path."""
        super().setUpClass()
        cls.version_script = os.path.join(
            cls.cli_dir, 'docker_image_version.sh'
        )

    def _source_version_script(self, cmd_suffix):
        """Source docker_image_version.sh and run command.

        Args:
            cmd_suffix: Bash command to run after sourcing.

        Returns:
            subprocess.CompletedProcess: Result.
        """
        return subprocess.run(
            ['bash', '-x', '-c',
             f'source {self.version_script}; {cmd_suffix}'],
            capture_output=True, text=True, timeout=10
        )

    def test_source_exports(self):
        """Source the file and verify exports."""
        result = self._source_version_script(
            'echo "P=$PLATFORM_DOCKER_IMAGE"; '
            'echo "A=$APPLICATION_DOCKER_IMAGE"'
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn('P=docker.io/starlingx/', result.stdout)
        self.assertIn('A=docker.io/starlingx/', result.stdout)

    def test_both_vars_exported(self):
        """Verify both variables are set after sourcing."""
        result = self._source_version_script('env | grep DOCKER_IMAGE')
        self.assertIn('PLATFORM_DOCKER_IMAGE', result.stdout)
        self.assertIn('APPLICATION_DOCKER_IMAGE', result.stdout)


class TestConfigureClientAllPaths(ConfigureClientTestCase):
    """Exercise remaining configure_client.sh paths."""

    def test_relative_rc_file_path(self):
        """Exercise relative RC file path branch."""
        create_rc_file(self.tmpdir, 'rel-openrc.sh')
        out_file = os.path.join(self.tmpdir, 'rel-out.sh')
        result = self.run_configure(
            ['-t', 'openstack', '-r', 'rel-openrc.sh',
             '-o', out_file, '-w', self.tmpdir]
        )
        self.assertEqual(result.returncode, 0)
        content = self.read_file(out_file)
        self.assertIn('source', content)

    def test_relative_workdir_path(self):
        """Exercise relative workdir path branch."""
        rc_file = create_rc_file(self.tmpdir, 'rw-openrc.sh')
        out_file = os.path.join(self.tmpdir, 'rw-out.sh')
        result = self.run_configure(
            ['-t', 'openstack', '-r', rc_file, '-o', out_file, '-w', '.']
        )
        self.assertEqual(result.returncode, 0)

    def test_relative_k8s_file_path(self):
        """Exercise relative K8S file path branch."""
        result, content = self.run_configure_workflow(
            'platform', 'rk-openrc.sh', 'rk-out.sh',
            k8s_name='rk-kubeconfig'
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn('K8S_CONFIG_FILE=', content)

    def test_absolute_k8s_file_path(self):
        """Exercise absolute K8S file path branch."""
        rc_file = create_rc_file(self.tmpdir, 'ak-openrc.sh')
        k8s_file = create_k8s_file(self.tmpdir, 'ak-kubeconfig')
        out_file = os.path.join(self.tmpdir, 'ak-out.sh')
        result = self.run_configure(
            ['-t', 'platform', '-r', rc_file, '-k', k8s_file,
             '-o', out_file, '-w', self.tmpdir]
        )
        self.assertEqual(result.returncode, 0)
        content = self.read_file(out_file)
        self.assertIn(f'K8S_CONFIG_FILE={k8s_file}', content)

    def test_both_image_overrides(self):
        """Exercise both -p and -a overrides."""
        result, content = self.run_configure_workflow(
            'platform', 'bo-openrc.sh', 'bo-out.sh',
            k8s_name='bo-kubeconfig',
            extra_args=['-p', 'my/platform:v2', '-a', 'my/app:v2']
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn('PLATFORM_DOCKER_IMAGE=', content)
        self.assertIn('APPLICATION_DOCKER_IMAGE=', content)

    def test_default_no_explicit_type(self):
        """Exercise default which defaults to platform."""
        result, content = self.run_configure_workflow(
            None, 'dn-openrc.sh', 'dn-out.sh',
            k8s_name='dn-kubeconfig'
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn('CONFIG_TYPE=platform', content)


if __name__ == '__main__':
    unittest.main()
