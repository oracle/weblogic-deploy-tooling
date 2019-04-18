"""
Copyright (c) 2017, 2019, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""
import javaos as os
from oracle.weblogic.deploy.create import RCURunner
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import ADMIN_PASSWORD
from wlsdeploy.aliases.model_constants import ADMIN_SERVER_NAME
from wlsdeploy.aliases.model_constants import ADMIN_USERNAME
from wlsdeploy.aliases.model_constants import APP_DIR
from wlsdeploy.aliases.model_constants import ATP_ADMIN_USER
from wlsdeploy.aliases.model_constants import ATP_TNS_ENTRY
from wlsdeploy.aliases.model_constants import ATP_DEFAULT_TABLESPACE
from wlsdeploy.aliases.model_constants import ATP_TEMPORARY_TABLESPACE
from wlsdeploy.aliases.model_constants import CLUSTER
from wlsdeploy.aliases.model_constants import CREATE_ONLY_DOMAIN_ATTRIBUTES
from wlsdeploy.aliases.model_constants import DEFAULT_ADMIN_SERVER_NAME
from wlsdeploy.aliases.model_constants import DEFAULT_WLS_DOMAIN_NAME
from wlsdeploy.aliases.model_constants import DOMAIN_NAME
from wlsdeploy.aliases.model_constants import DRIVER_NAME
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_KEYSTOREPWD_PROPERTY
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_KEYSTORETYPE_PROPERTY
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_NET_FAN_ENABLED
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_NET_SERVER_DN_MATCH_PROPERTY
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_NET_SSL_VERSION
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_NET_TNS_ADMIN
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_PROPERTY_VALUE
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_TRUSTSTOREPWD_PROPERTY
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_TRUSTSTORETYPE_PROPERTY
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_TRUSTSTORE_PROPERTY
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_USER_PROPERTY
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_kEYSTORE_PROPERTY
from wlsdeploy.aliases.model_constants import JDBC_DRIVER_PARAMS
from wlsdeploy.aliases.model_constants import JDBC_DRIVER_PARAMS_PROPERTIES
from wlsdeploy.aliases.model_constants import JDBC_RESOURCE
from wlsdeploy.aliases.model_constants import JDBC_SYSTEM_RESOURCE
from wlsdeploy.aliases.model_constants import LOG_FILTER
from wlsdeploy.aliases.model_constants import MACHINE
from wlsdeploy.aliases.model_constants import MIGRATABLE_TARGET
from wlsdeploy.aliases.model_constants import NAME
from wlsdeploy.aliases.model_constants import PARTITION
from wlsdeploy.aliases.model_constants import PASSWORD
from wlsdeploy.aliases.model_constants import PASSWORD_ENCRYPTED
from wlsdeploy.aliases.model_constants import RCU_DB_CONN
from wlsdeploy.aliases.model_constants import RCU_DB_INFO
from wlsdeploy.aliases.model_constants import RCU_PREFIX
from wlsdeploy.aliases.model_constants import RCU_SCHEMA_PASSWORD
from wlsdeploy.aliases.model_constants import RCU_ADMIN_PASSWORD
from wlsdeploy.aliases.model_constants import RESOURCE_GROUP
from wlsdeploy.aliases.model_constants import RESOURCE_GROUP_TEMPLATE
from wlsdeploy.aliases.model_constants import SECURITY
from wlsdeploy.aliases.model_constants import SECURITY_CONFIGURATION
from wlsdeploy.aliases.model_constants import SERVER
from wlsdeploy.aliases.model_constants import SERVER_START_MODE
from wlsdeploy.aliases.model_constants import SERVER_TEMPLATE
from wlsdeploy.aliases.model_constants import SET_OPTION_APP_DIR
from wlsdeploy.aliases.model_constants import SET_OPTION_DOMAIN_NAME
from wlsdeploy.aliases.model_constants import SET_OPTION_JAVA_HOME
from wlsdeploy.aliases.model_constants import SET_OPTION_SERVER_START_MODE
from wlsdeploy.aliases.model_constants import UNIX_MACHINE
from wlsdeploy.aliases.model_constants import URL
from wlsdeploy.aliases.model_constants import USER
from wlsdeploy.aliases.model_constants import VIRTUAL_TARGET
from wlsdeploy.aliases.model_constants import WS_RELIABLE_DELIVERY_POLICY
from wlsdeploy.aliases.model_constants import XML_ENTITY_CACHE
from wlsdeploy.aliases.model_constants import XML_REGISTRY
from wlsdeploy.exception import exception_helper
from wlsdeploy.exception.expection_types import ExceptionType
from wlsdeploy.tool.create import atp_helper
from wlsdeploy.tool.create.rcudbinfo_helper import RcuDbInfo
from wlsdeploy.tool.create.creator import Creator
from wlsdeploy.tool.create.security_provider_creator import SecurityProviderCreator
from wlsdeploy.tool.deploy import deployer_utils
from wlsdeploy.tool.deploy import model_deployer
from wlsdeploy.tool.util.archive_helper import ArchiveHelper
from wlsdeploy.tool.util.library_helper import LibraryHelper
from wlsdeploy.tool.util.target_helper import TargetHelper
from wlsdeploy.tool.util.topology_helper import TopologyHelper
from wlsdeploy.util import dictionary_utils
from wlsdeploy.util import model as model_helper


class DomainCreator(Creator):
    """
    The class that driver domain creation.
    """
    __program_name = 'createDomain'
    __class_name = 'DomainCreator'

    def __init__(self, model_dictionary, model_context, aliases):
        _method_name = '__init__'
        Creator.__init__(self, model_dictionary, model_context, aliases)

        # domainInfo section is required to get the admin password, everything else
        # is optional and will use the template defaults
        if model_helper.get_model_domain_info_key() not in model_dictionary:
            ex = exception_helper.create_create_exception('WLSDPLY-12200', self.__program_name,
                                                          model_helper.get_model_domain_info_key(),
                                                          self.model_context.get_model_file())
            self.logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex

        self.topology_helper = TopologyHelper(self.aliases, ExceptionType.CREATE, self.logger)
        self.security_provider_creator = SecurityProviderCreator(model_dictionary, model_context, aliases,
                                                                 ExceptionType.CREATE, self.logger)

        self._domain_typedef = self.model_context.get_domain_typedef()
        self._topology = self.model.get_model_topology()
        self._domain_info = self.model.get_model_domain_info()

        if DOMAIN_NAME in self._topology:
            self._domain_name = self._topology[DOMAIN_NAME]
        else:
            self._domain_name = DEFAULT_WLS_DOMAIN_NAME

        # if domain home specified on command line, set it here, otherwise append domain name to domain parent
        model_domain_home = self.model_context.get_domain_home()
        if model_domain_home:
            self._domain_home = model_domain_home
        else:
            self._domain_home = os.path.join(self.model_context.get_domain_parent_dir(), self._domain_name)

        if ADMIN_SERVER_NAME in self._topology:
            self._admin_server_name = self._topology[ADMIN_SERVER_NAME]
        else:
            self._admin_server_name = DEFAULT_ADMIN_SERVER_NAME

        self.__default_domain_name = None
        self.__default_admin_server_name = None
        self.__default_security_realm_name = None

        archive_file_name = self.model_context.get_archive_file_name()
        if archive_file_name is not None:
            self.archive_helper = ArchiveHelper(archive_file_name, self._domain_home, self.logger,
                                                exception_helper.ExceptionType.CREATE)

        self.library_helper = LibraryHelper(self.model, self.model_context, self.aliases, self._domain_home,
                                            ExceptionType.CREATE, self.logger)

        self.target_helper = TargetHelper(self.model, self.model_context, self.aliases, ExceptionType.CREATE,
                                          self.logger)

        #
        # This list gets modified as the domain is being created so do use this list for anything else...
        #
        self.__topology_folder_list = self.alias_helper.get_model_topology_top_level_folder_names()
        return

    def create(self):
        """
        The create() method triggers domain creation.
        :raises CreateException: if domain creation fails
        :raises DeployException: if resource and application deployment fails
        """
        _method_name = 'create'

        self.logger.entering(class_name=self.__class_name, method_name=_method_name)
        self.__run_rcu()
        self.__fail_mt_1221_domain_creation()
        self.__create_domain()
        self.__deploy()
        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return

    # Override
    def _create_named_mbeans(self, type_name, model_nodes, base_location, log_created=False):
        """
        Override default behavior to create placeholders for referenced Coherence clusters.
        :param type_name: the model folder type
        :param model_nodes: the model dictionary of the specified model folder type
        :param base_location: the base location object to use to create the MBeans
        :param log_created: whether or not to log created at INFO level, by default it is logged at the FINE level
        :raises: CreateException: if an error occurs
        """
        self.topology_helper.check_coherence_cluster_references(type_name, model_nodes)
        # continue with regular processing

        Creator._create_named_mbeans(self, type_name, model_nodes, base_location, log_created=log_created)

    # Override
    def _create_mbean(self, type_name, model_nodes, base_location, log_created=False):
        Creator._create_mbean(self, type_name, model_nodes, base_location, log_created)

        # check for file paths that need to be qualified
        self.topology_helper.qualify_nm_properties(type_name, model_nodes, base_location, self.model_context,
                                                   self.attribute_setter)

    def __validate_rcudbinfo_entries(self, rcu_dbinfo_properties, keys):
        _method_name = '_validate_rcudbinfo_entries'
        error = 0
        last_error = None
        for key in keys:
            if key in rcu_dbinfo_properties:
                if rcu_dbinfo_properties[key] is None:
                    error = 1
            else:
                error = 1
            if error:
                last_error = key
                break

        if error:
            ex = exception_helper.create_create_exception('WLSDPLY-12413', last_error, str(keys))
            self.logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex

    def __run_rcu(self):
        """
        The method that runs RCU to drop and then create the schemas.
        :raises CreateException: if running rcu fails
        """
        _method_name = '__run_rcu'

        self.logger.entering(class_name=self.__class_name, method_name=_method_name)
        if not self.model_context.is_run_rcu():
            self.logger.exiting(class_name=self.__class_name, method_name=_method_name)
            return
        elif not self.wls_helper.is_weblogic_version_or_above('12.1.2'):
            ex = exception_helper.create_create_exception('WLSDPLY-12201', self.__program_name,
                                                          self.wls_helper.get_actual_weblogic_version())
            self.logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex

        rcu_schemas = self._domain_typedef.get_rcu_schemas()
        if len(rcu_schemas) == 0:
            self.logger.exiting(class_name=self.__class_name, method_name=_method_name)
            return

        domain_type = self.model_context.get_domain_type()
        oracle_home = self.model_context.get_oracle_home()
        java_home = self.model_context.get_java_home()

        if RCU_DB_INFO in self.model.get_model_domain_info():
            rcu_properties_map = self.model.get_model_domain_info()[RCU_DB_INFO]
            rcu_db_info = RcuDbInfo(self.alias_helper, rcu_properties_map)

            if rcu_db_info.has_atpdbinfo():

                # Need to validate they are non null
                rcu_schema_pass = rcu_db_info.get_rcu_schema_password()
                rcu_sys_pass = rcu_db_info.get_admin_password()

                # make a copy of model's map to pass to RCURunner, since we will modify some values
                rcu_runner_map = dict(rcu_properties_map)

                # update password fields with decrypted passwords
                rcu_runner_map[DRIVER_PARAMS_KEYSTOREPWD_PROPERTY] = rcu_db_info.get_keystore_password()
                rcu_runner_map[DRIVER_PARAMS_TRUSTSTOREPWD_PROPERTY] = rcu_db_info.get_truststore_password()

                # Set it if it needs it
                # The java RCURunner use it to construct the argument
                # If we don't set it to non null then RCURunner will NPE
                rcu_runner_map[ATP_ADMIN_USER] = rcu_db_info.get_atp_admin_user()
                rcu_runner_map[ATP_TEMPORARY_TABLESPACE] = rcu_db_info.get_atp_temporary_tablespace()
                rcu_runner_map[ATP_DEFAULT_TABLESPACE] = rcu_db_info.get_atp_default_tablespace()

                self.__validate_rcudbinfo_entries(rcu_runner_map, [RCU_ADMIN_PASSWORD,
                                                                   RCU_SCHEMA_PASSWORD,
                                                                   ATP_TNS_ENTRY, RCU_PREFIX,
                                                                   DRIVER_PARAMS_TRUSTSTOREPWD_PROPERTY,
                                                                   DRIVER_PARAMS_KEYSTOREPWD_PROPERTY])

                runner = RCURunner(domain_type, oracle_home, java_home, rcu_schemas, rcu_runner_map,
                                   rcu_db_info.get_rcu_variables())
                runner.runRcu(rcu_sys_pass, rcu_schema_pass)
            else:
                rcu_db = rcu_db_info.get_rcu_regular_db_conn()
                rcu_prefix = rcu_db_info.get_rcu_prefix()
                rcu_sys_pass = rcu_db_info.get_admin_password()
                rcu_schema_pass = rcu_db_info.get_rcu_schema_password()
                self.__validate_rcudbinfo_entries(rcu_properties_map, [RCU_PREFIX, RCU_SCHEMA_PASSWORD,
                                                                       RCU_ADMIN_PASSWORD, RCU_DB_CONN])
                runner = RCURunner(domain_type, oracle_home, java_home, rcu_db, rcu_prefix, rcu_schemas,
                                   rcu_db_info.get_rcu_variables())
                runner.runRcu(rcu_sys_pass, rcu_schema_pass)
        else:
            rcu_db = self.model_context.get_rcu_database()
            rcu_prefix = self.model_context.get_rcu_prefix()
            rcu_sys_pass = self.model_context.get_rcu_sys_pass()
            rcu_schema_pass = self.model_context.get_rcu_schema_pass()

            runner = RCURunner(domain_type, oracle_home, java_home, rcu_db, rcu_prefix, rcu_schemas, None)
            runner.runRcu(rcu_sys_pass, rcu_schema_pass)

        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return

    def __fail_mt_1221_domain_creation(self):
        """
        Abort create if domain contains MT artifacts that cannot be created in the version of WLST offline being used.
        :raises: CreateException: if the MT domain cannot be provision on the specified version of WLST offline
        """
        _method_name = '__fail_mt_1221_domain_creation'

        if self.wls_helper.is_mt_offline_provisioning_supported():
            return

        resources_dict = self.model.get_model_resources()
        if (not dictionary_utils.is_empty_dictionary_element(self._topology, VIRTUAL_TARGET)) or \
                (not dictionary_utils.is_empty_dictionary_element(resources_dict, RESOURCE_GROUP_TEMPLATE)) or \
                (not dictionary_utils.is_empty_dictionary_element(resources_dict, RESOURCE_GROUP)) or \
                (not dictionary_utils.is_empty_dictionary_element(resources_dict, PARTITION)):

            ex = exception_helper.create_create_exception('WLSDPLY-12202', self.wls_helper.wl_version)
            self.logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return

    def __create_domain(self):
        """
        Create the domain.
        :raises: CreateException: if an error occurs
        """
        _method_name = '__create_domain'

        self.logger.entering(class_name=self.__class_name, method_name=_method_name)
        domain_type = self.model_context.get_domain_type()
        self.logger.info('WLSDPLY-12203', domain_type, class_name=self.__class_name, method_name=_method_name)
        self.model_context.set_domain_home(self._domain_home)

        if self.wls_helper.is_select_template_supported():
            self.__create_domain_with_select_template(self._domain_home)
        else:
            self.__create_base_domain(self._domain_home)
            self.__extend_domain(self._domain_home)

        if len(self.files_to_extract_from_archive) > 0:
            for file_to_extract in self.files_to_extract_from_archive:
                self.archive_helper.extract_file(file_to_extract)

        self.library_helper.install_domain_libraries()
        self.library_helper.extract_classpath_libraries()
        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return

    def __deploy(self):
        """
        Update the domain with domain attributes, resources and deployments.
        :raises: CreateException: if an error occurs while reading or updating the domain.
        """
        self.model_context.set_domain_home(self._domain_home)
        self.wlst_helper.read_domain(self._domain_home)
        self.__set_domain_attributes()
        self._configure_security_configuration()
        self.__deploy_resources_and_apps()
        self.wlst_helper.update_domain()
        self.wlst_helper.close_domain()
        return

    def __deploy_resources_and_apps(self):
        """
        Deploy the resources and applications.
        :raises: DeployException: if an error occurs while deploy the resources or applications
        """
        _method_name = '__deploy_resources_and_apps'

        self.logger.entering(class_name=self.__class_name, method_name=_method_name)
        model_deployer.deploy_resources_and_apps_for_create(self.model, self.model_context, self.aliases)
        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return

    def __create_base_domain(self, domain_home):
        """
        Create the base domain for versions of WLS prior to 12.2.1.
        :param domain_home: the domain home directory
        :raises: CreateException: if an error occurs
        """
        _method_name = '__create_base_domain'

        self.logger.entering(domain_home, class_name=self.__class_name, method_name=_method_name)
        base_template = self._domain_typedef.get_base_template()
        self.logger.info('WLSDPLY-12204', base_template, class_name=self.__class_name, method_name=_method_name)
        self.wlst_helper.read_template(base_template)
        self.__apply_base_domain_config(self.__topology_folder_list)

        self.logger.info('WLSDPLY-12205', self._domain_name, domain_home,
                         class_name=self.__class_name, method_name=_method_name)
        self.wlst_helper.write_domain(domain_home)

        self.logger.info('WLSDPLY-12206', self._domain_name, class_name=self.__class_name, method_name=_method_name)
        self.wlst_helper.close_template()

        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return

    def __extend_domain(self, domain_home):
        """
        Extend the base domain with extension templates, as needed, for versions of WebLogic Server prior to 12.2.1.
        :param domain_home: the domain home directory
        :raises: CreateException: if an error occurs
        """
        _method_name = '__extend_domain'

        self.logger.entering(domain_home, class_name=self.__class_name, method_name=_method_name)
        extension_templates = self._domain_typedef.get_extension_templates()
        if len(extension_templates) == 0:
            return

        self.logger.info('WLSDPLY-12207', self._domain_name, domain_home,
                         class_name=self.__class_name, method_name=_method_name)
        self.wlst_helper.read_domain(domain_home)
        self.__set_app_dir()

        for extension_template in extension_templates:
            self.logger.info('WLSDPLY-12208', extension_template,
                             class_name=self.__class_name, method_name=_method_name)
            self.wlst_helper.add_template(extension_template)

        self.__configure_fmw_infra_database()

        if self.wls_helper.is_set_server_groups_supported():
            server_groups_to_target = self._domain_typedef.get_server_groups_to_target()
            self.target_helper.target_server_groups_to_servers(server_groups_to_target)
            self.wlst_helper.update_domain()
        elif self._domain_typedef.is_jrf_domain_type():
            self.target_helper.target_jrf_groups_to_clusters_servers(domain_home)

        self.wlst_helper.close_domain()
        self.logger.info('WLSDPLY-12209', self._domain_name,
                         class_name=self.__class_name, method_name=_method_name)

        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return

    def __create_domain_with_select_template(self, domain_home):
        """
        Create and extend the domain, as needed, for WebLogic Server versions 12.2.1 and above.
        :param domain_home: the domain home directory
        :raises: CreateException: if an error occurs
        """
        _method_name = '__create_domain_with_select_template'

        self.logger.entering(domain_home, class_name=self.__class_name, method_name=_method_name)
        base_template = self._domain_typedef.get_base_template()
        self.logger.info('WLSDPLY-12210', base_template,
                         class_name=self.__class_name, method_name=_method_name)

        self.wlst_helper.select_template(base_template)

        extension_templates = self._domain_typedef.get_extension_templates()
        for extension_template in extension_templates:
            self.logger.info('WLSDPLY-12211', extension_template,
                             class_name=self.__class_name, method_name=_method_name)
            self.wlst_helper.select_template(extension_template)

        self.logger.info('WLSDPLY-12212', class_name=self.__class_name, method_name=_method_name)
        self.wlst_helper.load_templates()

        topology_folder_list = self.alias_helper.get_model_topology_top_level_folder_names()
        self.__apply_base_domain_config(topology_folder_list)

        if len(extension_templates) > 0:
            self.__set_app_dir()
            self.__configure_fmw_infra_database()

        self.logger.info('WLSDPLY-12206', self._domain_name, domain_home,
                         class_name=self.__class_name, method_name=_method_name)

        server_groups_to_target = self._domain_typedef.get_server_groups_to_target()
        server_assigns, dynamic_assigns = self.target_helper.target_server_groups_to_servers(server_groups_to_target)
        if server_assigns is not None:
            self.target_helper.target_server_groups(server_assigns)

        self.wlst_helper.write_domain(domain_home)
        self.wlst_helper.close_template()

        if dynamic_assigns is not None:
            self.target_helper.target_server_groups_to_dynamic_clusters(dynamic_assigns)

        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return

    def __apply_base_domain_config(self, topology_folder_list):
        """
        Apply the base domain configuration from the model topology section.
        :param topology_folder_list: the model topology folder list to process
        :raises: CreateException: if an error occurs
        """
        _method_name = '__apply_base_domain_config'

        self.logger.entering(topology_folder_list, class_name=self.__class_name, method_name=_method_name)
        self.logger.fine('WLSDPLY-12219', class_name=self.__class_name, method_name=_method_name)

        location = LocationContext()
        domain_name_token = self.alias_helper.get_name_token(location)
        location.add_name_token(domain_name_token, self._domain_name)

        self.__set_core_domain_params()

        self.__create_security_folder(location)
        topology_folder_list.remove(SECURITY)

        topology_folder_list.remove(SECURITY_CONFIGURATION)

        self.__create_mbeans_used_by_topology_mbeans(location, topology_folder_list)

        self.__create_machines(location)
        topology_folder_list.remove(MACHINE)
        topology_folder_list.remove(UNIX_MACHINE)

        self.__create_clusters_and_servers(location)
        topology_folder_list.remove(CLUSTER)
        if SERVER_TEMPLATE in topology_folder_list:
            topology_folder_list.remove(SERVER_TEMPLATE)
        topology_folder_list.remove(SERVER)

        self.__create_migratable_targets(location)
        topology_folder_list.remove(MIGRATABLE_TARGET)

        self.__create_other_domain_artifacts(location, topology_folder_list)

        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return

    def __set_core_domain_params(self):
        """
        Set the core domain parameters.
        :raises: CreateException: if an error occurs
        """
        _method_name = '__set_core_domain_params'

        self.logger.entering(class_name=self.__class_name, method_name=_method_name)
        self.wlst_helper.set_option_if_needed(SET_OPTION_DOMAIN_NAME, self._domain_name)

        java_home = self.model_context.get_java_home()
        self.wlst_helper.set_option_if_needed(SET_OPTION_JAVA_HOME, java_home)

        if SERVER_START_MODE in self._domain_info:
            server_start_mode = self._domain_info[SERVER_START_MODE]
            self.wlst_helper.set_option_if_needed(SET_OPTION_SERVER_START_MODE, server_start_mode)

        self.__set_domain_name()
        self.__set_admin_password()
        self.__set_admin_server_name()

        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return

    def __create_mbeans_used_by_topology_mbeans(self, location, topology_folder_list):
        """
        Create the entities that are referenced by domain, machine, server and server template attributes.
        :param location: current location
        :raises: CreateException: if an error occurs
        """
        self.__create_log_filters(location)
        topology_folder_list.remove(LOG_FILTER)
        self.__create_reliable_delivery_policy(location)
        topology_folder_list.remove(WS_RELIABLE_DELIVERY_POLICY)
        self.__create_xml_entity_cache(location)
        topology_folder_list.remove(XML_ENTITY_CACHE)
        self.__create_xml_registry(location)
        topology_folder_list.remove(XML_REGISTRY)

    def __create_security_folder(self, location):
        """
        Create the /Security folder objects, if any.
        :param location: the location to use
        :raises: CreateException: if an error occurs
        """
        _method_name = '__create_security_folder'

        self.logger.entering(str(location), class_name=self.__class_name, method_name=_method_name)
        security_nodes = dictionary_utils.get_dictionary_element(self._topology, SECURITY)
        if len(security_nodes) > 0:
            self._create_mbean(SECURITY, security_nodes, location)
        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return

    def __create_log_filters(self, location):
        """
        Create the /LogFilter objects if any for use in the logs of the base components like domain and server
        :param location: the location to use
        :raises: CreateException: if an error occurs
        """
        _method_name = '__create_log_filters'

        self.logger.entering(str(location), class_name=self.__class_name, method_name=_method_name)
        log_filter_nodes = dictionary_utils.get_dictionary_element(self._topology, LOG_FILTER)

        if len(log_filter_nodes) > 0:
            self._create_named_mbeans(LOG_FILTER, log_filter_nodes, location, log_created=True)
        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return

    def __create_reliable_delivery_policy(self, location):
        """
        Create the /WSReliableDeliverPolicy objects if any for use by the server and server templates.
        :param location: the location to use
        :raises: CreateException: if an error occurs
        """
        _method_name = '__create_reliable_delivery_policy'

        self.logger.entering(str(location), class_name=self.__class_name, method_name=_method_name)
        policy_nodes = dictionary_utils.get_dictionary_element(self._topology, WS_RELIABLE_DELIVERY_POLICY)

        if len(policy_nodes) > 0:
            self._create_named_mbeans(WS_RELIABLE_DELIVERY_POLICY, policy_nodes, location, log_created=True)
        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return

    def __create_xml_entity_cache(self, location):
        """
        Create the /XMLEntityCache objects if any for use by the server and server templates.
        :param location: the location to use
        :raises: CreateException: if an error occurs
        """
        _method_name = '__create_xml_entity_cache'

        self.logger.entering(str(location), class_name=self.__class_name, method_name=_method_name)
        cache_nodes = dictionary_utils.get_dictionary_element(self._topology, XML_ENTITY_CACHE)

        if len(cache_nodes) > 0:
            self._create_named_mbeans(XML_ENTITY_CACHE, cache_nodes, location, log_created=True)
        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return

    def __create_xml_registry(self, location):
        """
        Create the /XMLRegistry objects if any for use by the server and server templates.
        :param location: the location to use
        :raises: CreateException: if an error occurs
        """
        _method_name = '__create_xml_registry'

        self.logger.entering(str(location), class_name=self.__class_name, method_name=_method_name)
        registry_nodes = dictionary_utils.get_dictionary_element(self._topology, XML_REGISTRY)

        if len(registry_nodes) > 0:
            self._create_named_mbeans(XML_REGISTRY, registry_nodes, location, log_created=True)
        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return

    def __create_machines(self, location):
        """
        Create the /Machine and /UnixMachine folder objects, if any.
        :param location: the location to use
        :raises: CreateException: if an error occurs
        """
        _method_name = '__create_machines'

        self.logger.entering(str(location), class_name=self.__class_name, method_name=_method_name)
        machine_nodes = dictionary_utils.get_dictionary_element(self._topology, MACHINE)
        unix_machine_nodes = dictionary_utils.get_dictionary_element(self._topology, UNIX_MACHINE)

        if len(machine_nodes) > 0:
            self._create_named_mbeans(MACHINE, machine_nodes, location, log_created=True)
        if len(unix_machine_nodes) > 0:
            self._create_named_mbeans(UNIX_MACHINE, unix_machine_nodes, location, log_created=True)
        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return

    def __create_clusters_and_servers(self, location):
        """
        Create the /Cluster, /ServerTemplate, and /Server folder objects.
        :param location: the location to use
        :raises: CreateException: if an error occurs
        """
        _method_name = '__create_clusters_and_servers'

        self.logger.entering(str(location), class_name=self.__class_name, method_name=_method_name)

        #
        # In order for source domain provisioning to work with dynamic clusters, we have to provision
        # the ServerTemplates.  There is a cyclical dependency between Server Template and Clusters so we
        # need for the ServerTemplates to exist before create clusters.  Once the clusters are provisioned,
        # then we can fully populate the ServerTemplates.
        #
        self.topology_helper.create_placeholder_server_templates(self._topology)

        # create placeholders for JDBC resources that may be referenced in cluster definition.
        resources_dict = self.model.get_model_resources()
        self.topology_helper.create_placeholder_jdbc_resources(resources_dict)

        cluster_nodes = dictionary_utils.get_dictionary_element(self._topology, CLUSTER)
        if len(cluster_nodes) > 0:
            self._create_named_mbeans(CLUSTER, cluster_nodes, location, log_created=True)

        #
        # Now, fully populate the ServerTemplates, if any.
        #
        server_template_nodes = dictionary_utils.get_dictionary_element(self._topology, SERVER_TEMPLATE)
        if len(server_template_nodes) > 0:
            self._create_named_mbeans(SERVER_TEMPLATE, server_template_nodes, location, log_created=True)

        #
        # Finally, create/update the servers.
        #
        server_nodes = dictionary_utils.get_dictionary_element(self._topology, SERVER)
        # There may be a dependency to other servers when the server is in a cluster
        self.topology_helper.create_placeholder_servers_in_cluster(self._topology)
        if len(server_nodes) > 0:
            self._create_named_mbeans(SERVER, server_nodes, location, log_created=True)

        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return

    def __create_migratable_targets(self, location):
        """
        Create the /MigratableTarget folder objects, if any.
        :param location: the location to use
        :raises: CreateException: if an error occurs
        """
        _method_name = '__create_migratable_targets'

        self.logger.entering(str(location), class_name=self.__class_name, method_name=_method_name)
        migratable_target_nodes = dictionary_utils.get_dictionary_element(self._topology, MIGRATABLE_TARGET)

        if len(migratable_target_nodes) > 0:
            self._create_named_mbeans(MIGRATABLE_TARGET, migratable_target_nodes, location, log_created=True)

        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return

    def __create_other_domain_artifacts(self, location, mbean_type_list):
        """
        Create the remaining model topology-related folder objects, if any.
        :param location: the location to use
        :raises: CreateException: if an error occurs
        """
        _method_name = '__create_other_domain_artifacts'

        self.logger.entering(str(location), mbean_type_list, class_name=self.__class_name, method_name=_method_name)
        for mbean_type in mbean_type_list:
            mbean_nodes = dictionary_utils.get_dictionary_element(self._topology, mbean_type)

            if len(mbean_nodes) > 0:
                mbean_location = LocationContext(location).append_location(mbean_type)
                if self.alias_helper.supports_multiple_mbean_instances(mbean_location):
                    self._create_named_mbeans(mbean_type, mbean_nodes, location, log_created=True)
                else:
                    self._create_mbean(mbean_type, mbean_nodes, location, log_created=True)

        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return

    def __set_atp_connection_property(self, root_location, property_name, property_value):
        create_path = self.alias_helper.get_wlst_create_path(root_location)

        self.wlst_helper.cd(create_path)

        token_name = self.alias_helper.get_name_token(root_location)

        if token_name is not None:
            root_location.add_name_token(token_name, property_name)

        mbean_name = self.alias_helper.get_wlst_mbean_name(root_location)
        mbean_type = self.alias_helper.get_wlst_mbean_type(root_location)

        self.wlst_helper.create(mbean_name, mbean_type)

        wlst_path = self.alias_helper.get_wlst_attributes_path(root_location)

        self.wlst_helper.cd(wlst_path)

        wlst_name, wlst_value = \
            self.alias_helper.get_wlst_attribute_name_and_value(root_location, DRIVER_PARAMS_PROPERTY_VALUE,
                                                                property_value)
        self.wlst_helper.set(wlst_name, wlst_value)

        root_location.remove_name_token(property_name)

    def __configure_fmw_infra_database(self):
        """
        Configure the FMW Infrastructure DataSources.
        :raises: CreateException: if an error occurs
        """
        _method_name = '__configure_fmw_infra_database'
        self.logger.entering(class_name=self.__class_name, method_name=_method_name)

        has_atp = 0
        # For ATP databases :  we need to set all the property for each datasource
        # load atp connection properties from properties file
        #
        domain_info = self.model.get_model_domain_info()

        if RCU_DB_INFO in domain_info:
            rcu_db_info = RcuDbInfo(self.alias_helper, domain_info[RCU_DB_INFO])

            # HANDLE ATP case

            if rcu_db_info.has_atpdbinfo():
                has_atp = 1
                # parse the tnsnames.ora file and retrieve the connection string
                tns_admin = rcu_db_info.get_atp_tns_admin()
                rcu_database = atp_helper.get_atp_connect_string(tns_admin + os.sep + 'tnsnames.ora',
                                                                 rcu_db_info.get_atp_entry())

                rcu_prefix = rcu_db_info.get_rcu_prefix()
                rcu_schema_pwd = rcu_db_info.get_rcu_schema_password()
                keystore_pwd = rcu_db_info.get_keystore_password()
                truststore_pwd = rcu_db_info.get_truststore_password()

                # Need to set for the connection proeprty for each datasource

                fmw_database = self.wls_helper.get_jdbc_url_from_rcu_connect_string(rcu_database)

                location = LocationContext()
                location.append_location(JDBC_SYSTEM_RESOURCE)

                folder_path = self.alias_helper.get_wlst_list_path(location)
                self.wlst_helper.cd(folder_path)
                ds_names = self.wlst_helper.lsc()

                for ds_name in ds_names:
                    location = LocationContext()
                    location.append_location(JDBC_SYSTEM_RESOURCE)
                    token_name = self.alias_helper.get_name_token(location)
                    location.add_name_token(token_name, ds_name)

                    location.append_location(JDBC_RESOURCE)
                    location.append_location(JDBC_DRIVER_PARAMS)
                    wlst_path = self.alias_helper.get_wlst_attributes_path(location)
                    self.wlst_helper.cd(wlst_path)

                    wlst_name, wlst_value = \
                        self.alias_helper.get_wlst_attribute_name_and_value(location, URL, fmw_database)
                    self.wlst_helper.set_if_needed(wlst_name, wlst_value, JDBC_DRIVER_PARAMS, ds_name)

                    wlst_name, wlst_value = \
                        self.alias_helper.get_wlst_attribute_name_and_value(location, PASSWORD_ENCRYPTED,
                                                                            rcu_schema_pwd, masked=True)
                    self.wlst_helper.set_if_needed(wlst_name, wlst_value, JDBC_DRIVER_PARAMS, ds_name, masked=True)

                    location.append_location(JDBC_DRIVER_PARAMS_PROPERTIES)
                    token_name = self.alias_helper.get_name_token(location)
                    if token_name is not None:
                        location.add_name_token(token_name, DRIVER_PARAMS_USER_PROPERTY)

                    wlst_path = self.alias_helper.get_wlst_attributes_path(location)
                    self.wlst_helper.cd(wlst_path)
                    orig_user = self.wlst_helper.get('Value')
                    stb_user = orig_user.replace('DEV', rcu_prefix)
                    wlst_name, wlst_value = \
                        self.alias_helper.get_wlst_attribute_name_and_value(location, DRIVER_PARAMS_PROPERTY_VALUE,
                                                                            stb_user)
                    self.wlst_helper.set_if_needed(wlst_name, wlst_value,
                                                   JDBC_DRIVER_PARAMS_PROPERTIES, DRIVER_PARAMS_USER_PROPERTY)

                    # need to set other properties

                    location.remove_name_token(DRIVER_PARAMS_USER_PROPERTY)

                    self.__set_atp_connection_property(location, DRIVER_PARAMS_kEYSTORE_PROPERTY, tns_admin + os.sep
                                                       + 'keystore.jks')
                    self.__set_atp_connection_property(location, DRIVER_PARAMS_KEYSTORETYPE_PROPERTY,
                                                       'JKS')
                    self.__set_atp_connection_property(location, DRIVER_PARAMS_KEYSTOREPWD_PROPERTY, keystore_pwd)
                    self.__set_atp_connection_property(location, DRIVER_PARAMS_TRUSTSTORE_PROPERTY, tns_admin + os.sep
                                                       + 'truststore.jks')
                    self.__set_atp_connection_property(location, DRIVER_PARAMS_TRUSTSTORETYPE_PROPERTY,
                                                       'JKS')
                    self.__set_atp_connection_property(location, DRIVER_PARAMS_TRUSTSTOREPWD_PROPERTY, truststore_pwd)

                    self.__set_atp_connection_property(location, DRIVER_PARAMS_NET_SSL_VERSION, '1.2')
                    self.__set_atp_connection_property(location, DRIVER_PARAMS_NET_SERVER_DN_MATCH_PROPERTY, 'true')
                    self.__set_atp_connection_property(location, DRIVER_PARAMS_NET_TNS_ADMIN, tns_admin)
                    self.__set_atp_connection_property(location, DRIVER_PARAMS_NET_FAN_ENABLED, 'false')

        if not has_atp:
            if RCU_DB_INFO in domain_info:
                rcu_db_info = RcuDbInfo(self.alias_helper, domain_info[RCU_DB_INFO])
                rcu_prefix = rcu_db_info.get_rcu_prefix()
                rcu_database = rcu_db_info.get_rcu_regular_db_conn()
                rcu_schema_pwd = rcu_db_info.get_rcu_schema_password()
            else:
                rcu_database = self.model_context.get_rcu_database()
                if rcu_database is None:
                    return
                rcu_prefix = self.model_context.get_rcu_prefix()
                rcu_schema_pwd = self.model_context.get_rcu_schema_pass()

            fmw_database = self.wls_helper.get_jdbc_url_from_rcu_connect_string(rcu_database)
            self.logger.fine('WLSDPLY-12221', fmw_database, class_name=self.__class_name, method_name=_method_name)

            location = LocationContext()
            location.append_location(JDBC_SYSTEM_RESOURCE)
            token_name = self.alias_helper.get_name_token(location)
            svc_table_ds_name = self.wls_helper.get_jrf_service_table_datasource_name()
            if token_name is not None:
                location.add_name_token(token_name, svc_table_ds_name)

            location.append_location(JDBC_RESOURCE)
            location.append_location(JDBC_DRIVER_PARAMS)
            wlst_path = self.alias_helper.get_wlst_attributes_path(location)
            self.wlst_helper.cd(wlst_path)

            svc_table_driver_name = self.wls_helper.get_stb_data_source_jdbc_driver_name()
            wlst_name, wlst_value = \
                self.alias_helper.get_wlst_attribute_name_and_value(location, DRIVER_NAME, svc_table_driver_name)
            self.wlst_helper.set_if_needed(wlst_name, wlst_value, JDBC_DRIVER_PARAMS, svc_table_ds_name)

            wlst_name, wlst_value = \
                self.alias_helper.get_wlst_attribute_name_and_value(location, URL, fmw_database)
            self.wlst_helper.set_if_needed(wlst_name, wlst_value, JDBC_DRIVER_PARAMS, svc_table_ds_name)

            wlst_name, wlst_value = \
                self.alias_helper.get_wlst_attribute_name_and_value(location, PASSWORD_ENCRYPTED,
                                                                    rcu_schema_pwd, masked=True)
            self.wlst_helper.set_if_needed(wlst_name, wlst_value, JDBC_DRIVER_PARAMS, svc_table_ds_name, masked=True)

            location.append_location(JDBC_DRIVER_PARAMS_PROPERTIES)
            token_name = self.alias_helper.get_name_token(location)

            if token_name is not None:
                location.add_name_token(token_name, DRIVER_PARAMS_USER_PROPERTY)

            stb_user = self.wls_helper.get_stb_user_name(rcu_prefix)
            self.logger.fine('WLSDPLY-12222', stb_user, class_name=self.__class_name, method_name=_method_name)
            wlst_path = self.alias_helper.get_wlst_attributes_path(location)
            self.wlst_helper.cd(wlst_path)
            wlst_name, wlst_value = \
                self.alias_helper.get_wlst_attribute_name_and_value(location, DRIVER_PARAMS_PROPERTY_VALUE, stb_user)
            self.wlst_helper.set_if_needed(wlst_name, wlst_value,
                                           JDBC_DRIVER_PARAMS_PROPERTIES, DRIVER_PARAMS_USER_PROPERTY)

            self.logger.info('WLSDPLY-12223', class_name=self.__class_name, method_name=_method_name)
            if self.wls_helper.is_database_defaults_supported():
                self.wlst_helper.get_database_defaults()

        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return

    def __set_app_dir(self):
        """
        Set the AppDir domain option.
        :raises: CreateException: if an error occurs
        """
        _method_name = '__set_app_dir'

        self.logger.entering(class_name=self.__class_name, method_name=_method_name)
        if APP_DIR in self._domain_info:
            app_dir = self._domain_info[APP_DIR]
            self.logger.fine('WLSDPLY-12225', model_helper.get_model_domain_info_key(), APP_DIR, app_dir,
                             class_name=self.__class_name, method_name=_method_name)
        else:
            app_parent = self.model_context.get_domain_parent_dir()
            if not app_parent:
                app_parent = os.path.dirname(self.model_context.get_domain_home())

            app_dir = os.path.join(app_parent, 'applications')
            self.logger.fine('WLSDPLY-12226', model_helper.get_model_domain_info_key(), APP_DIR, app_dir,
                             class_name=self.__class_name, method_name=_method_name)

        self.wlst_helper.set_option_if_needed(SET_OPTION_APP_DIR, app_dir)

        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return

    def __set_domain_name(self):
        _method_name = '__set_domain_name'
        # Stash the default name since the SecurityConfiguration subfolder name does not change
        # to the new domain name until after the domain has been written to disk and re-read.
        #
        self.__default_domain_name = self.wlst_helper.get(NAME)
        if self.__default_domain_name is None or len(self.__default_domain_name) == 0:
            self.__default_domain_name = DEFAULT_WLS_DOMAIN_NAME

        # set this option, in case domain name is different from domain directory name
        self.wlst_helper.set_option_if_needed('DomainName', self._domain_name)

        if self._domain_name != self.__default_domain_name:
            #
            # We cannot use the aliases for the Server Name attribute since we
            # filter out any name fields.
            #
            self.wlst_helper.set_if_needed(DOMAIN_NAME, self._domain_name, DOMAIN_NAME, self._domain_name)
            self.logger.info('WLSDPLY-12227', self.__default_domain_name, self._domain_name,
                             class_name=self.__class_name, method_name=_method_name)
        return

    def __set_admin_password(self):
        """
        Set the administrative user's password.
        :raises: CreateException: if an error occurs
        """
        _method_name = '__set_admin_password'

        if ADMIN_PASSWORD in self._domain_info:
            admin_password = self._domain_info[ADMIN_PASSWORD]
            admin_username = self.wls_helper.get_default_admin_username()
            if ADMIN_USERNAME in self._domain_info:
                admin_username = self._domain_info[ADMIN_USERNAME]

            location = LocationContext().append_location(SECURITY)
            token_name = self.alias_helper.get_name_token(location)
            if token_name is not None:
                location.add_name_token(token_name, self._domain_name)

            location.append_location(USER)
            token_name = self.alias_helper.get_name_token(location)
            if token_name is not None:
                location.add_name_token(token_name, self.wls_helper.get_default_admin_username())

            admin_user_path = self.alias_helper.get_wlst_attributes_path(location)
            self.wlst_helper.cd(admin_user_path)
            wlst_name, wlst_value = \
                self.alias_helper.get_wlst_attribute_name_and_value(location, NAME, admin_username)
            self.wlst_helper.set_if_needed(wlst_name, wlst_value, NAME, admin_username)
            wlst_name, wlst_value = \
                self.alias_helper.get_wlst_attribute_name_and_value(location, PASSWORD, admin_password, masked=True)
            self.wlst_helper.set_if_needed(wlst_name, wlst_value, PASSWORD, '<masked>', masked=True)

        else:
            ex = exception_helper.create_create_exception('WLSDPLY-12228', 'AdminPassword',
                                                          model_helper.get_model_domain_info_key())
            self.logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return

    def __set_admin_server_name(self):
        """
        Set the name of the AdminServer, if required.
        :raises: CreateException: if an error occurs
        """
        _method_name = '__set_admin_server_name'

        # Test to see if the name was specified to see whether we need to do this or not...
        self.wlst_helper.cd('/')
        self.__default_admin_server_name = self.wlst_helper.get(ADMIN_SERVER_NAME)
        if self._admin_server_name != self.__default_admin_server_name:
            location = LocationContext().append_location(SERVER)
            token_name = self.alias_helper.get_name_token(location)
            if token_name is not None:
                location.add_name_token(token_name, self.__default_admin_server_name)

            wlst_path = self.alias_helper.get_wlst_attributes_path(location)
            self.wlst_helper.cd(wlst_path)
            #
            # We cannot use the aliases for the Server Name attribute since we
            # filter out any name fields.
            #
            self.wlst_helper.set_if_needed(NAME, self._admin_server_name, SERVER, self.__default_admin_server_name)
            self.logger.info('WLSDPLY-12229', self.__default_admin_server_name, self._admin_server_name,
                             class_name=self.__class_name, method_name=_method_name)
        else:
            self._admin_server_name = self.__default_admin_server_name
        return

    def __set_domain_attributes(self):
        """
        Set the Domain attributes
        """
        _method_name = '__set_domain_attributes'
        self.logger.finer('WLSDPLY-12231', self._domain_name, class_name=self.__class_name, method_name=_method_name)
        attrib_dict = dictionary_utils.get_dictionary_attributes(self.model.get_model_topology())

        # skip any attributes that have special handling
        for attribute in CREATE_ONLY_DOMAIN_ATTRIBUTES:
            if attribute in attrib_dict:
                del attrib_dict[attribute]

        location = LocationContext()
        attribute_path = self.alias_helper.get_wlst_attributes_path(location)
        self.wlst_helper.cd(attribute_path)
        self._set_attributes(location, attrib_dict)
        return

    def _configure_security_configuration(self):
        """
        Configure the SecurityConfiguration MBean and its Realm sub-folder. In 11g, the SecurityConfiguration MBean
        is not persisted to the domain config until the domain is first written.
        :return:
        """
        _method_name = '_configure_security_configuration'
        self.logger.entering(class_name=self.__class_name, method_name=_method_name)
        # SecurityConfiguration is special since the subfolder name does not change when you change the domain name.
        # It only changes once the domain is written and re-read...
        location = LocationContext()
        domain_name_token = deployer_utils.get_domain_token(self.alias_helper)
        security_config_location = LocationContext().add_name_token(domain_name_token, self._domain_name)
        self.security_provider_creator.create_security_configuration(security_config_location)
        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return
