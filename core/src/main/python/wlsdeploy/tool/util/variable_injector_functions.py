"""
Copyright (c) 2018, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""
from wlsdeploy.logging.platform_logger import PlatformLogger

import wlsdeploy.aliases.model_constants as model_constants
import wlsdeploy.util.model as model_sections

_class_name = 'variable_injector'
_logger = PlatformLogger('wlsdeploy.tool.util')


def managed_server_list(model):
    """
    Return a managed server name list from the provided model.
    :param model: to process for managed server list
    :return: list of managed server names or empty list if no managed servers
    """
    _method_name = 'managed_server_list'
    _logger.entering(class_name=_class_name, method_name=_method_name)
    ms_name_list = []
    topology_constant = model_sections.get_model_topology_key()
    if topology_constant in model:
        topology = model[topology_constant]
        if model_constants.SERVER in topology:
            ms_name_list = topology[model_constants.SERVER].keys()
            if model_constants.ADMIN_SERVER_NAME in topology:
                admin_server = topology[model_constants.ADMIN_SERVER_NAME]
                if admin_server in ms_name_list:
                    ms_name_list.remove(admin_server)
    _logger.exiting(class_name=_class_name, method_name=_method_name, result=ms_name_list)
    return ms_name_list


def admin_server_list(model):
    """
    Return the domain admin server in list format
    :param model: to process for admin server list
    :return: admin server in list format
    """
    _method_name = 'admin_server_list'
    _logger.entering(class_name=_class_name, method_name=_method_name)
    as_name_list = []
    topology_constant = model_sections.get_model_topology_key()
    if topology_constant in model:
        topology = model[topology_constant]
        if topology and model_constants.ADMIN_SERVER_NAME in topology:
            as_name_list.append(topology[model_constants.ADMIN_SERVER_NAME])
    _logger.exiting(class_name=_class_name, method_name=_method_name, result=as_name_list)
    return as_name_list
