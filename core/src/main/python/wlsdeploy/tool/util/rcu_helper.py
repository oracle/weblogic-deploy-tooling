"""
Copyright (c) 2017, 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import exceptions
import os
import re
import sys

from java.io import File
from java.lang import Class as JClass
from java.lang import Exception as JException
from java.lang import IllegalArgumentException
from java.lang import System
from java.sql import DriverManager
from java.util import Properties
from oracle.weblogic.deploy.create import CreateDomainLifecycleHookScriptRunner
from oracle.weblogic.deploy.create import RCURunner
from oracle.weblogic.deploy.create.RCURunner import COMPONENT_INFO_LOCATION_SWITCH
from oracle.weblogic.deploy.create.RCURunner import DB2_DB_TYPE
from oracle.weblogic.deploy.create.RCURunner import EBR_DB_TYPE
from oracle.weblogic.deploy.create.RCURunner import EDITION_SWITCH
from oracle.weblogic.deploy.create.RCURunner import MYSQL_DB_TYPE
from oracle.weblogic.deploy.create.RCURunner import ORACLE_DB_TYPE
from oracle.weblogic.deploy.create.RCURunner import SQLSERVER_DB_TYPE
from oracle.weblogic.deploy.create.RCURunner import STORAGE_LOCATION_SWITCH
from oracle.weblogic.deploy.create.RCURunner import TABLESPACE_SWITCH
from oracle.weblogic.deploy.create.RCURunner import TEMP_TABLESPACE_SWITCH
from oracle.weblogic.deploy.create.RCURunner import UNICODE_SUPPORT
from oracle.weblogic.deploy.create.RCURunner import VARIABLES_SWITCH
from oracle.weblogic.deploy.util import FileUtils
from oracle.weblogic.deploy.util import WLSDeployArchive

from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import DRIVER_NAME
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_KEYSTOREPWD_PROPERTY
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_KEYSTORETYPE_PROPERTY
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_KEYSTORE_PROPERTY
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_NET_FAN_ENABLED
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_NET_SERVER_DN_MATCH_PROPERTY
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_NET_SSL_VERSION
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_NET_SSL_VERSION_VALUE
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_NET_TNS_ADMIN
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_PROPERTY_VALUE
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_PROPERTY_VALUE_ENCRYPTED
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_PROPERTY_SYS_PROP_VALUE
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_TRUSTSTOREPWD_PROPERTY
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_TRUSTSTORETYPE_PROPERTY
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_TRUSTSTORE_PROPERTY
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_USER_PROPERTY
from wlsdeploy.aliases.model_constants import JDBC_DRIVER_PARAMS
from wlsdeploy.aliases.model_constants import JDBC_DRIVER_PARAMS_PROPERTIES
from wlsdeploy.aliases.model_constants import JDBC_RESOURCE
from wlsdeploy.aliases.model_constants import JDBC_SYSTEM_RESOURCE
from wlsdeploy.aliases.model_constants import PASSWORD_ENCRYPTED
from wlsdeploy.aliases.model_constants import RCU_COMP_INFO
from wlsdeploy.aliases.model_constants import RCU_STG_INFO
from wlsdeploy.aliases.model_constants import RESOURCES
from wlsdeploy.aliases.model_constants import URL
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception import exception_helper
from wlsdeploy.exception.exception_types import ExceptionType
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.logging.platform_logger import get_logged_value
from wlsdeploy.tool.create import rcudbinfo_helper
from wlsdeploy.tool.create.domain_typedef import POST_CREATE_RCU_SCHEMAS_LIFECYCLE_HOOK
from wlsdeploy.tool.create.jps_config_helper import JpsConfigHelper
from wlsdeploy.tool.create.tnsnames_helper import TnsNamesHelper
from wlsdeploy.tool.deploy import deployer_utils
from wlsdeploy.tool.deploy.datasource_deployer import DatasourceDeployer
from wlsdeploy.tool.util.wlst_helper import WlstHelper
from wlsdeploy.util import dictionary_utils
from wlsdeploy.util import string_utils
from wlsdeploy.util import unicode_helper as str_helper
from wlsdeploy.util.model_context import ModelContext

POST_CREATE_RCU_SCHEMA_LOG_BASENAME = 'postCreateRcuSchemasScript'


class RCUHelper(object):
    """
    Provides methods for configuring and running RCU
    """
    __program_name = 'createDomain'
    __class_name = 'RcuHelper'
    __logger = PlatformLogger('wlsdeploy.create')

    def __init__(self, model_object, archive_helper, model_context, aliases, exception_type=ExceptionType.CREATE):
        _method_name = '__init__'

        self._model_object = model_object
        self._archive_helper = archive_helper
        self._model_context = model_context  # type: ModelContext
        self._aliases = aliases

        self._wls_helper = model_context.get_weblogic_helper()
        self._domain_typedef = self._model_context.get_domain_typedef()
        self._wlst_helper = WlstHelper(exception_type)

        model_dictionary = model_object.get_model()
        self._rcu_db_info = rcudbinfo_helper.create(model_dictionary, model_context, aliases)

    ####################
    # PUBLIC METHODS
    ####################

    def check_or_run_rcu(self):
        # This squelches the following error during JRF domain creation with an ATP database.
        #
        # ####<Mar 29, 2024 3:19:53 PM> <SEVERE> <FanManager> <configure> <> <attempt to configure
        # ONS in FanManager failed with oracle.ons.NoServersAvailable: Subscription time out>
        #
        if self._rcu_db_info.is_use_atp():
            System.setProperty('oracle.jdbc.fanEnabled', 'false')

        if self._model_context.get_domain_typedef().requires_rcu():
            if self._model_context.is_run_rcu():
                self.__run_rcu()
            else:
                self.__precheck_rcu_connectivity()

    def configure_fmw_infra_database(self):
        """
        Configure the FMW Infrastructure DataSources.
        :return: a list of FMW template default data source names
        :raises: CreateException: if an error occurs
        """
        _method_name = 'configure_fmw_infra_database'
        self.__logger.entering(class_name=self.__class_name, method_name=_method_name)

        # only continue with RCU configuration for domain type that requires RCU.
        if not self._domain_typedef.requires_rcu():
            self.__logger.finer('WLSDPLY-12249', class_name=self.__class_name, method_name=_method_name)
            return

        ds_names = self.__set_rcu_datasource_parameters_without_shadow_table()

        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=ds_names)
        return ds_names

    def reset_fmw_template_data_source_defaults_from_model(self, fmw_data_source_names):
        """
        Configure data sources from the original FMW template
        :param fmw_data_source_names: a list of FMW template default data source names
        """
        if not fmw_data_source_names:
            return

        # Go through the model to find any FMW data sources to override the defaults
        # from user's model before the first writeDomain.
        resources_dict = self._model_object.get_model_resources()
        if JDBC_SYSTEM_RESOURCE in resources_dict:
            fmw_resources = {RESOURCES: {JDBC_SYSTEM_RESOURCE: {}}}
            fmw_jdbc_resources = fmw_resources[RESOURCES][JDBC_SYSTEM_RESOURCE]
            ds_dict = resources_dict[JDBC_SYSTEM_RESOURCE]
            for ds_name in ds_dict:
                fmw_ds = ds_dict[ds_name]
                if ds_name in fmw_data_source_names:
                    fmw_jdbc_resources[ds_name] = fmw_ds
            if len(fmw_resources[RESOURCES][JDBC_SYSTEM_RESOURCE]) != 0:
                ds_location = LocationContext()
                data_source_deployer = DatasourceDeployer(self._model_object, self._model_context, self._aliases,
                                                          WlstModes.OFFLINE)
                data_source_deployer.add_data_sources(fmw_resources[RESOURCES], ds_location)

    def update_rcu_password(self, modify_bootstrap_credential=True):
        """
        Update the password of each rcu schema and then update the bootstrap password
        """
        _method_name = 'update_rcu_password'

        rcu_schema_pass = self._rcu_db_info.get_rcu_schema_password()
        # upper case the prefix, the user may specify prefix as lower case
        # but the prefix will always be upper case in the db.
        rcu_prefix = self._rcu_db_info.get_rcu_prefix().upper()

        location = LocationContext()
        location.append_location(JDBC_SYSTEM_RESOURCE)

        folder_path = self._aliases.get_wlst_list_path(location)
        self._wlst_helper.cd(folder_path)
        ds_names = self._wlst_helper.lsc()
        domain_typedef = self._model_context.get_domain_typedef()
        rcu_schemas = domain_typedef.get_rcu_schemas()
        if len(rcu_schemas) == 0:
            return
        schemas_len = len(rcu_schemas)

        for i in range(0,schemas_len):
            rcu_schemas[i] = rcu_prefix + '_' + rcu_schemas[i]

        for ds_name in ds_names:
            location = deployer_utils.get_jdbc_driver_params_location(ds_name, self._aliases)
            password_location = LocationContext(location)
            list_path = self._aliases.get_wlst_list_path(location)
            if not self._wlst_helper.path_exists(list_path):
                # For update case when a new custom data source has not been persisted,
                # the driver params location is just a placeholder and will result in error
                # if we try to get the attribute list from the location.
                # Since we only care about rcu stock data sources from the template for changing
                # rcu schema password; we can skip for any new custom data source.
                continue

            wlst_path = self._aliases.get_wlst_attributes_path(location)
            self._wlst_helper.cd(wlst_path)

            location.append_location(JDBC_DRIVER_PARAMS_PROPERTIES)
            deployer_utils.set_flattened_folder_token(location, self._aliases)
            token_name = self._aliases.get_name_token(location)
            if token_name is not None:
                location.add_name_token(token_name, DRIVER_PARAMS_USER_PROPERTY)
            wlst_path = self._aliases.get_wlst_attributes_path(location)
            self._wlst_helper.cd(wlst_path)
            ds_user = self._wlst_helper.get('Value')

            if ds_user in rcu_schemas:
                wlst_path = self._aliases.get_wlst_attributes_path(password_location)
                self._wlst_helper.cd(wlst_path)
                wlst_name, wlst_value = \
                    self._aliases.get_wlst_attribute_name_and_value(password_location, PASSWORD_ENCRYPTED,
                                                                   rcu_schema_pass, masked=True)
                self._wlst_helper.set(wlst_name, wlst_value, masked=True)

            domain_home = self._model_context.get_domain_home()
            config_file = domain_home + '/config/fmwconfig/jps-config-jse.xml'
            opss_user = rcu_prefix + '_OPSS'
            if modify_bootstrap_credential:
                self._wlst_helper.modify_bootstrap_credentials(
                    jps_configfile=config_file, username=opss_user, password=rcu_schema_pass)

    def fix_jps_config(self):
        if self._model_context.get_domain_typedef().requires_rcu():
            jps_config_helper = JpsConfigHelper(self._model_object, self._model_context, self._rcu_db_info)
            jps_config_helper.fix_jps_config()

    ####################
    # PRIVATE METHODS
    ####################

    def __precheck_rcu_connectivity(self):
        _method_name = 'precheck_rcu_connectivity'
        self.__logger.entering(class_name=self.__class_name, method_name=_method_name)

        domain_typename = self._model_context.get_domain_typedef().get_domain_type()

        rcu_prefix = self._rcu_db_info.get_rcu_prefix()
        schema_name = None
        user_name = None
        if not string_utils.is_empty(rcu_prefix):
            user_name = self._model_context.get_weblogic_helper().get_stb_user_name(rcu_prefix)
            schema_name = user_name[len(rcu_prefix) + 1:]

        if schema_name is None or schema_name not in self._model_context.get_domain_typedef().get_rcu_schemas():
            self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)
            return

        db_conn_props = None

        rcu_database_type = self._rcu_db_info.get_rcu_database_type()
        tns_admin, rcu_prefix, jdbc_conn_string, rcu_schema_pwd = \
            self.__get_rcu_datasource_basic_connection_info()

        if self._rcu_db_info.is_use_atp() or self._rcu_db_info.is_use_ssl():
            db_conn_props = self.__get_jdbc_ssl_connection_properties(tns_admin, self._rcu_db_info.is_use_atp())

        jdbc_driver_name = self.__get_jdbc_driver_class_name(rcu_database_type)

        try:
            props = Properties()
            if db_conn_props is not None:
                for item in db_conn_props:
                    for key in item.keys():
                        props.put(key, item[key])

            self.__logger.info('WLSDPLY_12275', 'test datasource', jdbc_conn_string, schema_name, props,
                               class_name=self.__class_name, method_name=_method_name)

            props.put('user', user_name)
            props.put('password', rcu_schema_pwd)

            # Pick up any values overridden by any model resources section overrides for the STB datasource.
            jdbc_driver_name, jdbc_conn_string = \
                self.__update_precheck_from_model_data_source(jdbc_driver_name, jdbc_conn_string, props)

            # Force the driver to be loaded and registered...
            JClass.forName(jdbc_driver_name)
            DriverManager.getConnection(jdbc_conn_string, props)

        except exceptions.Exception, e:
            exc_type, exc_obj, _exc_tb = sys.exc_info()
            ex = exception_helper.create_create_exception('WLSDPLY-12281', domain_typename,
                                                          str_helper.to_string(exc_type),
                                                          str_helper.to_string(exc_obj), error=e)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        except JException, e:
            ex = exception_helper.create_create_exception('WLSDPLY-12281', domain_typename,
                                                          e.getClass().getName(), e.getLocalizedMessage(), error=e)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        except ee:
            ex = exception_helper.create_create_exception('WLSDPLY-12282', domain_typename, error=ee)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex

        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def __run_rcu(self):
        """
        The method that runs RCU to drop and then create the schemas.
        :raises CreateException: if running rcu fails
        """
        _method_name = 'run_rcu'
        self.__logger.entering(class_name=self.__class_name, method_name=_method_name)

        if not self._wls_helper.is_weblogic_version_or_above('12.1.2'):
            ex = exception_helper.create_create_exception('WLSDPLY-12201', self.__program_name,
                                                          self._model_context.get_local_wls_version())
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex

        rcu_schemas = self._domain_typedef.get_rcu_schemas()
        if len(rcu_schemas) == 0:
            self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)
            return

        rcu_db_info = self._rcu_db_info
        oracle_home = self._model_context.get_oracle_home()
        java_home = self._model_context.get_java_home()
        rcu_database_type = rcu_db_info.get_rcu_database_type()
        oracle_database_connection_type = rcu_db_info.get_oracle_database_connection_type()
        rcu_db_conn_string = rcu_db_info.get_rcu_db_conn_string()
        rcu_prefix = rcu_db_info.get_rcu_prefix()
        rcu_admin_user = rcu_db_info.get_rcu_admin_user()
        rcu_admin_pass = rcu_db_info.get_rcu_admin_password()
        rcu_schema_pass = rcu_db_info.get_rcu_schema_password()
        extra_rcu_args_map = self.__get_extra_rcu_args_map()

        ssl_conn_properties = None
        if rcu_db_info.is_oracle_database_type():
            tns_admin, rcu_db_conn_string = self.__get_rcu_db_connect_string()
            if rcu_db_info.is_use_atp() or rcu_db_info.is_use_ssl():
                ssl_conn_properties = self.__get_rcu_ssl_args_properties(tns_admin)

                if rcu_db_info.is_use_atp():
                    # hard coding for now, may need to expose it if ATP access changed later
                    ssl_conn_properties[DRIVER_PARAMS_NET_FAN_ENABLED] = 'false'
                    ssl_conn_properties[DRIVER_PARAMS_NET_SSL_VERSION] = DRIVER_PARAMS_NET_SSL_VERSION_VALUE

                ssl_conn_properties[DRIVER_PARAMS_NET_SERVER_DN_MATCH_PROPERTY] = 'false'

        rcu_db_conn_string = self._wls_helper.get_jdbc_url_from_rcu_connect_string(
            rcu_db_conn_string, rcu_database_type)

        if rcu_db_conn_string is None:
            ex = exception_helper.create_create_exception('WLSDPLY-12272')
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex

        disable_rcu_drop_schema = self._model_context.get_model_config().get_disable_rcu_drop_schema() == 'true'
        rcu_runner = RCURunner(oracle_home, java_home, rcu_database_type, oracle_database_connection_type,
                               rcu_db_conn_string, rcu_prefix, rcu_admin_user, rcu_schemas, extra_rcu_args_map,
                               ssl_conn_properties)
        rcu_runner.runRcu(rcu_admin_pass, rcu_schema_pass, disable_rcu_drop_schema)

        self.__run_post_create_rcu_schemas_script()
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def __extract_rcu_xml_file(self, xml_type, path):
        _method_name = '__extract_rcu_xml_files'
        self.__logger.entering(xml_type, path, class_name=self.__class_name, method_name=_method_name)

        result = None
        if path is not None:
            resolved_path = self._model_context.replace_token_string(path)
            if self._archive_helper is not None and self._archive_helper.contains_file(resolved_path):
                domain_home = self._model_context.get_domain_home()
                directory = File(domain_home)
                if (not directory.isDirectory()) and (not directory.mkdirs()):
                    ex = exception_helper.create_create_exception(
                        'WLSDPLY-12259', domain_home, xml_type, path)
                    self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                    raise ex
                resolved_path = self._archive_helper.extract_file(resolved_path)
            try:
                resolved_file = FileUtils.validateFileName(resolved_path)
                result = resolved_file.getPath()
            except IllegalArgumentException, iae:
                ex = exception_helper.create_create_exception('WLSDPLY-12258', xml_type, path,
                                                              iae.getLocalizedMessage(), error=iae)
                self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                raise ex

        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result

    def __get_rcu_db_connect_string(self):
        _method_name = '__get_rcu_db_connect_string'
        self.__logger.entering(class_name=self.__class_name, method_name=_method_name)

        rcu_db_conn_string = self._rcu_db_info.get_rcu_db_conn_string()
        tns_admin = self.__get_tns_admin_path(self._rcu_db_info.get_tns_admin())
        # If user specify connect string, no need to fetch from tnsnames.ora
        if string_utils.is_empty(rcu_db_conn_string):
            if string_utils.is_empty(tns_admin) and self._archive_helper is not None:
                if self._archive_helper.has_rcu_wallet_path():
                    # Extracting the RCU wallet from the archive always puts it into the new location.
                    archive_elements = WLSDeployArchive.DEFAULT_RCU_WALLET_PATH.split('/')
                    tns_admin = \
                        os.path.join(self._model_context.get_domain_home(), *archive_elements)

            if string_utils.is_empty(tns_admin) or not os.path.exists(os.path.join(tns_admin, 'tnsnames.ora')):
                ex = exception_helper.create_create_exception('WLSDPLY-12262')
                self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                raise ex

            if self._rcu_db_info.get_tns_entry() is None:
                ex = exception_helper.create_create_exception('WLSDPLY-12416','tns.alias')
                self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                raise ex

            tnsnames_helper = TnsNamesHelper(self._model_context, os.path.join(tns_admin, 'tnsnames.ora'))
            rcu_db_conn_string = tnsnames_helper.get_connect_string(self._rcu_db_info.get_tns_entry())

        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name,
                              result=[tns_admin, rcu_db_conn_string])
        return tns_admin, rcu_db_conn_string

    def __get_rcu_ssl_args_properties(self, tns_admin):
        _method_name = '__get_rcu_ssl_args_properties'
        self.__logger.entering(tns_admin, class_name=self.__class_name, method_name=_method_name)

        rcu_db_info = self._rcu_db_info
        keystore = rcu_db_info.get_keystore()
        keystore_type = rcu_db_info.get_keystore_type()
        keystore_password = rcu_db_info.get_keystore_password()
        truststore = rcu_db_info.get_truststore()
        truststore_type = rcu_db_info.get_truststore_type()
        truststore_password = rcu_db_info.get_truststore_password()

        ssl_conn_properties = dict()
        if not string_utils.is_empty(tns_admin):
            ssl_conn_properties[DRIVER_PARAMS_NET_TNS_ADMIN] = tns_admin
        if not string_utils.is_empty(keystore):
            ssl_conn_properties[DRIVER_PARAMS_KEYSTORE_PROPERTY] = self.__get_store_path(tns_admin, keystore)
        if not string_utils.is_empty(keystore_type):
            ssl_conn_properties[DRIVER_PARAMS_KEYSTORETYPE_PROPERTY] = keystore_type
        if not string_utils.is_empty(keystore_password):
            ssl_conn_properties[DRIVER_PARAMS_KEYSTOREPWD_PROPERTY] = keystore_password
        if not string_utils.is_empty(truststore):
            ssl_conn_properties[DRIVER_PARAMS_TRUSTSTORE_PROPERTY] = self.__get_store_path(tns_admin, truststore)
        if not string_utils.is_empty(truststore_type):
            ssl_conn_properties[DRIVER_PARAMS_TRUSTSTORETYPE_PROPERTY] = truststore_type
        if not string_utils.is_empty(truststore_password):
            ssl_conn_properties[DRIVER_PARAMS_TRUSTSTOREPWD_PROPERTY] = truststore_password

        if DRIVER_PARAMS_KEYSTORE_PROPERTY in ssl_conn_properties and \
                not os.path.exists(ssl_conn_properties[DRIVER_PARAMS_KEYSTORE_PROPERTY]):
            ex = exception_helper.create_create_exception('WLSDPLY-12274',
                                                          ssl_conn_properties[DRIVER_PARAMS_KEYSTORE_PROPERTY],
                                                          DRIVER_PARAMS_KEYSTORE_PROPERTY)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex

        if DRIVER_PARAMS_TRUSTSTORE_PROPERTY in ssl_conn_properties and \
                not os.path.exists(ssl_conn_properties[DRIVER_PARAMS_TRUSTSTORE_PROPERTY]):
            ex = exception_helper.create_create_exception('WLSDPLY-12274',
                                                          ssl_conn_properties[DRIVER_PARAMS_TRUSTSTORE_PROPERTY],
                                                          DRIVER_PARAMS_TRUSTSTORE_PROPERTY)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex

        if not ssl_conn_properties:
            ssl_conn_properties = None

        # don't log the dictionary being returned since it may contain keystore passwords
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return ssl_conn_properties

    def __get_extra_rcu_args_map(self):
        _method_name = '_get_extra_rcu_args_map'
        self.__logger.entering(class_name=self.__class_name, method_name=_method_name)

        rcu_db_info = self._rcu_db_info
        tablespace = rcu_db_info.get_rcu_default_tablespace()
        temp_tablespace = rcu_db_info.get_rcu_temp_tablespace()
        comp_info_xml_location = self.__extract_rcu_xml_file(RCU_COMP_INFO, rcu_db_info.get_comp_info_location())
        storage_xml_location = self.__extract_rcu_xml_file(RCU_STG_INFO, rcu_db_info.get_storage_location())
        rcu_variables = rcu_db_info.get_rcu_variables()
        rcu_edition = rcu_db_info.get_rcu_edition()
        rcu_unicode_support = rcu_db_info.get_rcu_unicode_support()

        extra_rcu_args = dict()
        if not string_utils.is_empty(tablespace):
            extra_rcu_args[TABLESPACE_SWITCH] = tablespace

        if not string_utils.is_empty(temp_tablespace):
            extra_rcu_args[TEMP_TABLESPACE_SWITCH] = temp_tablespace

        if not string_utils.is_empty(comp_info_xml_location):
            extra_rcu_args[COMPONENT_INFO_LOCATION_SWITCH] = comp_info_xml_location

        if not string_utils.is_empty(storage_xml_location):
            extra_rcu_args[STORAGE_LOCATION_SWITCH] = storage_xml_location

        if not string_utils.is_empty(rcu_variables):
            extra_rcu_args[VARIABLES_SWITCH] = rcu_variables

        if not string_utils.is_empty(rcu_edition):
            extra_rcu_args[EDITION_SWITCH] = rcu_edition

        if not string_utils.is_empty(rcu_unicode_support):
            extra_rcu_args[UNICODE_SUPPORT] = rcu_unicode_support

        if not extra_rcu_args:
            extra_rcu_args = None

        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=extra_rcu_args)
        return extra_rcu_args

    def __run_post_create_rcu_schemas_script(self):
        _method_name = '__run_post_create_rcu_schemas_script'

        self.__logger.entering(self.__class_name, _method_name)
        script = self._domain_typedef.get_post_create_rcu_schemas_script()
        if script is None:
            self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)
            return

        java_home = self._model_context.get_java_home()
        oracle_home = self._model_context.get_oracle_home()
        runner = CreateDomainLifecycleHookScriptRunner(
            POST_CREATE_RCU_SCHEMAS_LIFECYCLE_HOOK, POST_CREATE_RCU_SCHEMA_LOG_BASENAME, script, java_home,
            oracle_home, self._model_context.get_domain_home(), self._model_context.get_domain_name())

        runner.runScript()
        self.__logger.info('WLSDPLY-12277', script, class_name=self.__class_name, method_name=_method_name)
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def __set_connection_property_info(self, root_location, property_name, property_value, info_bucket, encrypted=False):
        p = self.__set_connection_property(root_location, property_name, property_value, encrypted)
        info_bucket.append(p)

    def __set_connection_property(self, root_location, property_name, property_value, encrypted=False):
        create_path = self._aliases.get_wlst_create_path(root_location)

        self._wlst_helper.cd(create_path)

        token_name = self._aliases.get_name_token(root_location)

        if token_name is not None:
            root_location.add_name_token(token_name, property_name)

        mbean_name = self._aliases.get_wlst_mbean_name(root_location)
        mbean_type = self._aliases.get_wlst_mbean_type(root_location)
        existing_properties =  self._wlst_helper.lsc(create_path + '/Property')
        if property_name not in existing_properties:
            self._wlst_helper.create(mbean_name, mbean_type)

        wlst_path = self._aliases.get_wlst_attributes_path(root_location)

        self._wlst_helper.cd(wlst_path)
        if encrypted:
            value_property = DRIVER_PARAMS_PROPERTY_VALUE_ENCRYPTED
        else:
            value_property = DRIVER_PARAMS_PROPERTY_VALUE

        wlst_name, wlst_value = \
            self._aliases.get_wlst_attribute_name_and_value(root_location, value_property,
                                                            property_value)
        self._wlst_helper.set(wlst_name, wlst_value)

        root_location.remove_name_token(property_name)
        if encrypted:
            return {property_name: '******'}
        else:
            return {property_name: property_value}

    def __set_rcu_datasource_parameters_without_shadow_table(self):
        """
        Setting the rcu default datasources connection parameters by looping through the default list of data sources
        from the template instead of using getDatabaseDefaults()
        :return: a list of the updated data sources
        """
        _method_name = '__set_rcu_datasource_parameters_without_shadow_table'
        self.__logger.entering(class_name=self.__class_name, method_name=_method_name)

        tns_admin, rcu_prefix, data_source_conn_string, rcu_schema_pwd = \
            self.__get_rcu_datasource_basic_connection_info()
        keystore, keystore_type, keystore_pwd, truststore, truststore_type, truststore_pwd = \
            self.__get_rcu_datasource_ssl_connection_info()

        location = LocationContext()
        location.append_location(JDBC_SYSTEM_RESOURCE)
        folder_path = self._aliases.get_wlst_list_path(location)
        self._wlst_helper.cd(folder_path)
        ds_names = self._wlst_helper.lsc()

        rcu_database_type = self._rcu_db_info.get_rcu_database_type()
        jdbc_driver_class_name = self.__get_jdbc_driver_class_name(rcu_database_type)

        for ds_name in ds_names:
            # Set the driver params
            actual_url = self.__set_datasource_driver_and_url(ds_name, rcu_database_type,
                                                              jdbc_driver_class_name, data_source_conn_string)
            self.__set_datasource_password(ds_name, rcu_schema_pwd)
            actual_schema = self.__reset_datasource_template_userid(ds_name, rcu_prefix)

            property_set = None
            if self._rcu_db_info.is_use_atp() or self._rcu_db_info.is_use_ssl():
                is_atp = self._rcu_db_info.is_use_atp()
                property_set = self.__set_rcu_datasource_ssl_connection_properties(
                    ds_name, is_atp, tns_admin, truststore, truststore_type, truststore_pwd, keystore,
                    keystore_type, keystore_pwd)

            self.__logger.info('WLSDPLY-12275', ds_name, actual_url, actual_schema, property_set,
                               class_name=self.__class_name, method_name=_method_name)

        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=ds_names)
        return ds_names

    def __set_datasource_password(self, datasource_name, rcu_schema_pwd):
        location = deployer_utils.get_jdbc_driver_params_location(datasource_name, self._aliases)
        wlst_name, wlst_value = \
            self._aliases.get_wlst_attribute_name_and_value(location, PASSWORD_ENCRYPTED,
                                                            rcu_schema_pwd, masked=True)
        self._wlst_helper.set_if_needed(wlst_name, wlst_value, masked=True)

    def __set_datasource_driver_and_url(self, datasource_name, database_type, driver_class_name, url):
        location = deployer_utils.get_jdbc_driver_params_location(datasource_name, self._aliases)

        wlst_path = self._aliases.get_wlst_attributes_path(location)
        self._wlst_helper.cd(wlst_path)
        self.__set_datasource_driver(datasource_name, database_type, location)

        wlst_name, wlst_value = \
            self._aliases.get_wlst_attribute_name_and_value(location, URL, url)
        self._wlst_helper.set_if_needed(wlst_name, wlst_value)

        return wlst_value

    def __set_datasource_driver(self, datasource_name, database_type, location):
        _method_name = '__set_datasource_driver'
        if database_type != ORACLE_DB_TYPE and database_type != EBR_DB_TYPE:
            wlst_driver_name, __ = self._aliases.get_wlst_attribute_name_and_value(location, DRIVER_NAME, 'dummy')
            driver_params = self._wlst_helper.lsa()

            current_driver_name = dictionary_utils.get_element(driver_params, wlst_driver_name)
            if current_driver_name == 'oracle.jdbc.xa.client.OracleXADataSource':
                new_driver_name = self.__get_jdbc_driver_class_name(database_type, is_xa=True)
            else:
                new_driver_name = self.__get_jdbc_driver_class_name(database_type, is_xa=False)

            self.__logger.fine('WLSDPLY-12278', datasource_name, database_type, new_driver_name,
                               class_name=self.__class_name, method_name=_method_name)

            wlst_name, wlst_value = \
                self._aliases.get_wlst_attribute_name_and_value(location, DRIVER_NAME, new_driver_name)
            self._wlst_helper.set_if_needed(wlst_name, wlst_value)

    def __get_tns_admin_path(self, tns_admin):
        _method_name = '__get_tns_admin_path'
        self.__logger.entering(tns_admin, class_name=self.__class_name, method_name=_method_name)

        result = tns_admin
        if deployer_utils.is_path_into_archive(tns_admin) or \
                (not string_utils.is_empty(tns_admin) and not os.path.isabs(tns_admin)):
            result = os.path.join(self._model_context.get_domain_home(), tns_admin)

        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result

    def __get_store_path(self, tns_admin, store):
        _method_name = '__get_store_path'
        self.__logger.entering(tns_admin, store, class_name=self.__class_name, method_name=_method_name)

        result = store
        if not string_utils.is_empty(store):
            if deployer_utils.is_path_into_archive(store):
                result = os.path.join(self._model_context.get_domain_home(), store)
            elif not string_utils.is_empty(tns_admin) and not os.path.isabs(store) and not store.startswith(tns_admin):
                result = os.path.join(tns_admin, store)

        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result

    def __reset_datasource_template_userid(self, datasource_name, rcu_prefix):
        location = deployer_utils.get_jdbc_driver_params_location(datasource_name, self._aliases)
        location.append_location(JDBC_DRIVER_PARAMS_PROPERTIES)
        deployer_utils.set_flattened_folder_token(location, self._aliases)
        token_name = self._aliases.get_name_token(location)
        if token_name is not None:
            location.add_name_token(token_name, DRIVER_PARAMS_USER_PROPERTY)
        wlst_path = self._aliases.get_wlst_attributes_path(location)
        self._wlst_helper.cd(wlst_path)
        # Change the schema from the template and just change the prefix
        template_schema_user = self._wlst_helper.get('Value')
        schema_user = re.sub('^DEV_', rcu_prefix + '_', template_schema_user)
        wlst_name, wlst_value = \
            self._aliases.get_wlst_attribute_name_and_value(location, DRIVER_PARAMS_PROPERTY_VALUE,
                                                            schema_user)
        self._wlst_helper.set_if_needed(wlst_name, wlst_value)
        return wlst_value

    def __set_rcu_datasource_ssl_connection_properties(self, ds_name, is_atp_db, tns_admin, truststore, truststore_type,
                                                       truststore_pwd, keystore, keystore_type, keystore_pwd):
        _method_name = '__set_rcu_datasource_ssl_connection_properties'
        self.__logger.entering(ds_name, is_atp_db, tns_admin, truststore, truststore_type,
                               get_logged_value(truststore_pwd), keystore, keystore_type, get_logged_value(keystore_pwd),
                               class_name=self.__class_name, method_name=_method_name)

        location = deployer_utils.get_jdbc_driver_params_properties_location(ds_name, self._aliases)
        properties_set = []

        # Should always have trust store
        self.__set_connection_property_info(location, DRIVER_PARAMS_TRUSTSTORE_PROPERTY,
                                            self.__get_store_path(tns_admin, truststore), properties_set)

        self.__set_connection_property_info(location, DRIVER_PARAMS_TRUSTSTORETYPE_PROPERTY,
                                            truststore_type, properties_set)

        if not string_utils.is_empty(truststore_pwd):
            self.__set_connection_property_info(location, DRIVER_PARAMS_TRUSTSTOREPWD_PROPERTY, truststore_pwd,
                                                properties_set, encrypted=True)

        # if it is 2 way SSL
        if not string_utils.is_empty(keystore):
            self.__set_connection_property_info(location, DRIVER_PARAMS_KEYSTORE_PROPERTY,
                                                self.__get_store_path(tns_admin, keystore), properties_set)

        if not string_utils.is_empty(keystore_type):
            self.__set_connection_property_info(location, DRIVER_PARAMS_KEYSTORETYPE_PROPERTY, keystore_type,
                                                properties_set)

        if not string_utils.is_empty(keystore_pwd):
            self.__set_connection_property_info(location, DRIVER_PARAMS_KEYSTOREPWD_PROPERTY, keystore_pwd,
                                                properties_set, encrypted=True)

        if not string_utils.is_empty(tns_admin):
            self.__set_connection_property_info(location, DRIVER_PARAMS_NET_TNS_ADMIN, tns_admin, properties_set)

        if is_atp_db:
            self.__set_connection_property_info(location, DRIVER_PARAMS_NET_SSL_VERSION,
                                                DRIVER_PARAMS_NET_SSL_VERSION_VALUE, properties_set)
            self.__set_connection_property_info(location, DRIVER_PARAMS_NET_SERVER_DN_MATCH_PROPERTY,
                                                'true', properties_set)
            self.__set_connection_property_info(location, DRIVER_PARAMS_NET_FAN_ENABLED, 'false', properties_set)

        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=properties_set)
        return properties_set

    def __get_rcu_datasource_basic_connection_info(self):
        _method_name = '__get_rcu_datasource_basic_connection_info'
        self.__logger.entering(class_name=self.__class_name, method_name=_method_name)

        rcu_prefix = self._rcu_db_info.get_rcu_prefix()
        rcu_schema_pwd = self._rcu_db_info.get_rcu_schema_password()

        # For ATP databases :  we need to set all the property for each datasource
        # load atp connection properties from properties file
        # HANDLE ATP case

        tns_admin, rcu_db_conn_string = self.__get_rcu_db_connect_string()
        if rcu_db_conn_string is None:
            ex = exception_helper.create_create_exception('WLSDPLY-12264')
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex

        # Need to set for the connection property for each datasource
        rcu_database_type = self._rcu_db_info.get_rcu_database_type()
        data_source_conn_string = \
            self._wls_helper.get_jdbc_url_from_rcu_connect_string(rcu_db_conn_string, rcu_database_type)
        self.__logger.fine('WLSDPLY-12221', data_source_conn_string,
                           class_name=self.__class_name, method_name=_method_name)

        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name,
                              result=[tns_admin, rcu_prefix, data_source_conn_string, rcu_schema_pwd])
        return tns_admin, rcu_prefix, data_source_conn_string, rcu_schema_pwd

    def __get_rcu_datasource_ssl_connection_info(self):
        _method_name = '__get_rcu_datasource_ssl_connection_info'
        self.__logger.entering(class_name=self.__class_name, method_name=_method_name)

        keystore = None
        keystore_type = None
        keystore_pwd = None
        truststore = None
        truststore_type = None
        truststore_pwd = None

        rcu_db_info = self._rcu_db_info
        if rcu_db_info.is_use_atp() or rcu_db_info.is_use_ssl():
            keystore = rcu_db_info.get_keystore()
            keystore_type = rcu_db_info.get_keystore_type()
            keystore_pwd = rcu_db_info.get_keystore_password()
            truststore = rcu_db_info.get_truststore()
            truststore_type = rcu_db_info.get_truststore_type()
            truststore_pwd = rcu_db_info.get_truststore_password()

        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name,
                              result=[keystore, keystore_type, get_logged_value(keystore_pwd),
                                      truststore, truststore_type, get_logged_value(truststore_pwd)])
        return keystore, keystore_type, keystore_pwd, truststore, truststore_type, truststore_pwd

    def __get_jdbc_ssl_connection_properties(self, tns_admin, is_atp):
        _method_name = '__get_jdbc_ssl_connection_properties'
        self.__logger.entering(tns_admin, is_atp, class_name=self.__class_name, method_name=_method_name)

        keystore, keystore_type, keystore_pwd, truststore, truststore_type, truststore_pwd = \
            self.__get_rcu_datasource_ssl_connection_info()

        properties_set = []
        if not string_utils.is_empty(keystore):
            properties_set.append({DRIVER_PARAMS_KEYSTORE_PROPERTY: keystore})
        if not string_utils.is_empty(keystore_type):
            properties_set.append({DRIVER_PARAMS_KEYSTORETYPE_PROPERTY: keystore_type})
        if not string_utils.is_empty(keystore_pwd):
            properties_set.append({DRIVER_PARAMS_KEYSTOREPWD_PROPERTY: keystore_pwd})
        if not string_utils.is_empty(truststore):
            properties_set.append({DRIVER_PARAMS_TRUSTSTORE_PROPERTY: truststore})
        if not string_utils.is_empty(truststore_type):
            properties_set.append({DRIVER_PARAMS_TRUSTSTORETYPE_PROPERTY: truststore_type})
        if not string_utils.is_empty(truststore_pwd):
            properties_set.append({DRIVER_PARAMS_TRUSTSTOREPWD_PROPERTY: truststore_pwd})
        if not string_utils.is_empty(tns_admin):
            properties_set.append({DRIVER_PARAMS_NET_TNS_ADMIN: tns_admin})

        if is_atp:
            properties_set.append({DRIVER_PARAMS_NET_SSL_VERSION: DRIVER_PARAMS_NET_SSL_VERSION_VALUE})
            properties_set.append({DRIVER_PARAMS_NET_SERVER_DN_MATCH_PROPERTY: 'true'})
            properties_set.append({DRIVER_PARAMS_NET_FAN_ENABLED: 'false'})

        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return properties_set

    def __get_jdbc_driver_class_name(self, rcu_database_type, is_xa=False):
        _method_name = '__get_jdbc_driver_class_name'
        self.__logger.entering(rcu_database_type, is_xa, class_name=self.__class_name, method_name=_method_name)

        if rcu_database_type == ORACLE_DB_TYPE or rcu_database_type == EBR_DB_TYPE:
            if is_xa:
                driver_name = 'oracle.jdbc.xa.client.OracleXADataSource'
            else:
                driver_name = 'oracle.jdbc.OracleDriver'
        elif rcu_database_type == SQLSERVER_DB_TYPE:
            if is_xa:
                driver_name = 'weblogic.jdbcx.sqlserver.SQLServerDataSource'
            else:
                driver_name = 'weblogic.jdbc.sqlserver.SQLServerDriver'
        elif rcu_database_type == DB2_DB_TYPE:
            if is_xa:
                driver_name = 'weblogic.jdbcx.db2.DB2DataSource'
            else:
                driver_name = 'weblogic.jdbc.db2.DB2Driver'
        elif rcu_database_type == MYSQL_DB_TYPE:
            if is_xa:
                driver_name = 'com.mysql.cj.jdbc.MysqlXADataSource'
            else:
                driver_name = 'com.mysql.cj.jdbc.Driver'
        else:
            ex = exception_helper.create_create_exception('WLSDPLY-12220', rcu_database_type)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex

        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=driver_name)
        return driver_name

    def __update_precheck_from_model_data_source(self, jdbc_driver_name, jdbc_conn_string, props):
        _method_name = '__update_precheck_from_model_data_source'
        self.__logger.entering(jdbc_driver_name, jdbc_conn_string,
                               class_name=self.__class_name, method_name=_method_name)

        model_resources_dict = self._model_object.get_model_resources()
        data_source_name = self._model_context.get_weblogic_helper().get_jrf_service_table_datasource_name()
        data_sources_dict = dictionary_utils.get_dictionary_element(model_resources_dict, JDBC_SYSTEM_RESOURCE)
        model_data_source_dict = dictionary_utils.get_dictionary_element(data_sources_dict, data_source_name)
        model_jdbc_resource_dict = dictionary_utils.get_dictionary_element(model_data_source_dict, JDBC_RESOURCE)
        model_driver_params_dict = dictionary_utils.get_dictionary_element(model_jdbc_resource_dict, JDBC_DRIVER_PARAMS)
        model_properties_dict = \
            dictionary_utils.get_dictionary_element(model_driver_params_dict, JDBC_DRIVER_PARAMS_PROPERTIES)

        new_jdbc_driver_name = dictionary_utils.get_element(model_driver_params_dict, DRIVER_NAME, jdbc_driver_name)
        new_jdbc_conn_string = dictionary_utils.get_element(model_driver_params_dict, URL, jdbc_conn_string)

        new_password = dictionary_utils.get_element(model_driver_params_dict, PASSWORD_ENCRYPTED)
        if new_password is not None:
            new_password = self._aliases.decrypt_password(new_password)
            props.put('password', new_password)

        for prop_key, prop_value in model_properties_dict.iteritems():
            if isinstance(prop_value, dict):
                if DRIVER_PARAMS_PROPERTY_VALUE in prop_value:
                    props.put(prop_key, prop_value[DRIVER_PARAMS_PROPERTY_VALUE])
                elif DRIVER_PARAMS_PROPERTY_SYS_PROP_VALUE in prop_value:
                    sys_prop_name = prop_value[DRIVER_PARAMS_PROPERTY_SYS_PROP_VALUE]
                    sys_prop_value = None
                    if sys_prop_name is not None:
                        sys_prop_value = System.getProperty(sys_prop_name)

                    if sys_prop_value is not None:
                        props.put(prop_key, sys_prop_value)
                    else:
                        if sys_prop_name is None:
                            self.__logger.warning('WLSDPLY-12271', data_source_name, prop_key,
                                                  DRIVER_PARAMS_PROPERTY_SYS_PROP_VALUE,
                                                  class_name=self.__class_name, method_name=_method_name)
                        else:
                            # The system property specified might be something like "weblogic.Name", which
                            # will be set for the actual DataSource inside the server but typically won't
                            # be set in a WDT createDomain environment so log as info instead of warning
                            # so that createDomain doesn't exit with a non-zero exit code.
                            #
                            self.__logger.info('WLSDPLY-12273', data_source_name, prop_key,
                                               DRIVER_PARAMS_PROPERTY_SYS_PROP_VALUE, sys_prop_name,
                                               class_name=self.__class_name, method_name=_method_name)
                else:
                    unhandled_field_name = None
                    if DRIVER_PARAMS_PROPERTY_VALUE_ENCRYPTED in prop_value:
                        unhandled_field_name = DRIVER_PARAMS_PROPERTY_VALUE_ENCRYPTED

                    if unhandled_field_name is not None:
                        ex = exception_helper.create_create_exception('WLSDPLY-12265', data_source_name,
                                                                      prop_key, DRIVER_PARAMS_PROPERTY_VALUE,
                                                                      unhandled_field_name)
                        self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                        raise ex
                    else:
                        unhandled_field_names = prop_value.keys()
                        if len(unhandled_field_names) > 0:
                            # This should never happen since validation should catch unsupported fields
                            unhandled_field_name = unhandled_field_names.join(',')
                            ex = exception_helper.create_create_exception('WLSDPLY-12266', data_source_name,
                                                                          prop_key, DRIVER_PARAMS_PROPERTY_VALUE,
                                                                          unhandled_field_name)
                        else:
                            ex = exception_helper.create_create_exception('WLSDPLY-12267', data_source_name,
                                                                          prop_key, DRIVER_PARAMS_PROPERTY_VALUE)
                        self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                        raise ex

        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name,
                              result=[new_jdbc_driver_name, new_jdbc_conn_string])
        return new_jdbc_driver_name, new_jdbc_conn_string
