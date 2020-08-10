"""
Copyright (c) 2020, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.

Methods and constants for building Kubernetes resource files,
including domain resource configuration for WebLogic Kubernetes Operator.
"""
import re

from wlsdeploy.aliases import alias_utils
from wlsdeploy.aliases.model_constants import CLUSTER
from wlsdeploy.aliases.model_constants import DYNAMIC_CLUSTER_SIZE
from wlsdeploy.aliases.model_constants import DYNAMIC_SERVERS
from wlsdeploy.aliases.model_constants import SERVER
from wlsdeploy.aliases.model_constants import TOPOLOGY
from wlsdeploy.util import dictionary_utils


def get_domain_uid(domain_name):
    """
    Determine the domain UID based on domain name.
    The domain UID must be DNS-1123 compatible, with the pattern ^[a-z0-9-.]{1,253}$
    :param domain_name: the domain name to be checked
    :return: the domain UID
    """
    result = domain_name.lower()
    # replace any disallowed character with hyphen
    result = re.sub('[^a-z0-9-.]', '-', result)
    return result


def get_server_count(cluster_name, cluster_values, model_dictionary):
    """
    Determine the number of servers associated with a cluster.
    :param cluster_name: the name of the cluster
    :param cluster_values: the value map for the cluster
    :param model_dictionary: the model dictionary
    :return: the number of servers
    """
    if DYNAMIC_SERVERS in cluster_values:
        # for dynamic clusters, return the value of DynamicClusterSize
        dynamic_servers_dict = cluster_values[DYNAMIC_SERVERS]
        cluster_size_value = dictionary_utils.get_element(dynamic_servers_dict, DYNAMIC_CLUSTER_SIZE)
        if cluster_size_value is not None:
            return alias_utils.convert_to_type('integer', cluster_size_value)
    else:
        # for other clusters, return the number of servers assigned to this cluster
        count = 0
        topology = dictionary_utils.get_dictionary_element(model_dictionary, TOPOLOGY)
        servers = dictionary_utils.get_dictionary_element(topology, SERVER)
        for server_name, server_value in servers.items():
            server_cluster = dictionary_utils.get_element(server_value, CLUSTER)
            if str(server_cluster) == cluster_name:
                count = count + 1
        return count

    return 0
