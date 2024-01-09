"""
Copyright (c) 2021, 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import os
import shutil
import unittest

from wlsdeploy.util import env_helper


class BaseTestCase(unittest.TestCase):
    """
    Base class for unit tests.
    Provides helper functions for working with test directories, testing dictionary structures, etc.
    """

    def __init__(self, *args):
        unittest.TestCase.__init__(self, *args)
        self.TEST_CLASSES_DIR = os.path.abspath(os.path.join(os.getcwd(), '../../test-classes'))
        self.TEST_OUTPUT_DIR = os.path.abspath(os.path.join(os.getcwd(), '../../unit-tests'))
        self.TEST_CONFIG_DIR = os.path.join(self.TEST_OUTPUT_DIR, 'wdt-config')
        self.log_levels = {}

        self.original_config_dir = env_helper.getenv('WDT_CUSTOM_CONFIG', self.TEST_CONFIG_DIR)
        # config items may need to be copied from here
        self.INSTALLER_LIB_DIR = os.path.abspath(os.path.join(self.TEST_CLASSES_DIR, '../../../installer/src/main/lib'))

    def setUp(self):
        # subclasses should call this
        self._establish_directory(self.TEST_OUTPUT_DIR)

    def tearDown(self):
        # nothing to do now, but subclasses should call
        pass

    def _set_custom_config_dir(self, test_config_dir_name):
        config_dir = os.path.abspath(os.path.join(self.TEST_OUTPUT_DIR, test_config_dir_name))
        # copy self.original_config_dir contents to config_dir
        if os.path.isdir(config_dir):
            shutil.rmtree(config_dir)
        shutil.copytree(self.original_config_dir, config_dir)

        os.environ['WDT_CUSTOM_CONFIG'] = str(config_dir)
        return config_dir

    def _clear_custom_config_dir(self):
        os.environ['WDT_CUSTOM_CONFIG'] = self.original_config_dir

    def _establish_directory(self, name):
        """
        Create the directory if it does not exist
        """
        if not os.path.isdir(name):
            os.mkdir(name)

    def _match(self, value, dictionary, *args):
        dictionary_value = self._traverse(dictionary, *args)
        if str(dictionary_value) != str(value):
            key = '/'.join(list(args))
            self.fail(key + ' equals ' + str(dictionary_value) + ', should equal ' + str(value))

    def _match_values(self, description, actual, expected):
        self.assertEqual(actual, expected, description + " equals " + str(actual) + ", should equal " + str(expected))

    def _no_dictionary_key(self, dictionary, key):
        if key in dictionary:
            self.fail('Dictionary should not contain ' + key)

    def _traverse(self, dictionary, *args):
        """
        Recursively resolve keys in nested dictionaries.
        Example: _traverse(model_dict, TOPOLOGY, SERVER, ms1)
        :return: the last element in the key list
        """
        value = dictionary
        for arg in args:
            if not isinstance(value, dict):
                self.fail('Element ' + arg + ' parent is not a dictionary in ' + '/'.join(list(args)))
            if arg not in value:
                self.fail('Element ' + arg + ' not found in ' + '/'.join(list(args)))
            value = value[arg]
        return value

    def _establish_injector_config(self, config_dir):
        """
        Copy injector configuration items from the installer module.
        By default, use the test-classes/config directory.
        :param config_dir: directory where config will be added (must exist)
        """
        injectors_dir = os.path.join(self.INSTALLER_LIB_DIR, 'injectors')
        test_injectors_dir = os.path.join(config_dir, 'injectors')
        self._establish_directory(test_injectors_dir)

        for injector_name in os.listdir(injectors_dir):
            if injector_name.endswith('.json'):
                test_file = os.path.join(test_injectors_dir, injector_name)
                if not os.path.exists(test_file):
                    injector_file = os.path.join(injectors_dir, injector_name)
                    shutil.copy(injector_file, test_file)