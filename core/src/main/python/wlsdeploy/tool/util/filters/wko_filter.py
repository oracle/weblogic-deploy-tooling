# Copyright (c) 2021, Oracle Corporation and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
#
# ------------
# Description:
# ------------
# WDT filters to prepare a model for use with WKO, using the createDomain or prepareModel tools.
# These operations can be invoked as a single call, or independently of each other.

from wlsdeploy.aliases import alias_utils
from wlsdeploy.aliases.model_constants import CALCULATED_LISTEN_PORTS
from wlsdeploy.aliases.model_constants import CLUSTER
from wlsdeploy.aliases.model_constants import DYNAMIC_SERVERS
from wlsdeploy.aliases.model_constants import LISTEN_PORT
from wlsdeploy.aliases.model_constants import SERVER
from wlsdeploy.aliases.model_constants import TOPOLOGY
from wlsdeploy.aliases.validation_codes import ValidationCodes
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception.expection_types import ExceptionType
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.util.filters.model_traverse import ModelTraverse
from wlsdeploy.util import dictionary_utils

_class_name = 'wko_filter'
_logger = PlatformLogger('wlsdeploy.aliases')


def filter_model(model, model_context):
    """
    Perform the following operations on the specified model:
    - Remove any online-only attributes
    - Check if servers in a cluster have different ports
    :param model: the model to be filtered
    :param model_context: used by nested filters
    """
    filter_online_attributes(model, model_context)
    check_clustered_server_ports(model, model_context)


def filter_online_attributes(model, model_context):
    """
    Remove any online-only attributes from the specified model.
    :param model: the model to be filtered
    :param model_context: used to configure aliases
    """
    online_filter = OnlineAttributeFilter(model_context, ExceptionType.PREPARE)
    online_filter.traverse_model(model)


def check_clustered_server_ports(model, _model_context):
    """
    Set the CalculatedListenPorts attribute to false for dynamic clusters in the specified model.
    Warn if servers in a static cluster have different ports in the specified model.
    :param model: the model to be filtered
    :param _model_context: unused, passed by filter_helper if called independently
    """
    _method_name = 'check_clustered_server_ports'

    topology_folder = dictionary_utils.get_dictionary_element(model, TOPOLOGY)

    # be sure every dynamic cluster has DynamicServers/CalculatedListenPorts set to false

    clusters_folder = dictionary_utils.get_dictionary_element(topology_folder, CLUSTER)
    for cluster_name, cluster_fields in clusters_folder.items():
        dynamic_folder = cluster_fields[DYNAMIC_SERVERS]
        if dynamic_folder:
            calculated_listen_ports = dynamic_folder[CALCULATED_LISTEN_PORTS]
            if (calculated_listen_ports is None) or alias_utils.convert_boolean(calculated_listen_ports):
                _logger.info('WLSDPLY-20202', CALCULATED_LISTEN_PORTS, CLUSTER, cluster_name, class_name=_class_name,
                             method_name=_method_name)
                dynamic_folder[CALCULATED_LISTEN_PORTS] = False

    # be sure every server assigned to a cluster has the same listen port

    server_port_map = {}
    servers_folder = dictionary_utils.get_dictionary_element(topology_folder, SERVER)
    for server_name, server_fields in servers_folder.items():
        server_cluster = server_fields[CLUSTER]
        server_port = server_fields[LISTEN_PORT]

        if server_cluster and (server_port is not None):
            server_port_text = str(server_port)
            if '@@' in server_port_text:
                # prepareModel filters the model before and after it is tokenized,
                # so disregard variable values in the tokenized pass
                continue

            if server_cluster in server_port_map:
                cluster_info = server_port_map[server_cluster]
                first_server = cluster_info["firstServer"]
                cluster_port = cluster_info["serverPort"]
                if server_port_text != cluster_port:
                    _logger.warning('WLSDPLY-20203', SERVER, first_server, server_name, CLUSTER, server_cluster,
                                    LISTEN_PORT, cluster_port, server_port_text, class_name=_class_name,
                                    method_name=_method_name)
            else:
                server_port_map[server_cluster] = {"firstServer": server_name, "serverPort": server_port_text}


class OnlineAttributeFilter(ModelTraverse):
    """
    Traverse the model and remove any online-only attributes.
    """

    def __init__(self, model_context, exception_type):
        # use OFFLINE regardless of tool configuration
        ModelTraverse.__init__(self, model_context, WlstModes.OFFLINE, exception_type)

    # Override
    def unrecognized_field(self, model_dict, key, model_location):
        """
        If the attribute name has status ValidationCodes.VERSION_INVALID, it is a valid attribute sometimes,
        but not for offline mode in this WLS version.
        """
        _method_name = 'unrecognized_field'

        result, message = self._aliases.is_valid_model_attribute_name(model_location, key)
        if result == ValidationCodes.VERSION_INVALID:
            path = self._aliases.get_model_folder_path(model_location)
            _logger.info('WLSDPLY-20201', key, path, class_name=_class_name, method_name=_method_name)
            del model_dict[key]
