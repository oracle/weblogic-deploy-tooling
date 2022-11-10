"""
Copyright (c) 2022, Oracle Corporation and/or its affiliates.  All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.

This module provides methods to help properly handle unicode across WLST versions of Jython
"""
import sys

# DO NOT import any WDT Python code into this file--ever!

__use_unicode = sys.version_info >= (2, 7)


def use_unicode():
    return __use_unicode


def to_string(value):
    if __use_unicode:
        return unicode(value, 'UTF8', 'strict')
    else:
        return str(value)

