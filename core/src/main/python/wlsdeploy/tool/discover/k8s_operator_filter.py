# Copyright (c) 2018, 2020, Oracle Corporation and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
#
# ------------
# Description:
# ------------
#  This is a WDT filter for primordial domain creation. It filters out all resources and
#  apps deployments, leaving only the domainInfo and admin server in topology.
#
def filter_model(model):
    __cleanup_topology(model)
    __cleanup_resources(model)

def __cleanup_resources(model):
    if model and 'resources' in model:
        resources = model['resources']

    for delthis in [ 'PartitionWorkManager', 'Partition', 'ResourceGroup', 'ResourceGroupTemplate']:
        if resources.has_key(delthis):
            del resources[delthis]

def __cleanup_topology(model):
    if model and 'topology' in model:
        topology = model['topology']
        for delthis in [ 'NMProperties', 'VirtualTarget', 'Machine']:
            if topology.has_key(delthis):
                del topology[delthis]

        if topology.has_key('Cluster'):
            clusters = topology['Cluster']
            for cluster in clusters:
                for delthis in ['MigrationBasis', 'CandidateMachinesForMigratableServer', 'DatabaseLessLeasingBasis',
                                'ClusterMessagingMode']:
                    if clusters[cluster].has_key(delthis):
                        del clusters[cluster][delthis]

        if topology.has_key('Server'):
            servers = topology['Server']
            for server in servers:
                for delthis in ['Machine', 'CandidateMachine', 'AutoMigrationEnabled']:
                    if servers[server].has_key(delthis):
                        del servers[server][delthis]

        if topology.has_key('SecurityConfiguration'):
            for delthis in ['NodeManagerPasswordEncrypted']:
                if topology['SecurityConfiguration'].has_key(delthis):
                    del topology['SecurityConfiguration'][delthis]

        if topology.has_key('SeverTemplate'):
            server_templates = topology['ServerTemplate']
            for server_template in server_templates:
                server_templates[server_template]['AutoMigrationEnabled'] = False
        else:
            topology['ServerTemplate'] = {}
            server_templates = topology['ServerTemplate']
            if topology.has_key('Cluster'):
                clusters = topology['Cluster']
                for cluster in clusters:
                    server_templates[cluster] = {}
                    server_template = server_templates[cluster]
                    server_template['Cluster'] = cluster
                    server_template['AutoMigrationEnabled'] = False


def __subtitute_secrets(current_dictionary, stack=None, recursive=False):
    for key in current_dictionary:
        if not recursive:
            stack = []
        current_node = current_dictionary[key]
        if isinstance(current_node, dict):
            stack.append(key)
            __subtitute_secrets(current_node, stack, True)
        else:
            if isinstance(current_node, str):
                if '--FIX ME--' == current_node:
                    current_dictionary[key] = '@@SECRET:' + stack[1] + ':' + key + '@@'


# fh = open('/tmp/domain_model.json')
# mydict = eval(fh.read())
# filter_model(mydict)
