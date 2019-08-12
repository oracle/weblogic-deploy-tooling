"""
Copyright (c) 2018, 2019, Oracle Corporation and/or its affiliates. All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl.
"""
import unittest

import wlsdeploy.util.variables as variables
import wlsdeploy.tool.util.variable_injector as variable_injector
from wlsdeploy.tool.util.variable_injector import VariableInjector
from wlsdeploy.util.model_translator import FileToPython


class VariableFileHelperTest(unittest.TestCase):
    _resources_dir = '../../test-classes'
    _variable_file = _resources_dir + '/variable.injector.test.properties'
    _model_file = _resources_dir + '/variable_insertion.yaml'
    _variable_injector_keyword = 'variable_injector_keyword.json'
    _keywords_file = 'keywords.json'

    def setUp(self):
        self.name = VariableFileHelperTest
        self._model = FileToPython(self._model_file).parse()
        self._helper = VariableInjector(self.name, self._model, None, '12.2.1.3')

    def testSingleVariableReplacement(self):
        replacement_dict = dict()
        replacement_dict['Machine.NodeManager.ListenAddress'] = dict()
        expected = dict()
        expected['Machine.machine1.NodeManager.ListenAddress'] = '127.0.0.1'
        actual = self._helper.inject_variables(replacement_dict)
        self._compare_to_expected_dictionary(expected, actual)

    def testMultiplesReplacement(self):
        expected = dict()
        expected['Server.AdminServer.SSL.ListenPort'] = '9002'
        expected['Server.AdminServer.ListenPort'] = '9001'
        expected['Server.m2.ListenPort'] = '9005'
        expected['Server.m1.ListenPort'] = '9003'
        expected['Server.m1.SSL.ListenPort'] = '9004'
        expected['Server.m2.SSL.ListenPort'] = '9006'
        expected['JMSSystemResource.MyJmsModule.JmsResource.ForeignServer.MyForeignServer.ConnectionURL'] \
            = 't3://my.other.cluster:7001'
        expected['JMSSystemResource.MyJmsModule.JmsResource.ForeignServer.MyForeignServer.'
                 'ForeignDestination.MyRemoteQ.LocalJNDIName'] = 'jms/remoteQ'
        replacement_dict = dict()
        replacement_dict['Server.ListenPort'] = dict()
        replacement_dict['JMSSystemResource.JmsResource.ForeignServer.ConnectionURL'] = dict()
        replacement_dict['JMSSystemResource.JmsResource.ForeignServer.ForeignDestination.LocalJNDIName'] = dict()
        replacement_dict['Server.SSL.ListenPort'] = dict()
        actual = self._helper.inject_variables(replacement_dict)
        self._compare_to_expected_dictionary(expected, actual)

    def testInvalidMBeanNameNoException(self):
        expected = dict()
        replacement_dict = dict()
        replacement_dict['JmsSystemResource.Notes'] = dict()
        actual = self._helper.inject_variables(replacement_dict)
        self._compare_to_expected_dictionary(expected, actual)

    def testInvalidAttributeName(self):
        expected = dict()
        replacement_dict = dict()
        replacement_dict['Server.listenaddress'] = dict()
        actual = self._helper.inject_variables(replacement_dict)
        self._compare_to_expected_dictionary(expected, actual)

    def testDomainAttributeReplacementAndModel(self):
        expected = dict()
        expected['Notes'] = 'Test note replacement'
        expected_replacement = '@@PROP:Notes@@'
        replacement_dict = dict()
        replacement_dict['Notes'] = dict()
        actual = self._helper.inject_variables(replacement_dict)
        self._compare_to_expected_dictionary(expected, actual)
        self.assertEqual(expected_replacement, self._model['topology']['Notes'])

    def testWithSegment(self):
        expected = dict()
        expected['JDBCSystemResource.Database2.JdbcResource.JDBCDriverParams.URL--Host'] = \
            'slc05til.us.oracle.com'
        expected['JDBCSystemResource.Database2.JdbcResource.JDBCDriverParams.URL--Port'] = \
            '1521'
        replacement_dict = dict()
        replacement_dict['JDBCSystemResource.JdbcResource.JDBCDriverParams.URL'] = dict()
        list_entry1 = dict()
        list_entry1[variable_injector.REGEXP_PATTERN] = '(?<=PORT=)[\w.-]+(?=\))'
        list_entry1[variable_injector.REGEXP_SUFFIX] = 'Port'
        list_entry2 = dict()
        list_entry2[variable_injector.REGEXP_PATTERN] = '(?<=HOST=)[\w.-]+(?=\))'
        list_entry2[variable_injector.REGEXP_SUFFIX] = 'Host'
        replacement_dict['JDBCSystemResource.JdbcResource.JDBCDriverParams.URL'][variable_injector.REGEXP] = [
            list_entry1, list_entry2]
        actual = self._helper.inject_variables(replacement_dict)
        self._compare_to_expected_dictionary(expected, actual)
        db2 = 'jdbc:oracle:thin:@(DESCRIPTION=(ADDRESS_LIST=(ADDRESS=(PROTOCOL=TCP)' \
              '(HOST=@@PROP:JDBCSystemResource.Database2.JdbcResource.JDBCDriverParams.URL--Host@@)' \
              '(PORT=@@PROP:JDBCSystemResource.Database2.JdbcResource.JDBCDriverParams.URL--Port@@)))' \
              '(CONNECT_DATA=(SERVICE_NAME=orcl.us.oracle.com)))'
        db1 = 'jdbc:oracle:thin:@//den00chv.us.oracle.com:1521/PDBORCL'
        self.assertEqual(db2, self._model['resources']['JDBCSystemResource']['Database2']['JdbcResource'][
            'JDBCDriverParams']['URL'])
        self.assertEqual(db1, self._model['resources']['JDBCSystemResource']['Database1']['JdbcResource'][
            'JDBCDriverParams']['URL'])

    def testWithSegmentInDictionary(self):
        expected = dict()
        expected['MailSession.MailSession-0.Properties--SmtpHost'] = 'stbeehive.oracle.com'
        expected['MailSession.MyMailSession.Properties--SmtpHost'] = 'stbeehive.oracle.com'
        expected['MailSession.MailSession-0.Properties--ImapHost'] = 'stbeehive.oracle.com'
        expected['MailSession.MyMailSession.Properties--ImapHost'] = 'stbeehive.oracle.com'
        replacement_dict = dict()
        replacement_dict['MailSession.Properties'] = dict()
        list_entry1 = dict()
        list_entry1[variable_injector.REGEXP_PATTERN] = 'mail.smtp.host'
        list_entry1[variable_injector.REGEXP_SUFFIX] = 'SmtpHost'
        list_entry2 = dict()
        list_entry2[variable_injector.REGEXP_PATTERN] = 'mail.imap.host'
        list_entry2[variable_injector.REGEXP_SUFFIX] = 'ImapHost'
        replacement_dict['MailSession.Properties'][variable_injector.REGEXP] = [list_entry1, list_entry2]
        actual = self._helper.inject_variables(replacement_dict)
        self._compare_to_expected_dictionary(expected, actual)
        self.assertEqual('@@PROP:MailSession.MyMailSession.Properties--SmtpHost@@',
                         self._model['resources']['MailSession']['MyMailSession']['Properties']['mail.smtp.host'])
        self.assertEqual('@@PROP:MailSession.MyMailSession.Properties--ImapHost@@',
                         self._model['resources']['MailSession']['MyMailSession']['Properties']['mail.imap.host'])

    def testWithSegmentInDictionaryAndAPattern(self):
        expected = dict()
        expected['MailSession.MyMailSession.Properties--Host'] = 'stbeehive.oracle.com'
        expected['MailSession.MailSession-0.Properties--Host'] = 'stbeehive.oracle.com'
        replacement_dict = dict()
        replacement_dict['MailSession.Properties'] = dict()
        list_entry = dict()
        list_entry[variable_injector.REGEXP_PATTERN] = '(?<=\w.)host'
        list_entry[variable_injector.REGEXP_SUFFIX] = 'Host'
        replacement_dict['MailSession.Properties'][variable_injector.REGEXP] = [list_entry]
        actual = self._helper.inject_variables(replacement_dict)
        self._compare_to_expected_dictionary(expected, actual)
        self.assertEqual('@@PROP:MailSession.MyMailSession.Properties--Host@@',
                         self._model['resources']['MailSession']['MyMailSession']['Properties']['mail.imap.host'])
        self.assertEqual('@@PROP:MailSession.MyMailSession.Properties--Host@@',
                         self._model['resources']['MailSession']['MyMailSession']['Properties']['mail.host'])
        self.assertEqual('@@PROP:MailSession.MyMailSession.Properties--Host@@',
                         self._model['resources']['MailSession']['MyMailSession']['Properties']['mail.smtp.host'])

    def testWithSegmentInList(self):
        expected = dict()
        expected['WLDFSystemResource.MyWldfModule.WLDFResource.Harvester.HarvestedType.weblogic.management.'
                 'runtime.ServerRuntimeMBean.HarvestedAttribute'] = 'OracleHome'
        replacement_dict = dict()
        replacement_dict['WLDFSystemResource.WLDFResource.Harvester.HarvestedType.HarvestedAttribute'] = dict()
        list_entry = dict()
        list_entry[variable_injector.REGEXP_PATTERN] = 'OracleHome'
        replacement_dict['WLDFSystemResource.WLDFResource.Harvester.HarvestedType.HarvestedAttribute'][
            variable_injector.REGEXP] = [list_entry]
        actual = self._helper.inject_variables(replacement_dict)
        self._compare_to_expected_dictionary(expected, actual)
        wldf_list = self._model['resources']['WLDFSystemResource']['MyWldfModule']['WLDFResource']['Harvester'][
            'HarvestedType']['weblogic.management.runtime.ServerRuntimeMBean']['HarvestedAttribute']
        found = False
        for entry in wldf_list:
            if entry == '@@PROP:WLDFSystemResource.MyWldfModule.WLDFResource.Harvester.HarvestedType.' \
                        'weblogic.management.runtime.ServerRuntimeMBean.HarvestedAttribute@@':
                found = True
                break
        self.assertEqual(True, found)

    def testWithSegmentInStringInList(self):
        expected = dict()
        expected['WLDFSystemResource.MyWldfModule.WLDFResource.Harvester.HarvestedType.weblogic.management.'
                 'runtime.ServerRuntimeMBean.HarvestedInstance--ManagedServer'] = 'm1'
        replacement_dict = dict()
        replacement_dict['WLDFSystemResource.WLDFResource.Harvester.HarvestedType.HarvestedInstance'] = dict()
        list_entry = dict()
        list_entry[variable_injector.REGEXP_PATTERN] = 'm1'
        list_entry[variable_injector.REGEXP_SUFFIX] = 'ManagedServer'
        replacement_dict['WLDFSystemResource.WLDFResource.Harvester.HarvestedType.HarvestedInstance'][
            variable_injector.REGEXP] = [list_entry]
        actual = self._helper.inject_variables(replacement_dict)
        self._compare_to_expected_dictionary(expected, actual)
        wldf_list = self._model['resources']['WLDFSystemResource']['MyWldfModule']['WLDFResource']['Harvester'][
            'HarvestedType']['weblogic.management.runtime.ServerRuntimeMBean']['HarvestedInstance']
        found = False
        for entry in wldf_list:
            if entry == 'com.bea:Name=@@PROP:WLDFSystemResource.MyWldfModule.WLDFResource.Harvester.HarvestedType.' \
                        'weblogic.management.runtime.ServerRuntimeMBean.HarvestedInstance--ManagedServer@@' \
                        ',Type=ServerRuntime':
                found = True
                break
        self.assertEqual(True, found)

    def testWithMBeanName(self):
        expected = dict()
        expected['JDBCSystemResource.Database2.JdbcResource.JDBCDriverParams.Properties.user.Value'] = 'sys as dba'
        expected['JDBCSystemResource.Database1.JdbcResource.JDBCDriverParams.Properties.user.Value'] = 'admin'
        replacement_dict = dict()
        replacement_dict['JDBCSystemResource.JdbcResource.JDBCDriverParams.Properties[user].Value'] = dict()
        actual = self._helper.inject_variables(replacement_dict)
        self._compare_to_expected_dictionary(expected, actual)

    def testWithListMBeanName(self):
        expected = dict()
        expected['Server.m1.SSL.Enabled'] = 'True'
        expected['Server.m2.SSL.Enabled'] = 'True'
        replacement_dict = dict()
        replacement_dict['Server[m1,m2].SSL.Enabled'] = dict()
        actual = self._helper.inject_variables(replacement_dict)
        self._compare_to_expected_dictionary(expected, actual)

    def testWithManagedServerKeyword(self):
        expected = dict()
        expected['Server.m1.SSL.Enabled'] = 'True'
        expected['Server.m2.SSL.Enabled'] = 'True'
        replacement_dict = dict()
        replacement_dict['Server[MANAGED_SERVERS].SSL.Enabled'] = dict()
        actual = self._helper.inject_variables(replacement_dict)
        self._compare_to_expected_dictionary(expected, actual)

    def testWithMultiKeyword(self):
        expected = dict()
        expected['Server.AdminServer.SSL.Enabled'] = 'True'
        expected['Server.m1.SSL.Enabled'] = 'True'
        expected['Server.m2.SSL.Enabled'] = 'True'
        replacement_dict = dict()
        replacement_dict['Server[MANAGED_SERVERS,ADMIN_SERVER].SSL.Enabled'] = dict()
        actual = self._helper.inject_variables(replacement_dict)
        self._compare_to_expected_dictionary(expected, actual)

    def testWithVariableHelperKeywords(self):
        expected = dict()
        expected['JMSSystemResource.MyJmsModule.JmsResource.ForeignServer.MyForeignServer.ConnectionURL'] \
            = 't3://my.other.cluster:7001'
        expected['Server.AdminServer.ListenPort'] = '9001'
        expected['Server.m2.ListenPort'] = '9005'
        expected['Server.m1.ListenPort'] = '9003'
        expected['Machine.machine1.NodeManager.ListenPort'] = '5557'
        expected['Machine.machine1.NodeManager.PasswordEncrypted'] = '--FIX ME--'
        expected['Machine.machine1.NodeManager.UserName'] = 'admin'
        inserted, model, variable_file_name = self._helper.inject_variables_keyword_file(
            variable_file_name=self._variable_file,
            variable_injector_path_name=self._resources_dir,
            variable_injector_file_name=self._variable_injector_keyword,
            variable_keywords_path_name=self._resources_dir, variable_keywords_file_name=self._keywords_file)
        self.assertEqual(self._variable_file, variable_file_name)
        self.assertEqual(True, inserted)
        actual = variables.load_variables(self._variable_file)
        self._compare_to_expected_dictionary(expected, actual)

    def testForceAttribute(self):
        expected = dict()
        expected['Server.AdminServer.SSL.HostnameVerificationIgnored'] = 'false'
        expected['Server.m1.SSL.HostnameVerificationIgnored'] = 'false'
        expected['Server.m2.SSL.HostnameVerificationIgnored'] = 'false'
        replacement_dict = dict()
        replacement_dict['Server.SSL.HostnameVerificationIgnored'] = dict()
        replacement_dict['Server.SSL.HostnameVerificationIgnored'][variable_injector.FORCE] = True
        actual = self._helper.inject_variables(replacement_dict)
        self._compare_to_expected_dictionary(expected, actual)

    def testForceAttributeWithTwoDefaults(self):
        expected = dict()
        expected['JMSSystemResource.MyJmsModule.JmsResource.Template.JmsTemplate.MaximumMessageSize'] = '0'
        replacement_dict = dict()
        replacement_dict['JMSSystemResource.JmsResource.Template.MaximumMessageSize'] = dict()
        replacement_dict['JMSSystemResource.JmsResource.Template.MaximumMessageSize'][variable_injector.FORCE] = True
        actual = self._helper.inject_variables(replacement_dict)
        self._compare_to_expected_dictionary(expected, actual)

    def testReplaceVariableValueAttribute(self):
        expected = dict()
        expected[
            'JMSSystemResource.MyJmsModule.JmsResource.ForeignServer.MyForeignServer.JNDIProperty'
            '.java.naming.security.principal.Value'] = 'k8s'
        replacement_dict = dict()
        replacement_dict['JMSSystemResource.JmsResource.ForeignServer.'
                         'JNDIProperty[java.naming.security.principal].Value'] = dict()
        replacement_dict['JMSSystemResource.JmsResource.ForeignServer.'
                         'JNDIProperty[java.naming.security.principal].Value'][
            variable_injector.VARIABLE_VALUE] = 'k8s'
        actual = self._helper.inject_variables(replacement_dict)
        print actual
        self._compare_to_expected_dictionary(expected, actual)

    def testReplaceVariableValueSegmentInString(self):
        expected = dict()
        expected['JDBCSystemResource.Database2.JdbcResource.JDBCDriverParams.URL--Host'] = \
            'den00chv'
        replacement_dict = dict()
        replacement_dict['JDBCSystemResource[Database2].JdbcResource.JDBCDriverParams.URL'] = dict()
        list_entry = dict()
        list_entry[variable_injector.REGEXP_PATTERN] = '(?<=HOST=)[\w.-]+(?=\))'
        list_entry[variable_injector.REGEXP_SUFFIX] = 'Host'
        replacement_dict['JDBCSystemResource[Database2].JdbcResource.JDBCDriverParams.URL'][
            variable_injector.REGEXP] = [list_entry]
        replacement_dict['JDBCSystemResource[Database2].JdbcResource.JDBCDriverParams.URL'][
            variable_injector.VARIABLE_VALUE] = 'den00chv'
        actual = self._helper.inject_variables(replacement_dict)
        self._compare_to_expected_dictionary(expected, actual)

    def testReplaceVariableValueSegmentInDictionary(self):
        expected = dict()
        expected['MailSession.MailSession-0.Properties--SmtpHost'] = 'localhost'
        expected['MailSession.MyMailSession.Properties--SmtpHost'] = 'localhost'
        replacement_dict = dict()
        replacement_dict['MailSession.Properties'] = dict()
        list_entry = dict()
        list_entry[variable_injector.REGEXP_PATTERN] = 'mail.smtp.host'
        list_entry[variable_injector.REGEXP_SUFFIX] = 'SmtpHost'
        replacement_dict['MailSession.Properties'][variable_injector.REGEXP] = [list_entry]
        replacement_dict['MailSession.Properties'][variable_injector.VARIABLE_VALUE] = 'localhost'
        actual = self._helper.inject_variables(replacement_dict)
        self._compare_to_expected_dictionary(expected, actual)

    def _compare_to_expected_dictionary(self, expected, actual):
        self.assertEqual(len(expected), len(actual),
                         'Not the same number of entries : expected=' + str(len(expected)) + ', actual=' + str(
                             len(actual)))
        for k, v in actual.iteritems():
            self.assertEqual(True, k in expected and v == expected[k], 'Actual item not in expected ' + k +
                             ' : ' + v + '   expected=' + str(expected))


if __name__ == '__main__':
    unittest.main()
