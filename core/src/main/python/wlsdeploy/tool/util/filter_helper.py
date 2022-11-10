"""
Copyright (c) 2017, 2022, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import imp
import os
import sys

from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.util.filters import wko_filter
from wlsdeploy.util import dictionary_utils
from wlsdeploy.util import path_utils
from wlsdeploy.util.model_translator import FileToPython
import wlsdeploy.util.unicode_helper as str_helper

__class_name = 'filter_helper'
__logger = PlatformLogger('wlsdeploy.tool.util')

TARGET_CONFIG_TOKEN = '@@TARGET_CONFIG_DIR@@'

__id_filter_map = {
    # groups that execute multiple filters
    'k8s_filter': wko_filter.filter_model,
    'vz_filter': wko_filter.filter_model_for_vz,
    'wko_filter': wko_filter.filter_model_for_wko,

    # individual filters for custom target environments
    'online_attributes_filter': wko_filter.filter_online_attributes,
    'resources_filter': wko_filter.filter_resources,
    'topology_filter': wko_filter.filter_topology,
    'server_ports_filter': wko_filter.check_clustered_server_ports
}


def apply_filters(model, tool_type, model_context):
    """
    Apply any filters configured for the specified tool type to the specified model.
    :param model: the model to be filtered
    :param tool_type: the name of the filter tool type
    :param model_context: used to find target filters
    :return: True if any filter was applied, False otherwise
    :raises: BundleAwareException of the specified type: if an error occurs
    """
    _method_name = 'apply_filters'

    __filter_file_location = None
    filter_applied = False

    try:
        filters_dictionary = {}

        # if target specified in model context, use the filters from target config
        if model_context and model_context.get_target():
            __filter_file_location = model_context.get_target_configuration_file()
            filters_dictionary = model_context.get_target_configuration().get_model_filters()
            target_path = os.path.join('targets', model_context.get_target())

            # Fix the tokenized path in the filter path
            for filter_list in filters_dictionary:
                for current_filter in filters_dictionary[filter_list]:
                    filter_path = dictionary_utils.get_element(current_filter, 'path')
                    if (filter_path is not None) and filter_path.startswith(TARGET_CONFIG_TOKEN):
                        filter_path = target_path + filter_path.replace(TARGET_CONFIG_TOKEN, '')
                        current_filter['path'] = path_utils.find_config_path(filter_path)

        else:
            __filter_file_location = path_utils.find_config_path('model_filters.json')
            if os.path.isfile(__filter_file_location):
                filters_dictionary = FileToPython(__filter_file_location).parse()
            else:
                __logger.info('WLSDPLY-20017', __filter_file_location, class_name=__class_name,
                              method_name=_method_name)

        if tool_type in filters_dictionary:
            filter_list = filters_dictionary[tool_type]
            for filter in filter_list:
                filter_applied = _apply_filter(model, filter, model_context, __filter_file_location) or filter_applied
        else:
            __logger.info('WLSDPLY-20016', tool_type, __filter_file_location, class_name=__class_name,
                          method_name=_method_name)

    except Exception, ex:
        __logger.severe('WLSDPLY-20018', str_helper.to_string(ex), error=ex,
                        class_name=__class_name, method_name=_method_name)

    return filter_applied


def _apply_filter(model, the_filter, model_context, filter_file_location):
    """
    Apply the specified filter to the specified model.
    :param model: the model to be filtered
    :param the_filter: a dictionary containing the filter parameters
    :param model_context: may be used by internal (ID) filters
    :param filter_file_location: used for logging
    :return: True if the specified filter was applied, False otherwise
    :raises: BundleAwareException of the specified type: if an error occurs
    """
    _method_name = '_apply_filter'

    filter_id = dictionary_utils.get_element(the_filter, 'id')
    if filter_id is not None:
        __logger.info('WLSDPLY-20034', filter_id, class_name=__class_name, method_name=_method_name)
        return _apply_id_filter(model, filter_id, model_context)

    path = dictionary_utils.get_element(the_filter, 'path')
    if path is not None:
        name = dictionary_utils.get_element(the_filter, 'name')
        __logger.info('WLSDPLY-20033', name, class_name=__class_name, method_name=_method_name)
        return _apply_path_filter(model, path)

    __logger.severe('WLSDPLY-20019', str_helper.to_string(filter_file_location),
                    class_name=__class_name, method_name=_method_name)
    return False


def _apply_id_filter(model, id, model_context):
    """
    Apply the specified ID filter to the specified model.
    :param model: the model to be filtered
    :param id: the ID of the filter to be applied
    :param model_context: may be used by filters
    :return: True if the specified filter was applied, False otherwise
    :raises: BundleAwareException of the specified type: if an error occurs
    """
    _method_name = '_apply_id_filter'

    filter_method = dictionary_utils.get_element(__id_filter_map, id)
    if filter_method is None:
        __logger.severe('WLSDPLY-20020', str_helper.to_string(id), class_name=__class_name, method_name=_method_name)
        return False
    else:
        filter_method(model, model_context)
        return True


def _apply_path_filter(model, script_path):
    """
    Apply the specified path filter to the specified model.
    :param model: the model to be filtered
    :param script_path: the path of the filter to be applied
    :return: True if the specified filter was applied, False otherwise
    :raises: BundleAwareException of the specified type: if an error occurs
    """
    _method_name = '_apply_path_filter'

    if not os.path.isfile(script_path):
        __logger.severe('WLSDPLY-20021', str_helper.to_string(script_path),
                        class_name=__class_name, method_name=_method_name)
        return False

    python_path = os.path.dirname(script_path)
    path_present = python_path in sys.path
    if not path_present:
        sys.path.insert(0, python_path)

    try:
        module = imp.load_source('filter_script', script_path)
        module.filter_model(model)
        if not path_present:
            sys.path.remove(python_path)
        return True

    except Exception, ex:
        __logger.severe('WLSDPLY-20022', str_helper.to_string(script_path), ex, error=ex,
                        class_name=__class_name, method_name=_method_name)

    return False
