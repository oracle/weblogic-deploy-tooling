"""
Copyright (c) 2017, 2019, Oracle Corporation and/or its affiliates.  All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import os
from shutil import copy2
import unittest

from java.io import File
from java.lang import String
from java.lang import System

from oracle.weblogic.deploy.encrypt import EncryptionUtils

from wlsdeploy.util.cla_utils import CommandLineArgUtil
import encrypt
import wlsdeploy.util.variables as variables_helper
from wlsdeploy.util.model_translator import FileToPython

class EncryptionTestCase(unittest.TestCase):
    _execution_dir = '../../unit-tests/'
    _resources_dir = '../../test-classes/'
    _oracle_home = None

    _src_model_file_wo_variables = os.path.join(_resources_dir, 'encryption-test.yaml')
    _src_model_file_wo_variables_for_multi = os.path.join(_resources_dir, 'encryption-test-multiple.yaml')
    _src_model_file_w_variables = os.path.join(_resources_dir, 'encryption-test-variables.yaml')
    _src_model_file_w_variables_multi = os.path.join(_resources_dir, 'encryption-test-variables-multiple.yaml')
    _src_variable_file = os.path.join(_resources_dir, 'encryption-test-variables.properties')

    _target_model_test1 = os.path.join(_execution_dir, 'model-test1.yaml')
    _target_model_test2 = os.path.join(_execution_dir, 'model-test2.yaml')
    _target_model_test3 = os.path.join(_execution_dir, 'model-test3.yaml')
    _target_variables_test3 = os.path.join(_execution_dir, 'variables-test3.properties')

    _passphrase = 'my dog is a rottweiler'
    _unencrypted_password = 'welcome1'
    _unencrypted_password_second = 'another1'

    def setUp(self):
        if not os.path.exists(self._execution_dir):
            os.makedirs(self._execution_dir)

        wlst_dir = File(System.getProperty('unit-test-wlst-dir'))
        self._oracle_home = wlst_dir.getParentFile().getParentFile().getParentFile().getCanonicalPath()
        return

    def testDirectEncryption(self):
        copy2(self._src_model_file_wo_variables, self._target_model_test1)

        args = list()
        args.append('encrypt')  # dummy arg for args[0] to get arg padding right
        args.append(CommandLineArgUtil.ORACLE_HOME_SWITCH)
        args.append(self._oracle_home)
        args.append(CommandLineArgUtil.MODEL_FILE_SWITCH)
        args.append(self._target_model_test1)
        args.append(CommandLineArgUtil.PASSPHRASE_SWITCH)
        args.append(self._passphrase)
        exit_code = encrypt._process_request(args)
        self.assertEquals(exit_code, 0)

        model = FileToPython(self._target_model_test1).parse()
        passphrase_array = String(self._passphrase).toCharArray()

        admin_pass = model['domainInfo']['AdminPassword']
        self.assertEquals(admin_pass.startswith('{AES}'), True)
        _decrypted_admin_pass = EncryptionUtils.decryptString(admin_pass, passphrase_array)
        self.assertEquals(str(String(_decrypted_admin_pass)), self._unencrypted_password)

        nm_pass = model['topology']['SecurityConfiguration']['NodeManagerPasswordEncrypted']
        self.assertEquals(nm_pass.startswith('{AES}'), True)
        _decrypted_nm_pass = EncryptionUtils.decryptString(nm_pass, passphrase_array)
        self.assertEquals(str(String(_decrypted_nm_pass)), self._unencrypted_password)

        ds1_pass = model['resources']['JDBCSystemResource']['Generic1']['JdbcResource']['JDBCDriverParams']['PasswordEncrypted']
        self.assertEquals(ds1_pass.startswith('{AES}'), True)
        _decrypted_ds1_pass = EncryptionUtils.decryptString(ds1_pass, passphrase_array)
        self.assertEquals(str(String(_decrypted_ds1_pass)), self._unencrypted_password)

        ons_pass = \
            model['resources']['JDBCSystemResource']['Generic1']['JdbcResource']['JDBCOracleParams']['OnsWalletPasswordEncrypted']
        self.assertEquals(ons_pass.startswith('{AES}'), True)
        _decrypted_ons_pass = EncryptionUtils.decryptString(ons_pass, passphrase_array)
        self.assertEquals(str(String(_decrypted_ons_pass)), self._unencrypted_password)

        ds2_pass = model['resources']['JDBCSystemResource']['Generic2']['JdbcResource']['JDBCDriverParams']['PasswordEncrypted']
        self.assertEquals(ds2_pass.startswith('{AES}'), True)
        _decrypted_ds2_pass = EncryptionUtils.decryptString(ds2_pass, passphrase_array)
        self.assertEquals(str(String(_decrypted_ds2_pass)), self._unencrypted_password)
        return

    def testDirectEncryptionVariablesNoOverwrite(self):
        copy2(self._src_model_file_w_variables, self._target_model_test2)

        args = list()
        args.append('encrypt')  # dummy arg for args[0] to get arg padding right
        args.append(CommandLineArgUtil.ORACLE_HOME_SWITCH)
        args.append(self._oracle_home)
        args.append(CommandLineArgUtil.MODEL_FILE_SWITCH)
        args.append(self._target_model_test2)
        args.append(CommandLineArgUtil.PASSPHRASE_SWITCH)
        args.append(self._passphrase)
        exit_code = encrypt._process_request(args)
        self.assertEquals(exit_code, 0)

        model = FileToPython(self._target_model_test2).parse()
        passphrase_array = String(self._passphrase).toCharArray()

        admin_pass = model['domainInfo']['AdminPassword']
        self.assertNotEquals(admin_pass.startswith('{AES}'), True)

        nm_pass = model['topology']['SecurityConfiguration']['NodeManagerPasswordEncrypted']
        self.assertNotEquals(nm_pass.startswith('{AES}'), True)

        ds1_pass = model['resources']['JDBCSystemResource']['Generic1']['JdbcResource']['JDBCDriverParams']['PasswordEncrypted']
        self.assertEquals(ds1_pass.startswith('{AES}'), True)
        _decrypted_ds1_pass = EncryptionUtils.decryptString(ds1_pass, passphrase_array)
        self.assertEquals(str(String(_decrypted_ds1_pass)), self._unencrypted_password)

        ons_pass = \
            model['resources']['JDBCSystemResource']['Generic1']['JdbcResource']['JDBCOracleParams']['OnsWalletPasswordEncrypted']
        self.assertNotEquals(ons_pass.startswith('{AES}'), True)

        ds2_pass = model['resources']['JDBCSystemResource']['Generic2']['JdbcResource']['JDBCDriverParams']['PasswordEncrypted']
        self.assertEquals(ds2_pass.startswith('{AES}'), True)
        _decrypted_ds2_pass = EncryptionUtils.decryptString(ds2_pass, passphrase_array)
        self.assertEquals(str(String(_decrypted_ds2_pass)), self._unencrypted_password)
        return

    def testIndirectEncryptionVariables(self):
        copy2(self._src_model_file_w_variables, self._target_model_test3)
        copy2(self._src_variable_file, self._target_variables_test3)

        args = list()
        args.append('encrypt')  # dummy arg for args[0] to get arg padding right
        args.append(CommandLineArgUtil.ORACLE_HOME_SWITCH)
        args.append(self._oracle_home)
        args.append(CommandLineArgUtil.MODEL_FILE_SWITCH)
        args.append(self._target_model_test3)
        args.append(CommandLineArgUtil.VARIABLE_FILE_SWITCH)
        args.append(self._target_variables_test3)
        args.append(CommandLineArgUtil.PASSPHRASE_SWITCH)
        args.append(self._passphrase)
        exit_code = encrypt._process_request(args)
        self.assertEquals(exit_code, 0)

        model = FileToPython(self._target_model_test3).parse()
        variables = variables_helper.load_variables(self._target_variables_test3)
        passphrase_array = String(self._passphrase).toCharArray()

        admin_pass = model['domainInfo']['AdminPassword']
        self.assertNotEquals(admin_pass.startswith('{AES}'), True)
        admin_pass = variables['admin.password']
        self.assertEquals(admin_pass.startswith('{AES}'), True)
        _decrypted_admin_pass = EncryptionUtils.decryptString(admin_pass, passphrase_array)
        self.assertEquals(str(String(_decrypted_admin_pass)), self._unencrypted_password)

        nm_pass = model['topology']['SecurityConfiguration']['NodeManagerPasswordEncrypted']
        self.assertNotEquals(nm_pass.startswith('{AES}'), True)
        nm_pass = variables['nm.password']
        self.assertEquals(nm_pass.startswith('{AES}'), True)
        _decrypted_nm_pass = EncryptionUtils.decryptString(nm_pass, passphrase_array)
        self.assertEquals(str(String(_decrypted_nm_pass)), self._unencrypted_password)

        ds1_pass = model['resources']['JDBCSystemResource']['Generic1']['JdbcResource']['JDBCDriverParams']['PasswordEncrypted']
        self.assertEquals(ds1_pass.startswith('{AES}'), True)
        _decrypted_ds1_pass = EncryptionUtils.decryptString(ds1_pass, passphrase_array)
        self.assertEquals(str(String(_decrypted_ds1_pass)), self._unencrypted_password)

        ons_pass = \
            model['resources']['JDBCSystemResource']['Generic1']['JdbcResource']['JDBCOracleParams']['OnsWalletPasswordEncrypted']
        self.assertNotEquals(ons_pass.startswith('{AES}'), True)
        ons_pass = variables['slc05til.ons.pass']
        self.assertEquals(ons_pass.startswith('{AES}'), True)
        _decrypted_ons_pass = EncryptionUtils.decryptString(ons_pass, passphrase_array)
        self.assertEquals(str(String(_decrypted_ons_pass)), self._unencrypted_password)

        ds2_pass = model['resources']['JDBCSystemResource']['Generic2']['JdbcResource']['JDBCDriverParams']['PasswordEncrypted']
        self.assertEquals(ds2_pass.startswith('{AES}'), True)
        _decrypted_ds2_pass = EncryptionUtils.decryptString(ds2_pass, passphrase_array)
        self.assertEquals(str(String(_decrypted_ds2_pass)), self._unencrypted_password)
        return

    def testMultipleModelDirectEncryption(self):
        copy2(self._src_model_file_wo_variables, self._target_model_test1)
        copy2(self._src_model_file_wo_variables_for_multi, self._target_model_test2)

        args = list()
        args.append('encrypt')  # dummy arg for args[0] to get arg padding right
        args.append(CommandLineArgUtil.ORACLE_HOME_SWITCH)
        args.append(self._oracle_home)
        args.append(CommandLineArgUtil.MODEL_FILE_SWITCH)
        args.append(self._target_model_test1 + ',' + self._target_model_test2)
        args.append(CommandLineArgUtil.PASSPHRASE_SWITCH)
        args.append(self._passphrase)
        exit_code = encrypt._process_request(args)
        self.assertEquals(exit_code, 0)

        model1 = FileToPython(self._target_model_test1).parse()
        model2 = FileToPython(self._target_model_test2).parse()
        passphrase_array = String(self._passphrase).toCharArray()

        admin_pass = model1['domainInfo']['AdminPassword']
        self.assertEquals(admin_pass.startswith('{AES}'), True)
        _decrypted_admin_pass = EncryptionUtils.decryptString(admin_pass, passphrase_array)
        self.assertEquals(str(String(_decrypted_admin_pass)), self._unencrypted_password)

        admin_pass = model2['domainInfo']['AdminPassword']
        self.assertEquals(admin_pass.startswith('{AES}'), True)
        _decrypted_admin_pass = EncryptionUtils.decryptString(admin_pass, passphrase_array)
        self.assertEquals(str(String(_decrypted_admin_pass)), self._unencrypted_password_second)

        return

    def testMultipleModelsIndirectEncryptionVariables(self):
        copy2(self._src_model_file_w_variables, self._target_model_test2)
        copy2(self._src_model_file_w_variables_multi, self._target_model_test3)
        copy2(self._src_variable_file, self._target_variables_test3)

        args = list()
        args.append('encrypt')  # dummy arg for args[0] to get arg padding right
        args.append(CommandLineArgUtil.ORACLE_HOME_SWITCH)
        args.append(self._oracle_home)
        args.append(CommandLineArgUtil.MODEL_FILE_SWITCH)
        args.append(self._target_model_test2 + ',' + self._target_model_test3)
        args.append(CommandLineArgUtil.VARIABLE_FILE_SWITCH)
        args.append(self._target_variables_test3)
        args.append(CommandLineArgUtil.PASSPHRASE_SWITCH)
        args.append(self._passphrase)
        exit_code = encrypt._process_request(args)
        self.assertEquals(exit_code, 0)

        model2 = FileToPython(self._target_model_test2).parse()
        model3 = FileToPython(self._target_model_test3).parse()
        variables = variables_helper.load_variables(self._target_variables_test3)
        passphrase_array = String(self._passphrase).toCharArray()

        admin_pass = model2['domainInfo']['AdminPassword']
        self.assertNotEquals(admin_pass.startswith('{AES}'), True)
        admin_pass = model3['domainInfo']['AdminPassword']
        self.assertNotEquals(admin_pass.startswith('{AES}'), True)
        admin_pass = variables['admin.password']
        self.assertEquals(admin_pass.startswith('{AES}'), True)
        _decrypted_admin_pass = EncryptionUtils.decryptString(admin_pass, passphrase_array)
        self.assertEquals(str(String(_decrypted_admin_pass)), self._unencrypted_password)

        nm_pass = model2['topology']['SecurityConfiguration']['NodeManagerPasswordEncrypted']
        self.assertNotEquals(nm_pass.startswith('{AES}'), True)
        nm_pass = variables['nm.password']
        self.assertEquals(nm_pass.startswith('{AES}'), True)
        _decrypted_nm_pass = EncryptionUtils.decryptString(nm_pass, passphrase_array)
        self.assertEquals(str(String(_decrypted_nm_pass)), self._unencrypted_password)

        ds1_pass = model2['resources']['JDBCSystemResource']['Generic1']['JdbcResource']['JDBCDriverParams']['PasswordEncrypted']
        self.assertEquals(ds1_pass.startswith('{AES}'), True)
        _decrypted_ds1_pass = EncryptionUtils.decryptString(ds1_pass, passphrase_array)
        self.assertEquals(str(String(_decrypted_ds1_pass)), self._unencrypted_password)

        return

    def testMultipleModelsDirectAndVariables(self):
        copy2(self._src_model_file_w_variables, self._target_model_test1)
        copy2(self._src_model_file_wo_variables_for_multi, self._target_model_test2)
        copy2(self._src_variable_file, self._target_variables_test3)

        args = list()
        args.append('encrypt')  # dummy arg for args[0] to get arg padding right
        args.append(CommandLineArgUtil.ORACLE_HOME_SWITCH)
        args.append(self._oracle_home)
        args.append(CommandLineArgUtil.MODEL_FILE_SWITCH)
        args.append(self._target_model_test1 + ',' + self._target_model_test2)
        args.append(CommandLineArgUtil.VARIABLE_FILE_SWITCH)
        args.append(self._target_variables_test3)
        args.append(CommandLineArgUtil.PASSPHRASE_SWITCH)
        args.append(self._passphrase)
        exit_code = encrypt._process_request(args)
        self.assertEquals(exit_code, 0)

        model2 = FileToPython(self._target_model_test1).parse()
        model3 = FileToPython(self._target_model_test2).parse()
        variables = variables_helper.load_variables(self._target_variables_test3)
        passphrase_array = String(self._passphrase).toCharArray()

        admin_pass = model2['domainInfo']['AdminPassword']
        self.assertNotEquals(admin_pass.startswith('{AES}'), True)
        admin_pass = variables['admin.password']
        self.assertEquals(admin_pass.startswith('{AES}'), True)
        _decrypted_admin_pass = EncryptionUtils.decryptString(admin_pass, passphrase_array)
        self.assertEquals(str(String(_decrypted_admin_pass)), self._unencrypted_password)
        admin_pass = model3['domainInfo']['AdminPassword']
        self.assertEquals(admin_pass.startswith('{AES}'), True)
        _decrypted_admin_pass = EncryptionUtils.decryptString(admin_pass, passphrase_array)
        self.assertEquals(str(String(_decrypted_admin_pass)), self._unencrypted_password_second)

        return