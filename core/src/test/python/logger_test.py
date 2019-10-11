"""
Copyright (c) 2017, 2019, Oracle Corporation and/or its affiliates.  All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import unittest

import wlsdeploy.exception.exception_helper as exception_helper
import wlsdeploy.logging.platform_logger as platform_logger
from wlsdeploy.util.weblogic_helper import WebLogicHelper
import oracle.weblogic.deploy.deploy.DeployException as DeployException

class LoggerTestCase(unittest.TestCase):

    def setUp(self):
        self.name = 'LoggerTestCase'
        self.logger = platform_logger.PlatformLogger(self.name)
        self.wls_helper = WebLogicHelper(self.logger)

    def raiseDeployException(self):
        map = { 'name':'Derek', 'address':'1234' }
        try:
            print map['bad key']
        except KeyError, key_error:
            self.logger.fine('WLSDPLY-01760', str(key_error), error=key_error, class_name=self.name,
                                method_name='testPythonException')
            raise exception_helper.create_deploy_exception('WLSDPLY-01760', str(key_error), error=key_error)

    def testPythonException(self):
        try:
            self.raiseDeployException()
        except DeployException, e:
            pass
        else:
            self.fail('Test must raise DeployException to test logger handling of python exception')

if __name__ == '__main__':
    unittest.main()