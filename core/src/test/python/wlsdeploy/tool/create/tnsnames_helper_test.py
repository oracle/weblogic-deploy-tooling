"""
Copyright (c) 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import os

from base_test import BaseTestCase

from wlsdeploy.exception.exception_types import ExceptionType
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.create.tnsnames_helper import TnsNamesHelper
from wlsdeploy.util import path_helper
from wlsdeploy.util.cla_utils import CommandLineArgUtil
from wlsdeploy.util.model_context import ModelContext


class TnsNamesHelperTest(BaseTestCase):
    __class_name = 'TnsNamesHelperTest'
    __logger = PlatformLogger('wlsdeploy.create')
    __resources_dir = os.path.abspath('../../test-classes')
    __atp_tnsnames_ora_path = 'config/wlsdeploy/dbWallets/atp/tnsnames.ora'
    __ssl_tnsnames_ora_path = 'config/wlsdeploy/dbWallets/ssl/tnsnames.ora'

    wls_version = '12.2.1.3'

    arg_map = {
        CommandLineArgUtil.ORACLE_HOME_SWITCH: '/oracleHome',
        CommandLineArgUtil.DOMAIN_HOME_SWITCH: __resources_dir
    }

    path_helper.initialize_path_helper(ExceptionType.CREATE, unit_test_force=True)
    model_context = ModelContext("test", arg_map)

    def __init__(self, *args):
        BaseTestCase.__init__(self, *args)

    def setUp(self):
        BaseTestCase.setUp(self)

    def tearDown(self):
        BaseTestCase.tearDown(self)

    def test_get_connect_string_with_absolute_path_to_atp_tnsnames(self):
        tnsnames_file = os.path.join(self.__resources_dir, self.__atp_tnsnames_ora_path)
        tnsnames_helper = TnsNamesHelper(self.model_context, tnsnames_file)
        expected_content = '(connect_data=(service_name=abcdefg1234567_wdt_tp.adb.oraclecloud.com))'

        actual = tnsnames_helper.get_connect_string('wdt_tp')

        self.assertEqual(True, actual is not None, 'wdt_tp alias should return an entry')
        self.assertEqual(True, expected_content in actual, 'wdt_alias service name should include abcdefg1234567_wdt_tp')

    def test_get_connect_string_with_archive_path_to_atp_tnsnames(self):
        tnsnames_helper = TnsNamesHelper(self.model_context, self.__atp_tnsnames_ora_path)
        expected_content = '(connect_data=(service_name=abcdefg1234567_wdt_high.adb.oraclecloud.com))'

        actual = tnsnames_helper.get_connect_string('wdt_high')

        self.assertEqual(True, actual is not None, 'wdt_high alias should return an entry')
        self.assertEqual(True, expected_content in actual, 'wdt_alias service name should include abcdefg1234567_wdt_high')

    def test_get_connect_string_with_absolute_path_to_ssl_tnsnames(self):
        tnsnames_file = os.path.join(self.__resources_dir, self.__ssl_tnsnames_ora_path)
        tnsnames_helper = TnsNamesHelper(self.model_context, tnsnames_file)
        expected_content = '(SERVICE_NAME=orclpdb.rpatrick-db.dummy.oraclevcn.com)'

        actual = tnsnames_helper.get_connect_string('ORCLPDB')

        self.assertEqual(True, actual is not None, 'ORCLPDB alias should return an entry')
        self.assertEqual(True, expected_content in actual, 'ORCLPDB service name should include orclpdb.rpatrick-db')

    def test_get_connect_string_with_archive_path_to_ssl_tnsnames(self):
        tnsnames_helper = TnsNamesHelper(self.model_context, self.__ssl_tnsnames_ora_path)
        expected_content = '(SERVICE_NAME=orclpdb.rpatrick-db.dummy.oraclevcn.com)'

        actual = tnsnames_helper.get_connect_string('ORCLPDB')

        self.assertEqual(True, actual is not None, 'ORCLPDB alias should return an entry')
        self.assertEqual(True, expected_content in actual, 'ORCLPDB service name should include orclpdb.rpatrick-db')

    def testFixingDescriptionList(self):
        tnsnames_file = os.path.join(self.__resources_dir, self.__atp_tnsnames_ora_path)
        tnsnames_helper = TnsNamesHelper(self.model_context, tnsnames_file)

        src_url = '(description_list=(failover=on)(load_balance=off)(description=(retry_count=15)(retry_delay=3)' \
                  '(address=(protocol=tcps)(port=1522)(host=somewhere-in.oraclecloud.com))' \
                  '(connect_data=(service_name=some-service-in.oraclecloud.com))' \
                  '(security=(ssl_server_cert_dn="CN=some-cn-in.oraclecloud.com, OU=Oracle BMCS US, O=Oracle Corporation, L=Redwood City, ST=California, C=US")))' \
                  '(description=(retry_count=15)(retry_delay=3)(address=(protocol=tcps)(port=1522)(host=somewhere2-in.oraclecloud.com))' \
                  '(connect_data=(service_name=some-service-in.oraclecloud.com))' \
                  '(security=(ssl_server_cert_dn="CN=some-cn-in.oraclecloud.com, OU=Oracle BMCS US, O=Oracle Corporation, L=Redwood City, ST=California, C=US")))' \
                  '(description=(retry_count=15)(retry_delay=3)(address=(protocol=tcps)(port=1523)(host=somewhere2-in.oraclecloud.com))' \
                  '(connect_data=(service_name=some-service-in.oraclecloud.com))' \
                  '(security=(ssl_server_cert_dn="CN=some-cn-in.oraclecloud.com, OU=Oracle BMCS US, O=Oracle Corporation, L=Redwood City, ST=California, C=US")) ) )'

        expected_url = '(description_list=(failover=on)(load_balance=off)(description=(retry_count=15)(retry_delay=3)' \
                       '(address=(protocol=tcps)(port=1522)(host=somewhere-in.oraclecloud.com))' \
                       '(connect_data=(service_name=some-service-in.oraclecloud.com))' \
                       '(security=(ssl_server_cert_dn="CN=some-cn-in.oraclecloud.com, OU=Oracle BMCS US, O=Oracle Corporation, L=Redwood City, ST=California, C=US")))' \
                       '(description=(retry_count=15)(retry_delay=3)(address=(protocol=tcps)(port=1522)(host=somewhere2-in.oraclecloud.com))' \
                       '(connect_data=(service_name=some-service-in.oraclecloud.com))' \
                       '(security=(ssl_server_cert_dn="CN=some-cn-in.oraclecloud.com, OU=Oracle BMCS US, O=Oracle Corporation, L=Redwood City, ST=California, C=US")))' \
                       '(description=(retry_count=15)(retry_delay=3)(address=(protocol=tcps)(port=1523)(host=somewhere2-in.oraclecloud.com))' \
                       '(connect_data=(service_name=some-service-in.oraclecloud.com))' \
                       '(security=(ssl_server_cert_dn="CN=some-cn-in.oraclecloud.com, OU=Oracle BMCS US, O=Oracle Corporation, L=Redwood City, ST=California, C=US"))))'


        fixed_url = tnsnames_helper._cleanup_connect_string(src_url)
        self.assertEqual(fixed_url, expected_url)
        return

    def testFixingNonDescriptionList(self):
        tnsnames_file = os.path.join(self.__resources_dir, self.__atp_tnsnames_ora_path)
        tnsnames_helper = TnsNamesHelper(self.model_context, tnsnames_file)

        src_url = '(description= (address=(protocol=tcps)(port=1522)(host=some-cn-in.oraclecloud.com))' \
                  '(connect_data=(service_name=some-service-in.oraclecloud.com))' \
                  '(security=(ssl_server_cert_dn= "CN=some-cn-in.oraclecloud.com,OU=Oracle BMCS US,O=Oracle Corporation,L=Redwood City,ST=California,C=US")) )'

        expected_url = '(description=(address=(protocol=tcps)(port=1522)(host=some-cn-in.oraclecloud.com))' \
                       '(connect_data=(service_name=some-service-in.oraclecloud.com))' \
                       '(security=(ssl_server_cert_dn="CN=some-cn-in.oraclecloud.com,OU=Oracle BMCS US,O=Oracle Corporation,L=Redwood City,ST=California,C=US")))'

        fixed_url = tnsnames_helper._cleanup_connect_string(src_url)

        self.assertEqual(fixed_url, expected_url)
        return

    def testFixingDescriptionListWithoutServerDN(self):
        tnsnames_file = os.path.join(self.__resources_dir, self.__atp_tnsnames_ora_path)
        tnsnames_helper = TnsNamesHelper(self.model_context, tnsnames_file)

        src_url = '(description_list=(failover=on)(load_balance=off)(description=(retry_count=15)(retry_delay=3)' \
                  '(address=(protocol=tcps)(port=1522)(host=somewhere-in.oraclecloud.com))' \
                  '(connect_data=(service_name=some-service-in.oraclecloud.com))' \
                  '(security=(ssl_server_dn_match=yes)))' \
                  '(description=(retry_count=15)(retry_delay=3)(address=(protocol=tcps)(port=1522)(host=somewhere2-in.oraclecloud.com))' \
                  '(connect_data=(service_name=some-service-in.oraclecloud.com))' \
                  '(security=(ssl_server_dn_match=yes)))' \
                  '(description=(retry_count=15)(retry_delay=3)(address=(protocol=tcps)(port=1523)(host=somewhere2-in.oraclecloud.com))' \
                  '(connect_data=(service_name=some-service-in.oraclecloud.com))' \
                  '(security=(ssl_server_dn_match=yes)))'

        expected_url = '(description_list=(failover=on)(load_balance=off)(description=(retry_count=15)(retry_delay=3)' \
                       '(address=(protocol=tcps)(port=1522)(host=somewhere-in.oraclecloud.com))' \
                       '(connect_data=(service_name=some-service-in.oraclecloud.com))' \
                       '(security=(ssl_server_dn_match=yes)))' \
                       '(description=(retry_count=15)(retry_delay=3)(address=(protocol=tcps)(port=1522)(host=somewhere2-in.oraclecloud.com))' \
                       '(connect_data=(service_name=some-service-in.oraclecloud.com))' \
                       '(security=(ssl_server_dn_match=yes)))' \
                       '(description=(retry_count=15)(retry_delay=3)(address=(protocol=tcps)(port=1523)(host=somewhere2-in.oraclecloud.com))' \
                       '(connect_data=(service_name=some-service-in.oraclecloud.com))' \
                       '(security=(ssl_server_dn_match=yes)))'


        fixed_url = tnsnames_helper._cleanup_connect_string(src_url)
        self.assertEqual(fixed_url, expected_url)
        return

    def testFixingNonDescriptionListWithoutServerDN(self):
        tnsnames_file = os.path.join(self.__resources_dir, self.__atp_tnsnames_ora_path)
        tnsnames_helper = TnsNamesHelper(self.model_context, tnsnames_file)

        src_url = '(description= (address=(protocol=tcps)(port=1522)(host=some-cn-in.oraclecloud.com))' \
                  '(connect_data=(service_name=some-service-in.oraclecloud.com))' \
                  '(security=(ssl_server_dn_match=yes)) )'

        expected_url = '(description=(address=(protocol=tcps)(port=1522)(host=some-cn-in.oraclecloud.com))' \
                       '(connect_data=(service_name=some-service-in.oraclecloud.com))' \
                       '(security=(ssl_server_dn_match=yes)))'

        fixed_url = tnsnames_helper._cleanup_connect_string(src_url)

        self.assertEqual(fixed_url, expected_url)
        return
