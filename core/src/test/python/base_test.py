"""
Copyright (c) 2021, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import os
import shutil
import unittest

from java.util.logging import Level

from wlsdeploy.logging.platform_logger import PlatformLogger


class BaseTestCase(unittest.TestCase):
    """
    Base class for unit tests.
    Provides helper functions for working with test directories, testing dictionary structures, etc.
    """

    def __init__(self, *args):
        unittest.TestCase.__init__(self, *args)
        self.TEST_CLASSES_DIR = os.path.abspath(os.getcwd() + '/../../test-classes')
        self.TEST_OUTPUT_DIR = os.path.abspath(os.getcwd() + '/../../unit-tests')
        self.log_levels = {}

        # config items may need to be copied from here
        self.INSTALLER_LIB_DIR = os.path.abspath(self.TEST_CLASSES_DIR + '/../../../installer/src/main/lib')

    def setUp(self):
        # subclasses should call this
        self._establish_directory(self.TEST_OUTPUT_DIR)

    def tearDown(self):
        # nothing to do now, but subclasses should call
        pass

    def _set_custom_config_dir(self, dir):
        os.environ['WDT_CUSTOM_CONFIG'] = str(dir)

    def _clear_custom_config_dir(self):
        del os.environ['WDT_CUSTOM_CONFIG']

    def _establish_directory(self, name):
        """
        Create the directory if it does not exist
        """
        if not os.path.isdir(name):
            os.mkdir(name)

    def _suspend_logs(self, *args):
        """
        Disable the specified log names, and store their previous levels
        """
        for name in args:
            logger = PlatformLogger(name)
            self.log_levels[name] = logger.get_level()
            logger.set_level(Level.OFF)

    def _restore_logs(self):
        """
        Restore suspended logs to their original levels
        """
        for key in self.log_levels:
            logger = PlatformLogger(key)
            logger.set_level(self.log_levels[key])

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

        test_keywords_file = os.path.join(config_dir, 'variable_keywords.json')
        if not os.path.exists(test_keywords_file):
            keywords_file = os.path.join(self.INSTALLER_LIB_DIR, 'variable_keywords.json')
            shutil.copy(keywords_file, test_keywords_file)
