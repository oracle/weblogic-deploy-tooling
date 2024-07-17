"""
Copyright (c) 2017, 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import os

from java.io import FileOutputStream
from java.util import Properties
from oracle.weblogic.deploy.create import CreateDomainLifecycleHookScriptRunner
from weblogic.security.internal import SerializedSystemIni
from weblogic.security.internal.encryption import ClearOrEncryptedService

from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import ADMIN_PASSWORD
from wlsdeploy.aliases.model_constants import ADMIN_SERVER_NAME
from wlsdeploy.aliases.model_constants import ADMIN_USERNAME
from wlsdeploy.aliases.model_constants import APP_DIR
from wlsdeploy.aliases.model_constants import CLUSTER
from wlsdeploy.aliases.model_constants import CREATE_ONLY_DOMAIN_ATTRIBUTES
from wlsdeploy.aliases.model_constants import DEFAULT_ADMIN_SERVER_NAME
from wlsdeploy.aliases.model_constants import DEFAULT_WLS_DOMAIN_NAME
from wlsdeploy.aliases.model_constants import DOMAIN_INFO
from wlsdeploy.aliases.model_constants import DOMAIN_NAME
from wlsdeploy.aliases.model_constants import ENABLE_JMS_DB_PERSISTENCE
from wlsdeploy.aliases.model_constants import ENABLE_JTALOG_DB_PERSISTENCE
from wlsdeploy.aliases.model_constants import FRONTEND_HOST
from wlsdeploy.aliases.model_constants import LISTEN_PORT
from wlsdeploy.aliases.model_constants import LOG_FILTER
from wlsdeploy.aliases.model_constants import MACHINE
from wlsdeploy.aliases.model_constants import MIGRATABLE_TARGET
from wlsdeploy.aliases.model_constants import NAME
from wlsdeploy.aliases.model_constants import OPSS_SECRETS
from wlsdeploy.aliases.model_constants import OPSS_WALLET_PASSPHRASE
from wlsdeploy.aliases.model_constants import PARTITION
from wlsdeploy.aliases.model_constants import PASSWORD
from wlsdeploy.aliases.model_constants import PRODUCTION_MODE_ENABLED
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
from wlsdeploy.aliases.model_constants import USER
from wlsdeploy.aliases.model_constants import USE_SAMPLE_DATABASE
from wlsdeploy.aliases.model_constants import VIRTUAL_TARGET
from wlsdeploy.aliases.model_constants import WEB_SERVICE_SECURITY
from wlsdeploy.aliases.model_constants import WLS_USER_PASSWORD_CREDENTIAL_MAPPINGS
from wlsdeploy.aliases.model_constants import WS_RELIABLE_DELIVERY_POLICY
from wlsdeploy.aliases.model_constants import XML_ENTITY_CACHE
from wlsdeploy.aliases.model_constants import XML_REGISTRY
from wlsdeploy.aliases.validation_codes import ValidationCodes
from wlsdeploy.exception import exception_helper
from wlsdeploy.exception.exception_types import ExceptionType
from wlsdeploy.tool.create import opss_helper
from wlsdeploy.tool.create.creator import Creator
from wlsdeploy.tool.create.domain_typedef import POST_CREATE_DOMAIN_LIFECYCLE_HOOK
from wlsdeploy.tool.create.security_provider_creator import SecurityProviderCreator
from wlsdeploy.tool.create.wlspolicies_helper import WLSPolicies
from wlsdeploy.tool.create.wlsroles_helper import WLSRoles
from wlsdeploy.tool.deploy import deployer_utils
from wlsdeploy.tool.deploy.model_deployer import ModelDeployer
from wlsdeploy.tool.util.archive_helper import ArchiveList
from wlsdeploy.tool.util.credential_map_helper import CredentialMapHelper
from wlsdeploy.tool.util.default_authenticator_helper import DefaultAuthenticatorHelper
from wlsdeploy.tool.util.library_helper import LibraryHelper
from wlsdeploy.tool.util.rcu_helper import RCUHelper
from wlsdeploy.tool.util.saml2_security_helper import Saml2SecurityHelper
from wlsdeploy.tool.util.target_helper import TargetHelper
from wlsdeploy.tool.util.targeting_types import TargetingType
from wlsdeploy.tool.util.topology_helper import TopologyHelper
from wlsdeploy.tool.util.topology_profiles import TopologyProfile
from wlsdeploy.util import dictionary_utils
from wlsdeploy.util import model
from wlsdeploy.util import model_helper
from wlsdeploy.util import string_utils
from wlsdeploy.util import unicode_helper as str_helper

POST_CREATE_DOMAIN_LOG_BASENAME = 'postCreateDomainScript'


class DomainCreator(Creator):
    """
    The class that drives domain creation.
    """
    __program_name = 'createDomain'
    __class_name = 'DomainCreator'

    def __init__(self, model_dictionary, model_context, aliases):
        _method_name = '__init__'
        Creator.__init__(self, model_dictionary, model_context, aliases)

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

        # domain_home has already been corrected in model context if -domain_parent was used
        self._domain_home = self.model_context.get_domain_home()

        self.model_deployer = ModelDeployer(self.model, model_context, aliases)

        if ADMIN_SERVER_NAME in self._topology:
            self._admin_server_name = self._topology[ADMIN_SERVER_NAME]
        else:
            self._admin_server_name = DEFAULT_ADMIN_SERVER_NAME

        self.__default_domain_name = None
        self.__default_admin_server_name = None

        archive_file_name = self.model_context.get_archive_file_name()
        if archive_file_name is not None:
            self.archive_helper = ArchiveList(archive_file_name, self.model_context,
                                              exception_helper.ExceptionType.CREATE)

        self.library_helper = LibraryHelper(self.model, self.model_context, self.aliases, self._domain_home,
                                            ExceptionType.CREATE, self.logger)

        self.target_helper = TargetHelper(self.model, self.model_context, self.aliases, ExceptionType.CREATE,
                                          self.logger)

        self.rcu_helper = RCUHelper(self.model, self.archive_helper, self.model_context, self.aliases)

        self.wls_roles_helper = WLSRoles(self._domain_info, self._domain_home, self.model_context,
                                         ExceptionType.CREATE, self.logger, archive_helper=self.archive_helper)
        self.wls_policies_helper = WLSPolicies(self._domain_info, self.model_context, self.logger,
                                               archive_helper=self.archive_helper)

    def create(self):
        """
        The create() method triggers domain creation.
        :raises CreateException: if domain creation fails
        :raises DeployException: if resource and application deployment fails
        """
        _method_name = 'create'
        self.logger.entering(class_name=self.__class_name, method_name=_method_name)

        self.__fail_mt_1221_domain_creation()

        # run RCU or pre-check connectivity
        self.rcu_helper.check_or_run_rcu()

        self.__create_domain()
        self.__deploy()
        self.__deploy_after_update()
        self.__create_boot_dot_properties()
        self.__create_credential_mappings()
        self.__install_saml2_security_files()

        self.rcu_helper.fix_jps_config()
        self.__run_post_create_domain_script()

        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)

    ####################
    # OVERRIDE METHODS
    ####################

    # Override
    def _set_attributes(self, location, model_nodes):
        model_type, model_name = self.aliases.get_model_type_and_name(location)
        if model_type == CLUSTER:
            if FRONTEND_HOST in model_nodes:
                model_value = model_nodes[FRONTEND_HOST]
                Creator._set_attribute(self, location, FRONTEND_HOST, model_value, list())
        Creator._set_attributes(self, location, model_nodes)

    # Override
    def _create_named_mbeans(self, type_name, model_nodes, base_location, log_created=False, delete_now=True):
        """
        Override default behavior to create placeholders for referenced Coherence clusters.
        :param type_name: the model folder type
        :param model_nodes: the model dictionary of the specified model folder type
        :param base_location: the base location object to use to create the MBeans
        :param log_created: whether to log created at INFO level, by default it is logged at the FINE level
        :raises: CreateException: if an error occurs
        """
        self.topology_helper.check_coherence_cluster_references(type_name, model_nodes)
        # continue with regular processing

        Creator._create_named_mbeans(self, type_name, model_nodes, base_location, log_created=log_created, delete_now=delete_now)

    # Override
    def _create_mbean(self, type_name, model_nodes, base_location, log_created=False):
        Creator._create_mbean(self, type_name, model_nodes, base_location, log_created)

        # check for file paths that need to be qualified
        self.topology_helper.qualify_nm_properties(type_name, model_nodes, base_location, self.model_context,
                                                   self.attribute_setter)

    ####################
    # PRIVATE METHODS
    ####################

    def __fail_mt_1221_domain_creation(self):
        """
        Abort create if domain contains MT artifacts that cannot be created in the version of WLST offline being used
        or if the version of WebLogic no longer supports MT.
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
            if not self.wls_helper.is_mt_provisioning_supported():
                ex = exception_helper.create_create_exception('WLSDPLY-12254', self.wls_helper.wl_version)
            else:
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

        if self.wls_helper.is_select_template_supported():
            self.__create_base_domain_with_select_template(self._domain_home)
            self.__extend_domain_with_select_template(self._domain_home)
        else:
            self.__create_base_domain(self._domain_home)
            self.__extend_domain(self._domain_home)

        if len(self.files_to_extract_from_archive) > 0:
            for file_to_extract in self.files_to_extract_from_archive:
                # extract path may differ from archive path, such as config/wlsdeploy/*
                destination_path = self.topology_helper.get_archive_extract_path(file_to_extract)
                destination_directory = self.topology_helper.get_archive_extract_directory(destination_path,
                                                                                           self._domain_home)
                self.archive_helper.extract_file(file_to_extract, destination_directory)

        self.library_helper.install_domain_libraries()
        self.library_helper.extract_classpath_libraries()
        self.library_helper.install_domain_scripts()
        self.wls_roles_helper.process_roles()
        self.wls_policies_helper.process_policies()

        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return

    def __deploy(self):
        """
        Update the domain with domain attributes, resources and deployments.
        Check for the correct method of updating the domain for creation.
        :raises: CreateException: if an error occurs while reading or updating the domain.
        """
        self.model_context.set_domain_home(self._domain_home)
        self.__set_domain_attributes()
        self.__configure_security_configuration()
        self.__deploy_resources_and_apps()
        self.wlst_helper.update_domain()
        self.wlst_helper.close_domain()

        return

    def __deploy_after_update(self):
        _method_name = '__deploy_after_update'
        self.logger.entering(class_name=self.__class_name, method_name=_method_name)
        self.model_deployer.deploy_model_after_update()
        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def __deploy_resources_and_apps(self):
        """
        Deploy the resources and applications.
        :raises: DeployException: if an error occurs while deploy the resources or applications
        """
        _method_name = '__deploy_resources_and_apps'

        self.logger.entering(class_name=self.__class_name, method_name=_method_name)
        self.model_deployer.deploy_resources_and_apps_for_create()
        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)

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
        self.__set_core_domain_params()

        self.logger.info('WLSDPLY-12205', self._domain_name, domain_home,
                         class_name=self.__class_name, method_name=_method_name)
        self.wlst_helper.write_domain(domain_home)

        self.logger.info('WLSDPLY-12206', self._domain_name, class_name=self.__class_name, method_name=_method_name)
        self.wlst_helper.close_template()
        self.wlst_helper.read_domain(domain_home)
        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def __extend_domain(self, domain_home):
        """
        Extend the base domain with extension templates, as needed, for versions of WebLogic Server prior to 12.2.1.
        :param domain_home: the domain home directory
        :raises: CreateException: if an error occurs
        """
        _method_name = '__extend_domain'

        self.logger.entering(domain_home, class_name=self.__class_name, method_name=_method_name)

        extension_templates = self._domain_typedef.get_extension_templates()
        custom_templates = self._domain_typedef.get_custom_extension_templates()
        # if (len(extension_templates) == 0) and (len(custom_templates) == 0):
        #     return

        self.logger.info('WLSDPLY-12207', self._domain_name, domain_home,
                         class_name=self.__class_name, method_name=_method_name)
        self.__set_app_dir()

        for extension_template in extension_templates:
            self.logger.info('WLSDPLY-12208', extension_template,
                             class_name=self.__class_name, method_name=_method_name)
            self.wlst_helper.add_template(extension_template)

        for custom_template in custom_templates:
            self.logger.info('WLSDPLY-12246', custom_template,
                             class_name=self.__class_name, method_name=_method_name)
            self.wlst_helper.add_template(custom_template)

        topology_folder_list = self.aliases.get_model_topology_top_level_folder_names()
        topology_folder_list.remove(SECURITY)

        resources_dict = self.model.get_model_resources()
        jdbc_names = self.topology_helper.create_placeholder_jdbc_resources(resources_dict)
        self.__create_mbeans_used_by_topology_mbeans(topology_folder_list)
        self.__create_machines_clusters_and_servers(delete_now=False)
        fmw_ds_names = self.rcu_helper.configure_fmw_infra_database()

        if self.wls_helper.is_set_server_groups_supported():
            # 12c versions set server groups directly
            server_groups_to_target = self._domain_typedef.get_server_groups_to_target()
            self.target_helper.target_server_groups_to_servers(server_groups_to_target)

        elif self._domain_typedef.has_jrf_with_database_store() or \
                (self._domain_typedef.get_targeting() == TargetingType.APPLY_JRF):
            # for 11g, if template list includes JRF, or if specified in domain typedef, use applyJRF
            self.target_helper.target_jrf_groups_to_clusters_servers()

        self.logger.info('WLSDPLY-12209', self._domain_name,
                         class_name=self.__class_name, method_name=_method_name)

        # targets may have been inadvertently assigned when clusters were added
        self.topology_helper.clear_jdbc_placeholder_targeting(jdbc_names)

        # This is a second pass. We will not do a third pass after extend templates
        # as it would require a updatedomain and reopen. If reported, revisit this
        # known issue
        self.__apply_base_domain_config(topology_folder_list, fmw_ds_names, delete=True)
        self.__create_security_folder()
        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def __create_base_domain_with_select_template(self, domain_home):
        """
        Create and extend the domain, as needed, for WebLogic Server versions 12.2.1 and above.
        :param domain_home: the domain home directory
        :raises: CreateException: if an error occurs
        """
        _method_name = '__create_base_domain_with_select_template'

        self.logger.entering(domain_home, class_name=self.__class_name, method_name=_method_name)

        topology_profile = self._domain_typedef.get_topology_profile()
        if topology_profile in TopologyProfile:
            self.logger.info('WLSDPLY-12269', topology_profile, class_name=self.__class_name, method_name=_method_name)
            self.wlst_helper.set_topology_profile(topology_profile)

        base_template = self._domain_typedef.get_base_template()
        self.logger.info('WLSDPLY-12210', base_template,
                         class_name=self.__class_name, method_name=_method_name)

        self.wlst_helper.select_template(base_template)

        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def __extend_domain_with_select_template(self, domain_home):
        """
        Create and extend the domain, as needed, for WebLogic Server versions 12.2.1 and above.
        :param domain_home: the domain home directory
        :raises: CreateException: if an error occurs
        """
        _method_name = '__extend_domain_with_select_template'

        self.logger.entering(domain_home, class_name=self.__class_name, method_name=_method_name)

        extension_templates = self._domain_typedef.get_extension_templates()
        custom_templates = self._domain_typedef.get_custom_extension_templates()

        for extension_template in extension_templates:
            self.logger.info('WLSDPLY-12211', extension_template,
                             class_name=self.__class_name, method_name=_method_name)
            self.wlst_helper.select_template(extension_template)

        for custom_template in custom_templates:
            self.logger.info('WLSDPLY-12245', custom_template,
                             class_name=self.__class_name, method_name=_method_name)
            self.wlst_helper.select_custom_template(custom_template)

        self.logger.info('WLSDPLY-12212', class_name=self.__class_name, method_name=_method_name)
        self.wlst_helper.load_templates()

        self.__set_core_domain_params()
        self.__set_app_dir()

        self.__enable_jms_db_persistence_if_set()
        self.__enable_jta_tlog_db_persistence_if_set()

        fmw_ds_names = []
        if len(extension_templates) > 0:
            fmw_ds_names = self.rcu_helper.configure_fmw_infra_database()
            self.__configure_opss_wallet_and_passphrase()

        topology_folder_list = self.aliases.get_model_topology_top_level_folder_names()
        topology_folder_list.remove(SECURITY)

        resources_dict = self.model.get_model_resources()
        jdbc_names = self.topology_helper.create_placeholder_jdbc_resources(resources_dict)
        self.__create_mbeans_used_by_topology_mbeans(topology_folder_list)
        self.__create_machines_clusters_and_servers(delete_now=False)

        server_groups_to_target = self._domain_typedef.get_server_groups_to_target()
        dynamic_cluster_server_groups_to_target = self._domain_typedef.get_dynamic_cluster_server_groups()
        server_assigns = self.target_helper.target_server_groups_to_servers(server_groups_to_target)
        dynamic_assigns = \
            self.target_helper.target_server_groups_to_dynamic_clusters(dynamic_cluster_server_groups_to_target)

        if len(server_assigns) > 0:
            self.target_helper.target_server_groups(server_assigns)

        if len(dynamic_assigns) > 0:
            self.target_helper.target_dynamic_server_groups(dynamic_assigns)

        # targets may have been inadvertently assigned when clusters were added
        self.topology_helper.clear_jdbc_placeholder_targeting(jdbc_names)

        self.__apply_base_domain_config(topology_folder_list, fmw_ds_names, delete=True)

        # apply OPSS configuration before the first domain write
        opss_helper.create_credentials(self.model.get_model(), self.model_context, self.aliases, self.wlst_helper)

        self.logger.info('WLSDPLY-12205', self._domain_name, domain_home,
                         class_name=self.__class_name, method_name=_method_name)
        self.wlst_helper.write_domain(domain_home)
        self.wlst_helper.close_template()
        self.logger.info('WLSDPLY-12206', self._domain_name, domain_home,
                         class_name=self.__class_name, method_name=_method_name)
        self.wlst_helper.read_domain(domain_home)
        # Third pass will perform No deletes, set the attributes again.This will address the
        # problem where a template's final.py overwrites attributes during the
        # write domain. This will allow the model value to take precedence over the final.py
        if len(extension_templates) > 0:
            self.__apply_base_domain_config(topology_folder_list, fmw_ds_names, delete=False)
        self.__create_security_folder()

        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def __apply_base_domain_config(self, topology_folder_list, fmw_ds_names, delete=True):
        """
        Apply the base domain configuration from the model topology section.
        This will be done in pass two and three of dealing with topology objects
        :param topology_folder_list: the model topology folder list to process
        :param fmw_ds_names: a list of FMW template default data source names
        :param delete: If the pass will do deletes
        :raises: CreateException: if an error occurs
        """
        _method_name = '__apply_base_domain_config'

        self.logger.entering(topology_folder_list, class_name=self.__class_name, method_name=_method_name)
        self.logger.fine('WLSDPLY-12219', class_name=self.__class_name, method_name=_method_name)

        topology_local_list = list(topology_folder_list)
        location = LocationContext()
        domain_name_token = self.aliases.get_name_token(location)
        location.add_name_token(domain_name_token, self._domain_name)

        topology_local_list.remove(SECURITY_CONFIGURATION)

        self.__create_reliable_delivery_policy(location)
        topology_local_list.remove(WS_RELIABLE_DELIVERY_POLICY)

        # the second pass will re-establish any attributes that were changed by templates,
        # and process deletes and re-adds of named elements in the model order.
        # the third pass will re-establish any attributes that were changed by templates, but will
        # not perform any deletes. re-adds will occur if for some reason they had an add with a delete
        # after, but this is not a scenario we are considering
        self.__create_machines_clusters_and_servers(delete_now=delete)
        topology_local_list.remove(MACHINE)
        topology_local_list.remove(UNIX_MACHINE)
        topology_local_list.remove(CLUSTER)
        if SERVER_TEMPLATE in topology_local_list:
            topology_local_list.remove(SERVER_TEMPLATE)
        topology_local_list.remove(SERVER)
        topology_local_list.remove(MIGRATABLE_TARGET)

        self.__create_other_domain_artifacts(location, topology_local_list)

        self.rcu_helper.reset_fmw_template_data_source_defaults_from_model(fmw_ds_names)

        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)

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

        if USE_SAMPLE_DATABASE in self._domain_info:
            use_sample_db = self._domain_info[USE_SAMPLE_DATABASE]
            if not isinstance(use_sample_db, basestring):
                use_sample_db = str_helper.to_string(use_sample_db)
            self.wlst_helper.set_option_if_needed(USE_SAMPLE_DATABASE, use_sample_db)

        self.__set_domain_name()
        self.__set_admin_password()
        self.__set_admin_server_name()

        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def __create_mbeans_used_by_topology_mbeans(self, topology_folder_list):
        """
        Create the entities that are referenced by domain, machine, server and server template attributes.
        :param topology_folder_list: the model topology folder list to process
        :raises: CreateException: if an error occurs
        """
        _method_name = '__create_mbeans_used_by_topology_mbeans'
        location = LocationContext()
        domain_name_token = self.aliases.get_name_token(location)
        location.add_name_token(domain_name_token, self._domain_name)

        self.logger.entering(str_helper.to_string(location), class_name=self.__class_name, method_name=_method_name)
        self.__create_log_filters(location)
        topology_folder_list.remove(LOG_FILTER)

        self.__create_xml_entity_cache(location)
        topology_folder_list.remove(XML_ENTITY_CACHE)
        self.__create_xml_registry(location)
        topology_folder_list.remove(XML_REGISTRY)

        self.__create_ws_security(location)
        topology_folder_list.remove(WEB_SERVICE_SECURITY)

    def __create_security_folder(self):
        """
        Create the security objects if any. The security information
        from the model will be writing to the DefaultAuthenticatorInit.ldift file
        :raises: CreateException: if an error occurs
        """
        _method_name = '__create_security_folder'
        self.logger.entering(class_name=self.__class_name, method_name=_method_name)
        security_folder = dictionary_utils.get_dictionary_element(self._topology, SECURITY)
        if security_folder is not None:
            admin_credentials = {
                'user': dictionary_utils.get_element(self._domain_info, ADMIN_USERNAME),
                'password': dictionary_utils.get_element(self._domain_info, ADMIN_PASSWORD)
            }
            using_password_digests = self.security_provider_creator.is_default_authenticator_password_digest_enabled()
            helper = DefaultAuthenticatorHelper(self.model_context, self.aliases, ExceptionType.CREATE,
                                                using_password_digests)
            helper.create_default_init_file(security_folder, admin_credentials)
        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def __create_log_filters(self, location):
        """
        Create the /LogFilter objects if any for use in the logs of the base components like domain and server
        :param location: the location to use
        :raises: CreateException: if an error occurs
        """
        _method_name = '__create_log_filters'

        self.logger.entering(str_helper.to_string(location), class_name=self.__class_name, method_name=_method_name)
        log_filter_nodes = dictionary_utils.get_dictionary_element(self._topology, LOG_FILTER)

        if len(log_filter_nodes) > 0:
            self._create_named_mbeans(LOG_FILTER, log_filter_nodes, location, log_created=True)
        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def __create_reliable_delivery_policy(self, location):
        """
        Create the /WSReliableDeliverPolicy objects if any for use by the server and server templates.
        :param location: the location to use
        :raises: CreateException: if an error occurs
        """
        _method_name = '__create_reliable_delivery_policy'

        self.logger.entering(str_helper.to_string(location), class_name=self.__class_name, method_name=_method_name)
        policy_nodes = dictionary_utils.get_dictionary_element(self._topology, WS_RELIABLE_DELIVERY_POLICY)

        if len(policy_nodes) > 0:
            self._create_named_mbeans(WS_RELIABLE_DELIVERY_POLICY, policy_nodes, location, log_created=True)
        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def __create_xml_entity_cache(self, location):
        """
        Create the /XMLEntityCache objects if any for use by the server and server templates.
        :param location: the location to use
        :raises: CreateException: if an error occurs
        """
        _method_name = '__create_xml_entity_cache'

        self.logger.entering(str_helper.to_string(location), class_name=self.__class_name, method_name=_method_name)
        cache_nodes = dictionary_utils.get_dictionary_element(self._topology, XML_ENTITY_CACHE)

        if len(cache_nodes) > 0:
            self._create_named_mbeans(XML_ENTITY_CACHE, cache_nodes, location, log_created=True)
        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def __create_xml_registry(self, location):
        """
        Create the /XMLRegistry objects if any for use by the server and server templates.
        :param location: the location to use
        :raises: CreateException: if an error occurs
        """
        _method_name = '__create_xml_registry'

        self.logger.entering(str_helper.to_string(location), class_name=self.__class_name, method_name=_method_name)
        registry_nodes = dictionary_utils.get_dictionary_element(self._topology, XML_REGISTRY)

        if len(registry_nodes) > 0:
            self._create_named_mbeans(XML_REGISTRY, registry_nodes, location, log_created=True)
        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def __create_ws_security(self, location):
        """
        Create the WebserviceSecurity objects, if any.
        :param location: the current location
        """
        _method_name = '__create_ws_security'
        self.logger.entering(str_helper.to_string(location), class_name=self.__class_name, method_name=_method_name)
        ws_security = dictionary_utils.get_dictionary_element(self._topology, WEB_SERVICE_SECURITY)

        if len(ws_security) > 0:
            self._create_named_mbeans(WEB_SERVICE_SECURITY, ws_security, location, log_created=True)
        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def __create_machines(self, location, delete_now=True):
        """
        Create the /Machine and /UnixMachine folder objects, if any.
        :param location: the location to use
        :raises: CreateException: if an error occurs
        """
        _method_name = '__create_machines'

        self.logger.entering(str_helper.to_string(location), class_name=self.__class_name, method_name=_method_name)
        machine_nodes = dictionary_utils.get_dictionary_element(self._topology, MACHINE)
        unix_machine_nodes = dictionary_utils.get_dictionary_element(self._topology, UNIX_MACHINE)

        if len(machine_nodes) > 0:
            self._create_named_mbeans(MACHINE, machine_nodes, location, log_created=True, delete_now=delete_now)
        if len(unix_machine_nodes) > 0:
            self._create_named_mbeans(UNIX_MACHINE, unix_machine_nodes, location, log_created=True,
                                      delete_now=delete_now)
        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def __create_machines_clusters_and_servers(self, delete_now=True):
        """
        Create the /Cluster, /ServerTemplate, and /Server folder objects.
        :param delete_now: Flag determining whether the delete of the elements will be delayed
        :raises: CreateException: if an error occurs
        """
        _method_name = '__create_machines_clusters_and_servers'

        location = LocationContext()
        domain_name_token = self.aliases.get_name_token(location)
        location.add_name_token(domain_name_token, self._domain_name)
        self.logger.entering(str_helper.to_string(location), class_name=self.__class_name, method_name=_method_name)

        self.__create_machines(location, delete_now=delete_now)
        #
        # In order for source domain provisioning to work with dynamic clusters, we have to provision
        # the ServerTemplates.  There is a cyclical dependency between Server Template and Clusters so we
        # need for the ServerTemplates to exist before create clusters.  Once the clusters are provisioned,
        # then we can fully populate the ServerTemplates.
        #
        self.topology_helper.create_placeholder_server_templates(self._topology)

        # create placeholders for JDBC resources that may be referenced in cluster definition.

        cluster_nodes = dictionary_utils.get_dictionary_element(self._topology, CLUSTER)
        if len(cluster_nodes) > 0:
            self._create_named_mbeans(CLUSTER, cluster_nodes, location, log_created=True, delete_now=delete_now)

        #
        # Now, fully populate the ServerTemplates, if any.
        #
        server_template_nodes = dictionary_utils.get_dictionary_element(self._topology, SERVER_TEMPLATE)

        if len(server_template_nodes) > 0:
            self._create_named_mbeans(SERVER_TEMPLATE, server_template_nodes, location, log_created=True,
                                      delete_now=delete_now)


        #
        # Finally, create/update the servers.
        #
        server_nodes = dictionary_utils.get_dictionary_element(self._topology, SERVER)
        # There may be a dependency to other servers when the server is in a cluster
        self.topology_helper.create_placeholder_servers_in_cluster(self._topology)
        if len(server_nodes) > 0:
            self._create_named_mbeans(SERVER, server_nodes, location, log_created=True, delete_now=delete_now)

        # Work around for bug in WLST where Server Template Listen Port must be set after Server
        # Listen Port for 7001 in order to show up in the config.xml
        if len(server_template_nodes) > 0:
            for template in server_template_nodes:
                listen_port = dictionary_utils.get_element(self._topology[SERVER_TEMPLATE][template], LISTEN_PORT)
                if listen_port is not None:
                    temp_loc = LocationContext()
                    temp_loc.append_location(SERVER_TEMPLATE)
                    temp_loc.add_name_token(self.aliases.get_name_token(temp_loc), template)
                    attribute_path = self.aliases.get_wlst_attributes_path(temp_loc)

                    self.wlst_helper.cd(attribute_path)
                    self._set_attribute(temp_loc, LISTEN_PORT, listen_port, [])

        self.__create_migratable_targets(location, delete_now=delete_now)

        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def __create_migratable_targets(self, location, delete_now=True):
        """
        Create the /MigratableTarget folder objects, if any.
        :param location: the location to use
        :param delete_now: Flag to determine if the delete of elements will be delayed
        :raises: CreateException: if an error occurs
        """
        _method_name = '__create_migratable_targets'

        self.logger.entering(str_helper.to_string(location), class_name=self.__class_name, method_name=_method_name)
        migratable_target_nodes = dictionary_utils.get_dictionary_element(self._topology, MIGRATABLE_TARGET)

        if len(migratable_target_nodes) > 0:
            self._create_named_mbeans(MIGRATABLE_TARGET, migratable_target_nodes, location, log_created=True,
                                      delete_now=delete_now)

        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def __create_other_domain_artifacts(self, location, mbean_type_list):
        """
        Create the remaining model topology-related folder objects, if any.
        :param location: the location to use
        :raises: CreateException: if an error occurs
        """
        _method_name = '__create_other_domain_artifacts'
        self.logger.entering(str_helper.to_string(location), mbean_type_list,
                             class_name=self.__class_name, method_name=_method_name)

        for mbean_type in mbean_type_list:
            mbean_nodes = dictionary_utils.get_dictionary_element(self._topology, mbean_type)

            if len(mbean_nodes) > 0:
                mbean_location = LocationContext(location).append_location(mbean_type)
                if self.aliases.supports_multiple_mbean_instances(mbean_location):
                    self._create_named_mbeans(mbean_type, mbean_nodes, location, log_created=True)
                else:
                    self._create_mbean(mbean_type, mbean_nodes, location, log_created=True)

        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def __set_app_dir(self):
        """
        Set the AppDir domain option.
        :raises: CreateException: if an error occurs
        """
        _method_name = '__set_app_dir'

        self.logger.entering(class_name=self.__class_name, method_name=_method_name)
        if APP_DIR in self._domain_info:
            app_dir = self._domain_info[APP_DIR]
            self.logger.fine('WLSDPLY-12225', model.get_model_domain_info_key(), APP_DIR, app_dir,
                             class_name=self.__class_name, method_name=_method_name)
        else:
            app_parent = self.model_context.get_domain_parent_dir()
            if not app_parent:
                app_parent = os.path.dirname(self.model_context.get_domain_home())

            app_dir = os.path.join(app_parent, 'applications')
            self.logger.fine('WLSDPLY-12226', model.get_model_domain_info_key(), APP_DIR, app_dir,
                             class_name=self.__class_name, method_name=_method_name)

        self.wlst_helper.set_option_if_needed(SET_OPTION_APP_DIR, app_dir)

        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def __enable_jms_db_persistence_if_set(self):
        """
        Enable jms db persistence if set
        """
        _method_name = '__enable_jms_db_persistence_if_set'

        self.logger.entering(class_name=self.__class_name, method_name=_method_name)
        if ENABLE_JMS_DB_PERSISTENCE in self._domain_info:
            location = self.aliases.get_model_section_attribute_location(DOMAIN_INFO)
            result, __ = self.aliases.is_valid_model_attribute_name(location,
                                                                    ENABLE_JMS_DB_PERSISTENCE)

            if result == ValidationCodes.VALID:
                enable_jms_db = self._domain_info[ENABLE_JMS_DB_PERSISTENCE]
                self.wlst_helper.enable_jms_store_db_persistence(enable_jms_db)

        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def __enable_jta_tlog_db_persistence_if_set(self):
        """
        Enable jta tlog db persistence if set
        """
        _method_name = '__enable_jta_tlog_db_persistence_if_set'

        self.logger.entering(class_name=self.__class_name, method_name=_method_name)
        if ENABLE_JTALOG_DB_PERSISTENCE in self._domain_info:
            location = self.aliases.get_model_section_attribute_location(DOMAIN_INFO)
            result, __ = self.aliases.is_valid_model_attribute_name(location,
                                                                      ENABLE_JTALOG_DB_PERSISTENCE)

            if result == ValidationCodes.VALID:
                enable_jta_db = self._domain_info[ENABLE_JTALOG_DB_PERSISTENCE]
                self.wlst_helper.enable_jta_tlog_store_db_persistence(enable_jta_db)


        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)

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
            self.wlst_helper.set_if_needed(DOMAIN_NAME, self._domain_name)
            self.logger.info('WLSDPLY-12227', self.__default_domain_name, self._domain_name,
                             class_name=self.__class_name, method_name=_method_name)

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
            token_name = self.aliases.get_name_token(location)
            if token_name is not None:
                location.add_name_token(token_name, self._domain_name)

            location.append_location(USER)
            token_name = self.aliases.get_name_token(location)
            if token_name is not None:
                location.add_name_token(token_name, self.wls_helper.get_default_admin_username())

            admin_user_path = self.aliases.get_wlst_attributes_path(location)
            self.wlst_helper.cd(admin_user_path)
            wlst_name, wlst_value = \
                self.aliases.get_wlst_attribute_name_and_value(location, NAME, admin_username)
            self.wlst_helper.set_if_needed(wlst_name, wlst_value)
            wlst_name, wlst_value = \
                self.aliases.get_wlst_attribute_name_and_value(location, PASSWORD, admin_password, masked=True)
            self.wlst_helper.set_if_needed(wlst_name, wlst_value, masked=True)

        else:
            ex = exception_helper.create_create_exception('WLSDPLY-12228', 'AdminPassword',
                                                          model.get_model_domain_info_key())
            self.logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex

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
            token_name = self.aliases.get_name_token(location)
            if token_name is not None:
                location.add_name_token(token_name, self.__default_admin_server_name)

            wlst_path = self.aliases.get_wlst_attributes_path(location)
            self.wlst_helper.cd(wlst_path)
            #
            # We cannot use the aliases for the Server Name attribute since we
            # filter out any name fields.
            #
            self.wlst_helper.set_if_needed(NAME, self._admin_server_name)
            self.logger.info('WLSDPLY-12229', self.__default_admin_server_name, self._admin_server_name,
                             class_name=self.__class_name, method_name=_method_name)
        else:
            self._admin_server_name = self.__default_admin_server_name

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
        attribute_path = self.aliases.get_wlst_attributes_path(location)
        self.wlst_helper.cd(attribute_path)
        self._set_attributes(location, attrib_dict)

    def __configure_security_configuration(self):
        """
        Configure the SecurityConfiguration MBean and its Realm sub-folder. In 11g, the SecurityConfiguration MBean
        is not persisted to the domain config until the domain is first written.
        :return:
        """
        _method_name = '_configure_security_configuration'
        self.logger.entering(class_name=self.__class_name, method_name=_method_name)
        # SecurityConfiguration is special since the subfolder name does not change when you change the domain name.
        # It only changes once the domain is written and re-read...
        domain_name_token = deployer_utils.get_domain_token(self.aliases)
        security_config_location = LocationContext().add_name_token(domain_name_token, self._domain_name)
        self.security_provider_creator.create_security_configuration(security_config_location)
        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def __create_boot_dot_properties(self):
        _method_name = '__create_boot_dot_properties'
        self.logger.entering(class_name=self.__class_name, method_name=_method_name)

        if SERVER_START_MODE in self._domain_info:
            server_start_mode = self._domain_info[SERVER_START_MODE]
            if server_start_mode == 'prod' or server_start_mode == 'PROD':
                return

        if PRODUCTION_MODE_ENABLED in self._topology:
            if string_utils.to_boolean(self._topology[PRODUCTION_MODE_ENABLED]):
                return

        system_ini = SerializedSystemIni.getEncryptionService(self._domain_home)
        encryption_service = ClearOrEncryptedService(system_ini)
        admin_password = self._domain_info[ADMIN_PASSWORD]
        admin_username = self.wls_helper.get_default_admin_username()
        if ADMIN_USERNAME in self._domain_info:
            admin_username = self._domain_info[ADMIN_USERNAME]

        server_nodes = dictionary_utils.get_dictionary_element(self._topology, SERVER)
        servers = [self._admin_server_name]

        for model_name in server_nodes:
            name = self.wlst_helper.get_quoted_name_for_wlst(model_name)
            servers.append(name)

        admin_username = self.aliases.decrypt_password(admin_username)
        admin_password = self.aliases.decrypt_password(admin_password)
        encrypted_username = encryption_service.encrypt(admin_username)
        encrypted_password = encryption_service.encrypt(admin_password)
        for server in servers:
            if model_helper.is_delete_name(server):
                continue
            properties = Properties()
            properties.put("username", encrypted_username)
            properties.put("password", encrypted_password)
            file_directory = self._domain_home + "/servers/" + server + "/security"
            file_location = file_directory + "/boot.properties"
            if not os.path.exists(file_directory):
                os.makedirs(file_directory)
            ostream = FileOutputStream(file_location)
            properties.store(ostream, None)
            ostream.close()
        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def __create_credential_mappings(self):
        """
        Create credential mappings from model elements.
        """
        default_nodes = dictionary_utils.get_dictionary_element(self._domain_info,
                                                                WLS_USER_PASSWORD_CREDENTIAL_MAPPINGS)
        if default_nodes:
            credential_map_helper = CredentialMapHelper(self.model_context, ExceptionType.CREATE)
            credential_map_helper.create_default_init_file(default_nodes)

    def __install_saml2_security_files(self):
        """
        Install SAML2 security files from model archive.
        """
        saml2_security_helper = Saml2SecurityHelper(self.model_context, ExceptionType.CREATE)
        saml2_security_helper.extract_initialization_files(self.archive_helper)

    def __run_post_create_domain_script(self):
        _method_name = '__run_post_create_domain_script'

        self.logger.entering(self.__class_name, _method_name)
        script = self._domain_typedef.get_post_create_domain_script()
        if script is None:
            self.logger.exiting(class_name=self.__class_name, method_name=_method_name)
            return

        java_home = self.model_context.get_java_home()
        oracle_home = self.model_context.get_oracle_home()
        runner = CreateDomainLifecycleHookScriptRunner(POST_CREATE_DOMAIN_LIFECYCLE_HOOK,
                                                       POST_CREATE_DOMAIN_LOG_BASENAME, script, java_home, oracle_home,
                                                       self._domain_home, self._domain_name)
        runner.runScript()
        self.logger.info('WLSDPLY-12276', script, class_name=self.__class_name, method_name=_method_name)
        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def __configure_opss_wallet_and_passphrase(self):
        _method_name = '__configure_opss_wallet_and_passphrase'
        self.logger.entering(class_name=self.__class_name, method_name=_method_name)

        if not self._domain_typedef.has_jrf_with_database_store():
            return

        # Check the model for the OPSS wallet passphrase first
        key = 'WLSDPLY-12279'
        opss_wallet_password = None
        if OPSS_WALLET_PASSPHRASE in self._domain_info:
            opss_wallet_password = self.aliases.decrypt_password(self._domain_info[OPSS_WALLET_PASSPHRASE])
        elif OPSS_SECRETS in self._domain_info:
            self.logger.deprecation('WLSDPLY-22000', OPSS_SECRETS, OPSS_WALLET_PASSPHRASE,
                                    class_name=self.__class_name, method_name=_method_name)
            opss_wallet_password = self.aliases.decrypt_password(self._domain_info[OPSS_SECRETS])

        # Check the command-line args for the OPSS wallet passphrase
        # and give it preference over the one in the model.
        cla_passphrase = self.model_context.get_opss_wallet_passphrase()
        if not string_utils.is_empty(cla_passphrase):
            opss_wallet_password = cla_passphrase
            key = 'WLSDPLY-12280'

        if not string_utils.is_empty(opss_wallet_password):
            opss_wallet = None

            # Check the archive for the OPSS wallet and extract it, if present
            if self.archive_helper:
                opss_wallet = self.archive_helper.extract_opss_wallet()

            # Check the OPSS wallet in the command-line args and give it
            # preference over the one in the archive.
            cla__wallet = self.model_context.get_opss_wallet()
            if not string_utils.is_empty(cla__wallet):
                opss_wallet = cla__wallet

            if not string_utils.is_empty(opss_wallet):
                self.wlst_helper.set_shared_secret_store_with_password(opss_wallet, opss_wallet_password)
            else:
                # It seems like the user wanted to create a domain with
                # RCU schemas and attach to the existing RCU schemas.
                ex = exception_helper.create_create_exception(key)
                self.logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                raise ex

        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)
