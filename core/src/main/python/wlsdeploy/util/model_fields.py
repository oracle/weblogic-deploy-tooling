"""
Copyright (c) 2017, 2018, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""

# WARNING: This file is slated for removal since it should not longer be needed once the existing code is
# completely switched to use the aliases.  DO NOT add anything to this file!

RESOURCE_GROUP_TEMPLATE_SUBFOLDERS = [
    'Application',
    'CoherenceClusterSystemResource',
    'FileStore',
    'ForeignJNDIProvider',
    'JDBCStore',
    'JDBCSystemResource',
    'JMSBridgeDestination',
    'JMSServer',
    'JMSSystemResource',
    'Library',
    'MailSession',
    'ManagedExecutorService',
    'ManagedScheduledExecutorService',
    'ManagedThreadFactory',
    'MessagingBridge',
    'OsgiFramework',
    'PathService',
    'SAFAgent',
    'WLDFSystemResource'
]

RESOURCE_GROUP_SUBFOLDERS = [
    'Application',
    'CoherenceClusterSystemResource',
    'FileStore',
    'ForeignJNDIProvider',
    'JDBCStore',
    'JDBCSystemResource',
    'JMSBridgeDestination',
    'JMSServer',
    'JMSSystemResource',
    'Library',
    'MailSession',
    'ManagedExecutorService',
    'ManagedScheduledExecutorService',
    'ManagedThreadFactory',
    'MessagingBridge',
    'OsgiFramework',
    'PathService',
    'SAFAgent',
    'WLDFSystemResource'
]

RESOURCE_GROUP_ATTR_NOT_IN_1221 = [
    'Administrative',
    'AutoTargetAdminServer'
]

PARTITION_SUBFOLDERS = [
    'AdminVirtualTarget',
    'CoherencePartitionCacheConfig',
    'DataSourcePartition',
    'ForeignJndiProviderOverride',
    'JdbcSystemResourceOverride',
    'JmsSystemResourceOverride',
    'JTAPartition',
    'MailSessionOverride',
    'ManagedExecutorServiceTemplate',
    'ManagedScheduledExecutorServiceTemplate',
    'ManagedThreadFactoryTemplate',
    'PartitionLog',
    'PartitionWorkManager',
    'ResourceGroup',
    'ResourceManager',
    'SelfTuning',
    'SystemFileSystem',
    'UserFileSystem',
    'WebService'
]

JDBC_SYSTEM_RESOURCE_OVERRIDE_ATTR_NOT_IN_1221 = [
    'InitialCapacity',
    'MaxCapacity',
    'MinCapacity'
]

RESOURCE_MANAGER_SUBFOLDERS = [
    'CpuUtilization',
    'FileOpen',
    'HeapRetained',
    'RestartLoopProtection'
]

JMS_FOREIGN_SERVER_OVERRIDE_SUBFOLDERS = [
    'JndiProperty',
    'ForeignConnectionFactory',
    'ForeignDestination'
]

SECURITY_REALM_1221_PARAMS = [
    'AutoRestartOnNonDynamicChanges',
    'RetireTimeoutSeconds'
]

DYN_SERVER_PARAMS_IN_1221_ONLY = [
    'DynamicClusterCooloffPeriodSeconds',
    'DynamicClusterShutdownTimeoutSeconds',
    'DynamicClusterSize',
    'IgnoreSessionsDuringShutdown',
    'MachineMatchExpression',
    'MachineMatchType',
    'MaxDynamicClusterSize',
    'MinDynamicClusterSize',
    'WaitForAllSessionsDuringShutdown'
]

COHERENCE_CLUSTER_SYSTEM_RESOURCE_SUBFOLDERS = [
    'CoherenceCacheConfig',
    'CoherenceResource'
]

COHERENCE_RESOURCE_SUBFOLDERS = [
    'CoherenceAddressProviders',
    'CoherenceClusterParams',
    'CoherenceFederationParams',
    'CoherenceLoggingParams',
    'CoherencePersistenceParams'
]

COHERENCE_CLUSTER_PARAMS_SUBFOLDERS = [
    'CoherenceCache',
    'CoherenceClusterWellKnownAddresses',
    'CoherenceIdentityAsserter',
    'CoherenceKeystoreParams',
    'CoherenceService'
]
