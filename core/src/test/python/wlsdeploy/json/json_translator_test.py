"""
Copyright (c) 2019, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""
import unittest

from java.io import ByteArrayInputStream
from oracle.weblogic.deploy.json import JsonStreamTranslator


class JsonTranslatorTest(unittest.TestCase):

    def testEscapeBackslash(self):
        # JSON "xy\\.z" should become String "xy\.z"
        text = "{ \"abc\": \"xy\\\\.z\" }"
        stream = ByteArrayInputStream(text.encode('utf-8'))
        json_translator = JsonStreamTranslator("String", stream)
        result = json_translator.parse()
        abc = result['abc']
        self.assertEquals("xy\\.z", abc, "Should be single slash")
