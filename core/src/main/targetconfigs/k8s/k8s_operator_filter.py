# Copyright (c) 2020, 2022, Oracle Corporation and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
#
# ------------
# Description:
# ------------
#  This is a WDT filter for primordial domain creation. It filters out all resources and
#  apps deployments, leaving only the domainInfo and admin server in topology.
#

from wlsdeploy.aliases import alias_utils


def filter_model(model):
    __cleanup_topology(model)
    __cleanup_resources(model)

def __cleanup_resources(model):
    if model and 'resources' in model:
        resources = model['resources']

        for delthis in [ 'PartitionWorkManager', 'Partition', 'ResourceGroup', 'ResourceGroupTemplate', 'VirtualHost',
                     'ResourceManager', 'ResourceManagement' ]:
            if resources.has_key(delthis):
                del resources[delthis]

def __cleanup_topology(model):
    if model and 'topology' in model:
        topology = model['topology']
        for delthis in [ 'NMProperties', 'VirtualTarget', 'Machine', 'UnixMachine']:
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
                for delthis in ['Machine', 'CandidateMachine', 'AutoMigrationEnabled', 'ServerStart']:
                    if servers[server].has_key(delthis):
                        del servers[server][delthis]

        if topology.has_key('SecurityConfiguration'):
            for delthis in ['NodeManagerPasswordEncrypted', 'NodeManagerUsername' ]:
                if topology['SecurityConfiguration'].has_key(delthis):
                    del topology['SecurityConfiguration'][delthis]
            if len(topology['SecurityConfiguration'].keys()) == 0:
                del topology['SecurityConfiguration']

        if topology.has_key('ServerTemplate'):
            server_templates = topology['ServerTemplate']
            for server_template in server_templates:
                auto_migration_enabled = server_templates[server_template]['AutoMigrationEnabled']
                if auto_migration_enabled is None or alias_utils.convert_boolean(auto_migration_enabled):
                    server_templates[server_template]['AutoMigrationEnabled'] = False
                for delthis in ['ServerStart']:
                    if server_templates[server_template].has_key(delthis):
                        del server_templates[server_template][delthis]
