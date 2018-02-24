"""
Copyright (c) 2017, 2018, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
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

