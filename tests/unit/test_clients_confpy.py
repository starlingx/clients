#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Tests that execute conf.py files to achieve code coverage."""

import os
import sys
import unittest

sys.path.insert(
    0, os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)
from base_test import ConfPyTestCase  # noqa: E402


class _SharedConfTests:
    """Mixin with shared conf.py assertions.

    Subclasses must also inherit from ConfPyTestCase.
    """

    def test_project_name(self):
        """Verify project name."""
        self.assert_conf_value('project', u'StarlingX Clients')

    def test_extensions_has_openstackdocstheme(self):
        """Verify extensions list."""
        self.assert_conf_contains('extensions', 'openstackdocstheme')

    def test_openstackdocs_repo_name(self):
        """Verify openstackdocs_repo_name."""
        self.assert_conf_value(
            'openstackdocs_repo_name', 'starlingx/clients'
        )

    def test_openstackdocs_use_storyboard(self):
        """Verify openstackdocs_use_storyboard."""
        self.assertTrue(self.ns['openstackdocs_use_storyboard'])

    def test_openstackdocs_auto_name(self):
        """Verify openstackdocs_auto_name."""
        self.assertFalse(self.ns['openstackdocs_auto_name'])

    def test_source_suffix(self):
        """Verify source_suffix."""
        self.assert_conf_value('source_suffix', '.rst')

    def test_master_doc(self):
        """Verify master_doc."""
        self.assert_conf_value('master_doc', 'index')

    def test_exclude_patterns(self):
        """Verify exclude_patterns."""
        self.assert_conf_value('exclude_patterns', [])

    def test_pygments_style(self):
        """Verify pygments_style."""
        self.assert_conf_value('pygments_style', 'native')

    def test_html_theme(self):
        """Verify html_theme."""
        self.assert_conf_value('html_theme', 'starlingxdocs')

    def test_latex_elements(self):
        """Verify latex_elements is a dict."""
        self.assert_conf_type('latex_elements', dict)

    def test_latex_documents(self):
        """Verify latex_documents is a single-item list."""
        self.assert_conf_type('latex_documents', list)
        self.assertEqual(len(self.ns['latex_documents']), 1)

    def test_man_pages(self):
        """Verify man_pages is a single-item list."""
        self.assert_conf_type('man_pages', list)
        self.assertEqual(len(self.ns['man_pages']), 1)

    def test_texinfo_documents(self):
        """Verify texinfo_documents is a single-item list."""
        self.assert_conf_type('texinfo_documents', list)
        self.assertEqual(len(self.ns['texinfo_documents']), 1)


class TestDocConfPy(_SharedConfTests, ConfPyTestCase):
    """Execute and validate doc/source/conf.py."""

    conf_rel_path = ('doc', 'source', 'conf.py')

    def test_copyright(self):
        """Verify copyright."""
        self.assert_conf_value('copyright', u'2018, StarlingX')

    def test_author(self):
        """Verify author."""
        self.assert_conf_value('author', u'StarlingX')

    def test_templates_path(self):
        """Verify templates_path."""
        self.assert_conf_value('templates_path', ['_templates'])

    def test_language(self):
        """Verify language."""
        self.assert_conf_value('language', 'en')

    def test_htmlhelp_basename(self):
        """Verify htmlhelp_basename."""
        self.assert_conf_value('htmlhelp_basename', 'stx-clientsdoc')

    def test_latex_documents_content(self):
        """Verify latex_documents has expected tex file."""
        self.assertIn('stx-clients.tex', self.ns['latex_documents'][0])

    def test_man_pages_content(self):
        """Verify man_pages entry."""
        self.assertEqual(self.ns['man_pages'][0][1], 'stx-clients')

    def test_texinfo_documents_content(self):
        """Verify texinfo_documents entry."""
        self.assertIn('stx-clients', self.ns['texinfo_documents'][0])


class TestReleaseNotesConfPy(_SharedConfTests, ConfPyTestCase):
    """Execute and validate releasenotes/source/conf.py."""

    conf_rel_path = ('releasenotes', 'source', 'conf.py')

    def test_extensions_has_reno(self):
        """Verify reno extension."""
        self.assert_conf_contains('extensions', 'reno.sphinxext')

    def test_release(self):
        """Verify release is empty."""
        self.assert_conf_value('release', '')

    def test_version(self):
        """Verify version is empty."""
        self.assert_conf_value('version', '')

    def test_htmlhelp_basename(self):
        """Verify htmlhelp_basename."""
        self.assert_conf_value(
            'htmlhelp_basename', 'stx-clientsreleasenotesdoc'
        )

    def test_locale_dirs(self):
        """Verify locale_dirs."""
        self.assert_conf_value('locale_dirs', ['locale/'])


if __name__ == '__main__':
    unittest.main()
