"""
Copyright (c) 2017, 2018, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""
import unittest

import wlsdeploy.util.variables as variables
from oracle.weblogic.deploy.util import VariableException
from wlsdeploy.util.model_translator import FileToPython


class VariablesTestCase(unittest.TestCase):
    _resources_dir = '../../test-classes'
    _variables_file = _resources_dir + '/variables.properties'

    def setUp(self):
        self.name = 'VariablesTestCase'

    def testReadVariables(self):
        variable_map = variables.load_variables(self._variables_file)
        self.assertEqual(variable_map['my-abc'], 'xyz')

    def testSubstituteYaml(self):
        model = FileToPython(self._resources_dir + '/variables-test.yaml').parse()
        variable_map = variables.load_variables(self._variables_file)
        variables.substitute(model, variable_map)
        self.assertEqual(model['topology']['Name'], 'xyz123')
        self.assertEqual(model['topology']['Server']['s1']['ListenPort'], '1009')
        self.assertEqual(True, 'myCluster' in model['topology']['Cluster'])

    def testSubstituteJson(self):
        model = FileToPython(self._resources_dir + '/variables-test.json').parse()
        variable_map = variables.load_variables(self._variables_file)
        variables.substitute(model, variable_map)
        self.assertEqual(model['topology']['Name'], 'xyz123')
        self.assertEqual(model['topology']['Server']['s1']['ListenPort'], '1009')
        self.assertEqual(True, 'myCluster' in model['topology']['Cluster'])

    def testVariableNotFound(self):
        try:
            model = FileToPython(self._resources_dir + '/variables-test.json').parse()
            model['topology']['Name'] = '${bad.variable}'
            variable_map = variables.load_variables(self._variables_file)
            variables.substitute(model, variable_map)
        except VariableException:
            pass
        else:
            self.fail('Test must raise VariableException when variable is not found')

if __name__ == '__main__':
    unittest.main()
