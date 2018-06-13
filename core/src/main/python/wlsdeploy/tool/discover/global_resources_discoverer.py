"""
Copyright (c) 2017, 2018, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""
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

    def __init__(self, model_context, resource_dictionary, base_location, wlst_mode=WlstModes.OFFLINE, aliases=None):
        """

        :param model_context: context about the model for this instance of the discover domain
        :param resource_dictionary: to populate with global resources. Uses the initialized resources if none passed
        """
        Discoverer.__init__(self, model_context, base_location, wlst_mode, aliases)
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
            location.add_name_token(self._alias_helper.get_name_token(location), tuning)
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
            name_token = self._alias_helper.get_name_token(location)
            for startup_class in startup_classes:
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
            name_token = self._alias_helper.get_name_token(location)
            for shutdown_class in shutdown_classes:
                _logger.info('WLSDPLY-06446', shutdown_class, class_name=_class_name, method_name=_method_name)
                result[shutdown_class] = OrderedDict()
                location.add_name_token(name_token, shutdown_class)
                self._populate_model_parameters(result[shutdown_class], location)
                location.remove_name_token(name_token)

        _logger.exiting(class_name=_class_name, method_name=_method_name, result=result)
        return model_top_folder_name, result
