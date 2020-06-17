"""
Copyright (c) 2020, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""

from wlsdeploy.util import dictionary_utils


class TargetConfiguration(object):
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

    def config_override_secrets(self):
        """
        Value of True indicates that we will put password placeholders in the model,
        and create a script to help create the secrets.
        :return: True if using config override secrets, False otherwise
        """
        value = dictionary_utils.get_element(self.config_dictionary, 'config_override_secrets')
        return (value is not None) and (str(value).lower() == 'true')

    def get_additional_output_types(self):
        """
        Return the additional output types for this target environment.
        This is a list of keys that map to output types.
        """
        types = dictionary_utils.get_element(self.config_dictionary, 'additional_output')
        if types is not None:
            return types.split(',')
        return []

    def get_validation_method(self):
        """
        Return the validation method for this target environment.
        :return: the validation method, or None
        """
        return dictionary_utils.get_element(self.config_dictionary, 'validation_method')

    def get_model_filters(self):
        """
        Return a dictionary of model filters for this target environment.
        :return: the dictionary of model filters
        """
        return dictionary_utils.get_dictionary_element(self.config_dictionary, 'model_filters')

    def get_variable_injectors(self):
        """
        Return a dictionary of variable injectors for this target environment.
        :return: the dictionary of variable injectors
        """
        return dictionary_utils.get_dictionary_element(self.config_dictionary, 'variable_injectors')

    def requires_secrets_script(self):
        """
        Determine if this configuration requires the generation of secrets scripts.
        :return: True if scripts should be generated, false otherwise
        """
        return self.credential_as_secret() or self.config_override_secrets()
