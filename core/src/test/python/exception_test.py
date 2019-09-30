"""
Copyright (c) 2017, 2019, Oracle Corporation and/or its affiliates.  All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import unittest

from wlsdeploy.exception import exception_helper
from wlsdeploy.exception.expection_types import ExceptionType

class ExceptionHelperTestCase(unittest.TestCase):

    def testCreateException(self):
        ex = exception_helper.create_exception(ExceptionType.CREATE, 'WLSDPLY-12400',
                                               'createDomain', '-oracle_home')
        self.assertNotEquals(ex, None)
        return

