"""
Copyright (c) 2017, 2022, Oracle Corporation and/or its affiliates.  All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import wlsdeploy.util.dictionary_utils as dictionary_utils
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import PARTITION
from wlsdeploy.aliases.model_constants import PARTITION_WORK_MANAGER
from wlsdeploy.aliases.model_constants import RESOURCE_GROUP
from wlsdeploy.aliases.model_constants import RESOURCE_GROUP_TEMPLATE
from wlsdeploy.aliases.model_constants import RESOURCE_MANAGEMENT
from wlsdeploy.tool.deploy.applications_deployer import ApplicationsDeployer
from wlsdeploy.tool.deploy.common_resources_deployer import CommonResourcesDeployer
from wlsdeploy.tool.deploy.datasource_deployer import DatasourceDeployer
from wlsdeploy.tool.deploy.deployer import Deployer
from wlsdeploy.tool.deploy.jms_resources_deployer import JmsResourcesDeployer
from wlsdeploy.tool.deploy.wldf_resources_deployer import WldfResourcesDeployer


class MultiTenantResourcesDeployer(Deployer):
    """
    Deploy multi-tenant elements to the domain using WLST. Entry point, add_multi_tenant_objects()
    """
    CLASS_NAME = "MultiTenantResourcesDeployer"

    def __init__(self, model, model_context, aliases, wlst_mode=WlstModes.OFFLINE):
        Deployer.__init__(self, model, model_context, aliases, wlst_mode)
        self._resources = self.model.get_model_resources()

        self.common_deployer = \
            CommonResourcesDeployer(self.model, self.model_context, self.aliases, wlst_mode=self.wlst_mode)

    def add_multi_tenant_objects(self, location):
        """
        Add multi-tenant elements to the specified location.
        :param location: the location where sub-folders should be added
        """
        self._add_resource_management(location)
        self._add_resource_group_templates(location)
        self._add_resource_groups(self._resources, location)
        self._add_partition_work_managers(self._resources, location)
        self._add_partitions(location)

    # Override
    def _add_subfolders(self, model_nodes, location, excludes=None):
        """
        Override the base method for sub-folders of resource group and template.
        Those sub-folders must be processed in a specific order, some with special processing.
        :param model_nodes: the child nodes of a model element
        :param location: the location where sub-folders should be added
        :param excludes: optional list of sub-folder names to be excluded from processing
        """
        parent_type = self.get_location_type(location)
        is_in = (parent_type == RESOURCE_GROUP) or (parent_type == RESOURCE_GROUP_TEMPLATE)
        if is_in:
            self._add_resource_group_resources(model_nodes, location)
            return

        Deployer._add_subfolders(self, model_nodes, location, excludes=excludes)

    # Override
    def _set_attributes_and_add_subfolders(self, location, model_nodes):
        """
        Override the base method for attributes and sub-folders of partition.
        Process sub-folders first to allow attributes to reference partition work manager and resource manager.
        :param location: the location of the attributes and sub-folders
        :param model_nodes: a map of model nodes including attributes and sub-folders
        :raise: DeployException: if an error condition is encountered
        """
        parent_type = self.get_location_type(location)
        if parent_type == PARTITION:
            self._add_subfolders(model_nodes, location)
            self.wlst_helper.cd(self.aliases.get_wlst_attributes_path(location))
            self.set_attributes(location, model_nodes)
            return

        Deployer._set_attributes_and_add_subfolders(self, location, model_nodes)

    def _add_partitions(self, location):
        partitions = dictionary_utils.get_dictionary_element(self._resources, PARTITION)
        self._add_named_elements(PARTITION, partitions, location)

    def _add_resource_groups(self, parent_dict, location):
        groups = dictionary_utils.get_dictionary_element(parent_dict, RESOURCE_GROUP)
        self._add_named_elements(RESOURCE_GROUP, groups, location)

    def _add_resource_group_templates(self, location):
        templates = dictionary_utils.get_dictionary_element(self._resources, RESOURCE_GROUP_TEMPLATE)
        self._add_named_elements(RESOURCE_GROUP_TEMPLATE, templates, location)

    def _add_resource_group_resources(self, parent_dict, location):
        """
        Add the resource elements in the dictionary at the specified location.
        These elements should be deployed in a specific order, with some special handling.
        :param parent_dict: the dictionary possibly containing resource elements
        :param location: the location to deploy the elements
        """
        data_source_deployer = DatasourceDeployer(self.model, self.model_context, self.aliases, self.wlst_mode)
        data_source_deployer.add_data_sources(parent_dict, location)

        common_deployer = CommonResourcesDeployer(self.model, self.model_context, self.aliases, self.wlst_mode)
        common_deployer.add_foreign_jndi_providers(parent_dict, location)
        common_deployer.add_file_stores(parent_dict, location)
        common_deployer.add_jdbc_stores(parent_dict, location)
        common_deployer.add_jms_servers(parent_dict, location)
        common_deployer.add_saf_agents(parent_dict, location)
        common_deployer.add_path_services(parent_dict, location)

        jms_deployer = JmsResourcesDeployer(self.model, self.model_context, self.aliases, self.wlst_mode)
        jms_deployer.add_jms_system_resources(parent_dict, location)

        common_deployer.add_jms_bridge_destinations(parent_dict, location)
        common_deployer.add_jms_bridges(parent_dict, location)
        common_deployer.add_mail_sessions(parent_dict, location)

        wldf_deployer = WldfResourcesDeployer(self.model, self.model_context, self.aliases, self.wlst_mode)
        wldf_deployer.add_wldf_modules(parent_dict, location)

        common_deployer.add_coherence_clusters(parent_dict, location)

        applications_deployer = \
            ApplicationsDeployer(self.model, self.model_context, self.aliases, self.wlst_mode, location)
        applications_deployer.deploy()

    def _add_partition_work_managers(self, parent_dict, location):
        managers = dictionary_utils.get_dictionary_element(parent_dict, PARTITION_WORK_MANAGER)
        self._add_named_elements(PARTITION_WORK_MANAGER, managers, location)

    def _add_resource_management(self, location):
        managements = dictionary_utils.get_dictionary_element(self._resources, RESOURCE_MANAGEMENT)
        if len(managements) > 0:
            m_location = LocationContext(location).append_location(RESOURCE_MANAGEMENT)
            token = self.aliases.get_name_token(m_location)
            location.add_name_token(token, self.model_context.get_domain_name())
            self._add_model_elements(RESOURCE_MANAGEMENT, managements, location)
