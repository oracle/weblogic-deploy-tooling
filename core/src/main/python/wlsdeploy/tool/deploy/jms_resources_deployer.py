"""
Copyright (c) 2017, 2020, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import oracle.weblogic.deploy.util.PyOrderedDict as OrderedDict

import wlsdeploy.util.dictionary_utils as dictionary_utils
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import CONNECTION_FACTORY
from wlsdeploy.aliases.model_constants import DESTINATION_KEY
from wlsdeploy.aliases.model_constants import DISTRIBUTED_QUEUE
from wlsdeploy.aliases.model_constants import DISTRIBUTED_TOPIC
from wlsdeploy.aliases.model_constants import FOREIGN_SERVER
from wlsdeploy.aliases.model_constants import GROUP_PARAMS
from wlsdeploy.aliases.model_constants import JMS_RESOURCE
from wlsdeploy.aliases.model_constants import JMS_SYSTEM_RESOURCE
from wlsdeploy.aliases.model_constants import JNDI_PROPERTY
from wlsdeploy.aliases.model_constants import KEY
from wlsdeploy.aliases.model_constants import QUEUE
from wlsdeploy.aliases.model_constants import QUOTA
from wlsdeploy.aliases.model_constants import SAF_ERROR_HANDLING
from wlsdeploy.aliases.model_constants import SAF_IMPORTED_DESTINATION
from wlsdeploy.aliases.model_constants import SAF_REMOTE_CONTEXT
from wlsdeploy.aliases.model_constants import SUB_DEPLOYMENT_NAME
from wlsdeploy.aliases.model_constants import TEMPLATE
from wlsdeploy.aliases.model_constants import TOPIC
from wlsdeploy.aliases.model_constants import UNIFORM_DISTRIBUTED_QUEUE
from wlsdeploy.aliases.model_constants import UNIFORM_DISTRIBUTED_TOPIC
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception.expection_types import ExceptionType
from wlsdeploy.tool.deploy import deployer_utils
from wlsdeploy.util import model_helper
from wlsdeploy.tool.deploy import log_helper
from wlsdeploy.tool.deploy.deployer import Deployer


class JmsResourcesDeployer(Deployer):
    """
    class docstring
    """
    _class_name = "JmsResourcesDeployer"

    # resource elements in deployment order
    resource_elements = [
        QUOTA,
        DESTINATION_KEY,
        QUEUE,
        DISTRIBUTED_QUEUE,
        TOPIC,
        DISTRIBUTED_TOPIC,
        UNIFORM_DISTRIBUTED_QUEUE,
        UNIFORM_DISTRIBUTED_TOPIC,
        TEMPLATE,
        CONNECTION_FACTORY,
        FOREIGN_SERVER,
        SAF_REMOTE_CONTEXT,
        SAF_IMPORTED_DESTINATION,
        SAF_ERROR_HANDLING
    ]

    # used for placeholder template generation
    template_destination_type_names = [
        QUEUE,
        TOPIC,
        UNIFORM_DISTRIBUTED_QUEUE,
        UNIFORM_DISTRIBUTED_TOPIC
    ]

    def __init__(self, model, model_context, aliases, wlst_mode=WlstModes.OFFLINE):
        Deployer.__init__(self, model, model_context, aliases, wlst_mode)

    def add_jms_system_resources(self, parent_dict, location):
        system_resources = dictionary_utils.get_dictionary_element(parent_dict, JMS_SYSTEM_RESOURCE)
        self._add_named_elements(JMS_SYSTEM_RESOURCE, system_resources, location)
        return

    # Override
    def _add_named_elements(self, type_name, model_nodes, location):
        """
        Override the base method for these special cases:
        1) Group params require special handling.
        2) Destinations may require placeholder templates.
        """
        if type_name == GROUP_PARAMS:
            self._add_group_params(model_nodes, location)
            return

        if type_name == JNDI_PROPERTY:
            self._add_jndi_properties(model_nodes, location)
            return

        if type_name in self.template_destination_type_names:
            self._check_destination_template(model_nodes, location)
            # continue with regular processing

        Deployer._add_named_elements(self, type_name, model_nodes, location)

    # Override
    def _add_model_elements(self, type_name, model_nodes, location):
        """
        Override the base method for these special cases:
        1) JMS resources must be deployed in specific order.
        2) JNDI properties require special handling.
        """
        if type_name == JMS_RESOURCE:
            self._add_jms_resources(model_nodes, location)
            return

        Deployer._add_model_elements(self, type_name, model_nodes, location)

    def _add_jms_resources(self, resource_nodes, location):
        """
        Special processing to process child nodes in specific order
        :param resource_nodes: the JMS resource model nodes
        :param location: the location to add resources
        """
        if not len(resource_nodes):
            return

        location = LocationContext(location).append_location(JMS_RESOURCE)
        if not self._check_location(location):
            return
        deployer_utils.set_single_folder_token(location, self.aliases)

        # SAF imported destination may reference error handling, and vice versa
        self.topology_helper.create_placeholder_named_elements(location, SAF_ERROR_HANDLING, resource_nodes)
        # Error destinations for Topics, Queues, Templates reference other Topics, Queues
        self._create_placeholder_for_error_destinations(location, resource_nodes)

        for element_name in self.resource_elements:
            model_nodes = dictionary_utils.get_dictionary_element(resource_nodes, element_name)
            self._add_named_elements(element_name, model_nodes, location)
        return

    def _create_placeholder_for_error_destinations(self, location, resource_nodes):
        self.topology_helper.create_placeholder_named_elements(location, QUEUE, resource_nodes)
        self.topology_helper.create_placeholder_named_elements(location, DISTRIBUTED_QUEUE, resource_nodes)
        self.topology_helper.create_placeholder_named_elements(location, UNIFORM_DISTRIBUTED_QUEUE, resource_nodes)
        self.topology_helper.create_placeholder_named_elements(location, TOPIC, resource_nodes)
        self.topology_helper.create_placeholder_named_elements(location, DISTRIBUTED_TOPIC, resource_nodes)
        self.topology_helper.create_placeholder_named_elements(location, UNIFORM_DISTRIBUTED_TOPIC, resource_nodes)
        self.topology_helper.create_placeholder_named_elements(location, TEMPLATE, resource_nodes)

    def _add_jndi_properties(self, property_name_nodes, location):
        """
        Add each property entry from property nodes and set its attributes.
        A two-pass approach is required since the new folder's name does not always match the property name.
        :param property_name_nodes: the nodes containing property names
        :param location: the WLST location where the properties should be added
        """
        _method_name = '_add_jndi_properties'
        if len(property_name_nodes) == 0:
            return

        # use a copy of the dictionary to remove items as they are deleted
        remaining_name_nodes = property_name_nodes.copy()

        parent_type, parent_name = self.get_location_type_and_name(location)
        is_online = self.wlst_mode == WlstModes.ONLINE
        if is_online and deployer_utils.is_in_resource_group_or_template(location):
            self.logger.info('WLSDPLY-09501', JNDI_PROPERTY, parent_type, parent_name, class_name=self._class_name,
                             method_name=_method_name)
            return

        foreign_server_path = self.aliases.get_wlst_subfolders_path(location)
        properties_location = LocationContext(location).append_location(JNDI_PROPERTY)
        properties_token = self.aliases.get_name_token(properties_location)
        name_attribute = self.aliases.get_wlst_attribute_name(properties_location, KEY)
        mbean_type = self.aliases.get_wlst_mbean_type(properties_location)

        for property_name in property_name_nodes:
            if model_helper.is_delete_name(property_name):
                name = model_helper.get_delete_item_name(property_name)
                self._delete_mapped_mbean(properties_location, properties_token, mbean_type, name_attribute, name)
                del remaining_name_nodes[property_name]

        # loop once to create and name any missing folders.
        folder_map = self._build_folder_map(properties_location, properties_token, name_attribute)

        for property_name in remaining_name_nodes:
            folder_name = dictionary_utils.get_element(folder_map, property_name)
            if folder_name is None:
                self.wlst_helper.cd(foreign_server_path)
                new_property = self.wlst_helper.create(property_name, mbean_type)
                new_property.setKey(property_name)

        # loop a second time to set attributes
        new_folder_map = self._build_folder_map(properties_location, properties_token, name_attribute)

        for property_name in remaining_name_nodes:
            is_add = property_name not in folder_map
            log_helper.log_updating_named_folder(JNDI_PROPERTY, property_name, parent_type, parent_name, is_add,
                                                 self._class_name, _method_name)

            folder_name = dictionary_utils.get_element(new_folder_map, property_name)
            properties_location.add_name_token(properties_token, folder_name)
            self.wlst_helper.cd(self.aliases.get_wlst_attributes_path(properties_location))

            property_nodes = remaining_name_nodes[property_name]
            self.set_attributes(properties_location, property_nodes)

    def _add_group_params(self, group_name_nodes, location):
        """
        Add each group param entry from group name nodes and set its attributes.
        A two-pass approach is required since the new folder's name does not always match the group name.
        Special processing for error destination attributes (build mbean)
        :param group_name_nodes: the nodes containing group parameter names
        :param location: the WLST location where the parameters should be added
        """
        _method_name = '_add_group_params'
        if len(group_name_nodes) == 0:
            return

        # use a copy of the dictionary to remove items as they are deleted
        remaining_name_nodes = group_name_nodes.copy()

        parent_type, parent_name = self.get_location_type_and_name(location)
        template_path = self.aliases.get_wlst_subfolders_path(location)
        groups_location = LocationContext(location)
        groups_location.append_location(GROUP_PARAMS)
        groups_token = self.aliases.get_name_token(groups_location)
        name_attribute = self.aliases.get_wlst_attribute_name(groups_location, SUB_DEPLOYMENT_NAME)
        mbean_type = self.aliases.get_wlst_mbean_type(groups_location)

        for group_name in group_name_nodes:
            if model_helper.is_delete_name(group_name):
                group_nodes = group_name_nodes[group_name]
                name = model_helper.get_delete_item_name(group_name)
                sub_name = self._get_subdeployment_name(group_nodes, name)
                self._delete_mapped_mbean(groups_location, groups_token, mbean_type, name_attribute, sub_name)
                del remaining_name_nodes[group_name]

        # loop once to create and name any missing folders.
        folder_map = self._build_folder_map(groups_location, groups_token, name_attribute)

        for group_name in remaining_name_nodes:
            group_nodes = remaining_name_nodes[group_name]
            sub_deployment_name = self._get_subdeployment_name(group_nodes, group_name)
            folder_name = dictionary_utils.get_element(folder_map, sub_deployment_name)
            if folder_name is None:
                self.wlst_helper.cd(template_path)
                group = self.wlst_helper.create(sub_deployment_name, mbean_type)
                group.setSubDeploymentName(sub_deployment_name)

        # loop a second time to set attributes
        new_folder_map = self._build_folder_map(groups_location, groups_token, name_attribute)

        for group_name in remaining_name_nodes:
            group_nodes = remaining_name_nodes[group_name]
            sub_deployment_name = self._get_subdeployment_name(group_nodes, group_name)
            is_add = sub_deployment_name not in folder_map
            log_helper.log_updating_named_folder(GROUP_PARAMS, group_name, parent_type, parent_name, is_add,
                                                 self._class_name, _method_name)

            folder_name = dictionary_utils.get_element(new_folder_map, sub_deployment_name)
            groups_location.add_name_token(groups_token, folder_name)
            self.wlst_helper.cd(self.aliases.get_wlst_attributes_path(groups_location))
            self.set_attributes(groups_location, group_nodes)

    def _delete_mapped_mbean(self, folder_location, folder_token, mbean_type, name_attribute, name):
        """
        Delete the child MBean with an attribute value that matches the specified name.
        This requires looping through the child MBeans for each deletion, since the MBean names change on delete.
        :param folder_location: the WLST location for the folder with named sub-elements
        :param folder_token: the folder token used to iterate through the MBean names
        :param mbean_type: the MBean type of the sub-elements
        :param name_attribute: the attribute for the name in each sub-element
        :param name: the name of the sub-element to be deleted
        """
        _method_name = '_delete_mapped_mbean'

        original_path = self.wlst_helper.get_pwd()
        mapped_folder_name = None

        folder_names = deployer_utils.get_existing_object_list(folder_location, self.aliases)
        for folder_name in folder_names:
            folder_location.add_name_token(folder_token, folder_name)
            self.wlst_helper.cd(self.aliases.get_wlst_attributes_path(folder_location))
            attribute_value = self.wlst_helper.get(name_attribute)
            if attribute_value == name:
                mapped_folder_name = folder_name
                break

        self.wlst_helper.cd(original_path)

        if mapped_folder_name is None:
            self.logger.warning('WLSDPLY-09109', mbean_type, name,
                                class_name=self._class_name, method_name=_method_name)
        else:
            self.logger.info('WLSDPLY-09110', mbean_type, name,
                             class_name=self._class_name, method_name=_method_name)
            self.wlst_helper.delete(mapped_folder_name, mbean_type)

    def _build_folder_map(self, folder_location, folder_token, name_attribute):
        """
        Build a map of existing sub-element names to folders.
        :param folder_location: the WLST location for the folder with named sub-elements
        :param folder_token: the folder token used to set the mbean name
        :param name_attribute: the attribute for the name in each sub-element
        :return: a map of existing sub-element names to folder names
        """
        original_path = self.wlst_helper.get_pwd()

        folder_names = deployer_utils.get_existing_object_list(folder_location, self.aliases)
        folder_map = OrderedDict()

        for folder_name in folder_names:
            folder_location.add_name_token(folder_token, folder_name)
            self.wlst_helper.cd(self.aliases.get_wlst_attributes_path(folder_location))
            name = self.wlst_helper.get(name_attribute)
            folder_map[name] = folder_name

        self.wlst_helper.cd(original_path)
        return folder_map

    def _get_subdeployment_name(self, group_nodes, group_name):
        """
        Returns the derived sub-deployment name for the specified group name.
        The sub-deployment name attribute is returned if specified, otherwise the group name is returned.
        :param group_nodes: the group nodes from the model
        :param group_name: the group name being examined
        :return: the derived sub-deployment name
        """
        sub_deployment_name = dictionary_utils.get_element(group_nodes, SUB_DEPLOYMENT_NAME)
        if sub_deployment_name is not None:
            return sub_deployment_name
        return group_name

    def _check_destination_template(self, destination_nodes, location):
        """
        Check the destination nodes for a template element, and create a placeholder template if required.
        :param destination_nodes: the destination nodes to be examined
        :param location: the location of the destination parent
        """
        for name in destination_nodes:
            child_nodes = dictionary_utils.get_dictionary_element(destination_nodes, name)
            template_name = dictionary_utils.get_element(child_nodes, TEMPLATE)
            if template_name is not None:
                self._create_placeholder_jms_template(template_name, location)
        return

    def _create_placeholder_jms_template(self, template_name, resource_location):
        """
        :param template_name: the name of the template to be added
        :param resource_location: the location where the template should be added
        """
        _method_name = '_create_placeholder_jms_template'
        original_location = self.wlst_helper.get_pwd()
        template_location = LocationContext(resource_location).append_location(TEMPLATE)
        existing_names = deployer_utils.get_existing_object_list(template_location, self.aliases)

        if template_name not in existing_names:
            self.logger.info('WLSDPLY-09500', template_name, class_name=self._class_name, method_name=_method_name)

        template_token = self.aliases.get_name_token(template_location)
        template_location.add_name_token(template_token, template_name)
        result = deployer_utils.create_and_cd(template_location, existing_names, self.aliases)

        self.wlst_helper.cd(original_location)
        return result
