"""
Copyright (c) 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import os

from java.lang import Exception as JException

from base_test import BaseTestCase
from wlsdeploy.json.json_translator import JsonToPython
from wlsdeploy.util import unicode_helper as str_helper
from wlsdeploy.util.target_configuration import TargetConfiguration

MIN_TARGET_FILES = 3

class TargetConfigurationTestCase(BaseTestCase):
    """
    Verify the syntax and content of every target configuration JSON file.
    """
    def __init__(self, *args):
        BaseTestCase.__init__(self, *args)
        self.TARGET_CONFIGS_DIR = (
            os.path.abspath(os.path.join(self.TEST_CLASSES_DIR, '../../../core/src/main/targetconfigs')))

    def setUp(self):
        BaseTestCase.setUp(self)

    def test_target_configurations(self):
        count = 0
        for subdir in os.listdir(self.TARGET_CONFIGS_DIR):
            directory = os.path.join(self.TARGET_CONFIGS_DIR, subdir)
            if os.path.isdir(directory):
                target_file = os.path.join(directory, 'target.json')
                if os.path.isfile(target_file):
                    try:
                        config_dictionary = JsonToPython(target_file).parse()
                        target_configuration = TargetConfiguration(config_dictionary)
                        target_configuration.validate_configuration(0, target_file)
                    except (Exception, JException), e:
                        self.fail('Error validating ' + target_file + ': ' + str_helper.to_string(e))

                    count += 1

        self.assertEquals(True, count >= MIN_TARGET_FILES, 'should be at least ' +
                          str_helper.to_string(MIN_TARGET_FILES) + ' target configuration files')
