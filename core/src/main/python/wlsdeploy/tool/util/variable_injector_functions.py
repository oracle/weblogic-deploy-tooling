"""
Copyright (c) 2018, 2022, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import re

import wlsdeploy.aliases.model_constants as model_constants
import wlsdeploy.util.model as model_sections
from oracle.weblogic.deploy.aliases import AliasException
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.logging.platform_logger import PlatformLogger
import wlsdeploy.util.unicode_helper as str_helper

_class_name = 'variable_injector'
_logger = PlatformLogger('wlsdeploy.tool.util')

_fake_name_marker = 'fakename'
_fake_name_replacement = re.compile('.' + _fake_name_marker)
_white_space_replacement = re.compile('\\s')

# bad characters for a property name - anything that isn't a good character
_bad_chars_replacement = re.compile('[^\\w.-]')


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


def format_variable_name(location, attribute, aliases):
    """
    Return a variable name for the specified attribute and location.
    Example: ServerTemp.template1.SSL.ListenPort
    :param location: the location of the attribute
    :param attribute: the attribute to be evaluated
    :param aliases: for information about the location and attribute
    :return: the variable name
    """
    _method_name = 'format_variable_name'

    short_list = __traverse_location(LocationContext(location), attribute, list(), aliases)

    short_name = ''
    for node in short_list:
        if node is not None and len(node) > 0:
            short_name += node + '.'
    short_name += attribute

    # remove or replace invalid characters in the variable name for use as a property name.
    short_name = short_name.replace('/', '.')
    short_name = _white_space_replacement.sub('-', short_name)
    short_name = _bad_chars_replacement.sub('-', short_name)
    short_name = _fake_name_replacement.sub('', short_name)
    return short_name


def __traverse_location(iterate_location, attribute, name_list, aliases, last_folder=None, last_folder_short=None):
    """
    Update a list of names representing the location and attribute specified.
    :param iterate_location: the location to be examined
    :param attribute: used for logging
    :param name_list: the list to be updated
    :param aliases: used to examine location
    :param last_folder: folder from the previous recursive call
    :param last_folder_short: short name of the last folder
    :return: the list that was passed
    """
    _method_name = '__traverse_location'

    current_folder = iterate_location.get_current_model_folder()
    if current_folder == model_constants.DOMAIN:
        if last_folder is not None:
            # If a short name is not defined for the top level folder, use the full name
            if len(last_folder_short) == 0:
                last_folder_short = last_folder
            name_list.insert(0, last_folder_short)
    else:
        current_folder = iterate_location.get_current_model_folder()
        short_folder = aliases.get_folder_short_name(iterate_location)
        if last_folder_short is not None:
            name_list.insert(0, last_folder_short)
        try:
            if not aliases.is_artificial_type_folder(iterate_location) and \
                    (aliases.supports_multiple_mbean_instances(iterate_location) or
                     aliases.is_custom_folder_allowed(iterate_location)):
                name_token = aliases.get_name_token(iterate_location)
                name = iterate_location.get_name_for_token(name_token)
                name_list.insert(0, name)
                iterate_location.remove_name_token(name_token)
            iterate_location.pop_location()
        except AliasException, ae:
            _logger.warning('WLSDPLY-19531', str_helper.to_string(iterate_location), attribute,
                            ae.getLocalizedMessage(), class_name=_class_name, method_name=_method_name)
        __traverse_location(iterate_location, attribute, name_list, aliases, current_folder, short_folder)
    return name_list
