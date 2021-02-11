"""
Copyright (c) 2020, 2021, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.

Methods and constants for building Kubernetes resource files,
including domain resource configuration for WebLogic Kubernetes Operator.
"""
import re

from wlsdeploy.aliases import alias_utils
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import CLUSTER
from wlsdeploy.aliases.model_constants import DYNAMIC_CLUSTER_SIZE
from wlsdeploy.aliases.model_constants import DYNAMIC_SERVERS
from wlsdeploy.aliases.model_constants import MAX_DYNAMIC_SERVER_COUNT
from wlsdeploy.aliases.model_constants import SERVER
from wlsdeploy.aliases.model_constants import TOPOLOGY
from wlsdeploy.aliases.validation_codes import ValidationCodes
from wlsdeploy.util import dictionary_utils


def get_domain_uid(domain_name):
    """
    Determine the domain UID based on domain name.
    The domain UID must be DNS-1123 compatible, with the pattern ^[a-z0-9-.]{1,253}$
    :param domain_name: the domain name to be checked
    :return: the domain UID
    """
    return get_dns_name(domain_name)


def get_dns_name(name):
    """
    Return a DNS-1123 compatible name, with the pattern ^[a-z0-9-.]{1,253}$
    :param name: the domain name to be converted
    :return: the DNS-1123 compatible name
    """
    result = name.lower()
    # replace any disallowed character with hyphen
    result = re.sub('[^a-z0-9-.]', '-', result)
    return result


def get_server_count(cluster_name, cluster_values, model_dictionary, aliases):
    """
    Determine the number of servers associated with a cluster.
    :param cluster_name: the name of the cluster
    :param cluster_values: the value map for the cluster
    :param model_dictionary: the model dictionary
    :param aliases: aliases instance for validation
    :return: the number of servers
    """
    if DYNAMIC_SERVERS in cluster_values:
        # for dynamic clusters, return the value of DynamicClusterSize
        dynamic_servers_dict = cluster_values[DYNAMIC_SERVERS]
        location = LocationContext()
        location.append_location(CLUSTER)
        location.add_name_token(aliases.get_name_token(location), 'cluster')
        location.append_location(DYNAMIC_SERVERS)
        location.add_name_token(aliases.get_name_token(location), 'server')
        present, __ = aliases.is_valid_model_attribute_name(location, DYNAMIC_CLUSTER_SIZE)
        if present == ValidationCodes.VALID:
            cluster_size_value = dictionary_utils.get_element(dynamic_servers_dict, DYNAMIC_CLUSTER_SIZE)
        else:
            cluster_size_value = dictionary_utils.get_element(dynamic_servers_dict, MAX_DYNAMIC_SERVER_COUNT)
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
