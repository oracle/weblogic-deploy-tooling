"""
Copyright (c) 2020, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import unittest

import wlsdeploy.tool.discover.topology_discoverer as topology_discoverer


class DiscoverTest(unittest.TestCase):

    def testDynamicServerValid(self):
        server_name = 'ps0'
        prefix = 'ps'
        dynamic_size = 3
        starting = 0
        result = topology_discoverer.check_against_server_list(server_name, dynamic_size, prefix, starting)
        self.assertEqual(True, result)

    def testDynamicServerInValid(self):
        server_name = 'ps0'
        prefix = 'ps'
        dynamic_size = 3
        starting = 1
        result = topology_discoverer.check_against_server_list(server_name, dynamic_size, prefix, starting)
        self.assertEqual(False, result)

    def testDynamicServerValidEnd(self):
        server_name = 'managed-server-112'
        prefix = 'managed-server-'
        dynamic_size = 12
        starting = 101
        result = topology_discoverer.check_against_server_list(server_name, dynamic_size, prefix, starting)
        self.assertEqual(True, result)
