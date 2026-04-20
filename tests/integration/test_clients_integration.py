#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Integration tests for the clients project."""

import os
import subprocess
import sys
import unittest

import yaml

sys.path.insert(
    0, os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)
from base_test import ConfigureClientTestCase  # noqa: E402


class TestProjectIntegration(ConfigureClientTestCase):
    """Cross-component integration tests."""

    SCRIPT_REFERENCES = [
        'client_wrapper.sh', 'config_aliases.sh',
        'docker_image_version.sh', 'configure_client.sh',
    ]
    CROSS_REFERENCES = [
        ('configure_client.sh', ['config_aliases.sh',
                                 'docker_image_version.sh']),
        ('config_aliases.sh', ['client_wrapper.sh']),
    ]

    def test_all_shell_scripts_have_valid_syntax(self):
        """Verify all .sh files pass bash -n syntax check."""
        for fname in os.listdir(self.cli_dir):
            if not fname.endswith('.sh'):
                continue
            fpath = os.path.join(self.cli_dir, fname)
            result = subprocess.run(
                ['bash', '-n', fpath],
                capture_output=True, text=True
            )
            self.assertEqual(
                result.returncode, 0,
                msg=f"Syntax error in {fname}: {result.stderr}"
            )

    def test_all_yaml_files_valid(self):
        """Verify all YAML files are parseable."""
        for dirpath, _, filenames in os.walk(self.root):
            if '.tox' in dirpath:
                continue
            for fname in filenames:
                if not fname.endswith(('.yaml', '.yml')):
                    continue
                fpath = os.path.join(dirpath, fname)
                content = self.read_file(fpath)
                if '!encrypted' in content:
                    continue
                try:
                    yaml.safe_load(content)
                except yaml.YAMLError:
                    self.fail(f"Invalid YAML: {fpath}")

    def test_zuul_references_valid_tox_envs(self):
        """Verify .zuul.yaml job names reference valid tox envs."""
        data = self.load_zuul_yaml()
        project_entry = next(
            (i['project'] for i in data if 'project' in i), None
        )
        self.assertIsNotNone(project_entry)
        self.assertIn('check', project_entry)

    def test_tox_ini_references_test_requirements(self):
        """Verify tox.ini references test-requirements.txt."""
        content = self.read_root_file('tox.ini')
        self.assertIn('test-requirements.txt', content)

    def test_cross_script_references(self):
        """Verify scripts reference each other correctly."""
        for script_name, refs in self.CROSS_REFERENCES:
            content = self.read_file(
                os.path.join(self.cli_dir, script_name)
            )
            for ref in refs:
                self.assertIn(
                    ref, content,
                    msg=f"{script_name} missing ref to {ref}"
                )

    def test_no_broken_script_references(self):
        """Verify scripts don't reference non-existent files."""
        for ref in self.SCRIPT_REFERENCES:
            self.assert_file_exists('remote_cli', ref)


class TestEndToEndWorkflow(ConfigureClientTestCase):
    """Test end-to-end configure_client workflow."""

    def test_full_openstack_workflow(self):
        """Test complete openstack client config."""
        result, content = self.run_configure_workflow(
            'openstack', 'e2e-openrc.sh', 'e2e-output.sh', keystone=True
        )
        self.assertEqual(result.returncode, 0)
        for expected in ['source', 'CONFIG_TYPE=application', 'OSC_WORKDIR=']:
            self.assertIn(expected, content)

    def test_full_platform_workflow(self):
        """Test complete platform client config."""
        result, content = self.run_configure_workflow(
            'platform', 'e2e-plat-openrc.sh', 'e2e-plat-output.sh',
            keystone=True, k8s_name='e2e-kubeconfig'
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn('CONFIG_TYPE=platform', content)
        self.assertIn('K8S_CONFIG_FILE=', content)

    def test_default_type_is_platform(self):
        """Verify default client type is platform."""
        result, content = self.run_configure_workflow(
            None, 'def-openrc.sh', 'def-output.sh',
            k8s_name='def-kubeconfig'
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn('CONFIG_TYPE=platform', content)

    def test_workdir_absolute_path(self):
        """Verify absolute workdir path is preserved."""
        result, content = self.run_configure_workflow(
            'openstack', 'abs-openrc.sh', 'abs-output.sh'
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn(f'OSC_WORKDIR={self.tmpdir}', content)


if __name__ == '__main__':
    unittest.main()
