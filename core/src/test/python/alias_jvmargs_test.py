"""
Copyright (c) 2017, 2019, Oracle Corporation and/or its affiliates.  All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import unittest

from wlsdeploy.aliases.alias_jvmargs import JVMArguments
from wlsdeploy.logging.platform_logger import PlatformLogger


class JVMArgumentsTestCase(unittest.TestCase):

    _logger = PlatformLogger('wlsdeploy.aliases')

    def testArgParsing(self):
        input = '-XX:MaxPermSize=512m -verify:none -XX:+HeapDumpOnOutOfMemoryError -Xms1024m -Dfoo=bar -Xmx2g -server -dsa -verbose:gc -Xrs'
        expected = '-server -Xms1024m -Xmx2g -Xrs -XX:+HeapDumpOnOutOfMemoryError -XX:MaxPermSize=512m -Dfoo=bar -verify:none -dsa -verbose:gc'

        args = JVMArguments(self._logger, input)
        actual = args.get_arguments_string()
        self.assertEqual(actual, expected)

    def testArgMerging(self):
        existing = '-XX:MaxPermSize=512m -verify:none -XX:+HeapDumpOnOutOfMemoryError -Xms1024m -Dfoo=bar -Xmx2g -server -dsa -verbose:gc -Xrs'
        model = '-Dmodel=testme -Xmx4096m -client'
        expected = '-client -Xms1024m -Xmx4096m -Xrs -XX:+HeapDumpOnOutOfMemoryError -XX:MaxPermSize=512m -Dfoo=bar -Dmodel=testme -verify:none -dsa -verbose:gc'

        existing_args = JVMArguments(self._logger, existing)
        model_args = JVMArguments(self._logger, model)
        existing_args.merge_jvm_arguments(model_args)
        actual = existing_args.get_arguments_string()
        self.assertEqual(actual, expected)

    def testExArgs(self):
        # verify size keys in lower/upper case.
        # these are in correct order, so result should match exactly.
        model = '-Xms1024m -Xmx4096M -Xa=1024k -Xb=4096K -Xc=1024g -Xd=4096G'

        model_args = JVMArguments(self._logger, model)
        result = model_args.get_arguments_string()
        self.assertEqual(result, model)
