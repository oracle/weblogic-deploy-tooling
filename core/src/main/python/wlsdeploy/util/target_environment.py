"""
Copyright (c) 2020, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""

from wlsdeploy.util import dictionary_utils


class TargetEnvironment(object):
    """
    Provide access to fields in the target.json JSON file of a target environment.
    """
    _class_name = 'TargetEnvironment'

    def __init__(self, config_dictionary):
        """
        Initialize the configuration with the target file's dictionary.
        :param config_dictionary: the top-level dictionary from the target.json file
        """
        if config_dictionary is None:
            self.config_dictionary = {}
        else:
            self.config_dictionary = config_dictionary

    def credential_as_secret(self):
        """
        Value of True indicates that credential fields in the model should use secret tokens,
        and we will create a script to help create the secrets.
        :return: True if credentials should be represented as secrets, False otherwise
        """
        value = dictionary_utils.get_element(self.config_dictionary, 'credential_as_secret')
        return (value is not None) and (str(value).lower() == 'true')
