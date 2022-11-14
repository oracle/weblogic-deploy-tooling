"""
Copyright (c) 2017, 2022, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
from java.lang import IllegalArgumentException

from oracle.weblogic.deploy.util import PyOrderedDict as OrderedDict
from oracle.weblogic.deploy.util import WLSDeployArchive
from oracle.weblogic.deploy.util import WLSDeployArchiveIOException

from wlsdeploy.aliases import model_constants
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import FILE_URI
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.deploy import deployer_utils
from wlsdeploy.tool.discover import discoverer
from wlsdeploy.tool.discover.discoverer import Discoverer
import wlsdeploy.util.unicode_helper as str_helper

_class_name = 'JmsResourcesDiscoverer'
_logger = PlatformLogger(discoverer.get_discover_logger_name())


class JmsResourcesDiscoverer(Discoverer):
    """
    Discover the weblogic jms resources from the domain. Store the discovered values in the schema approved
    model format json or yaml file.
    """

    def __init__(self, model_context, resource_dictionary, base_location,
                 wlst_mode=WlstModes.OFFLINE, aliases=None, credential_injector=None):
        Discoverer.__init__(self, model_context, base_location, wlst_mode, aliases, credential_injector)
        self._dictionary = resource_dictionary

    def discover(self):
        """
        Discover weblogic resources from the on-premise domain.
        :return: resources dictionary created or updated during the jms discover
        """
        _method_name = 'discover'
        _logger.entering(class_name=_class_name, method_name=_method_name)
        _logger.fine('WLSDPLY-06460', class_name=_class_name, method_name=_method_name)
        model_folder_name, jms_servers = self.get_jms_servers()
        discoverer.add_to_model_if_not_empty(self._dictionary, model_folder_name, jms_servers)
        model_folder_name, saf_agents = self.get_saf_agents()
        discoverer.add_to_model_if_not_empty(self._dictionary, model_folder_name, saf_agents)
        model_folder_name, jms_resources = self.get_jms_system_resources()
        discoverer.add_to_model_if_not_empty(self._dictionary, model_folder_name, jms_resources)
        model_folder_name, bridge_destinations = self.get_jms_bridge_destinations()
        discoverer.add_to_model_if_not_empty(self._dictionary, model_folder_name, bridge_destinations)
        model_folder_name, bridges = self.get_jms_bridges()
        discoverer.add_to_model_if_not_empty(self._dictionary, model_folder_name, bridges)

        _logger.exiting(class_name=_class_name, method_name=_method_name, result=self._dictionary)
        return self._dictionary

    def get_jms_servers(self):
        """
        Discover the JMS servers from the domain.
        :return: model folder name: dictionary containing the discovered JMS servers
        """
        _method_name = 'get_jms_servers'
        _logger.entering(class_name=_class_name, method_name=_method_name)
        result = OrderedDict()
        model_top_folder_name = model_constants.JMS_SERVER
        location = LocationContext(self._base_location)
        location.append_location(model_top_folder_name)
        jms_servers = self._find_names_in_folder(location)
        if jms_servers is not None:
            _logger.info('WLSDPLY-06470', len(jms_servers), class_name=_class_name, method_name=_method_name)
            typedef = self._model_context.get_domain_typedef()
            name_token = self._aliases.get_name_token(location)
            for jms_server in jms_servers:
                if typedef.is_system_jms_server(jms_server):
                    _logger.info('WLSDPLY-06490', typedef.get_domain_type(), jms_server, class_name=_class_name,
                                 method_name=_method_name)
                else:
                    _logger.info('WLSDPLY-06471', jms_server, class_name=_class_name, method_name=_method_name)
                    location.add_name_token(name_token, jms_server)
                    result[jms_server] = OrderedDict()
                    self._populate_model_parameters(result[jms_server], location)
                    self._discover_subfolders(result[jms_server], location)
                    location.remove_name_token(name_token)

        _logger.exiting(class_name=_class_name, method_name=_method_name, result=result)
        return model_top_folder_name, result

    def get_saf_agents(self):
        """
        Discover the SAF agents from the domain.
        :return: model folder name: dictionary containing the discovered SAF agents
        """
        _method_name = 'get_saf_agents'
        _logger.entering(class_name=_class_name, method_name=_method_name)
        result = OrderedDict()
        model_top_folder_name = model_constants.SAF_AGENT
        location = LocationContext(self._base_location)
        location.append_location(model_top_folder_name)
        agents = self._find_names_in_folder(location)
        if agents is not None:
            _logger.info('WLSDPLY-06472', len(agents), class_name=_class_name, method_name=_method_name)
            name_token = self._aliases.get_name_token(location)
            for agent in agents:
                _logger.info('WLSDPLY-06473', agent, class_name=_class_name, method_name=_method_name)
                location.add_name_token(name_token, agent)
                result[agent] = OrderedDict()
                self._populate_model_parameters(result[agent], location)
                self._discover_subfolders(result[agent], location)
                location.remove_name_token(name_token)
        _logger.exiting(class_name=_class_name, method_name=_method_name, result=result)
        return model_top_folder_name, result

    def get_jms_bridge_destinations(self):
        """
        Discover the JMS bridge destinations from the domain.
        :return: model folder name: dictionary containing the discovered bridge destinations
        """
        _method_name = 'get_jms_bridge_destinations'
        _logger.entering(class_name=_class_name, method_name=_method_name)
        result = OrderedDict()
        model_top_folder_name = model_constants.JMS_BRIDGE_DESTINATION
        location = LocationContext(self._base_location)
        location.append_location(model_top_folder_name)
        destinations = self._find_names_in_folder(location)
        if destinations is not None:
            _logger.info('WLSDPLY-06474', len(destinations), class_name=_class_name, method_name=_method_name)
            name_token = self._aliases.get_name_token(location)
            for destination in destinations:
                _logger.info('WLSDPLY-06475', destination, class_name=_class_name, method_name=_method_name)
                result[destination] = OrderedDict()
                location.add_name_token(name_token, destination)
                self._populate_model_parameters(result[destination], location)
                location.remove_name_token(name_token)
        _logger.exiting(class_name=_class_name, method_name=_method_name, result=result)
        return model_top_folder_name, result

    def get_jms_bridges(self):
        """
        Discover the JMS Bridges from the domain.
        :return: model folder name: dictionary containing the discovered JMS bridges
        """
        _method_name = 'get_jms_bridges'
        _logger.entering(class_name=_class_name, method_name=_method_name)
        result = OrderedDict()
        model_top_folder_name = model_constants.MESSAGING_BRIDGE
        location = LocationContext(self._base_location)
        location.append_location(model_top_folder_name)
        bridges = self._find_names_in_folder(location)
        if bridges is not None:
            _logger.info('WLSDPLY-06476', len(bridges), class_name=_class_name, method_name=_method_name)
            name_token = self._aliases.get_name_token(location)
            for bridge in bridges:
                _logger.info('WLSDPLY-06477', bridge, class_name=_class_name, method_name=_method_name)
                result[bridge] = OrderedDict()
                location.add_name_token(name_token, bridge)
                self._populate_model_parameters(result[bridge], location)
                location.remove_name_token(name_token)
        _logger.exiting(class_name=_class_name, method_name=_method_name, result=result)
        return model_top_folder_name, result

    def get_jms_system_resources(self):
        """
        Discover the JMS system resources, including the sub-deployments, system resource attributes and all
        the entities contained within a system resource from the domain.
        :return: model folder name: dictionary with the discovered JMS system resources
        """
        _method_name = 'get_jms_system_resources'
        _logger.entering(class_name=_class_name, method_name=_method_name)
        result = OrderedDict()
        model_top_folder_name = model_constants.JMS_SYSTEM_RESOURCE
        location = LocationContext(self._base_location)
        location.append_location(model_top_folder_name)
        jms_resources = self._find_names_in_folder(location)
        if jms_resources is not None:
            _logger.info('WLSDPLY-06478', len(jms_resources), class_name=_class_name, method_name=_method_name)
            typedef = self._model_context.get_domain_typedef()
            name_token = self._aliases.get_name_token(location)
            for jms_resource in jms_resources:
                if typedef.is_system_jms(jms_resource):
                    _logger.info('WLSDPLY-06491', typedef.get_domain_type(), jms_resource, class_name=_class_name,
                                 method_name=_method_name)
                else:
                    _logger.info('WLSDPLY-06479', jms_resource, class_name=_class_name, method_name=_method_name)
                    result[jms_resource] = OrderedDict()
                    location.add_name_token(name_token, jms_resource)
                    self._populate_model_parameters(result[jms_resource], location)
                    model_subfolder_name, subfolder_result = self._get_subdeployments(location)
                    discoverer.add_to_model_if_not_empty(result[jms_resource], model_subfolder_name, subfolder_result)
                    model_subfolder_name, subfolder_result = self._get_jms_resources(location)
                    discoverer.add_to_model_if_not_empty(result[jms_resource], model_subfolder_name, subfolder_result)
                    location.remove_name_token(name_token)

        _logger.exiting(class_name=_class_name, method_name=_method_name, result=result)
        return model_top_folder_name, result

    #  Private methods

    def _get_subdeployments(self, location):
        _method_name = '_get_subdeployments'
        _logger.entering(class_name=_class_name, method_name=_method_name)
        model_subfolder_name = model_constants.SUB_DEPLOYMENT
        location.append_location(model_subfolder_name)
        result = self._discover_subfolder_with_names(model_subfolder_name, location,
                                                     self._aliases.get_name_token(location))
        location.pop_location()
        _logger.exiting(class_name=_class_name, method_name=_method_name)
        return model_subfolder_name, result

    def _get_jms_resources(self, location):
        _method_name = '_get_jms_resources'
        _logger.entering(class_name=_class_name, method_name=_method_name)
        result = OrderedDict()
        model_name = model_constants.JMS_RESOURCE
        location.append_location(model_name)
        deployer_utils.set_single_folder_token(location, self._aliases)
        self._populate_model_parameters(result, location)
        wlst_subfolders = self._find_subfolders(location)
        if wlst_subfolders is not None:
            for wlst_subfolder in wlst_subfolders:
                model_subfolder_name = self._get_model_name(location, wlst_subfolder)
                if model_subfolder_name:
                    if model_subfolder_name == model_constants.TEMPLATE:
                        model_subfolder_name, subfolder_result = self._get_jms_templates(location)
                        discoverer.add_to_model_if_not_empty(result, model_subfolder_name, subfolder_result)
                    elif model_subfolder_name == model_constants.FOREIGN_SERVER:
                        model_subfolder_name, subfolder_result = self._get_foreign_servers(location)
                        discoverer.add_to_model_if_not_empty(result, model_subfolder_name, subfolder_result)
                    else:
                        self._discover_subfolder(model_subfolder_name, location, result)
        location.pop_location()
        _logger.exiting(class_name=_class_name, method_name=_method_name, result=result)
        return model_name, result

    def _get_foreign_servers(self, location):
        """
        Discover the foreign servers for the JMS resource from the domain.
        :param location: context containing the current location information
        :return: model folder name: dictionary containing the discovered foreign servers for the JMS resource
        """
        _method_name = '_get_foreign_servers'
        _logger.entering(str_helper.to_string(location), class_name=_class_name, method_name=_method_name)
        result = OrderedDict()
        model_top_folder_name = model_constants.FOREIGN_SERVER
        location.append_location(model_top_folder_name)
        servers = self._find_names_in_folder(location)
        if servers is not None:
            name_token = self._aliases.get_name_token(location)
            for server in servers:
                _logger.finer('WLSDPLY-06480', server, self._aliases.get_model_folder_path(location),
                              class_name=_class_name, method_name=_method_name)
                result[server] = OrderedDict()
                location.add_name_token(name_token, server)
                self._populate_model_parameters(result[server], location)
                if model_constants.CONNECTION_URL in result[server]:
                    _logger.finer('WLSDPLY-06494', server, class_name=_class_name, method_name=_method_name)
                    result[server][model_constants.CONNECTION_URL] = \
                        self._add_foreign_server_binding(server, model_constants.CONNECTION_URL,
                                                         result[server][model_constants.CONNECTION_URL])
                wlst_subfolders = self._find_subfolders(location)
                if wlst_subfolders is not None:
                    for wlst_subfolder in wlst_subfolders:
                        model_subfolder_name = self._get_model_name(location, wlst_subfolder)
                        if model_subfolder_name and model_subfolder_name == model_constants.JNDI_PROPERTY:
                            model_subfolder_name, subfolder_result = self._get_foreign_server_properties(location)
                            discoverer.add_to_model_if_not_empty(result[server], model_subfolder_name, subfolder_result)
                        else:
                            self._discover_subfolder(model_subfolder_name, location, result[server])
                location.remove_name_token(name_token)
        location.pop_location()
        _logger.exiting(class_name=_class_name, method_name=_method_name, result=result)
        return model_top_folder_name, result

    def _get_jms_templates(self, location):
        """
        Discover the JMS templates for the JMS resource from the domain.
        :param location: context containing the current location information
        :return: model folder name: dictionary containing the discovered JMS template
        """
        _method_name = '_get_jms_templates'
        _logger.entering(str_helper.to_string(location), class_name=_class_name, method_name=_method_name)
        result = OrderedDict()
        model_top_folder_name = model_constants.TEMPLATE
        location.append_location(model_top_folder_name)
        templates = self._find_names_in_folder(location)
        if templates is not None:
            name_token = self._aliases.get_name_token(location)
            for template in templates:
                _logger.finer('WLSDPLY-06481', template, self._aliases.get_model_folder_path(location),
                              class_name=_class_name, method_name=_method_name)
                result[template] = OrderedDict()
                location.add_name_token(name_token, template)
                self._populate_model_parameters(result[template], location)
                wlst_subfolders = self._find_subfolders(location)
                if wlst_subfolders is not None:
                    for wlst_subfolder in wlst_subfolders:
                        model_subfolder_name = self._aliases.get_model_subfolder_name(location, wlst_subfolder)
                        _logger.finer('WLSDPLY-06485', model_subfolder_name, template, class_name=_class_name,
                                      method_name=_method_name)
                        if model_subfolder_name == model_constants.GROUP_PARAMS:
                            model_subfolder_name, subfolder_result = self._get_group_params(location)
                            discoverer.add_to_model_if_not_empty(result[template], model_subfolder_name,
                                                                 subfolder_result)
                        else:
                            self._discover_subfolder(model_subfolder_name, location, result[template])
                location.remove_name_token(name_token)
        location.pop_location()
        _logger.exiting(class_name=_class_name, method_name=_method_name, result=result)
        return model_top_folder_name, result

    def _get_group_params(self, location):
        """
        This is a private method.

        Discover the JMS Resource Group Params. The group param subdeployment name is the name
        entry for a group param in the model.
        :param location: context containing the current location information
        :return: model folder name: dictionary containing the discovered group params
        """
        _method_name = '_get_group_params'
        _logger.entering(str_helper.to_string(location), class_name=_class_name, method_name=_method_name)

        model_subfolder_name = model_constants.GROUP_PARAMS
        subfolder_result = OrderedDict()
        location.append_location(model_subfolder_name)
        folder_names = self._find_names_in_folder(location)
        if folder_names is not None:
            name_token = self._aliases.get_name_token(location)
            for folder_name in folder_names:
                location.add_name_token(name_token, folder_name)
                wlst_subdeployment = self._aliases.get_wlst_attribute_name(location,
                                                                                model_constants.SUB_DEPLOYMENT_NAME)
                attributes = self._get_attributes_for_current_location(location)
                if wlst_subdeployment is None or wlst_subdeployment not in attributes:
                    _logger.warning('WLSDPLY-06486', folder_name, self._aliases.get_model_folder_path(location),
                                    class_name=_class_name, method_name=_method_name)
                else:
                    group_param_name = attributes[wlst_subdeployment]
                    if group_param_name is None:
                        _logger.warning('WLSDPLY-06486', folder_name,
                                        self._aliases.get_model_folder_path(location),
                                        class_name=_class_name, method_name=_method_name)
                    else:
                        _logger.finer('WLSDPLY-06487', group_param_name,
                                      self._aliases.get_model_folder_path(location),
                                      class_name=_class_name, method_name=_method_name)
                        subfolder_result[group_param_name] = OrderedDict()
                        self._populate_model_parameters(subfolder_result[group_param_name], location)
                location.remove_name_token(name_token)
        location.pop_location()
        _logger.exiting(class_name=_class_name, method_name=_method_name, result=subfolder_result)
        return model_subfolder_name, subfolder_result

    def _get_foreign_server_properties(self, location):
        """
        This is a private method.

        Discover the foreign server properties for the foreign server from the domain. Special handling of
        the properties is necessary to convert into the model format. The Key value of the Property is used
        as the Property name in the model in place of the Property name returned by wlst. In offline, this
        property name is a NO_NAME string value.
        :param location: context containing current location information
        :return: model name for the properties: dictionary containing the discovered foreign server properties
        """
        _method_name = '_get_foreign_server_properties'
        _logger.entering(str_helper.to_string(location), class_name=_class_name, method_name=_method_name)

        model_subfolder_name = model_constants.JNDI_PROPERTY
        subfolder_result = OrderedDict()
        location.append_location(model_subfolder_name)
        folder_names = self._find_names_in_folder(location)
        if folder_names is not None:
            name_token = self._aliases.get_name_token(location)
            for folder_name in folder_names:
                location.add_name_token(name_token, folder_name)
                wlst_key = self._aliases.get_wlst_attribute_name(location, model_constants.KEY)
                attributes = self._get_attributes_for_current_location(location)
                if wlst_key is None or wlst_key not in attributes:
                    _logger.warning('WLSDPLY-06488', folder_name, self._aliases.get_model_folder_path(location),
                                    class_name=_class_name, method_name=_method_name)
                else:
                    property_name = attributes[wlst_key]
                    _logger.finer('WLSDPLY-06489', property_name, self._aliases.get_model_folder_path(location),
                                  class_name=_class_name, method_name=_method_name)
                    subfolder_result[property_name] = OrderedDict()
                    self._populate_model_parameters(subfolder_result[property_name], location)
                location.remove_name_token(name_token)
        location.pop_location()
        _logger.exiting(class_name=_class_name, method_name=_method_name, result=subfolder_result)
        return model_subfolder_name, subfolder_result

    def _add_foreign_server_binding(self, server_name, model_name, model_value):
        """
        If the foreign server connection URL contains a file URI, then collect the file into the archive.
        The attribute value will be updated to point to the location where the file will
        exist after the archive file is deployed.
        :param model_name: name of the foreign server connection URL name attribute
        :param model_value: containing the foreign connection URI value
        :return: updated foreign server file value or original URL
        """
        _method_name = '_add_foreign_server_binding'
        _logger.entering(server_name, model_name, model_value, class_name=_class_name, method_name=_method_name)
        new_name = model_value
        if model_value is not None:
            success, _, file_name = self._get_from_url('Foreign Server ' + server_name + ' Connection URL', model_value)
            archive_file = self._model_context.get_archive_file()
            if success and file_name is not None:
                if not self._model_context.is_remote():
                    file_name = self._convert_path(file_name)
                    _logger.finer('WLSDPLY-06495', server_name, file_name, class_name=_class_name, method_name=_method_name)
                if self._model_context.is_remote():
                    new_name = archive_file.getForeignServerArchivePath(server_name, file_name)
                    self.add_to_remote_map(file_name, new_name,
                                           WLSDeployArchive.ArchiveEntryType.JMS_FOREIGN_SERVER.name())
                elif not self._model_context.skip_archive():
                    try:
                        new_name = archive_file.addForeignServerFile(server_name, file_name)
                        new_name = FILE_URI + self._model_context.tokenize_path(self._convert_path(new_name))
                        _logger.info('WLSDPLY-06492', server_name, file_name, new_name, class_name=_class_name,
                                     method_name=_method_name)
                    except (IllegalArgumentException, WLSDeployArchiveIOException), wioe:
                        _logger.warning('WLSDPLY-06493', server_name, file_name, wioe.getLocalizedMessage(),
                                        class_name=_class_name, method_name=_method_name)
                        new_name = None

        _logger.exiting(class_name=_class_name, method_name=_method_name, result=new_name)
        return new_name
