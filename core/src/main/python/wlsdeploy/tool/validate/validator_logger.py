"""
Copyright (c) 2020, 2022, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import java.util.logging.Level as Level

from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.util.enum import Enum

STANDALONE = 'STANDALONE'
TOOL = 'TOOL'


class ValidatorLogger(PlatformLogger):

    def __init__(self, logger_name, mode_type=TOOL,
                 resource_bundle_name='oracle.weblogic.deploy.messages.wlsdeploy_rb'):
        PlatformLogger.__init__(self, logger_name, resource_bundle_name)
        self._mode_type = mode_type
        # The logger properties is set to level FINE, which is for tool mode. Reset that to FINER for
        # standalone mode. This will of course not help the standalone user that wants FINE level
        # but the logs are for WDT troubleshooting.
        if self.get_level() == Level.FINE and self._mode_type == STANDALONE:
            self.set_level(Level.FINER)

    def info(self, message, *args, **kwargs):
        """
        Log an info-level message.
        :param message: the message key
        :param args: the arguments to use to populate the message placeholders
        :param kwargs: the keyword arguments
        """
        method = kwargs.pop('method_name', None)
        clazz = kwargs.pop('class_name', None)
        error = kwargs.pop('error', None)
        level = Level.INFO
        if self._mode_type == TOOL:
            level = Level.FINE
        record = self._get_log_record(level, clazz, method, message, error, *args)
        self.logger.log(record)
