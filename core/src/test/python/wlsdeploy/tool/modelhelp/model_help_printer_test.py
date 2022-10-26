"""
Copyright (c) 2020, 2022, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import unittest
from StringIO import StringIO

import sys
from oracle.weblogic.deploy.util import CLAException

from wlsdeploy.aliases.aliases import Aliases
from wlsdeploy.aliases.model_constants import ADMIN_PASSWORD, SOURCE_PATH
from wlsdeploy.aliases.model_constants import DOMAIN_INFO
from wlsdeploy.aliases.model_constants import JDBC_DRIVER_PARAMS
from wlsdeploy.aliases.model_constants import JDBC_RESOURCE
from wlsdeploy.aliases.model_constants import JDBC_SYSTEM_RESOURCE
from wlsdeploy.aliases.model_constants import RCU_DB_INFO
from wlsdeploy.aliases.model_constants import RESOURCES
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.modelhelp.model_help_printer import ModelHelpPrinter
from wlsdeploy.tool.modelhelp.model_help_utils import ControlOptions
from wlsdeploy.util.model_context import ModelContext


class ModelHelpPrinterTestCase(unittest.TestCase):
    _program_name = 'model_help_printer_test'
    _class_name = 'ModelHelpPrinterTestCase'

    wls_version = '12.2.1.3'

    def setUp(self):
        self.name = 'ModelHelpPrinterTestCase'
        self._logger = PlatformLogger('wlsdeploy.modelhelp')

    def testPrintHelpNormal(self):
        """
        Verify that the NORMAL option includes attribute and folder information.
        """
        path = DOMAIN_INFO
        result = self._get_model_help(DOMAIN_INFO, ControlOptions.NORMAL)

        # attribute should be present
        self.assertEquals(ADMIN_PASSWORD in result, True, path + " help should contain " + ADMIN_PASSWORD)

        # folder should be present
        self.assertEquals(RCU_DB_INFO in result, True, path + " help should contain " + RCU_DB_INFO)

    def testPrintHelpFoldersOnly(self):
        """
        Verify that the FOLDERS_ONLY option includes only folder information.
        """
        path = RESOURCES + ":/" + JDBC_SYSTEM_RESOURCE
        result = self._get_model_help(path, ControlOptions.FOLDERS_ONLY)

        # attribute should not be present
        self.assertEquals(SOURCE_PATH in result, False, path + " help should not contain " + SOURCE_PATH)

        # folder should be present
        self.assertEquals(JDBC_RESOURCE in result, True, path + " help should contain " + JDBC_RESOURCE)

    def testPrintHelpAttributesOnly(self):
        """
        Verify that the ATTRIBUTES_ONLY option includes only attribute information.
        """
        path = RESOURCES + ":/" + JDBC_SYSTEM_RESOURCE
        result = self._get_model_help(path, ControlOptions.ATTRIBUTES_ONLY)

        # attribute should be present
        self.assertEquals(SOURCE_PATH in result, True, path + " help should contain " + SOURCE_PATH)

        # folder should not be present
        self.assertEquals(JDBC_RESOURCE in result, False, path + " help should not contain " + JDBC_RESOURCE)

    def testPrintHelpRecursive(self):
        path = RESOURCES + ":/" + JDBC_SYSTEM_RESOURCE
        result = self._get_model_help(path, ControlOptions.RECURSIVE)

        # nested folder should be present
        self.assertEquals(JDBC_DRIVER_PARAMS in result, True, path + " help should contain " + JDBC_DRIVER_PARAMS)

    def _get_model_help(self, path, control_option):
        try:
            old_out = sys.stdout
            sys.stdout = StringIO()

            model_context = ModelContext(self._program_name, { })
            aliases = Aliases(model_context, WlstModes.OFFLINE, self.wls_version)
            printer = ModelHelpPrinter(model_context, aliases, self._logger)
            printer.print_model_help(path, control_option)

            sys.stdout.flush()
            text = sys.stdout.getvalue()
            sys.stdout = old_out
            return text

        except CLAException, e:
            self.fail(e.getLocalizedMessage())


if __name__ == '__main__':
    unittest.main()
