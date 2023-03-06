# Copyright (c) 2023, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
#
# ------------
# Description:
# ------------
# WDT final filters prepare a model for use in a target environment, using the createDomain or prepareModel tools.
# These filters are applied to a merged, substituted model.
# They apply any updates to a specified update model, to support use cases with multiple models.
# These operations can be invoked as a single call, or independently of each other.
from oracle.weblogic.deploy.util import PyOrderedDict

from wlsdeploy.aliases.model_constants import ADMIN_SERVER_NAME
from wlsdeploy.aliases.model_constants import CLUSTER
from wlsdeploy.aliases.model_constants import DEFAULT_ADMIN_SERVER_NAME
from wlsdeploy.aliases.model_constants import DYNAMIC_SERVERS
from wlsdeploy.aliases.model_constants import SERVER
from wlsdeploy.aliases.model_constants import SERVER_NAME_PREFIX
from wlsdeploy.aliases.model_constants import TOPOLOGY
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.util import dictionary_utils

_class_name = 'wko_final_filter'
_logger = PlatformLogger('wlsdeploy.tool.util')


def filter_final_model(model, update_model, model_context):
    """
    Perform the following operations on the specified model:
    - Remove any online-only attributes
    - Check if dynamic cluster prefixes are specified and unique
    :param model: the model to be filtered
    :param update_model: the model to be updated with any changes
    :param model_context: used by nested filters
    """
    check_dynamic_cluster_prefixes(model, update_model, model_context)


def filter_final_model_for_wko(model, update_model, model_context):
    """
    Perform filtering operations on the specified model to prepare for WKO deployment.
    Currently, matches the general k8s target filtering.
    :param model: the model to be filtered
    :param update_model: the model to be updated with any changes
    :param model_context: used by nested filters
    """
    filter_final_model(model, update_model, model_context)


def filter_final_model_for_wko3(model, update_model, model_context):
    """
    Perform filtering operations on the specified model to prepare for WKO deployment:
    - Perform general k8s target filtering
    - Check for explicit admin server declarations
    :param model: the model to be filtered
    :param update_model: the model to be updated with any changes
    :param model_context: used by nested filters
    """
    filter_final_model(model, update_model, model_context)
    check_admin_server_defined(model, update_model, model_context)


def filter_final_model_for_vz(model, update_model, model_context):
    """
    Perform filtering operations on the specified model to prepare for Verrazzano deployment.
    Currently, matches the general k8s target filtering.
    :param model: the model to be filtered
    :param update_model: the model to be updated with any changes
    :param model_context: used by nested filters
    """
    filter_final_model(model, update_model, model_context)


def check_dynamic_cluster_prefixes(model, update_model, _model_context):
    """
    All Dynamic Clusters must have a DynamicServers section with the ServerNamePrefix field explicitly declared.
    Ensure each cluster uses a unique value for this field.
    :param model: the model to be updated
    :param update_model: the model to be updated with any changes
    :param _model_context: unused, passed by filter_helper if called independently
    :return:
    """
    _method_name = 'check_dynamic_cluster_prefixes'

    server_name_prefixes = []
    target_key = _model_context.get_target_configuration().get_product_key()
    topology_folder = dictionary_utils.get_dictionary_element(model, TOPOLOGY)
    clusters_folder = dictionary_utils.get_dictionary_element(topology_folder, CLUSTER)
    for cluster_name, cluster_fields in clusters_folder.items():
        dynamic_folder = dictionary_utils.get_element(cluster_fields, DYNAMIC_SERVERS)
        if dynamic_folder:
            server_name_prefix = dictionary_utils.get_element(dynamic_folder, SERVER_NAME_PREFIX)

            if not server_name_prefix:
                # missing server prefix can be fixed by assigning the default: "clusterName-"
                server_name_prefix = cluster_name + '-'
                _logger.info('WLSDPLY-20204', SERVER_NAME_PREFIX, server_name_prefix, cluster_name, target_key,
                             class_name=_class_name, method_name=_method_name)
                update_dynamic_folder = _get_folder(update_model, TOPOLOGY, CLUSTER, cluster_name, DYNAMIC_SERVERS)
                update_dynamic_folder[SERVER_NAME_PREFIX] = server_name_prefix

            elif server_name_prefix in server_name_prefixes:
                # issue a warning for non-unique prefix - we won't try to fix this
                _logger.warning('WLSDPLY-20205', SERVER_NAME_PREFIX, server_name_prefix, class_name=_class_name,
                                method_name=_method_name)

            server_name_prefixes.append(server_name_prefix)


def check_admin_server_defined(model, update_model, _model_context):
    """
    Ensure that the AdminServerName attribute is set, and that the server is defined.
    This is required by WKO 3.0, and not by 4.0 and later.
    :param model: the model to be filtered
    :param update_model: the model to be updated with any changes
    :param _model_context: unused, passed by filter_helper if called independently
    """
    _method_name = 'check_admin_server_defined'

    target_key = _model_context.get_target_configuration().get_product_key()
    topology_folder = dictionary_utils.get_dictionary_element(model, TOPOLOGY)
    admin_server_name = dictionary_utils.get_element(topology_folder, ADMIN_SERVER_NAME)
    if not admin_server_name:
        admin_server_name = DEFAULT_ADMIN_SERVER_NAME
        _logger.info('WLSDPLY-20206', ADMIN_SERVER_NAME, admin_server_name, target_key, class_name=_class_name,
                     method_name=_method_name)
        update_topology_folder = _get_folder(update_model, TOPOLOGY)
        update_topology_folder[ADMIN_SERVER_NAME] = admin_server_name

    servers_folder = dictionary_utils.get_dictionary_element(topology_folder, SERVER)
    if admin_server_name not in servers_folder:
        _logger.info('WLSDPLY-20207', SERVER, admin_server_name, target_key, class_name=_class_name,
                     method_name=_method_name)
        update_servers_folder = _get_folder(update_model, TOPOLOGY, SERVER)
        update_servers_folder[admin_server_name] = PyOrderedDict()


def _get_folder(folder, *args):
    """
    Find or create nested sub-folders for the specified folder based on the argument list.
    :param folder: the top-level folder
    :param args: the names of the nested sub-folders to find or create
    :return: the nested sub-folder
    """
    result = folder
    for arg in args:
        if arg not in result:
            result[arg] = PyOrderedDict()
        result = result[arg]
    return result
