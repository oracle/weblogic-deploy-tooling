"""
Copyright (c) 2018, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""

class Statistics(object):
    """
    Collect information about the issues encountered during a invocation.
    """

    def __init__(self):
        self.success = True
        self.critical = 0
        self.warning = 0
        self.info = 0

    def add_info(self):
