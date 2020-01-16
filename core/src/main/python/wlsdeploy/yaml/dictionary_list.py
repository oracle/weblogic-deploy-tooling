"""
Copyright (c) 2020, Oracle Corporation and/or its affiliates.  All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""


class DictionaryList(list):
    """
    A subclass of list used for outputting a list of dictionary items.
    YAML and JSON formatters need to distinguish lists of dictionaries from other lists
    """
    def __init__(self):
        list()
