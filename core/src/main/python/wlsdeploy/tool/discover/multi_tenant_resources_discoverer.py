"""
Copyright (c) 2017, 2020, Oracle Corporation and/or its affiliates.  All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
from oracle.weblogic.deploy.util import PyOrderedDict as OrderedDict

from wlsdeploy.aliases import model_constants
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.discover import discoverer
from wlsdeploy.tool.discover.discoverer import Discoverer

_class_name = 'MultiTenantResourcesDiscoverer'
_logger = PlatformLogger(discoverer.get_discover_logger_name())


class MultiTenantResourcesDiscoverer(Discoverer):
    """
    Discover the weblogic multi-tenant resources from the domain.
    """

    def __init__(self, model_context, resources_dictionary, base_location,
                 wlst_mode=WlstModes.OFFLINE, aliases=None, credential_injector=None):
        Discoverer.__init__(self, model_context, base_location, wlst_mode, aliases, credential_injector)
        self._dictionary = resources_dictionary

    def discover(self):
        _method_name = 'discover'
        _logger.entering(class_name=_class_name, method_name=_method_name)
        _logger.info('WLSDPLY-06707', class_name=_class_name, method_name=_method_name)
        model_top_folder_name, result = self.get_resource_management()
        discoverer.add_to_model_if_not_empty(self._dictionary, model_top_folder_name, result)
        _logger.exiting(class_name=_class_name, method_name=_method_name)
        return self._dictionary

    def get_resource_management(self):
        """
        Discover the global resource management and the domain resource managers.
        :return: model name for resource management:dictionary containing discovered resource management
        """
        _method_name = 'get_resource_management'
        _logger.entering(class_name=_class_name, method_name=_method_name)
        result = OrderedDict()
        model_top_folder_name = model_constants.RESOURCE_MANAGEMENT
        location = LocationContext(self._base_location)
        location.append_location(model_top_folder_name)
        resource = self._find_singleton_name_in_folder(location)
        if resource is not None:
            _logger.info('WLSDPLY-06708', class_name=_class_name, method_name=_method_name)
            location.add_name_token(self._aliases.get_name_token(location), resource)
            self._populate_model_parameters(result, location)
            self._discover_subfolders(result, location)
        _logger.exiting(class_name=_class_name, method_name=_method_name, result=result)
        return model_top_folder_name, result
