"""
Copyright (c) 2017, 2022, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import java.lang.Exception as JException

import weblogic.management.provider.ManagementServiceClient as ManagementServiceClient
import weblogic.security.internal.SerializedSystemIni as SerializedSystemIni
import weblogic.security.internal.encryption.ClearOrEncryptedService as ClearOrEncryptedService
import weblogic.version as version_helper

from wlsdeploy.exception import exception_helper
from wlsdeploy.util import string_utils
import wlsdeploy.util.unicode_helper as str_helper

import os
import re


class WebLogicHelper(object):
    """
    Helper functions for version-specific WebLogic operations.
    """

    MINIMUM_WEBLOGIC_VERSION = '10.3.6'
    _class_name = 'WebLogicHelper'

    def __init__(self, logger, wls_version=None):
        """
        Initialization of helper class with logger and version
        :param logger: where to log information from version requests
        :param wls_version: represented by this helper instance. If None, then retrieve version from weblogic tool
        """
        self.logger = logger
        if wls_version is not None:
            self.wl_version = str_helper.to_string(wls_version)
            self.wl_version_actual = str_helper.to_string(version_helper.getReleaseBuildVersion())
        else:
            self.wl_version = str_helper.to_string(version_helper.getReleaseBuildVersion())
            self.wl_version_actual = self.wl_version

    def get_actual_weblogic_version(self):
        """
        Get the WebLogic version number of the WLST interpreter executing this code.
        :return: the WebLogic version number
        """
        return self.wl_version_actual

    def get_weblogic_version(self):
        """
        Get the WebLogic version specified during creation of the instance.  If no version was specified
        to the constructor, the version number of the WLST interpreter executing this code will be returned.
        :return: the WebLogic version number
        """
        return self.wl_version

    def is_supported_weblogic_version(self, use_actual_version=False):
        """
        Is the version of WebLogic supported by the WLS Deploy tooling?
        :param use_actual_version: whether to use the version of WLST executing or the version number passed in?
        :return: true if the version is supported; false otherwise
        """
        return self.is_weblogic_version_or_above(self.MINIMUM_WEBLOGIC_VERSION, use_actual_version)

    def is_mt_offline_provisioning_supported(self):
        """
        Is MultiTenant offline provisioning supported?
        :return: true if MT offline provisioning is supported; false otherwise
        """
        return self.is_weblogic_version_or_above('12.2.1.1') or not self.is_weblogic_version_or_above('12.2.1')

    def is_mt_provisioning_supported(self):
        """
        Is MultiTenant offline provisioning in a version that is still supports MT?
        :return: true if MT provisioning is supported; false otherwise
        """
        return not self.is_weblogic_version_or_above('14.1.1')

    def is_select_template_supported(self):
        """
        Is selectTemplate() supported in this version of WLST?
        :return: true if selectTemplate() is supported; false otherwise
        """
        return self.is_weblogic_version_or_above('12.2.1')

    def is_database_defaults_supported(self):
        """
        Is setDatabaseDefaults() supported by the version of JRF?
        :return: true if use the method to prime the JRF database defaults
        """
        return self.is_weblogic_version_or_above('12.1.2')

    def is_set_server_groups_supported(self):
        """
        Is setServerGroups() supported by the version of WLST?
        :return: true if the setServerGroups() is supported
        """
        return self.is_weblogic_version_or_above('12.1.2')

    def is_dynamic_clusters_supported(self):
        """
        Is dynamic clusters supported in this version of WLS?
        :return: true if dynamic clusters are supported; false otherwise
        """
        return self.is_weblogic_version_or_above('12.1.2')

    def is_dynamic_cluster_one_server_group_supported(self):
        """
        Is the version of WLST one that supports targeting one server group to dynamic cluster?
        :return: true if within the versions supporting the above
        """
        return self.is_weblogic_version_or_above('12.2.1.1') and not self.is_weblogic_version_or_above('12.2.1.4')

    def is_dynamic_cluster_multiple_server_groups_supported(self):
        """
        Is the version of WLST one that supports targeting one server group to dynamic cluster?
        :return: true if within the versions supporting the above
        """
        return self.is_weblogic_version_or_above('12.2.1.4')

    def is_topology_profile_supported(self):
        """
        Is topology profile supported in domain extension templates?
        :return: true if version is within the range supporting topology profiles, false otherwise
        """
        return self.is_weblogic_version_or_above('12.2.1')

    def get_jdbc_url_from_rcu_connect_string(self, rcu_connect_string):
        """
        Get the JDBC URL from the RCU connect string.
        :param rcu_connect_string: the RCU connect string
        :return: the JDBC URL
        """
        jdbc_url = rcu_connect_string
        if not rcu_connect_string.startswith('jdbc:oracle:'):
            if rcu_connect_string.startswith('('):
                # Long format
                jdbc_url = 'jdbc:oracle:thin:@' + rcu_connect_string
            elif rcu_connect_string.rfind('/') != -1:
                # host:port/service format
                jdbc_url = 'jdbc:oracle:thin:@//' + rcu_connect_string
            else:
                # host:port:sid format
                jdbc_url = 'jdbc:oracle:thin:@' + rcu_connect_string
        return jdbc_url

    def get_stb_data_source_jdbc_driver_name(self):
        """
        Get the Service Table JDBC Driver class name.
        :return: the Service Table JDBC Driver class name
        """
        return 'oracle.jdbc.OracleDriver'

    def get_stb_user_name(self, rcu_prefix):
        """
        Get the Service Table schema user name from the RCU prefix.
        :param rcu_prefix: the RCU prefix
        :return: the Service Table schema user name
        """
        if self.is_weblogic_version_or_above('12.1.2'):
            return rcu_prefix + '_STB'
        return rcu_prefix + '_MDS'

    def get_jrf_service_table_datasource_name(self):
        """
        Get the JRF DataSource name for the service table schema.
        :return: the JRF DataSource name
        """
        if self.is_weblogic_version_or_above('12.1.2'):
            return 'LocalSvcTblDataSource'
        return 'mds-owsm'

    def get_default_admin_username(self):
        """
        Get the default Administrative username.
        :return: the username
        """
        return 'weblogic'

    def get_default_wls_domain_name(self):
        """
        Get the default domain name in the WebLogic domain template.
        :return: the domain name
        """
        return 'base_domain'

    def get_default_security_realm_name(self):
        """
        Get the default name of the security realm
        :return: the default security realm name
        """
        return 'myrealm'

    def is_version_in_12c(self):
        """
        Is the weblogic version a 12c version?
        :return: True if the version is 12c
        """
        return self.is_weblogic_version_or_above('12.1.2')

    # This method should be deleted once all of the old code is converted to the new model.
    def get_wlst_exception_content(self, message):
        """
        Return a formatted message for the specific weblogic version exception message
        """
        if self.is_weblogic_version_or_above('12.1.2'):
            result = message
        else:
            result = JException(message)

        return result

    #
    # TODO(rpatrick) - missing logic for custom-installed 10.3.x and 12.1.1 WL_HOME locations.
    #
    def get_weblogic_home(self, oracle_home):
        """
        Return the weblogic home path, which is synonymous to the WL_HOME environment variable, for the
        running version of wlst.
        :param oracle_home: for the current wlst (is there a way to get oracle home from wlst?)
        :return: weblogic home path for the wlst version and oracle home
        """
        wl_home = None
        if oracle_home is not None:
            if self.is_weblogic_version_or_above('12.1.2'):
                wl_home = oracle_home + '/wlserver'
            elif self.is_weblogic_version_or_above('12.1.1'):
                wl_home = oracle_home + '/wlserver_12.1'
            else:
                wl_home = oracle_home + '/wlserver_10.3'

            # if the path is not a valid directory, try to infer it from the pattern
            if os.path.isdir(oracle_home) and not os.path.isdir(wl_home):
                dirs = [f for f in os.listdir(oracle_home) if re.match(r'wlserver.*', f)]
                if len(dirs) > 0:
                    wl_home = oracle_home + '/' + dirs[0]
                else:
                    wl_home = None

        return wl_home

    def is_weblogic_version_or_above(self, str_version, use_actual_version=False):
        """
        Is the provided version number equal to or greater than the version encapsualted by this version instance
        :param str_version: the string representation of the version to be compared
        :param use_actual_version: compare using all of the (period separated) places in the version string. If
                False (default), use version places up to the number represented by STANDARD_VERSION_NUMBER_PLACES
        :return: True if the provided version is equal or greater than the version represented by this helper instance
        """
        if use_actual_version:
            wl_version = self.wl_version_actual
        else:
            wl_version = self.wl_version
        result = string_utils.is_weblogic_version_or_above(wl_version, str_version)

        return result

    def get_bean_info_for_interface(self, interface_name):
        """
        Returns the MBean information for the specified MBean interface.
        :param interface_name: the class name of the interface to be checked
        :return: the bean info access object for the specified interface
        """
        bean_access = ManagementServiceClient.getBeanInfoAccess()
        return bean_access.getBeanInfoForInterface(interface_name, False, '9.0.0.0')

    def get_next_higher_order_version_number(self, version_number):
        """
        Get the next higher order version number.  For example, passing in '12.2.1.2' will return '12.2.1'.
        :param version_number: the original version number
        :return: the version number with the last digit removed, or none if there are no more digits to remove
        """
        periods = version_number.count('.')
        result = None
        if periods > 0:
            rsplit = string_utils.rsplit(version_number, '.', 1)
            if len(rsplit) > 0:
                result = rsplit[0]
        return result

    def encrypt(self, plain_text, domain_directory):
        """
        Encrypt the text using the domain's encryption service.
        :param plain_text: the text to encrypt
        :param domain_directory: the domain home directory
        :return: the encrypted text
        :raises: EncryptionException: if an error occurs getting the WebLogic encryption services
        """
        result = None
        if plain_text is not None and len(plain_text) > 0:
            encryption_service = self.__get_encryption_service(domain_directory)
            result = encryption_service.encrypt(plain_text)
        return result

    def decrypt(self, cipher_text, domain_directory):
        """
        Decrypt the cipher text using the domain's encryption service.
        :param cipher_text: the text to decrypt
        :param domain_directory: the domain home directory
        :return: the plain text
        :raises: EncryptionException: if an error occurs getting the WebLogic encryption services
        """
        result = None
        if cipher_text is not None and len(cipher_text) > 0:
            encryption_service = self.__get_encryption_service(domain_directory)
            result = encryption_service.decrypt(cipher_text)
        return result

    def __get_encryption_service(self, domain_home):
        """
        Get the encryption service for the specified domain.
        :param domain_home: the domain home directory
        :return: the encryption service
        :raises: EncryptionException: if an error occurs getting the WebLogic encryption services
        """
        _method_name = '__get_encryption_service'

        system_ini = SerializedSystemIni.getEncryptionService(domain_home)
        if system_ini is None:
            ex = exception_helper.create_encryption_exception('WLSDPLY-01840')
            self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

        encryption_service = ClearOrEncryptedService(system_ini)
        if encryption_service is None:
            ex = exception_helper.create_encryption_exception('WLSDPLY-01841')
            self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex
        return encryption_service
