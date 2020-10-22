"""
Copyright (c) 2020, Oracle Corporation and/or its affiliates.  All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""


class HyphenList(list):
    """
    A subclass of list used for outputting a list of items.
    JSON formatter needs to distinguish hyphen lists from other lists
    """
    def __init__(self):
        list()
