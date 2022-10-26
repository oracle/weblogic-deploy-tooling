"""
Copyright (c) 2022, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import unittest

from wlsdeploy.tool.create import atp_helper

class AtpHelperTestCase(unittest.TestCase):

    def testFixingDescriptionList(self):
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


        fixed_url = atp_helper.cleanup_connect_string(src_url)
        self.assertEqual(fixed_url, expected_url)
        return

    def testFixingNonDescriptionList(self):
        src_url = '(description= (address=(protocol=tcps)(port=1522)(host=some-cn-in.oraclecloud.com))' \
                  '(connect_data=(service_name=some-service-in.oraclecloud.com))' \
                  '(security=(ssl_server_cert_dn= "CN=some-cn-in.oraclecloud.com,OU=Oracle BMCS US,O=Oracle Corporation,L=Redwood City,ST=California,C=US")) )'

        expected_url = '(description=(address=(protocol=tcps)(port=1522)(host=some-cn-in.oraclecloud.com))' \
                  '(connect_data=(service_name=some-service-in.oraclecloud.com))' \
                  '(security=(ssl_server_cert_dn="CN=some-cn-in.oraclecloud.com,OU=Oracle BMCS US,O=Oracle Corporation,L=Redwood City,ST=California,C=US")))'

        fixed_url = atp_helper.cleanup_connect_string(src_url)

        self.assertEqual(fixed_url, expected_url)
        return
