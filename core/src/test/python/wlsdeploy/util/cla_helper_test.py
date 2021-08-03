"""
Copyright (c) 2019, 2021, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl.
"""
import os
import unittest

from wlsdeploy.aliases.aliases import Aliases
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception.expection_types import ExceptionType
from wlsdeploy.util.model_context import ModelContext
from wlsdeploy.util import cla_helper


class ClaHelperTest(unittest.TestCase):

    _resources_dir = '../../test-classes'
    # Model persistence file
    _wlsdeply_store_model = os.path.abspath(os.getcwd()) + '/' + _resources_dir + '/validate-mii-model.json'
    properties_file = '../../test-classes/test.properties'

    def setUp(self):
        # Define custom configuration path for WDT
        os.environ['WDT_CUSTOM_CONFIG'] = self._resources_dir
        # Indicate that WDT should persist model file
        os.environ['__WLSDEPLOY_STORE_MODEL__'] = self._wlsdeply_store_model

    def tearDown(self):
        # Clean up temporary WDT custom configuration environment variables
        # and model persistence files
        del os.environ['WDT_CUSTOM_CONFIG']
        del os.environ['__WLSDEPLOY_STORE_MODEL__']
        deleteFile(self._wlsdeply_store_model)

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

        cla_helper.merge_model_dictionaries(dictionary, new_dictionary, variables)
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
        cla_helper.merge_model_dictionaries(dictionary, new_dictionary, variables)
        # print("Merged model: " + str(dictionary))

        servers = dictionary['Servers']
        self.assertEquals(1, len(servers), "there should be one server")

        self._check_merged_server(dictionary, '@@PROP:server1@@')

    # two elements should be merged if they have different @@PROP variable keys that resolve to the same value.
    def testMergeDifferentProperties(self):
        dictionary = _build_model_one('@@PROP:server1a@@')
        new_dictionary = _build_model_two('@@PROP:server1b@@')
        variables = _build_variable_map()

        cla_helper.merge_model_dictionaries(dictionary, new_dictionary, variables)
        # print("Merged model: " + str(dictionary))

        self._check_merged_server(dictionary, '@@PROP:server1a@@')

    # an element with an @@PROP variable key should merge with a base element with a matching resolved key.
    def testMergePropertyToName(self):
        dictionary = _build_model_one('m1')
        new_dictionary = _build_model_two('@@PROP:server1b@@')
        variables = _build_variable_map()

        cla_helper.merge_model_dictionaries(dictionary, new_dictionary, variables)
        # print("Merged model: " + str(dictionary))

        self._check_merged_server(dictionary, 'm1')

    # an element should merge with a base element with a matching @@PROP variable key.
    def testMergeNameToProperty(self):
        dictionary = _build_model_one('@@PROP:server1a@@')
        new_dictionary = _build_model_two('m1')
        variables = _build_variable_map()

        cla_helper.merge_model_dictionaries(dictionary, new_dictionary, variables)
        # print("Merged model: " + str(dictionary))

        self._check_merged_server(dictionary, '@@PROP:server1a@@')

    # an element with delete notation should remove a base element with a matching name.
    def testMergeDeletedNameToName(self):
        dictionary = _build_model_one('m1')
        new_dictionary = _build_delete_model('m1')
        variables = {}

        cla_helper.merge_model_dictionaries(dictionary, new_dictionary, variables)
        # print("Merged model: " + str(dictionary))

        servers = dictionary['Servers']
        self.assertEquals(0, len(servers), "there should be no servers after delete")

    # an element with delete notation should leave a base element with a matching delete notation.
    def testMergeDeletedNameToDeleteName(self):
        dictionary = _build_delete_model('m1')
        new_dictionary = _build_delete_model('m1')
        variables = {}

        cla_helper.merge_model_dictionaries(dictionary, new_dictionary, variables)
        # print("Merged model: " + str(dictionary))

        server = self._check_single_server(dictionary, '!m1')
        self.assertEquals(0, len(server), "server should have no attributes")

    # an element should replace a base element with a matching name and delete notation.
    def testMergeNameToDeletedName(self):
        dictionary = _build_delete_model('m1')
        new_dictionary = _build_model_two('m1')
        variables = {}

        cla_helper.merge_model_dictionaries(dictionary, new_dictionary, variables)
        # print("Merged model: " + str(dictionary))

        server = self._check_single_server(dictionary, 'm1')
        self.assertEquals(2, len(server), "server should have two attributes")

    def testPersistModelAfterFilter(self):
        """
        Verify filter was run and changes are persisted to model file
        """
        # Setup model context arguments
        _model_file = self._resources_dir + '/simple-model.yaml'
        _archive_file = self._resources_dir + "/SingleAppDomain.zip"
        _method_name = 'testPersistModelAfterFilter'

        mw_home = os.environ['MW_HOME']

        args_map = {
            '-oracle_home': mw_home,
            '-model_file': _model_file,
            '-archive_file': _archive_file
        }

        model_context = ModelContext('validate', args_map)

        aliases = Aliases(model_context, wlst_mode=WlstModes.OFFLINE, exception_type=ExceptionType.DEPLOY)

        # Load model and invoke filter
        model_dictionary = cla_helper.load_model('validateModel', model_context, aliases, "validate", WlstModes.OFFLINE)

        # assert the validate filter made modifications and was persisted
        self.assertEquals('gumby1234', model_dictionary['domainInfo']['AdminPassword'], "Expected validate filter to have changed AdminPassword to 'gumby1234'")

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

def deleteFile(path):
    try:
        os.remove(path)
    except OSError:
        pass
