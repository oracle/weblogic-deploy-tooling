# Copyright (c) 2021, 2022, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
#
# ------------
# Description:
# ------------
# WDT filters to prepare a model for use a target environment, using the createDomain or prepareModel tools.
# These operations can be invoked as a single call, or independently of each other.
from oracle.weblogic.deploy.util import PyRealBoolean
from wlsdeploy.aliases import alias_utils
from wlsdeploy.aliases.model_constants import AUTO_MIGRATION_ENABLED
from wlsdeploy.aliases.model_constants import CALCULATED_LISTEN_PORTS
from wlsdeploy.aliases.model_constants import CANDIDATE_MACHINE
from wlsdeploy.aliases.model_constants import CANDIDATE_MACHINES_FOR_MIGRATABLE_SERVER
from wlsdeploy.aliases.model_constants import CLUSTER
from wlsdeploy.aliases.model_constants import CLUSTER_MESSAGING_MODE
from wlsdeploy.aliases.model_constants import DATABASE_LESS_LEASING_BASIS
from wlsdeploy.aliases.model_constants import DYNAMIC_SERVERS
from wlsdeploy.aliases.model_constants import LISTEN_PORT
from wlsdeploy.aliases.model_constants import MACHINE
from wlsdeploy.aliases.model_constants import MIGRATION_BASIS
from wlsdeploy.aliases.model_constants import NM_PROPERTIES
from wlsdeploy.aliases.model_constants import NODE_MANAGER_PW_ENCRYPTED
from wlsdeploy.aliases.model_constants import NODE_MANAGER_USER_NAME
from wlsdeploy.aliases.model_constants import PARTITION
from wlsdeploy.aliases.model_constants import PARTITION_WORK_MANAGER
from wlsdeploy.aliases.model_constants import RESOURCES
from wlsdeploy.aliases.model_constants import RESOURCE_GROUP
from wlsdeploy.aliases.model_constants import RESOURCE_GROUP_TEMPLATE
from wlsdeploy.aliases.model_constants import RESOURCE_MANAGEMENT
from wlsdeploy.aliases.model_constants import RESOURCE_MANAGER
from wlsdeploy.aliases.model_constants import SECURITY_CONFIGURATION
from wlsdeploy.aliases.model_constants import SERVER
from wlsdeploy.aliases.model_constants import SERVER_START
from wlsdeploy.aliases.model_constants import SERVER_TEMPLATE
from wlsdeploy.aliases.model_constants import TOPOLOGY
from wlsdeploy.aliases.model_constants import UNIX_MACHINE
from wlsdeploy.aliases.model_constants import VIRTUAL_HOST
from wlsdeploy.aliases.model_constants import VIRTUAL_TARGET
from wlsdeploy.aliases.validation_codes import ValidationCodes
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception.expection_types import ExceptionType
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.util.filters.model_traverse import ModelTraverse
from wlsdeploy.util import dictionary_utils
import wlsdeploy.util.unicode_helper as str_helper

_class_name = 'wko_filter'
_logger = PlatformLogger('wlsdeploy.tool.util')


def filter_model(model, model_context):
    """
    Perform the following operations on the specified model:
    - Remove any online-only attributes
    - Check if servers in a cluster have different ports
    :param model: the model to be filtered
    :param model_context: used by nested filters
    """
    filter_topology(model, model_context)
    filter_resources(model, model_context)
    filter_online_attributes(model, model_context)
    check_clustered_server_ports(model, model_context)


def filter_model_for_wko(model, model_context):
    """
    Perform filtering operations on the specified model to prepare for WKO deployment.
    Currently matches the general k8s target filtering.
    :param model: the model to be filtered
    :param model_context: used by nested filters
    """
    filter_model(model, model_context)


def filter_model_for_vz(model, model_context):
    """
    Perform filtering operations on the specified model to prepare for Verrazzano deployment.
    Currently matches the general k8s target filtering.
    :param model: the model to be filtered
    :param model_context: used by nested filters
    """
    filter_model(model, model_context)


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
                dynamic_folder[CALCULATED_LISTEN_PORTS] = PyRealBoolean(False)

    # be sure every server assigned to a cluster has the same listen port

    server_port_map = {}
    servers_folder = dictionary_utils.get_dictionary_element(topology_folder, SERVER)
    for server_name, server_fields in servers_folder.items():
        server_cluster = server_fields[CLUSTER]
        server_port = server_fields[LISTEN_PORT]

        if server_cluster and (server_port is not None):
            server_port_text = str_helper.to_string(server_port)
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


def filter_topology(model, _model_context):
    """
    Remove elements from the topology section of the model that are not relevant in a Kubernetes environment.
    This includes references to machine and node manager elements.
    :param model: the model to be updated
    :param _model_context: unused, passed by filter_helper if called independently
    """
    topology = dictionary_utils.get_dictionary_element(model, TOPOLOGY)
    for delete_key in [NM_PROPERTIES, VIRTUAL_TARGET, MACHINE, UNIX_MACHINE]:
        if delete_key in topology:
            del topology[delete_key]

    clusters = dictionary_utils.get_dictionary_element(topology, CLUSTER)
    for cluster in clusters:
        for delete_key in [MIGRATION_BASIS, CANDIDATE_MACHINES_FOR_MIGRATABLE_SERVER, DATABASE_LESS_LEASING_BASIS,
                           CLUSTER_MESSAGING_MODE]:
            if delete_key in clusters[cluster]:
                del clusters[cluster][delete_key]

    servers = dictionary_utils.get_dictionary_element(topology, SERVER)
    for server in servers:
        for delete_key in [MACHINE, CANDIDATE_MACHINE, AUTO_MIGRATION_ENABLED, SERVER_START]:
            if delete_key in servers[server]:
                del servers[server][delete_key]

    security_configuration = dictionary_utils.get_dictionary_element(topology, SECURITY_CONFIGURATION)
    for delete_key in [NODE_MANAGER_USER_NAME, NODE_MANAGER_PW_ENCRYPTED]:
        if delete_key in security_configuration:
            del security_configuration[delete_key]

    if (SECURITY_CONFIGURATION in topology) and not security_configuration:
        del topology[SECURITY_CONFIGURATION]

    server_templates = dictionary_utils.get_dictionary_element(topology, SERVER_TEMPLATE)
    for key in server_templates:
        server_template = server_templates[key]
        auto_migration_enabled = server_template[AUTO_MIGRATION_ENABLED]
        if auto_migration_enabled is None or alias_utils.convert_boolean(auto_migration_enabled):
            server_template[AUTO_MIGRATION_ENABLED] = PyRealBoolean(False)
        for delete_key in [MACHINE, SERVER_START]:
            if delete_key in server_template:
                del server_template[delete_key]


def filter_resources(model, _model_context):
    """
    Remove elements from the resources section of the model that are not relevant in a Kubernetes environment.
    This includes references to partitions and resource groups.
    :param model: the model to be updated
    :param _model_context: unused, passed by filter_helper if called independently
    """
    resources = dictionary_utils.get_dictionary_element(model, RESOURCES)
    for delete_key in [PARTITION, PARTITION_WORK_MANAGER, RESOURCE_GROUP, RESOURCE_GROUP_TEMPLATE,
                       RESOURCE_MANAGEMENT, RESOURCE_MANAGER, VIRTUAL_HOST]:
        if delete_key in resources:
            del resources[delete_key]


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
