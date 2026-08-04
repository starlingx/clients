#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Base test classes for clients test suite.

Provides shared setup, file reading, shell execution,
and conf.py validation helpers using OOP/DRY principles.
"""

import os
import shutil
import subprocess
import tempfile
import unittest

import yaml


class BaseClientTestCase(unittest.TestCase):
    """Base class with shared project paths.

    Provides cls.root and cls.cli_dir used by
    most test classes in this project.
    """

    @classmethod
    def setUpClass(cls):
        """Set up project root and cli paths."""
        cls.root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cls.cli_dir = os.path.join(cls.root, "remote_cli")

    @classmethod
    def load_zuul_yaml(cls):
        """Load .zuul.yaml handling !encrypted tags.

        Returns:
            list: Parsed YAML data as list of dicts.
        """
        path = os.path.join(cls.root, ".zuul.yaml")
        with open(path, "r", encoding="utf-8") as fobj:
            content = fobj.read()
        loader = yaml.SafeLoader
        loader.add_multi_constructor(
            "!encrypted/",
            lambda loader, sfx, node: (
                loader.construct_sequence(node)
                if node.id == "sequence"
                else loader.construct_mapping(node)
            ),
        )
        return yaml.load(content, Loader=loader)  # noqa

    def read_file(self, path):
        """Read and return file content.

        Args:
            path: Absolute path to file.

        Returns:
            str: File content.
        """
        with open(path, "r", encoding="utf-8") as fobj:
            return fobj.read()

    def read_root_file(self, *parts):
        """Read file relative to project root.

        Args:
            *parts: Path components relative to root.

        Returns:
            str: File content.
        """
        return self.read_file(os.path.join(self.root, *parts))

    def assert_file_exists(self, *parts):
        """Assert file exists relative to project root.

        Args:
            *parts: Path components relative to root.
        """
        path = os.path.join(self.root, *parts)
        self.assertTrue(os.path.isfile(path), f"Missing: {path}")

    def assert_dir_exists(self, *parts):
        """Assert directory exists relative to project root.

        Args:
            *parts: Path components relative to root.
        """
        path = os.path.join(self.root, *parts)
        self.assertTrue(os.path.isdir(path), f"Missing: {path}")

    def assert_file_contains(self, path, *strings):
        """Assert file contains all given strings.

        Args:
            path: Absolute path to file.
            *strings: Strings that must be present.
        """
        content = self.read_file(path)
        for s in strings:
            self.assertIn(s, content, f"Missing '{s}' in {path}")

    def assert_root_file_contains(self, parts, *strings):
        """Assert file relative to root contains strings.

        Args:
            parts: Tuple of path components relative to root.
            *strings: Strings that must be present.
        """
        path = os.path.join(self.root, *parts)
        self.assert_file_contains(path, *strings)


class ShellScriptTestCase(BaseClientTestCase):
    """Base for testing shell scripts.

    Provides syntax checks and content assertions.
    """

    script_name = None  # Override in subclass

    @classmethod
    def setUpClass(cls):
        """Set up script path."""
        super().setUpClass()
        if cls.script_name:
            cls.script = os.path.join(cls.cli_dir, cls.script_name)

    def assert_valid_bash_syntax(self):
        """Assert script passes bash -n syntax check."""
        result = subprocess.run(
            ["bash", "-n", self.script],
            capture_output=True, text=True
        )
        self.assertEqual(
            result.returncode, 0,
            msg=f"Syntax error: {result.stderr}"
        )

    def assert_shebang(self, expected="#!/bin/bash"):
        """Assert script starts with expected shebang.

        Args:
            expected: Expected first line content.
        """
        with open(self.script, "r", encoding="utf-8") as fobj:
            first_line = fobj.readline().strip()
        self.assertEqual(first_line, expected)

    def assert_script_contains(self, *strings):
        """Assert script file contains all given strings.

        Args:
            *strings: Strings that must be present.
        """
        self.assert_file_contains(self.script, *strings)

    def read_script(self):
        """Read and return script content.

        Returns:
            str: Script file content.
        """
        return self.read_file(self.script)


class TempDirTestCase(BaseClientTestCase):
    """Base with temporary directory lifecycle."""

    @classmethod
    def setUpClass(cls):
        """Set up paths and temp directory."""
        super().setUpClass()
        cls.tmpdir = tempfile.mkdtemp()

    @classmethod
    def tearDownClass(cls):
        """Clean up temp directory."""
        shutil.rmtree(cls.tmpdir, ignore_errors=True)

    def run_script(self, script, args, cwd=None, env=None, timeout=10):
        """Run a bash script and return result.

        Args:
            script: Path to script.
            args: List of arguments.
            cwd: Working directory.
            env: Environment dict.
            timeout: Timeout in seconds.

        Returns:
            subprocess.CompletedProcess: Execution result.
        """
        return subprocess.run(
            ["bash", script] + args,
            capture_output=True,
            text=True,
            cwd=cwd or self.tmpdir,
            env=env,
            timeout=timeout,
        )


class ConfigureClientTestCase(TempDirTestCase):
    """Base for testing configure_client.sh execution.

    Provides shared workflow for creating RC/K8S files,
    running configure_client.sh, and reading output.
    """

    @classmethod
    def setUpClass(cls):
        """Set up configure_client script path."""
        super().setUpClass()
        cls.configure_script = os.path.join(
            cls.cli_dir, 'configure_client.sh'
        )

    def run_configure(self, args, cwd=None):
        """Run configure_client.sh with args.

        Args:
            args: List of arguments.
            cwd: Working directory override.

        Returns:
            subprocess.CompletedProcess: Result.
        """
        return self.run_script(self.configure_script, args, cwd=cwd)

    def run_configure_workflow(
        self, client_type, rc_name, out_name,
        keystone=False, k8s_name=None, extra_args=None
    ):
        """Run configure_client.sh and return result with output.

        Args:
            client_type: Client type (openstack/platform) or None.
            rc_name: RC filename to create.
            out_name: Output filename.
            keystone: Use keystone auth URL.
            k8s_name: K8S filename to create.
            extra_args: Additional CLI arguments.

        Returns:
            tuple: (CompletedProcess, output file content str).
        """
        from tests.test_helpers import create_k8s_file
        from tests.test_helpers import create_rc_file
        rc_file = create_rc_file(self.tmpdir, rc_name, keystone=keystone)
        out_file = os.path.join(self.tmpdir, out_name)
        args = ['-r', rc_file, '-o', out_file, '-w', self.tmpdir]
        if client_type:
            args = ['-t', client_type] + args
        if k8s_name:
            k8s_file = create_k8s_file(self.tmpdir, k8s_name)
            args.extend(['-k', k8s_file])
        if extra_args:
            args.extend(extra_args)
        result = self.run_script(self.configure_script, args)
        content = ''
        if os.path.isfile(out_file):
            content = self.read_file(out_file)
        return result, content


class ConfPyTestCase(BaseClientTestCase):
    """Base for testing conf.py files via exec.

    Subclasses set conf_rel_path as tuple of path parts
    relative to project root.
    """

    conf_rel_path = ()  # Override: e.g. ('doc', 'source', 'conf.py')

    @classmethod
    def setUpClass(cls):
        """Load conf.py via exec."""
        super().setUpClass()
        cls.conf_path = os.path.join(cls.root, *cls.conf_rel_path)
        cls.ns = {}
        with open(cls.conf_path, "r", encoding="utf-8") as fobj:
            code = compile(fobj.read(), cls.conf_path, "exec")
            exec(code, cls.ns)  # noqa

    def assert_conf_value(self, key, expected):
        """Assert conf namespace has expected value.

        Args:
            key: Variable name in conf namespace.
            expected: Expected value.
        """
        self.assertEqual(self.ns[key], expected)

    def assert_conf_contains(self, key, item):
        """Assert conf namespace collection contains item.

        Args:
            key: Variable name in conf namespace.
            item: Item that must be in the collection.
        """
        self.assertIn(item, self.ns[key])

    def assert_conf_type(self, key, expected_type):
        """Assert conf namespace value is of expected type.

        Args:
            key: Variable name in conf namespace.
            expected_type: Expected type.
        """
        self.assertIsInstance(self.ns[key], expected_type)
