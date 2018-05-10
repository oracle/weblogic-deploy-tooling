"""
Copyright (c) 2017, 2018, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""
import javaos as os

from oracle.weblogic.deploy.create import RCURunner

from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.exception import exception_helper
from wlsdeploy.tool.create.creator import Creator
from wlsdeploy.tool.deploy import deployer_utils
from wlsdeploy.tool.deploy import model_deployer
from wlsdeploy.tool.util.archive_helper import ArchiveHelper
from wlsdeploy.util import dictionary_utils
from wlsdeploy.util import model as model_helper
from wlsdeploy.util.model import Model

from wlsdeploy.aliases.model_constants import ACTIVE_TYPE
from wlsdeploy.aliases.model_constants import ADJUDICATOR
from wlsdeploy.aliases.model_constants import ADMIN_PASSWORD
from wlsdeploy.aliases.model_constants import ADMIN_SERVER_NAME
from wlsdeploy.aliases.model_constants import ADMIN_USERNAME
from wlsdeploy.aliases.model_constants import APP_DIR
from wlsdeploy.aliases.model_constants import AUDITOR
from wlsdeploy.aliases.model_constants import AUTHENTICATION_PROVIDER
from wlsdeploy.aliases.model_constants import AUTHORIZER
from wlsdeploy.aliases.model_constants import CERT_PATH_PROVIDER
from wlsdeploy.aliases.model_constants import CLUSTER
from wlsdeploy.aliases.model_constants import COHERENCE_CLUSTER_SYSTEM_RESOURCE
from wlsdeploy.aliases.model_constants import CREDENTIAL_MAPPER
from wlsdeploy.aliases.model_constants import DEFAULT_ADJUDICATOR_NAME
from wlsdeploy.aliases.model_constants import DEFAULT_ADJUDICATOR_TYPE
from wlsdeploy.aliases.model_constants import DEFAULT_ADMIN_SERVER_NAME
from wlsdeploy.aliases.model_constants import DEFAULT_AUDITOR_NAME
from wlsdeploy.aliases.model_constants import DEFAULT_AUDITOR_TYPE
from wlsdeploy.aliases.model_constants import DEFAULT_AUTHENTICATOR_NAME
from wlsdeploy.aliases.model_constants import DEFAULT_AUTHENTICATOR_TYPE
from wlsdeploy.aliases.model_constants import DEFAULT_IDENTITY_ASSERTER_NAME
from wlsdeploy.aliases.model_constants import DEFAULT_IDENTITY_ASSERTER_TYPE
from wlsdeploy.aliases.model_constants import DEFAULT_AUTHORIZER_NAME
from wlsdeploy.aliases.model_constants import DEFAULT_AUTHORIZER_TYPE
from wlsdeploy.aliases.model_constants import DEFAULT_CERT_PATH_PROVIDER_NAME
from wlsdeploy.aliases.model_constants import DEFAULT_CERT_PATH_PROVIDER_TYPE
from wlsdeploy.aliases.model_constants import DEFAULT_CREDENTIAL_MAPPER_NAME
from wlsdeploy.aliases.model_constants import DEFAULT_CREDENTIAL_MAPPER_TYPE
from wlsdeploy.aliases.model_constants import DEFAULT_PASSWORD_VALIDATOR_NAME
from wlsdeploy.aliases.model_constants import DEFAULT_PASSWORD_VALIDATOR_TYPE
from wlsdeploy.aliases.model_constants import DEFAULT_ROLE_MAPPER_NAME
from wlsdeploy.aliases.model_constants import DEFAULT_ROLE_MAPPER_TYPE
from wlsdeploy.aliases.model_constants import DEFAULT_WLS_DOMAIN_NAME
from wlsdeploy.aliases.model_constants import DOMAIN_INFO
from wlsdeploy.aliases.model_constants import DOMAIN_LIBRARIES
from wlsdeploy.aliases.model_constants import DRIVER_NAME
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_PROPERTY_VALUE
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_USER_PROPERTY
from wlsdeploy.aliases.model_constants import JDBC_DRIVER_PARAMS
from wlsdeploy.aliases.model_constants import JDBC_DRIVER_PARAMS_PROPERTIES
from wlsdeploy.aliases.model_constants import JDBC_RESOURCE
from wlsdeploy.aliases.model_constants import JDBC_SYSTEM_RESOURCE
from wlsdeploy.aliases.model_constants import DOMAIN_NAME
from wlsdeploy.aliases.model_constants import MACHINE
from wlsdeploy.aliases.model_constants import MIGRATABLE_TARGET
from wlsdeploy.aliases.model_constants import NAME
from wlsdeploy.aliases.model_constants import PARTITION
from wlsdeploy.aliases.model_constants import PASSWORD
from wlsdeploy.aliases.model_constants import PASSWORD_ENCRYPTED
from wlsdeploy.aliases.model_constants import PASSWORD_VALIDATOR
from wlsdeploy.aliases.model_constants import REALM
from wlsdeploy.aliases.model_constants import RESOURCE_GROUP
from wlsdeploy.aliases.model_constants import RESOURCE_GROUP_TEMPLATE
from wlsdeploy.aliases.model_constants import ROLE_MAPPER
from wlsdeploy.aliases.model_constants import SECURITY
from wlsdeploy.aliases.model_constants import SECURITY_CONFIGURATION
from wlsdeploy.aliases.model_constants import SERVER
from wlsdeploy.aliases.model_constants import SERVER_GROUP_TARGETING_LIMITS
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


class DomainCreator(Creator):
    """
    The class that driver domain creation.
    """
    __program_name = 'createDomain'
    __class_name = 'DomainCreator'

    def __init__(self, model_dictionary, model_context, aliases):
        _method_name = '__init__'
        Creator.__init__(self, model_dictionary, model_context, aliases)

        self._coherence_cluster_elements = [CLUSTER, SERVER, SERVER_TEMPLATE]

        # domainInfo section is required to get the admin password, everything else
        # is optional and will use the template defaults
        if model_helper.get_model_domain_info_key() not in model_dictionary:
            ex = exception_helper.create_create_exception('WLSDPLY-12200', self.__program_name,
                                                          model_helper.get_model_domain_info_key(),
                                                          self.model_context.get_model_file())
            self.logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex

        self._domain_typedef = self.model_context.get_domain_typedef()
        self._topology = self.model.get_model_topology()
        self._domain_info = self.model.get_model_domain_info()

        if DOMAIN_NAME in self._topology:
            self._domain_name = self._topology[DOMAIN_NAME]
        else:
            self._domain_name = DEFAULT_WLS_DOMAIN_NAME
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
        #
        # Creating domains with the wls.jar template is busted for pre-12.1.2 domains with regards to the
        # names of the default authentication providers (both the DefaultAuthenticator and the
        # DefaultIdentityAsserter names are 'Provider', making it impossible to work with in WLST.  If
        # the WLS version is earlier than fix this as part of domain creation...
        #
        self.__fix_default_authentication_provider_names = \
            self.wls_helper.do_default_authentication_provider_names_need_fixing()

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
        self.__deploy_resources_and_apps()
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
        if type_name in self._coherence_cluster_elements:
            self._check_coherence_cluster_references(model_nodes, base_location)
            # continue with regular processing

        Creator._create_named_mbeans(self, type_name, model_nodes, base_location, log_created=log_created)

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
        rcu_db = self.model_context.get_rcu_database()
        rcu_prefix = self.model_context.get_rcu_prefix()
        rcu_sys_pass = self.model_context.get_rcu_sys_pass()
        rcu_schema_pass = self.model_context.get_rcu_schema_pass()

        runner = RCURunner(domain_type, oracle_home, java_home, rcu_db, rcu_prefix, rcu_schemas)
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

        self.__install_domain_libraries(self._domain_home)
        self.__extract_classpath_libraries(self._domain_home)
        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return

    def __deploy_resources_and_apps(self):
        """
        Deploy the resources and applications.
        :raises: CreateException: if an error occurs while reading or updating the domain.
        :raises: DeployException: if an error occurs while deploy the resources or applications
        """
        _method_name = '__deploy_resources_and_apps'

        self.logger.entering(class_name=self.__class_name, method_name=_method_name)
        self.model_context.set_domain_home(self._domain_home)
        self.wlst_helper.read_domain(self._domain_home)
        model_deployer.deploy_resources_and_apps_for_create(self.model, self.model_context, self.aliases)
        self.wlst_helper.update_domain()
        self.wlst_helper.close_domain()
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

        server_groups_to_target = self._domain_typedef.get_server_groups_to_target()
        self.__target_server_groups_to_servers(server_groups_to_target)

        self.logger.info('WLSDPLY-12209', self._domain_name,
                         class_name=self.__class_name, method_name=_method_name)
        self.wlst_helper.update_domain()
        self.wlst_helper.close_domain()

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

            server_groups_to_target = self._domain_typedef.get_server_groups_to_target()
            self.__target_server_groups_to_servers(server_groups_to_target)

        self.logger.info('WLSDPLY-12206', self._domain_name, domain_home,
                         class_name=self.__class_name, method_name=_method_name)
        self.wlst_helper.write_domain(domain_home)
        self.wlst_helper.close_template()
        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return

    def __install_domain_libraries(self, domain_home):
        """
        Extract the domain libraries listed in the model, if any, to the <DOMAIN_HOME>/lib directory.
        :param domain_home: the domain home directory
        :raises: CreateException: if an error occurs
        """
        _method_name = '__install_domain_libraries'

        self.logger.entering(domain_home, class_name=self.__class_name, method_name=_method_name)
        domain_info_dict = self.model.get_model_domain_info()
        if DOMAIN_LIBRARIES not in domain_info_dict or len(domain_info_dict[DOMAIN_LIBRARIES]) == 0:
            self.logger.info('WLSDPLY-12213', class_name=self.__class_name, method_name=_method_name)
        else:
            domain_libs = dictionary_utils.get_dictionary_element(domain_info_dict, DOMAIN_LIBRARIES)
            if self.archive_helper is None:
                ex = exception_helper.create_create_exception('WLSDPLY-12214', domain_libs)
                self.logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                raise ex

            for domain_lib in domain_libs:
                self.logger.info('WLSDPLY-12215', domain_lib, domain_home,
                                 class_name=self.__class_name, method_name=_method_name)
                self.archive_helper.extract_domain_library(domain_lib)

        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return

    def __extract_classpath_libraries(self, domain_home):
        """
        Extract any classpath libraries in the archive to the domain home.
        :param domain_home: the domain home directory
        :raises: CreateException: if an error occurs
        """
        _method_name = '__extract_classpath_libraries'

        self.logger.entering(domain_home, class_name=self.__class_name, method_name=_method_name)
        if self.archive_helper is None:
            self.logger.info('WLSDPLY-12216', class_name=self.__class_name, method_name=_method_name)
        else:
            num_cp_libs = self.archive_helper.extract_classpath_libraries()
            if num_cp_libs > 0:
                self.logger.info('WLSDPLY-12217', num_cp_libs, domain_home,
                                 class_name=self.__class_name, method_name=_method_name)
            else:
                self.logger.info('WLSDPLY-12218', self.model_context.get_archive_file_name(),
                                 class_name=self.__class_name, method_name=_method_name)
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

        # SecurityConfiguration is special since the subfolder name does not change when you change the domain name.
        # It only changes once the domain is written and re-read...
        security_config_location = LocationContext().add_name_token(domain_name_token, self.__default_domain_name)
        self.__create_security_configuration(security_config_location)
        topology_folder_list.remove(SECURITY_CONFIGURATION)

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

    def __create_security_configuration(self, location):
        """
        Create the /SecurityConfiguration folder objects, if any.
        :param location: the location to use
        :raises: CreateException: if an error occurs
        """
        _method_name = '__create_security_configuration'

        self.logger.entering(str(location), class_name=self.__class_name, method_name=_method_name)
        security_configuration_nodes = dictionary_utils.get_dictionary_element(self._topology, SECURITY_CONFIGURATION)

        self.__handle_default_security_providers(location, security_configuration_nodes)
        if len(security_configuration_nodes) > 0:
            self._create_mbean(SECURITY_CONFIGURATION, security_configuration_nodes, location, log_created=True)
        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return

    def __handle_default_security_providers(self, base_location, security_configuration_dict):
        _method_name = '__handle_default_security_providers'

        self.logger.entering(str(base_location), class_name=self.__class_name, method_name=_method_name)
        location = self.__get_default_realm_location()
        if security_configuration_dict is None or len(security_configuration_dict) == 0:
            if self.__fix_default_authentication_provider_names:
                self.__handle_default_authentication_providers(location)
            self.logger.exiting(class_name=self.__class_name, method_name=_method_name)
            return

        if REALM in security_configuration_dict and 'myrealm' in security_configuration_dict[REALM]:
            myrealm = security_configuration_dict[REALM]['myrealm']
            if ADJUDICATOR in myrealm:
                adj_providers = myrealm[ADJUDICATOR]
                self.__handle_default_adjudicators(location, adj_providers)
            if AUDITOR in myrealm:
                audit_providers = myrealm[AUDITOR]
                self.__handle_default_auditors(location, audit_providers)
            if AUTHENTICATION_PROVIDER in myrealm:
                atn_providers = myrealm[AUTHENTICATION_PROVIDER]
                self.__handle_default_authentication_providers(location, atn_providers)
            elif self.__fix_default_authentication_provider_names:
                self.__handle_default_authentication_providers(location)
            if AUTHORIZER in myrealm:
                atz_providers = myrealm[AUTHORIZER]
                self.__handle_default_authorizers(location, atz_providers)
            if CERT_PATH_PROVIDER in myrealm:
                cert_path_providers = myrealm[CERT_PATH_PROVIDER]
                self.__handle_default_cert_path_providers(location, cert_path_providers)
            if CREDENTIAL_MAPPER in myrealm:
                credential_mapping_providers = myrealm[CREDENTIAL_MAPPER]
                self.__handle_default_credential_mappers(location, credential_mapping_providers)
            if PASSWORD_VALIDATOR in myrealm:
                password_validation_providers = myrealm[PASSWORD_VALIDATOR]
                self.__handle_default_password_validators(location, password_validation_providers)
            if ROLE_MAPPER in myrealm:
                role_mapping_providers = myrealm[ROLE_MAPPER]
                self.__handle_default_role_mappers(location, role_mapping_providers)
        elif self.__fix_default_authentication_provider_names:
            self.__handle_default_authentication_providers(location)

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
        server_template_nodes = dictionary_utils.get_dictionary_element(self._topology, SERVER_TEMPLATE)
        if len(server_template_nodes) > 0 and self._is_type_valid(location, SERVER_TEMPLATE):
            st_location = LocationContext(location).append_location(SERVER_TEMPLATE)
            st_mbean_type = self.alias_helper.get_wlst_mbean_type(st_location)
            st_create_path = self.alias_helper.get_wlst_create_path(st_location)
            self.wlst_helper.cd(st_create_path)

            st_token_name = self.alias_helper.get_name_token(st_location)
            for server_template_name in server_template_nodes:
                st_name = self.wlst_helper.get_quoted_name_for_wlst(server_template_name)
                if st_token_name is not None:
                    st_location.add_name_token(st_token_name, st_name)

                st_mbean_name = self.alias_helper.get_wlst_mbean_name(st_location)
                self.logger.info('WLSDPLY-12220', SERVER_TEMPLATE, st_mbean_name)
                self.wlst_helper.create(st_mbean_name, st_mbean_type)

        cluster_nodes = dictionary_utils.get_dictionary_element(self._topology, CLUSTER)
        if len(cluster_nodes) > 0:
            self._create_named_mbeans(CLUSTER, cluster_nodes, location, log_created=True)

        #
        # Now, fully populate the ServerTemplates, if any.
        #
        if len(server_template_nodes) > 0:
            self._create_named_mbeans(SERVER_TEMPLATE, server_template_nodes, location, log_created=True)

        #
        # Finally, create/update the servers.
        #
        server_nodes = dictionary_utils.get_dictionary_element(self._topology, SERVER)
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

    def __configure_fmw_infra_database(self):
        """
        Configure the FMW Infrastructure DataSources.
        :raises: CreateException: if an error occurs
        """
        _method_name = '__configure_fmw_infra_database'

        self.logger.entering(class_name=self.__class_name, method_name=_method_name)
        rcu_database = self.model_context.get_rcu_database()
        if rcu_database is None:
            return

        # No need to validate since these were validated at the entry point...
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
        self.wlst_helper.get_database_defaults()

        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return

    def __target_server_groups_to_servers(self, server_groups_to_target):
        """
        Target the server groups to the servers.
        :param server_groups_to_target: the list of server groups to target
        :raises: CreateException: if an error occurs
        """
        _method_name = '__target_server_groups_to_servers'

        self.logger.entering(server_groups_to_target, class_name=self.__class_name, method_name=_method_name)
        if len(server_groups_to_target) == 0:
            return

        location = LocationContext()
        root_path = self.alias_helper.get_wlst_attributes_path(location)
        self.wlst_helper.cd(root_path)

        # We need to get the effective list of servers for the domain.  Since any servers
        # referenced in the model have already been created but the templates may have
        # defined new servers not listed in the model, get the list from WLST.
        server_names = self._get_existing_server_names()

        # Get the clusters and and their members
        cluster_map = self._get_clusters_and_members_map()

        # Get any limits that may have been defined in the model
        domain_info = self.model.get_model_domain_info()
        server_group_targeting_limits = \
            dictionary_utils.get_dictionary_element(domain_info, SERVER_GROUP_TARGETING_LIMITS)
        if len(server_group_targeting_limits) > 0:
            server_group_targeting_limits = \
                self._get_server_group_targeting_limits(server_group_targeting_limits, cluster_map)

        # Get the map of server names to server groups to target
        server_to_server_groups_map = self._get_server_to_server_groups_map(self._admin_server_name,
                                                                            server_names,
                                                                            server_groups_to_target,
                                                                            server_group_targeting_limits)
        if len(server_names) > 1:
            for server, server_groups in server_to_server_groups_map.iteritems():
                if len(server_groups) > 0:
                    server_name = self.wlst_helper.get_quoted_name_for_wlst(server)
                    self.logger.info('WLSDPLY-12224', str(server_groups), server_name,
                                     class_name=self.__class_name, method_name=_method_name)
                    self.wlst_helper.set_server_groups(server_name, server_groups)

        elif len(server_group_targeting_limits) == 0:
            #
            # Domain has no managed servers and there were not targeting limits specified to target
            # server groups to the admin server so make sure that the server groups are targeted to
            # the admin server.
            #
            # This is really a best effort attempt.  It works for JRF domains but it is certainly possible
            # that it may cause problems with other custom domain types.  Of course, creating a domain with
            # no managed servers is not a primary use case of this tool so do it and hope for the best...
            #
            server_name = self.wlst_helper.get_quoted_name_for_wlst(server_names[0])
            self.wlst_helper.set_server_groups(server_name, server_groups_to_target)

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
            app_dir = os.path.join(self.model_context.get_domain_parent_dir(), 'applications')
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

    def __get_default_realm_location(self):
        """
        Ensure that the default realm exists and get the location object for it.
        :return: the location object to use to work on the default realm while creating a domain.
        """
        location = LocationContext().append_location(SECURITY_CONFIGURATION)
        # SecurityConfiguration is special since the subfolder name does not change when
        # you change the domain name.  It only changes once the domain is written and re-read...
        token_name = self.alias_helper.get_name_token(location)
        if token_name is not None:
            location.add_name_token(token_name, self.__default_domain_name)

        wlst_create_path = self.alias_helper.get_wlst_create_path(location)
        self.wlst_helper.cd(wlst_create_path)
        existing_folder_names = self.wlst_helper.get_existing_object_list(wlst_create_path)

        wlst_type, wlst_name = self.alias_helper.get_wlst_mbean_type_and_name(location)
        wlst_attribute_path = self.alias_helper.get_wlst_attributes_path(location)
        if wlst_type not in existing_folder_names:
            self.wlst_helper.create_and_cd(self.alias_helper, wlst_type, wlst_name, location, wlst_create_path)
        else:
            self.wlst_helper.cd(wlst_attribute_path)

        existing_folder_names = self.wlst_helper.get_existing_object_list(wlst_attribute_path)
        location.append_location(REALM)
        wlst_type = self.alias_helper.get_wlst_mbean_type(location)
        token_name = self.alias_helper.get_name_token(location)

        if wlst_type not in existing_folder_names:
            self.__default_security_realm_name = self.wls_helper.get_default_security_realm_name()
            if token_name is not None:
                location.add_name_token(token_name, self.__default_security_realm_name)
            wlst_name = self.alias_helper.get_wlst_mbean_name(location)
            self.wlst_helper.create_and_cd(self.alias_helper, wlst_type, wlst_name, location)
        else:
            wlst_list_path = self.alias_helper.get_wlst_list_path(location)
            existing_folder_names = self.wlst_helper.get_existing_object_list(wlst_list_path)
            if len(existing_folder_names) > 0:
                self.__default_security_realm_name = existing_folder_names[0]
            if token_name is not None:
                location.add_name_token(token_name, self.__default_security_realm_name)
            wlst_attribute_path = self.alias_helper.get_wlst_attributes_path(location)
            self.wlst_helper.cd(wlst_attribute_path)
        return location

    def __handle_default_adjudicators(self, base_location, adj_providers):
        if adj_providers is None or len(adj_providers) == 0 or DEFAULT_ADJUDICATOR_NAME is None:
            return

        if self.__need_to_delete_default_provider(adj_providers, DEFAULT_ADJUDICATOR_NAME, DEFAULT_ADJUDICATOR_TYPE):
            self.__delete_provider(base_location, DEFAULT_ADJUDICATOR_NAME, ADJUDICATOR)
        return

    def __handle_default_auditors(self, base_location, audit_providers):
        if audit_providers is None or len(audit_providers) == 0 or DEFAULT_AUDITOR_NAME is None:
            return

        if self.__need_to_delete_default_provider(audit_providers, DEFAULT_AUDITOR_NAME, DEFAULT_AUDITOR_TYPE):
            self.__delete_provider(base_location, DEFAULT_AUDITOR_NAME, AUDITOR)
        return

    def __handle_default_authentication_providers(self, base_location, atn_providers=None):
        _method_name = '__handle_default_authentication_providers'

        self.logger.entering(str(base_location), class_name=self.__class_name, method_name=_method_name)
        if atn_providers is None or len(atn_providers) == 0 or \
                (DEFAULT_AUTHENTICATOR_NAME is None and DEFAULT_IDENTITY_ASSERTER_NAME is None):
            if self.__fix_default_authentication_provider_names:
                # delete and recreate the default authenticator and default identity asserter with the correct names.
                self.__delete_and_recreate_provider(base_location, 'Provider', DEFAULT_AUTHENTICATOR_NAME,
                                                    AUTHENTICATION_PROVIDER, DEFAULT_AUTHENTICATOR_TYPE)
                self.__delete_and_recreate_provider(base_location, 'Provider', DEFAULT_IDENTITY_ASSERTER_NAME,
                                                    AUTHENTICATION_PROVIDER, DEFAULT_IDENTITY_ASSERTER_TYPE)
                self.__set_default_identity_aserter_attributes(base_location, DEFAULT_IDENTITY_ASSERTER_NAME,
                                                               AUTHENTICATION_PROVIDER, DEFAULT_IDENTITY_ASSERTER_TYPE)
            self.logger.exiting(class_name=self.__class_name, method_name=_method_name)
            return

        atn_names = atn_providers.keys()
        if atn_names[0] == DEFAULT_AUTHENTICATOR_NAME:
            default_authenticator = atn_providers[DEFAULT_AUTHENTICATOR_NAME]
            type_keys = default_authenticator.keys()
            if len(type_keys) == 0 or (len(type_keys) == 1 and type_keys[0] == DEFAULT_AUTHENTICATOR_TYPE):
                delete_default_authenticator = False
            else:
                delete_default_authenticator = True
        else:
            delete_default_authenticator = True

        if len(atn_names) > 1 and atn_names[1] == DEFAULT_IDENTITY_ASSERTER_NAME:
            default_identity_asserter = atn_providers
            type_keys = default_identity_asserter.keys()
            if len(type_keys) == 0 or (len(type_keys) == 1 and type_keys[0] == DEFAULT_IDENTITY_ASSERTER_TYPE):
                delete_default_identity_asserter = False
            else:
                delete_default_identity_asserter = True
        else:
            delete_default_identity_asserter = True

        if delete_default_authenticator:
            if self.__fix_default_authentication_provider_names:
                name = 'Provider'
            else:
                name = DEFAULT_AUTHENTICATOR_NAME
            self.__delete_provider(base_location, name, AUTHENTICATION_PROVIDER)
        elif self.__fix_default_authentication_provider_names:
            # delete and recreate the default authenticator with the correct name now.
            self.__delete_and_recreate_provider(base_location, 'Provider', DEFAULT_AUTHENTICATOR_NAME,
                                                AUTHENTICATION_PROVIDER, DEFAULT_AUTHENTICATOR_TYPE)

        if delete_default_identity_asserter:
            if self.__fix_default_authentication_provider_names:
                name = 'Provider'
            else:
                name = DEFAULT_IDENTITY_ASSERTER_NAME
            self.__delete_provider(base_location, name, AUTHENTICATION_PROVIDER)
            self.__fix_up_model_default_identity_asserter(base_location, DEFAULT_IDENTITY_ASSERTER_NAME,
                                                          AUTHENTICATION_PROVIDER, DEFAULT_IDENTITY_ASSERTER_TYPE,
                                                          atn_providers)
        elif self.__fix_default_authentication_provider_names:
            # delete and recreate the default identity asserter with the correct name now.
            self.__delete_and_recreate_provider(base_location, 'Provider', DEFAULT_IDENTITY_ASSERTER_NAME,
                                                AUTHENTICATION_PROVIDER, DEFAULT_IDENTITY_ASSERTER_TYPE)
            self.__set_default_identity_aserter_attributes(base_location, DEFAULT_IDENTITY_ASSERTER_NAME,
                                                           AUTHENTICATION_PROVIDER, DEFAULT_IDENTITY_ASSERTER_TYPE)

        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return

    def __handle_default_authorizers(self, base_location, authorization_providers):
        if authorization_providers is None or len(authorization_providers) == 0 or DEFAULT_AUTHORIZER_NAME is None:
            return

        if self.__need_to_delete_default_provider(authorization_providers, DEFAULT_AUTHORIZER_NAME,
                                                  DEFAULT_AUTHORIZER_TYPE):
            self.__delete_provider(base_location, DEFAULT_AUTHORIZER_NAME, AUTHORIZER)
        return

    def __handle_default_cert_path_providers(self, base_location, cert_path_providers):
        if cert_path_providers is None or len(cert_path_providers) == 0 or DEFAULT_CERT_PATH_PROVIDER_NAME is None:
            return

        if self.__need_to_delete_default_provider(cert_path_providers, DEFAULT_CERT_PATH_PROVIDER_NAME,
                                                  DEFAULT_CERT_PATH_PROVIDER_TYPE):
            self.__delete_provider(base_location, DEFAULT_CERT_PATH_PROVIDER_NAME, CERT_PATH_PROVIDER)
        return

    def __handle_default_credential_mappers(self, base_location, credential_mapping_providers):
        if credential_mapping_providers is None or len(credential_mapping_providers) == 0 or \
                DEFAULT_CREDENTIAL_MAPPER_NAME is None:
            return

        if self.__need_to_delete_default_provider(credential_mapping_providers, DEFAULT_CREDENTIAL_MAPPER_NAME,
                                                  DEFAULT_CREDENTIAL_MAPPER_TYPE):
            self.__delete_provider(base_location, DEFAULT_CREDENTIAL_MAPPER_NAME, CREDENTIAL_MAPPER)
        return

    def __handle_default_password_validators(self, base_location, password_validation_providers):
        if password_validation_providers is None or len(password_validation_providers) == 0 or \
                DEFAULT_PASSWORD_VALIDATOR_NAME is None:
            return

        if self.__need_to_delete_default_provider(password_validation_providers, DEFAULT_PASSWORD_VALIDATOR_NAME,
                                                  DEFAULT_PASSWORD_VALIDATOR_TYPE):
            self.__delete_provider(base_location, DEFAULT_PASSWORD_VALIDATOR_NAME, PASSWORD_VALIDATOR)
        return

    def __handle_default_role_mappers(self, base_location, role_mapping_providers):
        if role_mapping_providers is None or len(role_mapping_providers) == 0 or DEFAULT_ROLE_MAPPER_NAME is None:
            return

        if self.__need_to_delete_default_provider(role_mapping_providers, DEFAULT_ROLE_MAPPER_NAME,
                                                  DEFAULT_ROLE_MAPPER_TYPE):
            self.__delete_provider(base_location, DEFAULT_ROLE_MAPPER_NAME, ROLE_MAPPER)
        return

    def __need_to_delete_default_provider(self, providers_dict, default_name, default_type):
        provider_names = providers_dict.keys()
        if provider_names[0] == default_name:
            default_provider = providers_dict[default_name]
            type_keys = default_provider.keys()
            if len(type_keys) == 0 or (len(type_keys) == 1 and type_keys[0] == default_type):
                delete_default_provider = False
            else:
                delete_default_provider = True
        else:
            delete_default_provider = True
        return delete_default_provider

    def __delete_provider(self, base_location, model_name, model_base_type):
        location = LocationContext(base_location).append_location(model_base_type)
        token_name = self.alias_helper.get_name_token(location)
        if token_name is not None:
            location.add_name_token(token_name, model_name)

        wlst_create_path = self.alias_helper.get_wlst_create_path(location)
        wlst_type, wlst_name = self.alias_helper.get_wlst_mbean_type_and_name(location)
        self.wlst_helper.cd(wlst_create_path)
        self.wlst_helper.delete(wlst_name, wlst_type)
        return

    def __delete_and_recreate_provider(self, base_location, old_wlst_name, model_name, model_base_type, model_subtype):
        self.__delete_provider(base_location, old_wlst_name, model_base_type)

        location = LocationContext(base_location).append_location(model_base_type)
        token_name = self.alias_helper.get_name_token(location)
        if token_name is not None:
            location.add_name_token(token_name, model_name)

        wlst_create_path = self.alias_helper.get_wlst_create_path(location)
        wlst_base_type, wlst_name = self.alias_helper.get_wlst_mbean_type_and_name(location)
        location.append_location(model_subtype)
        wlst_type = self.alias_helper.get_wlst_mbean_type(location)
        self.wlst_helper.cd(wlst_create_path)
        self.wlst_helper.create(wlst_name, wlst_type, wlst_base_type)
        return

    def __set_default_identity_aserter_attributes(self, base_location, model_name, model_base_type, model_subtype):
        location = LocationContext(base_location).append_location(model_base_type)
        token_name = self.alias_helper.get_name_token(location)
        if token_name is not None:
            location.add_name_token(token_name, model_name)
        location.append_location(model_subtype)

        wlst_attribute_path = self.alias_helper.get_wlst_attributes_path(location)
        default_value = self.alias_helper.get_model_attribute_default_value(location, ACTIVE_TYPE)
        wlst_name = self.alias_helper.get_wlst_attribute_name(location, ACTIVE_TYPE)
        self.wlst_helper.cd(wlst_attribute_path)
        self.wlst_helper.set(wlst_name, default_value)
        return

    #
    # Since we are allowing the provider to be recreated, if needed, from the model,
    # we need to add the ActiveType attribute to the model if and only if no
    # attributes are specified in the model.
    #
    def __fix_up_model_default_identity_asserter(self, base_location, model_name, model_base_type,
                                                 model_subtype, atn_providers):
        if atn_providers is not None and DEFAULT_IDENTITY_ASSERTER_NAME in atn_providers:
            default_identity_asserter = \
                dictionary_utils.get_dictionary_element(atn_providers, DEFAULT_IDENTITY_ASSERTER_NAME)
            if DEFAULT_IDENTITY_ASSERTER_TYPE in default_identity_asserter:
                subtype_dict = dictionary_utils.get_dictionary_element(default_identity_asserter,
                                                                       DEFAULT_IDENTITY_ASSERTER_TYPE)
                if len(subtype_dict) == 0:
                    location = LocationContext(base_location).append_location(model_base_type)
                    token_name = self.alias_helper.get_name_token(location)
                    if token_name is not None:
                        location.add_name_token(token_name, model_name)
                    location.append_location(model_subtype)

                    default_value = self.alias_helper.get_model_attribute_default_value(location, ACTIVE_TYPE)
                    subtype_dict[ACTIVE_TYPE] = default_value
        return

    def _check_coherence_cluster_references(self, named_nodes, location):
        """
        If a named element has the Coherence cluster system resource attribute, confirm that the resource exists.
        If the resource does not exist, create a placeholder resource to allow assignment.
        :param named_nodes: a dictionary containing the named model elements
        :param location: the location of the cluster
        :return:
        """
        for name in named_nodes:
            child_nodes = dictionary_utils.get_dictionary_element(named_nodes, name)
            resource_name = dictionary_utils.get_element(child_nodes, COHERENCE_CLUSTER_SYSTEM_RESOURCE)
            if resource_name is not None:
                self._create_placeholder_coherence_cluster(resource_name)

    def _create_placeholder_coherence_cluster(self, cluster_name):
        """
        Create a placeholder Coherence cluster system resource to be referenced from a topology element.
        The new cluster will be created at the root domain level.
        Clusters referenced from the model's resources section should not require placeholder entries.
        :param cluster_name: the name of the Coherence cluster system resource to be added
        """
        _method_name = '_create_placeholder_coherence_cluster'
        original_location = self.wlst_helper.get_pwd()
        cluster_location = LocationContext().append_location(COHERENCE_CLUSTER_SYSTEM_RESOURCE)
        existing_names = deployer_utils.get_existing_object_list(cluster_location, self.alias_helper)

        if cluster_name not in existing_names:
            self.logger.info('WLSDPLY-12230', cluster_name, class_name=self.__class_name, method_name=_method_name)

        cluster_token = self.alias_helper.get_name_token(cluster_location)
        cluster_location.add_name_token(cluster_token, cluster_name)
        deployer_utils.create_and_cd(cluster_location, existing_names, self.alias_helper)

        self.wlst_helper.cd(original_location)
