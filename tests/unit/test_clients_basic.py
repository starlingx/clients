#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Basic functionality tests for the clients project."""

import os
import sys
import unittest

import yaml

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
from base_test import BaseClientTestCase  # noqa: E402


class TestProjectStructure(BaseClientTestCase):
    """Validate project file structure and layout."""

    EXPECTED_FILES = [
        'tox.ini', '.zuul.yaml', 'test-requirements.txt',
        'LICENSE', 'README.rst', '.gitignore', '.gitreview',
    ]
    EXPECTED_DIRS = ['remote_cli', 'doc', 'releasenotes']

    def test_project_root_exists(self):
        """Verify project root directory exists."""
        self.assertTrue(os.path.isdir(self.root))

    def test_expected_files_exist(self):
        """Verify all expected project files exist."""
        for fname in self.EXPECTED_FILES:
            self.assert_file_exists(fname)

    def test_expected_directories_exist(self):
        """Verify all expected directories exist."""
        for dname in self.EXPECTED_DIRS:
            self.assert_dir_exists(dname)


class TestShellScriptsPresence(BaseClientTestCase):
    """Verify all expected shell scripts are present."""

    SCRIPTS = [
        'client_wrapper.sh', 'configure_client.sh',
        'config_aliases.sh', 'docker_image_version.sh',
    ]
    EXECUTABLE_SCRIPTS = ['client_wrapper.sh', 'configure_client.sh']

    def test_scripts_exist(self):
        """Verify all expected shell scripts exist."""
        for fname in self.SCRIPTS:
            self.assert_file_exists('remote_cli', fname)

    def test_executable_scripts(self):
        """Verify expected scripts are executable."""
        for fname in self.EXECUTABLE_SCRIPTS:
            path = os.path.join(self.cli_dir, fname)
            self.assertTrue(
                os.access(path, os.X_OK),
                msg=f"{fname} not executable"
            )

    def test_readme_exists(self):
        """Verify README exists in remote_cli."""
        self.assert_file_exists('remote_cli', 'README')


class TestConfigurationFiles(BaseClientTestCase):
    """Test configuration file validity."""

    def test_tox_ini_not_empty(self):
        """Verify tox.ini is not empty."""
        path = os.path.join(self.root, 'tox.ini')
        self.assertGreater(os.path.getsize(path), 0)

    def test_tox_ini_has_required_sections(self):
        """Verify tox.ini contains required sections."""
        content = self.read_root_file('tox.ini')
        for section in ['envlist', '[testenv:linters]', '[testenv:pep8]']:
            self.assertIn(section, content)

    def test_zuul_yaml_valid(self):
        """Verify .zuul.yaml is valid YAML with project entry."""
        data = self.load_zuul_yaml()
        self.assertIsInstance(data, list)
        project_entries = [i for i in data if 'project' in i]
        self.assertGreater(len(project_entries), 0)

    def test_test_requirements_has_tools(self):
        """Verify test-requirements.txt includes required tools."""
        content = self.read_root_file('test-requirements.txt')
        for tool in ['bashate', 'bandit', 'yamllint']:
            self.assertIn(tool, content)

    def test_gitreview_content(self):
        """Verify .gitreview has proper content."""
        content = self.read_root_file('.gitreview')
        self.assertIn('[gerrit]', content)


class TestDocConfiguration(BaseClientTestCase):
    """Test documentation configuration files."""

    DOC_PATHS = [
        ('doc', 'source', 'conf.py'),
        ('releasenotes', 'source', 'conf.py'),
        ('doc', 'source', 'index.rst'),
        ('releasenotes', 'source', 'index.rst'),
        ('doc', 'requirements.txt'),
    ]

    def test_doc_files_exist(self):
        """Verify all documentation files exist."""
        for parts in self.DOC_PATHS:
            self.assert_file_exists(*parts)

    def test_conf_files_have_project_name(self):
        """Verify conf.py files have project name."""
        for parts in [
            ('doc', 'source', 'conf.py'),
            ('releasenotes', 'source', 'conf.py'),
        ]:
            content = self.read_root_file(*parts)
            self.assertIn('StarlingX Clients', content)

    def test_release_notes_yaml_valid(self):
        """Verify release notes YAML files are valid."""
        notes_dir = os.path.join(self.root, 'releasenotes', 'notes')
        if os.path.isdir(notes_dir):
            for fname in os.listdir(notes_dir):
                if fname.endswith('.yaml'):
                    fpath = os.path.join(notes_dir, fname)
                    with open(fpath, 'r', encoding='utf-8') as fobj:
                        data = yaml.safe_load(fobj)
                    self.assertIsNotNone(data)


class TestLicenseCompliance(BaseClientTestCase):
    """Test license and copyright compliance."""

    def test_license_is_apache(self):
        """Verify LICENSE file contains Apache 2.0."""
        content = self.read_root_file('LICENSE')
        self.assertIn('Apache License', content)

    def test_shell_scripts_have_license_header(self):
        """Verify shell scripts have SPDX license header."""
        for fname in os.listdir(self.cli_dir):
            if not fname.endswith('.sh'):
                continue
            fpath = os.path.join(self.cli_dir, fname)
            content = self.read_file(fpath)
            if len(content.splitlines()) > 5:
                self.assertIn(
                    'SPDX-License-Identifier', content,
                    msg=f"Missing license header in {fname}"
                )

    def test_python_configs_have_license_header(self):
        """Verify Python config files have SPDX license header."""
        for parts in [
            ('doc', 'source', 'conf.py'),
            ('releasenotes', 'source', 'conf.py'),
        ]:
            path = os.path.join(self.root, *parts)
            content = self.read_file(path)
            self.assertIn(
                'SPDX-License-Identifier', content,
                msg=f"Missing license in {path}"
            )


if __name__ == '__main__':
    unittest.main()
