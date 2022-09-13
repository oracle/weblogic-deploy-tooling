"""
Copyright (c) 2017, 2022, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""

import wlsdeploy.tool.deploy.deployer_utils as deployer_utils
import wlsdeploy.util.dictionary_utils as dictionary_utils
from oracle.weblogic.deploy.util import WLSDeployArchive

from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import CLUSTER
from wlsdeploy.aliases.model_constants import COHERENCE_CLUSTER_SYSTEM_RESOURCE
from wlsdeploy.aliases.model_constants import CUSTOM_IDENTITY_KEYSTORE_FILE
from wlsdeploy.aliases.model_constants import JDBC_RESOURCE
from wlsdeploy.aliases.model_constants import JDBC_SYSTEM_RESOURCE
from wlsdeploy.aliases.model_constants import NM_PROPERTIES
from wlsdeploy.aliases.model_constants import SERVER
from wlsdeploy.aliases.model_constants import SERVER_TEMPLATE
from wlsdeploy.util import model_helper
from wlsdeploy.util.weblogic_helper import WebLogicHelper
from wlsdeploy.tool.util.wlst_helper import WlstHelper


class TopologyHelper(object):
    """
    Shared code for topology section of model. Domain create and update use this code.
    """
    __class_name = 'TopologyHelper'

    def __init__(self, aliases, exception_type, logger):
        self.logger = logger
        self.aliases = aliases
        self.wlst_helper = WlstHelper(exception_type)
        self.wl_helper = WebLogicHelper(self.logger)
        self._coherence_cluster_elements = [CLUSTER, SERVER, SERVER_TEMPLATE]

    def check_coherence_cluster_references(self, type_name, model_nodes):
        """
        If the specified type has a Coherence cluster system resource attribute, verify that any referenced resource
        exists. If the resource does not exist, create an empty placeholder resource to allow assignment.
        :param type_name: the model folder type
        :param model_nodes: a dictionary containing the named model elements
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        if type_name in self._coherence_cluster_elements:
            for name in model_nodes.keys():
                child_nodes = dictionary_utils.get_dictionary_element(model_nodes, name)
                resource_name = dictionary_utils.get_element(child_nodes, COHERENCE_CLUSTER_SYSTEM_RESOURCE)
                if resource_name is not None:
                    self._create_placeholder_coherence_cluster(resource_name)

    def _create_placeholder_coherence_cluster(self, cluster_name):
        """
        Create a placeholder Coherence cluster system resource to be referenced from a topology element.
        The new cluster will be created at the root domain level.
        :param cluster_name: the name of the Coherence cluster system resource to be added
        """
        _method_name = '_create_placeholder_coherence_cluster'
        original_location = self.wlst_helper.get_pwd()
        cluster_location = LocationContext().append_location(COHERENCE_CLUSTER_SYSTEM_RESOURCE)
        existing_names = deployer_utils.get_existing_object_list(cluster_location, self.aliases)

        if cluster_name not in existing_names:
            self.logger.info('WLSDPLY-12230', cluster_name, class_name=self.__class_name, method_name=_method_name)

            cluster_token = self.aliases.get_name_token(cluster_location)
            cluster_location.add_name_token(cluster_token, cluster_name)
            deployer_utils.create_and_cd(cluster_location, existing_names, self.aliases)

        self.wlst_helper.cd(original_location)

    def create_placeholder_servers_in_cluster(self, topology):
        """
        Create a placeholder for servers that are in a cluster, as these are migratable entities that
        can reference other servers in the cluster.
        :param topology: The topology model nodes containing the full set of Servers to add for the create / update
        """
        _method_name = 'create_placeholder_servers_in_cluster'
        self.logger.entering(class_name=self.__class_name, method_name=_method_name)
        self.create_placeholder_named_elements(LocationContext(), SERVER, topology)
        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def create_placeholder_clusters(self, topology):
        """
        Create a placeholder cluster for each name in the topology.
        This is necessary because there is a circular dependency between certain attributes.
        :param topology: the topology model nodes
        """
        self.create_placeholder_named_elements(LocationContext(), CLUSTER, topology)

    def create_placeholder_server_templates(self, topology):
        """
        Create a placeholder server template for each name in the topology.
        This is necessary because there is a circular dependency between clusters and server templates.
        :param topology: the topology model nodes
        """
        self.create_placeholder_named_elements(LocationContext(), SERVER_TEMPLATE, topology)

    def create_placeholder_jdbc_resources(self, resources):
        """
        Create a placeholder JDBC resource for each name in the resources section.
        This is necessary because cluster attributes may reference JDBC resources.
        :param resources: the resource model nodes
        :return: a list of names of created placeholders
        """
        return self.create_placeholder_named_elements(LocationContext(), JDBC_SYSTEM_RESOURCE, resources)

    def create_placeholder_named_elements(self, location, model_type, model_nodes):
        """
        Create a placeholder entry for each element in the specified named element nodes.
        This is necessary when there can be circular references with other elements.
        :param location: the location for the nodes to be added
        :param model_type: the type of the specified model nodes
        :param model_nodes: the model nodes
        :return: a list of names of created placeholders
        """
        _method_name = 'create_placeholder_named_elements'
        holder_names = []
        original_location = self.wlst_helper.get_pwd()
        resource_location = LocationContext(location).append_location(model_type)

        if self.aliases.get_wlst_mbean_type(resource_location) is not None:
            existing_names = deployer_utils.get_existing_object_list(resource_location, self.aliases)

            name_nodes = dictionary_utils.get_dictionary_element(model_nodes, model_type)
            for name in name_nodes.keys():
                if model_helper.is_delete_name(name):
                    # don't create placeholder for delete names
                    continue

                if name not in existing_names:
                    self.logger.info('WLSDPLY-19403', model_type, name, class_name=self.__class_name,
                                     method_name=_method_name)

                    token = self.aliases.get_name_token(resource_location)
                    resource_location.add_name_token(token, name)
                    deployer_utils.create_and_cd(resource_location, existing_names, self.aliases)
                    self._update_placeholder(model_type, name, resource_location)
                    holder_names.append(name)

        self.wlst_helper.cd(original_location)
        return holder_names

    def _update_placeholder(self, type_name, name, location):
        """
        Make any required updates to a newly-created placeholder.
        :param type_name: the type name of the placeholder
        :param name: the name of the placeholder MBean
        :param location: the location of the placeholder
        """
        if type_name == JDBC_SYSTEM_RESOURCE:
            # for online update, Name must be assigned to each JDBCSystemResource / JdbcResource MBean.
            # (see datasource_deployer.set_attributes())
            child_location = LocationContext(location).append_location(JDBC_RESOURCE)
            deployer_utils.set_single_folder_token(child_location, self.aliases)
            wlst_path = self.aliases.get_wlst_attributes_path(child_location)
            if self.wlst_helper.path_exists(wlst_path):
                original_location = self.wlst_helper.get_pwd()
                self.wlst_helper.cd(wlst_path)
                existing_name = self.wlst_helper.get('Name')
                if existing_name is None:
                    self.wlst_helper.set('Name', name)
                self.wlst_helper.cd(original_location)

    def clear_jdbc_placeholder_targeting(self, jdbc_names):
        """
        Remove any targets for the JDBC resources in the specified list of names.
        Targets may have been inadvertently assigned when clusters were added after JDBC placeholders.
        :param jdbc_names: names of placeholders to clear
        """
        _method_name = 'clear_jdbc_placeholder_targeting'
        resource_location = LocationContext().append_location(JDBC_SYSTEM_RESOURCE)
        token = self.aliases.get_name_token(resource_location)

        for name in jdbc_names:
            self.logger.info('WLSDPLY-19404', JDBC_SYSTEM_RESOURCE, name, class_name=self.__class_name,
                             method_name=_method_name)

            resource_location.add_name_token(token, name)
            wlst_path = self.aliases.get_wlst_attributes_path(resource_location)
            if self.wlst_helper.path_exists(wlst_path):
                mbean = self.wlst_helper.get_mbean_for_wlst_path(wlst_path)
                mbean.setTargets(None)

    def qualify_nm_properties(self, type_name, model_nodes, base_location, model_context, attribute_setter):
        """
        For the NM properties MBean, update the keystore file path to be fully qualified with the domain directory.
        :param type_name: the type name of the MBean to be checked
        :param model_nodes: the model nodes of the MBean to be checked
        :param base_location: the parent location of the MBean
        :param model_context: the model context of the tool
        :param attribute_setter: the attribute setter to be used for update
        """
        if type_name == NM_PROPERTIES:
            location = LocationContext(base_location).append_location(type_name)
            keystore_file = dictionary_utils.get_element(model_nodes, CUSTOM_IDENTITY_KEYSTORE_FILE)
            if keystore_file and WLSDeployArchive.isPathIntoArchive(keystore_file):
                value = model_context.get_domain_home() + "/" + keystore_file
                attribute_setter.set_attribute(location, CUSTOM_IDENTITY_KEYSTORE_FILE, value)

    def is_clustered_server(self, server_name, servers_dictionary):
        """
        Return true if the server's Cluster attribute is set.
        :param server_name: name of the server in the dictionary
        :param servers_dictionary: model topology section of servers
        :return: True if a clustered server
        """
        server_dictionary = dictionary_utils.get_dictionary_element(servers_dictionary, server_name)
        if dictionary_utils.is_empty_dictionary_element(server_dictionary, CLUSTER):
            return False
        return True
