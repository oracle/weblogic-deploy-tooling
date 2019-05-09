"""
Copyright (c) 2017, 2019, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import ADMIN_CONSOLE
from wlsdeploy.aliases.model_constants import CLUSTER
from wlsdeploy.aliases.model_constants import CREATE_ONLY_DOMAIN_ATTRIBUTES
from wlsdeploy.aliases.model_constants import MACHINE
from wlsdeploy.aliases.model_constants import MIGRATABLE_TARGET
from wlsdeploy.aliases.model_constants import SECURITY
from wlsdeploy.aliases.model_constants import SECURITY_CONFIGURATION
from wlsdeploy.aliases.model_constants import SERVER
from wlsdeploy.aliases.model_constants import SERVER_TEMPLATE
from wlsdeploy.aliases.model_constants import UNIX_MACHINE
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception import exception_helper
from wlsdeploy.exception.expection_types import ExceptionType
from wlsdeploy.tool.create.security_provider_creator import SecurityProviderCreator
from wlsdeploy.tool.deploy import deployer_utils
from wlsdeploy.tool.deploy.deployer import Deployer
from wlsdeploy.tool.util.library_helper import LibraryHelper
from wlsdeploy.tool.util.target_helper import TargetHelper
from wlsdeploy.tool.util.topology_helper import TopologyHelper
from wlsdeploy.util import dictionary_utils


class TopologyUpdater(Deployer):
    """
    Deploy relevant resources at the domain level using WLST.  Entry point, deploy()
    """
    _class_name = "TopologyUpdater"

    def __init__(self, model, model_context, aliases, wlst_mode=WlstModes.OFFLINE):
        Deployer.__init__(self, model, model_context, aliases, wlst_mode)
        self._topology = self.model.get_model_topology()
        self._resources = self.model.get_model_resources()
        self._exception_type = ExceptionType.DEPLOY
        self._topology_helper = TopologyHelper(self.aliases, self._exception_type, self.logger)
        self._domain_typedef = self.model_context.get_domain_typedef()

        self._security_provider_creator = SecurityProviderCreator(model.get_model(), model_context, aliases,
                                                                  self._exception_type, self.logger)

        self.library_helper = LibraryHelper(self.model, self.model_context, self.aliases,
                                            model_context.get_domain_home(), self._exception_type, self.logger)

        self.target_helper = TargetHelper(self.model, self.model_context, self.aliases, self._exception_type,
                                          self.logger)

    # Override
    def _add_named_elements(self, type_name, model_nodes, location):
        """
        Override default behavior to create placeholders for referenced Coherence clusters.
        :param type_name: the model folder type
        :param model_nodes: the model dictionary of the specified model folder type
        :param location: the location object to use to create the MBeans
        :raises: DeployException: if an error occurs
        """
        self._topology_helper.check_coherence_cluster_references(type_name, model_nodes)
        # continue with regular processing

        Deployer._add_named_elements(self, type_name, model_nodes, location)

    # Override
    def _add_model_elements(self, type_name, model_nodes, location):
        Deployer._add_model_elements(self, type_name, model_nodes, location)

        # check for file paths that need to be qualified
        self._topology_helper.qualify_nm_properties(type_name, model_nodes, location, self.model_context,
                                                    self.attribute_setter)

    def update(self):
        """
        Deploy resource model elements at the domain level, including multi-tenant elements.
        """
        # For issue in setServerGroups in online mode (new configured clusters and stand-alone managed servers
        # will not have extension template resources targeted)
        existing_managed_servers, existing_configured_clusters = self._create_list_of_setservergroups_targets()
        domain_token = deployer_utils.get_domain_token(self.alias_helper)

        location = LocationContext()
        location.add_name_token(domain_token, self.model_context.get_domain_name())

        # create a list, then remove each element as it is processed
        folder_list = self.alias_helper.get_model_topology_top_level_folder_names()

        # /Security cannot be updated on existing domain
        folder_list.remove(SECURITY)

        self._security_provider_creator.create_security_configuration(location)
        folder_list.remove(SECURITY_CONFIGURATION)

        # set the domain attributes
        self._set_domain_attributes()

        self._process_section(self._topology, folder_list, ADMIN_CONSOLE, location)
        self._process_section(self._topology, folder_list, MACHINE, location)
        self._process_section(self._topology, folder_list, UNIX_MACHINE, location)

        # avoid circular references between clusters and server templates
        self._topology_helper.create_placeholder_server_templates(self._topology)

        # create placeholders for JDBC resources that may be referenced in cluster definition.
        self._topology_helper.create_placeholder_jdbc_resources(self._resources)

        self._process_section(self._topology, folder_list, CLUSTER, location)
        self._process_section(self._topology, folder_list, SERVER_TEMPLATE, location)

        # create placeholders for Servers that are in a cluster as /Server/JTAMigratableTarget
        # can reference "other" servers
        self._topology_helper.create_placeholder_servers_in_cluster(self._topology)

        self._process_section(self._topology, folder_list, SERVER, location)

        self._process_section(self._topology, folder_list, MIGRATABLE_TARGET, location)

        new_managed_server_list, new_configured_cluster_list = self._create_list_of_setservergroups_targets()

        self._check_for_online_setservergroups_issue(existing_managed_servers, new_managed_server_list)
        self._check_for_online_setservergroups_issue(existing_configured_clusters, new_configured_cluster_list)

        # process remaining top-level folders. copy list to avoid concurrent update in loop
        remaining = list(folder_list)
        for folder_name in remaining:
            self._process_section(self._topology, folder_list, folder_name, location)

        if self.wls_helper.is_set_server_groups_supported():
            server_groups_to_target = self._domain_typedef.get_server_groups_to_target()
            server_assigns, dynamic_assigns = \
                self.target_helper.target_server_groups_to_servers(server_groups_to_target)
            if dynamic_assigns is not None:
                self.wlst_helper.save_and_close(self.model_context)
                self.target_helper.target_server_groups_to_dynamic_clusters(dynamic_assigns)
                self.wlst_helper.reopen(self.model_context)
            if server_assigns is not None:
                self.target_helper.target_server_groups(server_assigns)
        elif self._domain_typedef.is_jrf_domain_type():
            self.target_helper.target_jrf_groups_to_clusters_servers()

        self.library_helper.install_domain_libraries()
        self.library_helper.extract_classpath_libraries()

    def _process_section(self, folder_dict, folder_list, key, location):
        if key in folder_dict:
            nodes = dictionary_utils.get_dictionary_element(folder_dict, key)
            sub_location = LocationContext(location).append_location(key)
            if self.alias_helper.supports_multiple_mbean_instances(sub_location):
                self._add_named_elements(key, nodes, location)
            else:
                self._add_model_elements(key, nodes, location)

        if key in folder_list:
            folder_list.remove(key)

    def _set_domain_attributes(self):
        _method_name = '_set_domain_attributes'
        self.logger.fine('WLSDPLY-09700', self.model_context.get_domain_name(), class_name=self._class_name,
                         method_name=_method_name)
        attrib_dict = dictionary_utils.get_dictionary_attributes(self._topology)

        # skip any attributes that have special handling in create
        for attribute in CREATE_ONLY_DOMAIN_ATTRIBUTES:
            if attribute in attrib_dict:
                del attrib_dict[attribute]

        location = LocationContext()
        attribute_path = self.alias_helper.get_wlst_attributes_path(location)
        self.wlst_helper.cd(attribute_path)
        self.set_attributes(location, attrib_dict)

    def is_online_with_ext_templates(self):
        return self.model_context.is_wlst_online() and self.model_context.get_domain_typedef().has_extension_templates()

    def _check_for_online_setservergroups_issue(self, existing_list, new_list):
        _method_name = '_check_for_online_setservergroups_issue'
        if len(existing_list) != len(new_list):
            for entity_name in new_list:
                if entity_name not in existing_list:
                    self.logger.warning('WLSDPLY-09701', entity_name,
                                        class_name=self._class_name, method_name=_method_name)
        return

    def _create_list_of_setservergroups_targets(self):
        """
        If an update is executed in online WLST mode, return a list of all existing configured / mixed clusters and
        stand-alone managed servers. This method will be invoked to create a list of existing, and a list of new
        as added by the update tool. These lists will be compared to determine if they will encounter
        the online WLST problem with setServerGroups. The setServerGroups will target template resources to the
        new entities, but this targeting is not persisted to the config.xml.
        """
        _method_name = '_create_list_of_setservergroups_targets'
        self.logger.entering(class_name=self._class_name, method_name=_method_name)

        if not self.is_online_with_ext_templates():
            self.logger.exiting(class_name=self._class_name, method_name=_method_name)
            return list(), list()

        location = LocationContext().append_location(SERVER)
        server_path = self.alias_helper.get_wlst_list_path(location)
        existing_managed_servers = list()
        existing_servers = self.wlst_helper.get_existing_object_list(server_path)
        if existing_servers is not None:
            name_token = self.alias_helper.get_name_token(location)
            for server_name in existing_servers:
                location.add_name_token(name_token, server_name)
                wlst_path = self.alias_helper.get_wlst_attributes_path(location)
                self.wlst_helper.cd(wlst_path)
                cluster_attribute = self.alias_helper.get_wlst_attribute_name(location, CLUSTER)
                cluster_value = self.wlst_helper.get(cluster_attribute)
                if cluster_value is None:
                    existing_managed_servers.append(server_name)
                location.remove_name_token(name_token)

        existing_configured_clusters = list()
        location = LocationContext().append_location(CLUSTER)
        cluster_path = self.alias_helper.get_wlst_list_path(location)
        existing_clusters = self.wlst_helper.get_existing_object_list(cluster_path)
        if existing_clusters is not None:
            name_token = self.alias_helper.get_name_token(location)
            for cluster_name in existing_clusters:
                location.add_name_token(name_token, cluster_name)
                wlst_path = self.alias_helper.get_wlst_attributes_path(location)
                self.wlst_helper.cd(wlst_path)
                ds_mbean = self.alias_helper.get_wlst_mbean_type(location)
                if not self.wlst_helper.subfolder_exists(ds_mbean,
                                                         self.alias_helper.get_wlst_subfolders_path(location)):
                    existing_configured_clusters.append(cluster_name)
                location.remove_name_token(name_token)

        self.logger.exiting(class_name=self._class_name, method_name=_method_name,
                            result='configured_clusters=' + str(existing_configured_clusters) +
                                   ' managed servers=' + str(existing_managed_servers))
        return existing_configured_clusters, existing_managed_servers
