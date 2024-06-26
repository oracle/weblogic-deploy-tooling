"""
Copyright (c) 2017, 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import unittest

from wlsdeploy.exception import exception_helper
from wlsdeploy.exception.exception_types import ExceptionType

class ExceptionHelperTestCase(unittest.TestCase):

    def testCreateException(self):
        ex = exception_helper.create_exception(ExceptionType.CREATE, 'WLSDPLY-12400',
                                               'createDomain', '-oracle_home')
        self.assertNotEquals(ex, None)
        return

