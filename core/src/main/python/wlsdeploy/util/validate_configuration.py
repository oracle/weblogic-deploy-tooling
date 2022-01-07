"""
Copyright (c) 2022, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""

# validation method keys
STRICT_METHOD = "strict"
LAX_METHOD = "lax"
WKTUI_METHOD = "wktui"

VALIDATION_METHODS = [STRICT_METHOD, LAX_METHOD, WKTUI_METHOD]


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
        self._allow_unresolved_archive_references = False
        self._allow_unresolved_environment_tokens = False
        self._allow_unresolved_file_tokens = False
        self._allow_unresolved_secret_tokens = False
        self._allow_unresolved_variable_tokens = False
        self._allow_version_invalid_attributes = False

        if key == LAX_METHOD:
            # almost no checks on archive, tokens, etc.
            self._allow_unresolved_archive_references = True
            self._allow_unresolved_environment_tokens = True
            self._allow_unresolved_file_tokens = True
            self._allow_unresolved_secret_tokens = True
            self._allow_unresolved_variable_tokens = True
            self._allow_version_invalid_attributes = True

        elif key == WKTUI_METHOD:
            # allow unresolved secret, file and environment tokens,
            # since they may not be present in the UI environment.
            # allow version-invalid attributes, since they are not applied.
            self._allow_unresolved_environment_tokens = True
            self._allow_unresolved_file_tokens = True
            self._allow_unresolved_secret_tokens = True
            self._allow_version_invalid_attributes = True

    def allow_unresolved_archive_references(self):
        """
        Returns True if unresolved archive references should be allowed during validation.
        Callers may reduce some message levels to INFO, or avoid throwing some exceptions.
        """
        return self._allow_unresolved_archive_references

    def allow_unresolved_environment_tokens(self):
        """
        Returns True if unresolved environment tokens should be allowed during validation.
        Callers may reduce some message levels to INFO, or avoid throwing some exceptions.
        """
        return self._allow_unresolved_environment_tokens

    def allow_unresolved_file_tokens(self):
        """
        Returns True if unresolved file tokens should be allowed during validation.
        This includes references to missing or empty token files.
        Callers may reduce some message levels to INFO, or avoid throwing some exceptions.
        """
        return self._allow_unresolved_file_tokens

    def allow_unresolved_variable_tokens(self):
        """
        Returns True if unresolved variable tokens should be allowed during validation.
        Callers may reduce some message levels to INFO, or avoid throwing some exceptions.
        """
        return self._allow_unresolved_variable_tokens

    def allow_unresolved_secret_tokens(self):
        """
        Returns True if unresolved secret tokens should be allowed during validation.
        This includes configured secrets directories that don't exist, or missing or empty secrets files.
        Callers may reduce some message levels to INFO, or avoid throwing some exceptions.
        """
        return self._allow_unresolved_secret_tokens

    def allow_version_invalid_attributes(self):
        """
        Returns True if version-invalid attributes should be overlooked during validation.
        Callers may reduce some message levels to INFO, or avoid throwing some exceptions.
        """
        return self._allow_version_invalid_attributes

    # set methods - use with caution

    def set_allow_unresolved_archive_references(self, allow):
        """
        Override the pre-defined setting to allow unresolved archive references.
        For use by tools that use non-lax validation mode, but don't consider archive files.
        """
        self._allow_unresolved_archive_references = allow
