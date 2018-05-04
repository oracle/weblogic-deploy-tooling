"""
Copyright (c) 2018, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""
import unittest
print unittest
from wlsdeploy.util.model_translator import FileToPython
from wlsdeploy.tool.util.variable_file_helper import VariableFileHelper


class VariableFileHelperTest(unittest.TestCase):
    _resources_dir = '../../test-classes'
    _model_file = _resources_dir + '/variable_insertion.yaml'

    def setUp(self):
        self.name = VariableFileHelperTest
        self._model = FileToPython(self._model_file).parse()
        self._helper = VariableFileHelper(self._model, None, '12.2.1.3')

    def testSingleVariableReplacement(self):
        replacement_list = ['topology:Machine.NodeManager.ListenAddress']
        expected = dict()
        expected['machine-machine1-nodemanager-listenaddress'] = '127.0.0.1'
        actual = self._helper.process_variable_replacement(replacement_list)
        self._compare_to_expected_dictionary(expected, actual)

    def testMultiplesReplacement(self):
        expected = dict()
        expected['server-AdminServer-listenport'] = 9001
        expected['server-AdminServer-ssl-listenport'] = 9002
        expected['server-m2-listenport'] = 9005
        expected['server-m1-listenport'] = 9003
        expected['server-m1-ssl-listenport'] = 9004
        expected['server-m2-ssl-listenport'] = 9006
        expected['jmssystemresource-MyJmsModule-jmsresource-foreignserver-MyForeignServer-connectionurl']\
            = 't3://my.other.cluster:7001'
        expected['jmssystemresource-MyJmsModule-jmsresource-foreignserver-MyForeignServer-' \
                 'foreigndestination-MyRemoteQ-localjndiname'] = 'jms/remoteQ'
        #'resources:JMSSystemResource.JmsResource.ForeignDestination.LocalJNDIName',
        replacement_list = ['topology:Server.ListenPort',
                            'resources:JMSSystemResource.JmsResource.ForeignServer.ConnectionURL',
                            'resources:JMSSystemResource.JmsResource.ForeignServer.ForeignDestination.LocalJNDIName',
                            'topology:Server.SSL.ListenPort']
        actual = self._helper.process_variable_replacement(replacement_list)
        self._compare_to_expected_dictionary(expected, actual)

    def testInvalidMBeanNameNoException(self):
        expected = dict()
        replacement_list = 'resources:JmsSystemResource.Notes'
        actual = self._helper.process_variable_replacement(replacement_list)
        self._compare_to_expected_dictionary(expected, actual)

    def testInvalidAttributeName(self):
        expected = dict()
        replacement_list = 'topology:Server.listenaddress'
        actual = self._helper.process_variable_replacement(replacement_list)
        self._compare_to_expected_dictionary(expected, actual)

    def testInvalidSection(self):
        expected = dict()
        replacement_list = 'topologies:Server.ListenAddress'
        actual = self._helper.process_variable_replacement(replacement_list)
        self._compare_to_expected_dictionary(expected, actual)

    def testDomainAttributeReplacementAndModel(self):
        expected = dict()
        expected['notes'] = 'Test note replacement'
        expected_replacement = '@@PROP:notes@@'
        replacement_list = ['topology:Notes']
        actual = self._helper.process_variable_replacement(replacement_list)
        self._compare_to_expected_dictionary(expected, actual)
        self.assertEqual(expected_replacement, self._model['topology']['Notes'])

    def _compare_to_expected_dictionary(self, expected, actual):
        self.assertEqual(len(expected), len(actual),
                         'Not the same number of entries : expected=' + str(len(expected)) + ', actual=' + str(
                             len(actual)))
        for k,v in actual.iteritems():
            self.assertEqual(True, k in expected and v == expected[k], 'Actual item not in expected ' + str(k) +
                             ' : ' + str(v) + '   expected=' + str(expected))

if __name__ == '__main__':
    unittest.main()