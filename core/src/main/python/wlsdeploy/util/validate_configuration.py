"""
Copyright (c) 2020, 2021, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""

# validation method keys
STRICT_METHOD = "strict"
LAX_METHOD = "lax"

VALIDATION_METHODS = [STRICT_METHOD, LAX_METHOD]


class ValidateConfiguration(object):
    """
    Provide validation configuration based on a validation method key.
    """
    _class_name = 'ValidateConfiguration'

    def __init__(self, key):
        """
        Initialize the validate configuration based on the key.
        :param key: a validation method key
        """
        self._key = key

        # defaults are values for STRICT mode
        self._allow_missing_environment_variables = False
        self._allow_missing_file_variables = False
        self._allow_missing_secrets = False
        self._allow_missing_variables = False
        self._allow_version_invalid_attributes = False

        if key == LAX_METHOD:
            self._allow_missing_environment_variables = True
            self._allow_missing_file_variables = True
            self._allow_missing_secrets = True
            self._allow_missing_variables = True
            self._allow_version_invalid_attributes = True

    def allow_missing_environment_variables(self):
        """
        Returns True if missing environment variables should be overlooked during validation.
        Callers may reduce some WARNING or SEVERE messages to INFO.
        """
        return self._allow_missing_environment_variables

    def allow_missing_file_variables(self):
        """
        Returns True if missing file variables should be overlooked during validation.
        This includes empty variable files.
        Callers may reduce some WARNING or SEVERE messages to INFO.
        """
        return self._allow_missing_file_variables

    def allow_missing_variables(self):
        """
        Returns True if missing variables should be overlooked during validation.
        Callers may reduce some WARNING or SEVERE messages to INFO.
        """
        return self._allow_missing_variables

    def allow_missing_secrets(self):
        """
        Returns True if missing secrets should be overlooked during validation.
        This includes declaring secrets directories that don't exist, or empty secrets files.
        Callers may reduce some WARNING or SEVERE messages to INFO.
        """
        return self._allow_missing_secrets

    def allow_version_invalid_attributes(self):
        """
        Returns True if version-invalid attributes should be overlooked during validation.
        Callers may reduce some WARNING or SEVERE messages to INFO.
        """
        return self._allow_version_invalid_attributes
