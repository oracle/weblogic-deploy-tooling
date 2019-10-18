"""
Copyright (c) 2017, 2019, Oracle and/or its affiliates. All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl.
"""
import unittest

import wlsdeploy.util.variables as variables
from oracle.weblogic.deploy.util import VariableException
from wlsdeploy.util.model_context import ModelContext
from wlsdeploy.util.model_translator import FileToPython


class VariablesTestCase(unittest.TestCase):
    _resources_dir = '../../test-classes'
    _variables_file = _resources_dir + '/variables.properties'
    _file_variable_name = 'file-variable.txt'
    _file_variable_path = _resources_dir + '/' + _file_variable_name
    _use_ordering = True

    def setUp(self):
        self.name = 'VariablesTestCase'

        # create a context with resource directory as Oracle home, to support @@ORACLE_HOME@@ resolution
        self.model_context = ModelContext("test", {'-oracle_home': self._resources_dir})

    def testReadVariables(self):
        variable_map = variables.load_variables(self._variables_file)
        self.assertEqual(variable_map['my-abc'], 'xyz')

    def testSubstituteYaml(self):
        model = FileToPython(self._resources_dir + '/variables-test.yaml', self._use_ordering).parse()
        variable_map = variables.load_variables(self._variables_file)
        variables.substitute(model, variable_map, self.model_context)
        self.assertEqual(model['topology']['Name'], 'xyz123')
        self.assertEqual(model['topology']['Server']['s1']['ListenPort'], '1009')
        self.assertEqual(model['topology']['Server']['s2']['Cluster'], 'myCluster')
        self.assertEqual(True, 'myCluster' in model['topology']['Cluster'])
        self.assertEqual(True, 's3' in model['topology']['Server'])

    def testSubstituteJson(self):
        model = FileToPython(self._resources_dir + '/variables-test.json', self._use_ordering).parse()
        variable_map = variables.load_variables(self._variables_file)
        variables.substitute(model, variable_map, self.model_context)
        self.assertEqual(model['topology']['Name'], 'xyz123')
        self.assertEqual(model['topology']['Server']['s1']['ListenPort'], '1009')
        self.assertEqual(model['topology']['Server']['s2']['Cluster'], 'myCluster')
        self.assertEqual(True, 'myCluster' in model['topology']['Cluster'])
        self.assertEqual(True, 's3' in model['topology']['Server'])

    def testVariableNotFound(self):
        """
        For ${key} substitution, no replacement is done, and no error is reported, if variable not found.
        ${key} substitution is deprecated.
        """
        model = FileToPython(self._resources_dir + '/variables-test.json', self._use_ordering).parse()
        model['topology']['Name'] = '${bad.variable}'
        variable_map = variables.load_variables(self._variables_file)
        variables.substitute(model, variable_map, self.model_context)
        self.assertEqual(model['topology']['Name'], '${bad.variable}')

    def testPropertyNotFound(self):
        """
        For @@PROP:key@@ substitution, an exception is thrown if variable not found.
        """
        try:
            model = FileToPython(self._resources_dir + '/variables-test.json', self._use_ordering).parse()
            model['topology']['Name'] = '@@PROP:bad.variable@@'
            variable_map = variables.load_variables(self._variables_file)
            variables.substitute(model, variable_map, self.model_context)
        except VariableException:
            pass
        else:
            self.fail('Test must raise VariableException when variable is not found')

    def testFileVariable(self):
        path = self._resources_dir + '/' + self._file_variable_name
        model = {'domainInfo': {'AdminUserName': '@@FILE:' + path + '@@'}}
        variables.substitute(model, {}, self.model_context)
        self.assertEqual(model['domainInfo']['AdminUserName'], 'file-variable-value')

    def testFileVariableWithVariable(self):
        model = {'domainInfo': {'AdminUserName': '@@FILE:${variable_dir}/' + self._file_variable_name + '@@'}}
        variables.substitute(model, {'variable_dir': self._resources_dir}, self.model_context)
        self.assertEqual(model['domainInfo']['AdminUserName'], 'file-variable-value')

    def testFileVariableWithConstant(self):
        model = {'domainInfo': {'AdminUserName': '@@FILE:@@ORACLE_HOME@@/' + self._file_variable_name + '@@'}}
        variables.substitute(model, {}, self.model_context)
        self.assertEqual(model['domainInfo']['AdminUserName'], 'file-variable-value')

    def testFileVariableNotFound(self):
        try:
            path = self._resources_dir + '/no-file.txt'
            model = {'domainInfo': {'AdminUserName': '@@FILE:' + path + '@@'}}
            variables.substitute(model, {}, self.model_context)
            self.assertEqual(model['domainInfo']['AdminUserName'], 'file-variable-value')
        except VariableException:
            pass
        else:
            self.fail('Test must raise VariableException when variable file is not found')


if __name__ == '__main__':
    unittest.main()
