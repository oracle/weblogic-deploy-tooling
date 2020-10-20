"""
Copyright (c) 2017, 2018, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""
import java.util.logging.Level as Level
from wlsdeploy.logging.platform_logger import PlatformLogger

from systemtest.aliases.verifier_helper import VerifierHelper
import systemtest.aliases.all_utils as all_utils

_logger = PlatformLogger('test.aliases.verify', resource_bundle_name='systemtest_rb')
_logger.set_level(Level.FINEST)
CLASS_NAME = 'Verifier'


class Verifier(VerifierHelper):
    """
    Verify the generated MBean and attribute information against the aliases.
    """

    IGNORE_DICT_FOLDERS = ['Realm']
    IGNORE_ALIAS_FOLDERS = []

    def __init__(self, model_context, dictionary):
        VerifierHelper.__init__(self, model_context, dictionary)

    def verify(self):
        """
        Verify the offline/online version generated dictionary.
        :return: False
        """
        _method_name = 'verify'
        _logger.entering(class_name=CLASS_NAME, method_name=_method_name)
        self.check_attributes()
        has_errors = self.has_errors()
        _logger.exiting(result=all_utils.str_bool(has_errors), class_name=CLASS_NAME, method_name=_method_name)
        return has_errors
