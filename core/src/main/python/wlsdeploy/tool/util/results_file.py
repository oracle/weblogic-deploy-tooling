"""
Copyright (c) 2023, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import os

from oracle.weblogic.deploy.json import JsonException
from oracle.weblogic.deploy.util import PyOrderedDict

from wlsdeploy.exception import exception_helper
from wlsdeploy.json.json_translator import PythonToJson

"""
This module acts as a singleton to collect results for the duration of a tool's execution,
without having to be passed to individual methods and classes.
"""

RESULTS_FILE_NAME = 'results.json'

NON_DYNAMIC_CHANGES_FOLDER = 'nonDynamicChanges'
RESTARTS_FOLDER = 'restarts'

CLUSTER_KEY = 'cluster'
NON_DYNAMIC_CHANGES_TEXT_KEY = 'nonDynamicChangesText'
RESOURCE_NAME_KEY = 'resourceName'
RESOURCE_TYPE_KEY = 'resourceType'
SERVER_KEY = 'server'
TEXT_KEY = 'text'

_results_dict = PyOrderedDict()


def check_and_write(model_context, exception_type):
    """
    Write the results file to the output directory, if output directory was specified.
    :param model_context: used to determine output directory
    :param exception_type: the exception type to be thrown on failure
    """
    output_dir = model_context.get_output_dir()
    if output_dir:
        results_file = os.path.join(output_dir, RESULTS_FILE_NAME)
        json_object = PythonToJson(_results_dict)

        try:
            json_object.write_to_json_file(results_file)
        except JsonException, ex:
            raise exception_helper.create_exception(exception_type, 'WLSDPLY-01681', results_file,
                                                    ex.getLocalizedMessage(), error=ex)


def add_restart_entry(cluster, server, resource_name, resource_type):
    restart = PyOrderedDict()
    if cluster:
        restart[CLUSTER_KEY] = cluster
    if server:
        restart[SERVER_KEY] = server
    if resource_name:
        restart[RESOURCE_NAME_KEY] = resource_name
    if resource_type:
        restart[RESOURCE_TYPE_KEY] = resource_type
    restarts = _add_or_create_array(_results_dict, RESTARTS_FOLDER)
    restarts.append(restart)


def add_non_dynamic_change(bean_name, attribute_name):
    non_dynamic_changes = _add_or_create_folder(_results_dict, NON_DYNAMIC_CHANGES_FOLDER)
    bean_array = _add_or_create_array(non_dynamic_changes, bean_name)
    bean_array.append(attribute_name)


def add_non_dynamic_changes_text(non_dynamic_changes_text):
    lines = non_dynamic_changes_text.splitlines()
    _results_dict[NON_DYNAMIC_CHANGES_TEXT_KEY] = lines


def _add_or_create_folder(parent_folder, folder_name):
    if folder_name not in parent_folder:
        parent_folder[folder_name] = PyOrderedDict()
    return parent_folder[folder_name]


def _add_or_create_array(parent_folder, folder_name):
    if folder_name not in parent_folder:
        parent_folder[folder_name] = []
    return parent_folder[folder_name]
