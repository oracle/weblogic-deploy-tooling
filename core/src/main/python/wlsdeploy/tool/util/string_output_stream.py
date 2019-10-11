"""
Copyright (c) 2017, 2019, Oracle Corporation and/or its affiliates.  All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""

from java.io import OutputStream, ByteArrayOutputStream
from java.lang import String

"""
 This class allows redirecting the stdout to a string array for wlst.
"""
class StringOutputStream(OutputStream):

    def __init__(self):
        self.stream = ByteArrayOutputStream()

    def write(self,b,off,len):
        self.stream.write(b,off,len)

    def get_string(self):
        output = String(self.stream.toByteArray())
        if self.stream is not None:
            self.stream.close()
        return output

