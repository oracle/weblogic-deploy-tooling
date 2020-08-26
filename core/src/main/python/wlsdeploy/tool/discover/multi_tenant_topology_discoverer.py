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

_class_name = 'MultiTenantTopologyDiscoverer'
_logger = PlatformLogger(discoverer.get_discover_logger_name())


class MultiTenantTopologyDiscoverer(Discoverer):
    """
    Discover the topology part of the model for multi tenant. The resulting data dictionary describes the specific
    topology of a multi tenant domain
    """

    def __init__(self, model_context, topology_dictionary, base_location,
                 wlst_mode=WlstModes.OFFLINE, aliases=None, credential_injector=None):
        Discoverer.__init__(self, model_context, base_location, wlst_mode, aliases, credential_injector)
        self._dictionary = topology_dictionary

    def discover(self):
        """
        Discover the entities that make up the topology for partitions in the domain.
        :return: dictionary containing discovered multi-tenant topology
        """
        _method_name = 'discover'
        _logger.entering(class_name=_class_name, method_name=_method_name)
        _logger.info('WLSDPLY-06709', class_name=_class_name, method_name=_method_name)
        model_top_folder_name, result = self._get_virtual_targets()
        discoverer.add_to_model_if_not_empty(self._dictionary, model_top_folder_name, result)
        _logger.exiting(class_name=_class_name, method_name=_method_name)
        return self._dictionary

    def _get_virtual_targets(self):
        """
        Discover the virtual targets used for targeting partition resources.
        :return: model name for virtual targets:dictionary with the discovered virtual targets
        """
        _method_name = '_get_virtual_targets'
        _logger.entering(class_name=_class_name, method_name=_method_name)
        result = OrderedDict()
        model_top_folder_name = model_constants.VIRTUAL_TARGET
        location = LocationContext(self._base_location)
        location.append_location(model_top_folder_name)
        targets = self._find_names_in_folder(location)
        if targets:
            _logger.info('WLSDPLY-06710', len(targets), class_name=_class_name, method_name=_method_name)
            name_token = self._aliases.get_name_token(location)
            for target in targets:
                _logger.info('WLSDPLY-06711', target, class_name=_class_name, method_name=_method_name)
                location.add_name_token(name_token, target)
                result[target] = OrderedDict()
                self._populate_model_parameters(result[target], location)
                self._discover_subfolders(result[target], location)
                location.remove_name_token(name_token)
        _logger.exiting(class_name=_class_name, method_name=_method_name, result=model_top_folder_name)
        return model_top_folder_name, result
