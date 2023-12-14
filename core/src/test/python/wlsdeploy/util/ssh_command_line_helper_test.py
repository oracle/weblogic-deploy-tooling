"""
Copyright (c) 2023, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at http://oss.oracle.com/licenses/upl.
"""
import os
import unittest

from wlsdeploy.util.ssh_command_line_helper import SSHUnixCommandLineHelper
from wlsdeploy.util.ssh_command_line_helper import SSHWindowsCommandLineHelper

class SSHCommandLineHelperTest(unittest.TestCase):
    _resources_dir = '../../test-classes'
    _windows_output = 'windows_dir_listing.txt'
    _unix_output = 'unix_dir_listing.txt'

    def __init__(self, *args):
        unittest.TestCase.__init__(self, *args)
        self._windows_output_lines = self._load_output_file(self._windows_output)
        self._unix_output_lines = self._load_output_file(self._unix_output)

    def test_windows_directory_listing_no_filtering(self):
        helper = SSHWindowsCommandLineHelper()
        listing = helper.get_directory_contents(self._windows_output_lines, False)
        self.assertNotEqual(listing, None)
        self.assertEqual(isinstance(listing, list), True)
        self.assertEqual(len(listing), 2)

    def test_windows_directory_listing_files_only(self):
        helper = SSHWindowsCommandLineHelper()
        listing = helper.get_directory_contents(self._windows_output_lines, True)
        self.assertNotEqual(listing, None)
        self.assertEqual(isinstance(listing, list), True)
        self.assertEqual(len(listing), 1)

    def test_windows_directory_listing_zip_only(self):
        helper = SSHWindowsCommandLineHelper()
        listing = helper.get_directory_contents(self._windows_output_lines, False, r'^.+\.zip$')
        self.assertNotEqual(listing, None)
        self.assertEqual(isinstance(listing, list), True)
        self.assertEqual(len(listing), 1)

    def test_windows_directory_listing_files_only_zip_only(self):
        helper = SSHWindowsCommandLineHelper()
        listing = helper.get_directory_contents(self._windows_output_lines, True, r'^.+\.zip$')
        self.assertNotEqual(listing, None)
        self.assertEqual(isinstance(listing, list), True)
        self.assertEqual(len(listing), 1)

    def test_windows_directory_listing_zip_only_not_found(self):
        helper = SSHWindowsCommandLineHelper()
        listing = helper.get_directory_contents(self._windows_output_lines, False, r'^.+\.jar$')
        self.assertNotEqual(listing, None)
        self.assertEqual(isinstance(listing, list), True)
        self.assertEqual(len(listing), 0)

    def test_windows_directory_listing_files_only_zip_only_not_found(self):
        helper = SSHWindowsCommandLineHelper()
        listing = helper.get_directory_contents(self._windows_output_lines, True, r'^.+\.jar$')
        self.assertNotEqual(listing, None)
        self.assertEqual(isinstance(listing, list), True)
        self.assertEqual(len(listing), 0)

    def test_windows_directory_listing_starts_with_weblogic_deploy(self):
        helper = SSHWindowsCommandLineHelper()
        listing = helper.get_directory_contents(self._windows_output_lines, False, r'^weblogic-deploy.*$')
        self.assertNotEqual(listing, None)
        self.assertEqual(isinstance(listing, list), True)
        self.assertEqual(len(listing), 2)

    def test_windows_directory_listing_starts_with_weblogic_deploy_files_only(self):
        helper = SSHWindowsCommandLineHelper()
        listing = helper.get_directory_contents(self._windows_output_lines, True, r'^weblogic-deploy.*$')
        self.assertNotEqual(listing, None)
        self.assertEqual(isinstance(listing, list), True)
        self.assertEqual(len(listing), 1)

    def test_unix_directory_listing_no_filtering(self):
        helper = SSHUnixCommandLineHelper()
        listing = helper.get_directory_contents(self._unix_output_lines, False)
        self.assertNotEqual(listing, None)
        self.assertEqual(isinstance(listing, list), True)
        self.assertEqual(len(listing), 2)

    def test_unix_directory_listing_files_only(self):
        helper = SSHUnixCommandLineHelper()
        listing = helper.get_directory_contents(self._unix_output_lines, True)
        self.assertNotEqual(listing, None)
        self.assertEqual(isinstance(listing, list), True)
        self.assertEqual(len(listing), 1)

    def test_unix_directory_listing_zip_only(self):
        helper = SSHUnixCommandLineHelper()
        listing = helper.get_directory_contents(self._unix_output_lines, False, r'^.+\.zip$')
        self.assertNotEqual(listing, None)
        self.assertEqual(isinstance(listing, list), True)
        self.assertEqual(len(listing), 1)

    def test_unix_directory_listing_files_only_zip_only(self):
        helper = SSHUnixCommandLineHelper()
        listing = helper.get_directory_contents(self._unix_output_lines, True, r'^.+\.zip$')
        self.assertNotEqual(listing, None)
        self.assertEqual(isinstance(listing, list), True)
        self.assertEqual(len(listing), 1)

    def test_unix_directory_listing_zip_only_not_found(self):
        helper = SSHUnixCommandLineHelper()
        listing = helper.get_directory_contents(self._unix_output_lines, False, r'^.+\.jar$')
        self.assertNotEqual(listing, None)
        self.assertEqual(isinstance(listing, list), True)
        self.assertEqual(len(listing), 0)

    def test_unix_directory_listing_files_only_zip_only_not_found(self):
        helper = SSHUnixCommandLineHelper()
        listing = helper.get_directory_contents(self._unix_output_lines, True, r'^.+\.jar$')
        self.assertNotEqual(listing, None)
        self.assertEqual(isinstance(listing, list), True)
        self.assertEqual(len(listing), 0)

    def test_unix_directory_listing_starts_with_weblogic_deploy(self):
        helper = SSHUnixCommandLineHelper()
        listing = helper.get_directory_contents(self._unix_output_lines, False, r'^weblogic-deploy.*$')
        self.assertNotEqual(listing, None)
        self.assertEqual(isinstance(listing, list), True)
        self.assertEqual(len(listing), 2)

    def test_unix_directory_listing_starts_with_weblogic_deploy_files_only(self):
        helper = SSHUnixCommandLineHelper()
        listing = helper.get_directory_contents(self._unix_output_lines, True, r'^weblogic-deploy.*$')
        self.assertNotEqual(listing, None)
        self.assertEqual(isinstance(listing, list), True)
        self.assertEqual(len(listing), 1)

    def _load_output_file(self, name):
        file_name = os.path.abspath(os.path.join(self._resources_dir, name))
        test_output_file = open(file_name, 'r')
        text = test_output_file.read()
        if text is not None:
            lines = text.split('\n')
        else:
            lines = None
        return lines