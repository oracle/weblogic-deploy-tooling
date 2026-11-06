"""
Copyright (c) 2017, 2026, Oracle Corporation and/or its affiliates.  All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import unittest

import os

import wlsdeploy.util.variables as variables
from oracle.weblogic.deploy.util import VariableException
from wlsdeploy.util.model_context import ModelContext
from wlsdeploy.util.model_translator import FileToPython
from wlsdeploy.logging import platform_logger
from java.util.logging import Level

class VariablesTestCase(unittest.TestCase):
    _resources_dir = '../../test-classes'
    _variables_file = _resources_dir + '/variables.properties'
    _variable_references_file = _resources_dir + '/variable-references.properties'
    _variable_references_base_file = _resources_dir + '/variable-references-base.properties'
    _variable_references_override_file = _resources_dir + '/variable-references-override.properties'
    _variable_references_missing_file = _resources_dir + '/variable-references-missing.properties'
    _variable_references_cycle_file = _resources_dir + '/variable-references-cycle.properties'
    _variable_references_self_cycle_file = _resources_dir + '/variable-references-self-cycle.properties'
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

    def testReadVariablesReferences(self):
        variable_map = variables.load_variables(self._variable_references_file)
        self.assertEqual(variable_map['foo'], 'abc')
        self.assertEqual(variable_map['bar'], 'abc')
        self.assertEqual(variable_map['baz'], 'pre-abc-post')
        self.assertEqual(variable_map['token-with-reference'], '@@ENV:TEST_ENV_NAME@@')
        self.assertEqual(variable_map['token-holder'], '@@ENV:SHOULD_NOT_CHANGE@@')

    def testReadVariablesReferencesAcrossMergedFiles(self):
        variable_files = self._variable_references_base_file + ',' + self._variable_references_override_file
        variable_map = variables.load_variables(variable_files, allow_multiple_files=True)
        self.assertEqual(variable_map['shared'], 'override')
        self.assertEqual(variable_map['selected'], 'override')
        self.assertEqual(variable_map['decorated'], 'pre-override-post')

    def testReadEscapedVariableReferences(self):
        variable_map = variables.load_variables(self._resources_dir + '/variable-references-escaped.properties')
        self.assertEqual(variable_map['literal'], '${missing}')
        self.assertEqual(variable_map['shell'], '-Djava.library.path=${LD_LIBRARY_PATH:=}:/opt/lib')
        self.assertEqual(variable_map['mixed'], '${foo}/abc/${foo}/abc')
        self.assertEqual(variable_map['dollars'], '$ $abc $${foo} $$ $5 $')
        self.assertEqual(variable_map['self'], '${self}')
        self.assertEqual(variable_map['indirect'], 'pre-${missing}-${self}-post')
        self.assertEqual(variable_map['ordered'], '${bar}/abc')
        self.assertEqual(variable_map['unusual-name'], 'literal-name')

    def testReadVariablesReferenceMissing(self):
        self._assert_load_variables_failure(self._variable_references_missing_file, ['owner', 'missing'])

    def testReadVariablesReferenceCycle(self):
        self._assert_load_variables_failure(self._variable_references_cycle_file, ['cycle', 'foo', 'bar'])

    def testReadVariablesReferenceSelfCycle(self):
        self._assert_load_variables_failure(self._variable_references_self_cycle_file, ['self', 'self -> self'])

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
        model = {'domainInfo': {'AdminUserName': '@@FILE:@@PROP:variable_dir@@/' + self._file_variable_name + '@@'}}
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

    def testEnvironmentVariable(self):
        os.environ['envVariable'] = 'the-admin-user'
        model = {'domainInfo': {'AdminUserName': '@@ENV:envVariable@@'}}
        variables.substitute(model, {}, self.model_context)
        self.assertEqual(model['domainInfo']['AdminUserName'], 'the-admin-user')

    def testFileVariableWithEnvironmentVariable(self):
        os.environ['variableDir'] = self._resources_dir
        model = {'domainInfo': {'AdminUserName': '@@FILE:@@ENV:variableDir@@/' + self._file_variable_name + '@@'}}
        variables.substitute(model, {}, self.model_context)
        self.assertEqual(model['domainInfo']['AdminUserName'], 'file-variable-value')

    def testEnvironmentVariableNotFound(self):
        try:
            model = {'domainInfo': {'AdminUserName': '@@ENV:notaVariable@@'}}
            variables.substitute(model, {}, self.model_context)
        except VariableException:
            pass
        else:
            self.fail('Test must raise VariableException when variable file is not found')

    def testSecretToken(self):
        """
        Verify that the WDT_MODEL_SECRETS_DIRS variable can be used to find a secret.
        Put two paths in the variable, the second is .../resources/secrets.
        It should find the file .../resources/secrets/my-secrets/secret2, containing "mySecret2".
        """
        os.environ['WDT_MODEL_SECRETS_DIRS'] = "/noDir/noSubdir," + self._resources_dir + "/secrets"
        model = {'domainInfo': {'AdminUserName': '@@SECRET:my-secrets:secret2@@'}}
        variables._clear_secret_token_map()
        variables.substitute(model, {}, self.model_context)
        self.assertEqual(model['domainInfo']['AdminUserName'], 'mySecret2')

    def testSecretTokenPairs(self):
        """
        Verify that the WDT_MODEL_SECRETS_NAME_DIR_PAIRS variable can be used to find a secret.
        Put two path assignments in the variable, the second is dirY=.../resources/secrets.
        It should find the file .../resources/secrets/secret1, containing "mySecret1".
        """
        os.environ['WDT_MODEL_SECRETS_NAME_DIR_PAIRS'] = "dirX=/noDir,dirY=" + self._resources_dir + "/secrets"
        model = {'domainInfo': {'AdminUserName': '@@SECRET:dirY:secret1@@'}}
        variables._clear_secret_token_map()
        variables.substitute(model, {}, self.model_context)
        self.assertEqual(model['domainInfo']['AdminUserName'], 'mySecret1')

    def testSecretTokenNotFound(self):
        try:
            model = {'domainInfo': {'AdminUserName': '@@SECRET:noName:noKey@@'}}
            variables.substitute(model, {}, self.model_context)
        except VariableException:
            pass
        else:
            self.fail('Test must raise VariableException when secret token is not found')

    def test_token_string_match(self):
        """
        Test that methods for token string work correctly.
        """
        self.assertEqual(variables.is_variable_string('@@PROP:abc@@'), True, 'Should be a variable string')
        self.assertEqual(variables.is_variable_string('aa@@PROP:abc@@bb'), False, 'Should not be a variable string')
        self.assertEqual(variables.is_variable_string('@@ENV:abc@@'), False, 'Should not be a variable string')
        self.assertEqual(variables.is_variable_string('value'), False, 'Should not be a variable string')
        self.assertEqual(variables.is_variable_string(999), False, 'Should not be a variable string')

        self.assertEqual(variables.is_secret_string('@@SECRET:abc:xyz@@'), True, 'Should be a secret string')
        self.assertEqual(variables.is_secret_string('x@@SECRET:abc:xyz@@y'), False, 'Should not be a secret string')
        self.assertEqual(variables.is_secret_string('@@SECRET:oops@@'), False, 'Should not be a secret string')
        self.assertEqual(variables.is_secret_string('value'), False, 'Should not be a secret string')

        self.assertEqual(variables.get_variable_string_key('@@PROP:abc@@'), 'abc', 'Variable string key should match')
        self.assertEqual(variables.get_variable_string_key('x@@PROP:abc@@y'), None, 'Variable string key should be None')
        self.assertEqual(variables.get_variable_string_key('abc'), None, 'Variable string key should be None')
        self.assertEqual(variables.get_variable_string_key(999), None, 'Variable string key should be None')

    def testTokenSyntaxErrors(self):
        """
        Test that exceptions are thrown for token syntax errors.
        """
        # Temporarily disable logging for this test. Each test is expected to fail and issue warning messages
        logger = platform_logger.PlatformLogger('wlsdeploy.variables')
        original_level = logger.get_level()
        logger.set_level(Level.OFF)
        self._test_token_syntax_error("@@SECRET:my-secret/my-key@@")
        self._test_token_syntax_error("@@SECRET:@@ENVmy-secret:-my-key@@-some-more-text")
        self._test_token_syntax_error("@@ENV:my-secret!@@")
        self._test_token_syntax_error("@@FILE:@@ORACLE_HOME@@/my-file")
        self._test_token_syntax_error("@@PROP:")
        # Restore original log level
        logger.set_level(original_level)

    def _test_token_syntax_error(self, value):
        """
        Test that an exception is thrown for a token syntax error in the specified value.
        :param value: the text value to be checked
        """
        try:
            model = {'domainInfo': {'AdminUserName': value}}
            variables.substitute(model, {}, self.model_context)
        except VariableException, e:
            pass
        else:
            self.fail('Test must raise VariableException when token has a syntax error')

    def _assert_load_variables_failure(self, file_name, expected_text_list):
        try:
            variables.load_variables(file_name)
        except VariableException, e:
            message = e.getLocalizedMessage()
            for expected_text in expected_text_list:
                self.assertEqual(True, expected_text in message, 'Expected "%s" in "%s"' % (expected_text, message))
        else:
            self.fail('Test must raise VariableException when variable references cannot be resolved')


if __name__ == '__main__':
    unittest.main()
