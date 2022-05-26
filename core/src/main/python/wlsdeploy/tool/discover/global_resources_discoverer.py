"""
Copyright (c) 2017, 2020, Oracle Corporation and/or its affiliates.  All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import os
from java.io import File
from oracle.weblogic.deploy.util import PyOrderedDict as OrderedDict

from wlsdeploy.aliases import model_constants
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.discover import discoverer
from wlsdeploy.tool.discover.discoverer import Discoverer

_class_name = 'GlobalResourcesDiscoverer'
_logger = PlatformLogger(discoverer.get_discover_logger_name())


class GlobalResourcesDiscoverer(Discoverer):
    """
    Discover the weblogic global only resources from the domain.
    """

    TYPE_domain = "Domain"

    def __init__(self, model_context, resource_dictionary, base_location,
                 wlst_mode=WlstModes.OFFLINE, aliases=None, credential_injector=None):
        """

        :param model_context: context about the model for this instance of the discover domain
        :param resource_dictionary: to populate with global resources. Uses the initialized resources if none passed
        """
        Discoverer.__init__(self, model_context, base_location, wlst_mode, aliases, credential_injector)
        self._dictionary = resource_dictionary

    def discover(self):
        """
        Discover weblogic global resources from the domain.
        :return: resources: dictionary containing the discovered global resources
        """
        _method_name = 'discover'
        _logger.entering(class_name=_class_name, method_name=_method_name)
        _logger.finer('WLSDPLY-06440', class_name=_class_name, method_name=_method_name)
        model_top_folder_name, self_tuning = self.get_self_tuning()
        discoverer.add_to_model_if_not_empty(self._dictionary, model_top_folder_name, self_tuning)
        model_top_folder_name, startups = self.get_startup_classes()
        discoverer.add_to_model_if_not_empty(self._dictionary, model_top_folder_name, startups)
        model_top_folder_name, shutdowns = self.get_shutdown_classes()
        discoverer.add_to_model_if_not_empty(self._dictionary, model_top_folder_name, shutdowns)
        model_top_folder_name, web_app_container = self.get_webapp_container()
        discoverer.add_to_model_if_not_empty(self._dictionary, model_top_folder_name, web_app_container)
        model_top_folder_name, singleton_services = self.get_singleton_service()
        discoverer.add_to_model_if_not_empty(self._dictionary, model_top_folder_name, singleton_services)
        model_top_folder_name, jolt_pools = self.get_jolt_connection_pool()
        discoverer.add_to_model_if_not_empty(self._dictionary, model_top_folder_name, jolt_pools)
        model_top_folder_name, wtc_servers = self.get_wtc_servers()
        discoverer.add_to_model_if_not_empty(self._dictionary, model_top_folder_name, wtc_servers)

        _logger.exiting(class_name=_class_name, method_name=_method_name)
        return self._dictionary

    def get_self_tuning(self):
        """
        Discover the self-tuning attributes from the domain.
        :return: model folder name: dictionary containing the discovered self tuning
        """
        _method_name = 'get_self_tuning'
        _logger.entering(class_name=_class_name, method_name=_method_name)
        result = OrderedDict()
        model_top_folder_name = model_constants.SELF_TUNING
        location = LocationContext(self._base_location)
        location.append_location(model_top_folder_name)
        tuning = self._find_singleton_name_in_folder(location)
        if tuning is not None:
            location.add_name_token(self._aliases.get_name_token(location), tuning)
            _logger.info('WLSDPLY-06441', class_name=_class_name, method_name=_method_name)
            self._discover_subfolders(result, location)
        _logger.exiting(class_name=_class_name, method_name=_method_name, result=result)
        return model_top_folder_name, result

    def get_startup_classes(self):
        """
        Discover the StartupClasses for the domain.
        :return: model name for the dictionary and the dictionary containing the startup class information
        """
        _method_name = 'get_startup_classes'
        _logger.entering(class_name=_class_name, method_name=_method_name)
        result = OrderedDict()
        model_top_folder_name = model_constants.STARTUP_CLASS
        location = LocationContext(self._base_location)
        location.append_location(model_top_folder_name)
        startup_classes = self._find_names_in_folder(location)
        if startup_classes is not None:
            _logger.info('WLSDPLY-06442', len(startup_classes), class_name=_class_name, method_name=_method_name)
            typedef = self._model_context.get_domain_typedef()
            name_token = self._aliases.get_name_token(location)
            for startup_class in startup_classes:
                if typedef.is_system_startup_class(startup_class):
                    _logger.info('WLSDPLY-06447', typedef.get_domain_type(), startup_class, class_name=_class_name,
                                 method_name=_method_name)
                else:
                    _logger.info('WLSDPLY-06443', startup_class, class_name=_class_name, method_name=_method_name)
                    result[startup_class] = OrderedDict()
                    location.add_name_token(name_token, startup_class)
                    self._populate_model_parameters(result[startup_class], location)
                    location.remove_name_token(name_token)

        _logger.exiting(class_name=_class_name, method_name=_method_name, result=result)
        return model_top_folder_name, result

    def get_shutdown_classes(self):
        """
        Discover ShutdownClass information for the domain.
        :return: model name for the dictionary and the dictionary containing the shutdown class information
        """
        _method_name = 'get_shutdown_classes'
        _logger.entering(class_name=_class_name, method_name=_method_name)
        result = OrderedDict()
        model_top_folder_name = model_constants.SHUTDOWN_CLASS
        location = LocationContext(self._base_location)
        location.append_location(model_top_folder_name)
        shutdown_classes = self._find_names_in_folder(location)
        if shutdown_classes is not None:
            _logger.info('WLSDPLY-06445', len(shutdown_classes), class_name=_class_name, method_name=_method_name)
            typedef = self._model_context.get_domain_typedef()
            name_token = self._aliases.get_name_token(location)
            for shutdown_class in shutdown_classes:
                if typedef.is_system_shutdown_class(shutdown_class):
                    _logger.info('WLSDPLY-06448', typedef.get_domain_type(), shutdown_class, class_name=_class_name,
                                 method_name=_method_name)
                else:
                    _logger.info('WLSDPLY-06446', shutdown_class, class_name=_class_name, method_name=_method_name)
                    result[shutdown_class] = OrderedDict()
                    location.add_name_token(name_token, shutdown_class)
                    self._populate_model_parameters(result[shutdown_class], location)
                    location.remove_name_token(name_token)

        _logger.exiting(class_name=_class_name, method_name=_method_name, result=result)
        return model_top_folder_name, result

    def get_webapp_container(self):
        """
        Discover the WebAppContainer global resource settings
        :return: model name for the folder: dictionary containing the discovered WebAppContainer
        """
        _method_name = '_get_webapp_container'
        _logger.entering(class_name=_class_name, method_name=_method_name)
        model_top_folder_name = model_constants.WEBAPP_CONTAINER
        result = OrderedDict()
        location = LocationContext(self._base_location)
        location.append_location(model_top_folder_name)
        webapp_container = self._find_singleton_name_in_folder(location)
        if webapp_container is not None:
            _logger.info('WLSDPLY-06615', class_name=_class_name, method_name=_method_name)
            location.add_name_token(self._aliases.get_name_token(location), webapp_container)
            self._populate_model_parameters(result, location)
            self._discover_subfolders(result, location)
            new_name = self._add_mimemapping_file_to_archive(result)
            if new_name:
                result[model_constants.MIME_MAPPING_FILE] = new_name

        _logger.exiting(class_name=_class_name, method_name=_method_name, result=model_top_folder_name)
        return model_top_folder_name, result

    def _add_mimemapping_file_to_archive(self, web_app_container):
        _method_name = '_add_mimemapping_file_to_archive'
        _logger.entering(web_app_container, class_name=_class_name, method_name=_method_name)
        new_name = None
        if web_app_container:
            if model_constants.MIME_MAPPING_FILE in web_app_container:
                model_value = web_app_container[model_constants.MIME_MAPPING_FILE]
                file_path = model_value
                if not self._model_context.is_remote():
                    file_path = self._convert_path(model_value)
                if os.path.exists(file_path):
                    # There is indeed a mime properties file
                    # we need to change the different path in the model
                    # and add file to the archive similar to apps
                    archive_file = self._model_context.get_archive_file()
                    base_name = os.path.basename(file_path)
                    new_name = archive_file.ARCHIVE_CONFIG_TARGET_DIR + '/' + base_name
                    archive_file.addMimeMappingFile(file_path)

        _logger.exiting(class_name=_class_name, method_name=_method_name, result=new_name)
        return new_name

    def get_singleton_service(self):
        """
        Discover the SingletonService global resource settings
        :return: model name for the folder: dictionary containing the discovered SingletonService
        """
        _method_name = 'get_singleton_service'
        _logger.entering(class_name=_class_name, method_name=_method_name)
        model_top_folder_name = model_constants.SINGLETON_SERVICE
        result = OrderedDict()
        location = LocationContext(self._base_location)
        location.append_location(model_top_folder_name)
        singleton_services = self._find_names_in_folder(location)
        if singleton_services is not None:
            _logger.info('WLSDPLY-06445', len(singleton_services), class_name=_class_name, method_name=_method_name)
            name_token = self._aliases.get_name_token(location)
            for singleton_service in singleton_services:
                _logger.info('WLSDPLY-06446', singleton_service, class_name=_class_name, method_name=_method_name)
                result[singleton_service] = OrderedDict()
                location.add_name_token(name_token, singleton_service)
                self._populate_model_parameters(result[singleton_service], location)
                location.remove_name_token(name_token)

        _logger.exiting(class_name=_class_name, method_name=_method_name, result=model_top_folder_name)
        return model_top_folder_name, result

    def get_jolt_connection_pool(self):
        """
        Discover the global resource Jolt Connection Pool
        :return: model name for the folder: dictionary containing the discovered JoltConnectionPool
        """
        _method_name = 'get_jolt_connection_pool'
        _logger.entering(class_name=_class_name, method_name=_method_name)
        model_top_folder_name = model_constants.JOLT_CONNECTION_POOL
        result = OrderedDict()
        location = LocationContext(self._base_location)
        location.append_location(model_top_folder_name)
        jolt_pools = self._find_names_in_folder(location)
        if jolt_pools is not None:
            _logger.info('WLSDPLY-06449', len(jolt_pools), class_name=_class_name, method_name=_method_name)
            name_token = self._aliases.get_name_token(location)
            for jolt_pool in jolt_pools:
                _logger.info('WLSDPLY-06450', jolt_pool, class_name=_class_name, method_name=_method_name)
                result[jolt_pool] = OrderedDict()
                location.add_name_token(name_token, jolt_pool)
                self._populate_model_parameters(result[jolt_pool], location)
                location.remove_name_token(name_token)

        _logger.exiting(class_name=_class_name, method_name=_method_name, result=model_top_folder_name)
        return model_top_folder_name, result

    def get_wtc_servers(self):
        """
        Discover the WTC servers from the domain.
        :return: model folder name: dictionary containing the discovered WTCServers
        """
        _method_name = 'get_wtc_servers'
        _logger.entering(class_name=_class_name, method_name=_method_name)
        model_top_folder_name = model_constants.WTC_SERVER
        result = OrderedDict()
        location = LocationContext(self._base_location)
        location.append_location(model_top_folder_name)
        wtc_servers = self._find_names_in_folder(location)
        if wtc_servers is not None:
            _logger.info('WLSDPLY-06451', len(wtc_servers), class_name=_class_name, method_name=_method_name)
            name_token = self._aliases.get_name_token(location)
            for wtc_server in wtc_servers:
                _logger.info('WLSDPLY-06452', wtc_server, class_name=_class_name, method_name=_method_name)
                result[wtc_server] = OrderedDict()
                location.add_name_token(name_token, wtc_server)
                self._populate_model_parameters(result[wtc_server], location)
                self._discover_subfolders(result[wtc_server], location)
                location.remove_name_token(name_token)

        _logger.exiting(class_name=_class_name, method_name=_method_name, result=result)
        return model_top_folder_name, result
