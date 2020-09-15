"""
Copyright (c) 2020, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""

from wlsdeploy.util import dictionary_utils

# types for credential method
CREDENTIALS_METHOD = "credentials_method"

# Overrides the Kubernetes secret name for the WebLogic admin user credential
WLS_CREDENTIALS_NAME = "wls_credentials_name"

# put secret tokens in the model, and build a script to create the secrets.
SECRETS_METHOD = 'secrets'

# put password placeholders in the model, and build a script to create the secrets.
CONFIG_OVERRIDES_SECRETS_METHOD = 'config_override_secrets'

CREDENTIALS_METHODS = [
    SECRETS_METHOD,
    CONFIG_OVERRIDES_SECRETS_METHOD
]


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

    def get_credentials_method(self):
        """
        Returns the method for handling credentials in the model.
        :return: the method for handling credentials
        """
        return dictionary_utils.get_element(self.config_dictionary, CREDENTIALS_METHOD)

    def get_wls_credentials_name(self):
        """
        Returns the method for handling credentials in the model.
        :return: the method for handling credentials
        """
        return dictionary_utils.get_element(self.config_dictionary, WLS_CREDENTIALS_NAME)

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

    def uses_credential_secrets(self):
        """
        Determine if this configuration uses secrets to manage credentials.
        :return: True if secrets are used, False otherwise
        """
        return self.get_credentials_method() in [SECRETS_METHOD, CONFIG_OVERRIDES_SECRETS_METHOD]

    def manages_credentials(self):
        """
        Determine if this configuration manages credential values in the model.
        If this is True, credentials will not go into the properties file.
        :return: True if credential values are managed, False otherwise
        """
        return self.get_credentials_method() in [SECRETS_METHOD, CONFIG_OVERRIDES_SECRETS_METHOD]
