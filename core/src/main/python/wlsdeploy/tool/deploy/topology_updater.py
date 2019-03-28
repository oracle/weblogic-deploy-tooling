"""
Copyright (c) 2017, 2019, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import ADMIN_CONSOLE
from wlsdeploy.aliases.model_constants import CLUSTER
from wlsdeploy.aliases.model_constants import DOMAIN_NAME
from wlsdeploy.aliases.model_constants import MACHINE
from wlsdeploy.aliases.model_constants import MIGRATABLE_TARGET
from wlsdeploy.aliases.model_constants import SECURITY
from wlsdeploy.aliases.model_constants import SECURITY_CONFIGURATION
from wlsdeploy.aliases.model_constants import SERVER
from wlsdeploy.aliases.model_constants import SERVER_TEMPLATE
from wlsdeploy.aliases.model_constants import UNIX_MACHINE
from wlsdeploy.aliases.wlst_modes import WlstModes
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
        self._topology_helper = TopologyHelper(self.aliases, ExceptionType.DEPLOY, self.logger)
        self._domain_typedef = self.model_context.get_domain_typedef()

        self._security_provider_creator = SecurityProviderCreator(model.get_model(), model_context, aliases,
                                                                  ExceptionType.DEPLOY, self.logger)

        self.library_helper = LibraryHelper(self.model, self.model_context, self.aliases,
                                            model_context.get_domain_home(), ExceptionType.DEPLOY, self.logger)

        self.target_helper = TargetHelper(self.model, self.model_context, self.aliases, ExceptionType.DEPLOY,
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

        # process remaining top-level folders. copy list to avoid concurrent update in loop
        remaining = list(folder_list)
        for folder_name in remaining:
            self._process_section(self._topology, folder_list, folder_name, location)

        if self.wls_helper.is_set_server_groups_supported():
            server_groups_to_target = self._domain_typedef.get_server_groups_to_target()
            self.target_helper.target_server_groups_to_servers(server_groups_to_target)
        elif self._domain_typedef.domain_type_has_jrf_resources():
            deployer_utils.save_changes(self.model_context)
            self.target_helper.target_jrf_groups_to_clusters_servers(self.model_context.get_domain_home())
            deployer_utils.read_again(self.model_context)

        # files referenced in attributes are extracted as attributes are processed

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
        if DOMAIN_NAME in attrib_dict:
            del attrib_dict[DOMAIN_NAME]
        location = LocationContext()
        attribute_path = self.alias_helper.get_wlst_attributes_path(location)
        self.wlst_helper.cd(attribute_path)
        self.set_attributes(location, attrib_dict)
