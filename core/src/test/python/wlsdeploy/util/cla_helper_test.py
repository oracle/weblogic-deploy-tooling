"""
Copyright (c) 2019, Oracle and/or its affiliates. All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl.
"""
import unittest

from wlsdeploy.util import cla_helper


class ClaHelperTest(unittest.TestCase):

    # merging should combine elements with the same name (m1), add any elements only in the second model (m3),
    # and leave existing elements (m2) in place.
    def testMergeModels(self):
        dictionary = {
            "Servers": {
                "m1": {
                    "ListenPort": 9000,
                    "ListenDelaySecs": 5
                },
                "m2": {
                    "ListenPort": 9002
                }
            }
        }

        new_dictionary = {
            "Servers": {
                "m1": {
                    "ListenPort": 9001,
                    "MaxOpenSockCount": 7,
                },
                "m3": {
                    "ListenPort": 9003
                }
            }
        }

        variables = {}
        cla_helper._merge_dictionaries(dictionary, new_dictionary, variables)
        # print("Merged model: " + str(dictionary))

        servers = dictionary['Servers']
        m1 = servers['m1']

        self.assertEquals(9001, m1['ListenPort'], "m1 should have listen port 9001")
        self.assertEquals(5, m1['ListenDelaySecs'], "m1 should have listen delay secs 5")
        self.assertEquals(7, m1['MaxOpenSockCount'], "m1 should have max open sock count 7")

        self.assertEquals(9002, servers['m2']['ListenPort'], "m2 should be in model, listen port 9002")
        self.assertEquals(9003, servers['m3']['ListenPort'], "m3 should be in model, listen port 9003")

    # if two named elements are identical @@PROP references, merge them.
    # no variables are required to resolve this case.
    def testMergeMatchingProperties(self):
        dictionary = _build_model_one('@@PROP:server1@@')
        new_dictionary = _build_model_two('@@PROP:server1@@')
        variables = {}

        # no variables are needed to resolve this
        cla_helper._merge_dictionaries(dictionary, new_dictionary, variables)
        # print("Merged model: " + str(dictionary))

        servers = dictionary['Servers']
        self.assertEquals(1, len(servers), "there should be one server")

        self._check_merged_server(dictionary, '@@PROP:server1@@')

    # two elements should be merged if they have different @@PROP variable keys that resolve to the same value.
    def testMergeDifferentProperties(self):
        dictionary = _build_model_one('@@PROP:server1a@@')
        new_dictionary = _build_model_two('@@PROP:server1b@@')
        variables = _build_variable_map()

        cla_helper._merge_dictionaries(dictionary, new_dictionary, variables)
        # print("Merged model: " + str(dictionary))

        self._check_merged_server(dictionary, '@@PROP:server1a@@')

    # an element with an @@PROP variable key should merge with a base element with a matching resolved key.
    def testMergePropertyToName(self):
        dictionary = _build_model_one('m1')
        new_dictionary = _build_model_two('@@PROP:server1b@@')
        variables = _build_variable_map()

        cla_helper._merge_dictionaries(dictionary, new_dictionary, variables)
        # print("Merged model: " + str(dictionary))

        self._check_merged_server(dictionary, 'm1')

    # an element should merge with a base element with a matching @@PROP variable key.
    def testMergeNameToProperty(self):
        dictionary = _build_model_one('@@PROP:server1a@@')
        new_dictionary = _build_model_two('m1')
        variables = _build_variable_map()

        cla_helper._merge_dictionaries(dictionary, new_dictionary, variables)
        # print("Merged model: " + str(dictionary))

        self._check_merged_server(dictionary, '@@PROP:server1a@@')

    # an element with delete notation should replace a base element with a matching name and no notation.
    def testMergeDeletedNameToName(self):
        dictionary = _build_model_one('m1')
        new_dictionary = _build_delete_model('m1')
        variables = {}

        cla_helper._merge_dictionaries(dictionary, new_dictionary, variables)
        # print("Merged model: " + str(dictionary))

        server = self._check_single_server(dictionary, '!m1')
        self.assertEquals(0, len(server), "delete server should have no attributes")

    # an element should replace a base element with a matching name and delete notation.
    def testMergeNameToDeletedName(self):
        dictionary = _build_delete_model('m1')
        new_dictionary = _build_model_two('m1')
        variables = {}

        cla_helper._merge_dictionaries(dictionary, new_dictionary, variables)
        # print("Merged model: " + str(dictionary))

        server = self._check_single_server(dictionary, 'm1')
        self.assertEquals(2, len(server), "server should have two attributes")

    # check that a single server exists in the result, and its attributes were merged correctly
    def _check_merged_server(self, dictionary, key):
        server = self._check_single_server(dictionary, key)
        self.assertEquals(9001, server['ListenPort'], "m1 should have listen port 9001")
        self.assertEquals(5, server['ListenDelaySecs'], "m1 should have listen delay secs 5")
        self.assertEquals(7, server['MaxOpenSockCount'], "m1 should have max open sock count 7")

    # check that a single server exists in the result, with the specified name
    def _check_single_server(self, dictionary, key):
        servers = dictionary['Servers']
        self.assertEquals(1, len(servers), "there should be one server")
        self.assertEquals(True, key in servers, "the single server name should be " + key)
        return servers[key]


# model 1 has one server with attributes
def _build_model_one(key):
    return {
        "Servers": {
            key: {
                "ListenPort": 9000,
                "ListenDelaySecs": 5
            }
        }
    }


# model 2 has one server, with a different listen port from model 1, and an additional attribute
def _build_model_two(key):
    return {
        "Servers": {
            key: {
                "ListenPort": 9001,
                "MaxOpenSockCount": 7,
            }
        }
    }


# the delete model 1 has one server with delete notation, and no attributes
def _build_delete_model(key):
    return {
        "Servers": {
            '!' + key: {}
        }
    }


# variable map maps two keys to the same server name
def _build_variable_map():
    return {
        "server1a": "m1",
        "server1b": "m1"
    }
