"""
Copyright (c) 2017, 2018, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""

import wlsdeploy.tool.deploy.deployer_utils as deployer_utils
import wlsdeploy.util.dictionary_utils as dictionary_utils

from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import CLUSTER
from wlsdeploy.aliases.model_constants import COHERENCE_CLUSTER_SYSTEM_RESOURCE
from wlsdeploy.aliases.model_constants import SERVER
from wlsdeploy.aliases.model_constants import SERVER_TEMPLATE
from wlsdeploy.tool.util.alias_helper import AliasHelper
from wlsdeploy.tool.util.wlst_helper import WlstHelper


class TopologyHelper(object):
    """
    Shared code for topology section of model. Domain create and update use this code.
    """
    __class_name = 'TopologyHelper'

    def __init__(self, aliases, exception_type, logger):
        self.logger = logger
        self.alias_helper = AliasHelper(aliases, self.logger, exception_type)
        self.wlst_helper = WlstHelper(self.logger, exception_type)

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
            for name in model_nodes:
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
        existing_names = deployer_utils.get_existing_object_list(cluster_location, self.alias_helper)

        if cluster_name not in existing_names:
            self.logger.info('WLSDPLY-12230', cluster_name, class_name=self.__class_name, method_name=_method_name)

            cluster_token = self.alias_helper.get_name_token(cluster_location)
            cluster_location.add_name_token(cluster_token, cluster_name)
            deployer_utils.create_and_cd(cluster_location, existing_names, self.alias_helper)

        self.wlst_helper.cd(original_location)

    def create_placeholder_server_templates(self, topology):
        """
        Create a placeholder server template for each name in the topology.
        This is necessary because there is a circular dependency between clusters and server templates.
        :param topology: the topology model nodes
        """
        _method_name = 'create_placeholder_server_templates'
        original_location = self.wlst_helper.get_pwd()
        template_location = LocationContext().append_location(SERVER_TEMPLATE)
        existing_names = deployer_utils.get_existing_object_list(template_location, self.alias_helper)

        template_nodes = dictionary_utils.get_dictionary_element(topology, SERVER_TEMPLATE)
        for template_name in template_nodes:
            if template_name not in existing_names:
                self.logger.info('WLSDPLY-19400', template_name, class_name=self.__class_name,
                                 method_name=_method_name)

                template_token = self.alias_helper.get_name_token(template_location)
                template_location.add_name_token(template_token, template_name)
                deployer_utils.create_and_cd(template_location, existing_names, self.alias_helper)

        self.wlst_helper.cd(original_location)
