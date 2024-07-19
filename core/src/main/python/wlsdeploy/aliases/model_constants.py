"""
Copyright (c) 2017, 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""

# lists may be represented in the model as comma-separated strings
MODEL_LIST_DELIMITER = ','
KSS_KEYSTORE_TYPE = 'kss'
KSS_KEYSTORE_FILE_INDICATOR = 'kss:'

# names used within model attributes
FILE_URI = 'file:///'

# names of model elements, alphabetically

ACTIVE_DIRECTORY_AUTHENTICATOR = 'ActiveDirectoryAuthenticator'
ADJUDICATOR = 'Adjudicator'
ALLOW_LIST = 'AllowList'
ADMIN_CONSOLE = 'AdminConsole'
ADMIN_PASSWORD = 'AdminPassword'
ADMIN_SERVER_NAME = 'AdminServerName'
ADMIN_USERNAME = 'AdminUserName'
APP_DEPLOYMENTS = 'appDeployments'
APP_DIR = 'AppDir'
APPEND = 'append'
APPLICATION = 'Application'
ATP_DEFAULT_TABLESPACE = 'atp.default.tablespace'  # deprecated field name in 4.0
ATP_TEMPORARY_TABLESPACE = 'atp.temp.tablespace'  # deprecated field name in 4.0
AUDITOR = 'Auditor'
AUTHENTICATION_PROVIDER = 'AuthenticationProvider'
AUTHORIZER = 'Authorizer'
CALCULATED_LISTEN_PORTS = 'CalculatedListenPorts'
CALLOUT = 'Callout'
CAPACITY = 'Capacity'
CDI_CONTAINER = 'CdiContainer'
CERT_PATH_PROVIDER = 'CertPathProvider'
CERTIFICATE_REGISTRY = 'CertificateRegistry'
CLASSPATH = 'ClassPath'
CLIENT_PARAMS = 'ClientParams'
CLUSTER = 'Cluster'
CLUSTER_MESSAGING_MODE = 'ClusterMessagingMode'
COHERENCE_ACTIVE_DIRECTORY = 'ActiveDirectory'
COHERENCE_ADDRESS_PROVIDERS = 'CoherenceAddressProviders'
COHERENCE_ADDRESS_PROVIDER = 'CoherenceAddressProvider'
COHERENCE_CACHE = 'CoherenceCache'
COHERENCE_CACHE_CONFIG = 'CoherenceCacheConfig'
COHERENCE_CACHE_CONFIG_FILE = 'CacheConfigurationFile'
COHERENCE_CLUSTER_SYSTEM_RESOURCE = 'CoherenceClusterSystemResource'
COHERENCE_CLUSTER_PARAMS = 'CoherenceClusterParams'
COHERENCE_CUSTOM_CLUSTER_CONFIGURATION = 'CustomClusterConfigurationFileName'
COHERENCE_FEDERATION_PARAMS = 'CoherenceFederationParams'
COHERENCE_INIT_PARAM = 'CoherenceInitParam'
COHERENCE_LOGGING_PARAMS = 'CoherenceLoggingParams'
COHERENCE_PARTITION_CACHE_CONFIGS = 'CoherencePartitionCacheConfig'
COHERENCE_PERSISTENCE_PARAMS = 'CoherencePersistenceParams'
COHERENCE_RESOURCE = 'CoherenceResource'
COHERENCE_RUNTIME_CACHE_CONFIG_URI = 'RuntimeCacheConfigurationUri'
COHERENCE_SERVICE = 'CoherenceService'
COHERENCE_SNAPSHOT_DIRECTORY = 'SnapshotDirectory'
COHERENCE_SOCKET_ADDRESS = 'CoherenceSocketAddress'
COHERENCE_TRASH_DIRECTORY = 'TrashDirectory'
COHERENCE_USE_CUSTOM_CLUSTER_CONFIG = 'UsingCustomClusterConfigurationFile'
COHERENCE_WELL_KNOWN_ADDRESSES = 'CoherenceClusterWellKnownAddresses'
COHERENCE_WELL_KNOWN_ADDRESS = 'CoherenceClusterWellKnownAddress'
CONFIGURATION_PROPERTY = 'ConfigurationProperty'
CONNECTION_FACTORY = 'ConnectionFactory'
CONNECTION_URL = 'ConnectionURL'
CONTEXT_CASE = 'ContextCase'
CONTEXT_REQUEST_CLASS = 'ContextRequestClass'
CPU_UTILIZATION = 'CpuUtilization'
CREATE_TABLE_DDL_FILE = 'CreateTableDDLFile'
CREDENTIAL = 'Credential'
CREDENTIAL_ENCRYPTED = 'CredentialEncrypted'
CREDENTIAL_MAPPER = 'CredentialMapper'
CROSS_DOMAIN = 'CrossDomain'
CUSTOM_DBMS_AUTHENTICATOR = 'CustomDBMSAuthenticator'
DATA_SOURCE = 'DataSource'

# Deprecated in WDT 4.0.0
DATABASE_TYPE = 'databaseType'

DEFAULT_ADJUDICATOR = 'DefaultAdjudicator'
DEFAULT_ADMIN_SERVER_NAME = 'AdminServer'
DEFAULT_AUDITOR = 'DefaultAuditor'
DEFAULT_AUTHENTICATOR = 'DefaultAuthenticator'
DEFAULT_CREDENTIAL_MAPPER = 'DefaultCredentialMapper'
DEFAULT_DELIVERY_PARAMS = 'DefaultDeliveryParams'
DEFAULT_IDENTITY_ASSERTER = 'DefaultIdentityAsserter'
DEFAULT_REALM = 'DefaultRealm'
DEFAULT_WLS_DOMAIN_NAME = 'base_domain'
DELIVERY_FAILURE_PARAMS = 'DeliveryFailureParams'
DELIVERY_PARAMS_OVERRIDES = 'DeliveryParamsOverrides'
DESCRIPTION = 'Description'
DESTINATION_KEY = 'DestinationKey'
DIRECTORY = 'Directory'
DISTRIBUTED_QUEUE = 'DistributedQueue'
DISTRIBUTED_QUEUE_MEMBER = 'DistributedQueueMember'
DISTRIBUTED_TOPIC = 'DistributedTopic'
DISTRIBUTED_TOPIC_MEMBER = 'DistributedTopicMember'
DOMAIN = 'Domain'
DOMAIN_NAME = 'Name'
DOMAIN_INFO = 'domainInfo'
DOMAIN_INFO_ALIAS = 'DomainInfo'
DOMAIN_LIBRARIES = 'domainLibraries'
DOMAIN_SCRIPTS = 'domainBin'
DYNAMIC_CLUSTER_SERVER_GROUP_TARGETING_LIMITS = 'DynamicClusterServerGroupTargetingLimits'
DOMAIN_VERSION = 'DomainVersion'
DYNAMIC_SERVERS = 'DynamicServers'
EMBEDDED_LDAP = 'EmbeddedLDAP'
ENABLE_JMS_DB_PERSISTENCE = 'EnableJMSStoreDBPersistence'
ENABLE_JTALOG_DB_PERSISTENCE = 'EnableJTATLogDBPersistence'
ERROR_DESTINATION = 'ErrorDestination'
EXECUTE_QUEUE = 'ExecuteQueue'
EXPRESSION = 'Expression'
FAIR_SHARE_REQUEST_CLASS = 'FairShareRequestClass'
FILE_OPEN = 'FileOpen'
FILE_STORE = 'FileStore'
FLOW_CONTROL_PARAMS = 'FlowControlParams'
FOREIGN_CONNECTION_FACTORY = 'ForeignConnectionFactory'
FOREIGN_DESTINATION = 'ForeignDestination'
FOREIGN_JNDI_PROVIDER = 'ForeignJNDIProvider'
FOREIGN_JNDI_PROVIDER_OVERRIDE = 'ForeignJndiProviderOverride'
FOREIGN_JNDI_PROVIDER_LINK = 'ForeignJNDILink'
FOREIGN_SERVER = 'ForeignServer'
FRONTEND_HOST = 'FrontendHost'
GROUP = 'Group'
GROUP_PARAMS = 'GroupParams'
GROUP_MEMBER_OF = 'GroupMemberOf'
GLOBAL_VARIABLE_SUBSTITUTION = 'VariableSubstitution'
HARVESTED_TYPE = 'HarvestedType'
HARVESTER = 'Harvester'
HEALTH_SCORE = "HealthScore"
HEAP_DUMP_ACTION = 'HeapDumpAction'
HEAP_RETAINED = 'HeapRetained'
IMAGE_NOTIFICATION = 'ImageNotification'
INSTRUMENTATION = 'Instrumentation'
IPLANET_AUTHENTICATOR = 'IPlanetAuthenticator'
JDBC_CONNECTION_POOL_PARAMS = 'JDBCConnectionPoolParams'
JDBC_DATASOURCE_PARAMS = 'JDBCDataSourceParams'
JDBC_DRIVER_PARAMS = 'JDBCDriverParams'
JDBC_DRIVER_PARAMS_PROPERTIES = 'Properties'
JDBC_DRIVER_PARAMS_PROPERTY = 'Property'
JDBC_ORACLE_PARAMS = 'JDBCOracleParams'
JDBC_STORE = 'JDBCStore'
JDBC_SYSTEM_RESOURCE = 'JDBCSystemResource'
JDBC_SYSTEM_RESOURCE_OVERRIDE = 'JdbcSystemResourceOverride'
JDBC_RESOURCE = 'JdbcResource'
JMS_BRIDGE_DESTINATION = 'JMSBridgeDestination'
JMS_CONNECTION_CONSUMER = 'JmsConnectionConsumer'
JMS_NOTIFICATION = 'JMSNotification'
JMS_RESOURCE = 'JmsResource'
JMS_SERVER = 'JMSServer'
JMS_SESSION_POOL = 'JmsSessionPool'
JMS_SYSTEM_RESOURCE = 'JMSSystemResource'
JMS_SYSTEM_RESOURCE_OVERRIDE = 'JmsSystemResourceOverride'
JMX = 'JMX'
JMX_NOTIFICATION = 'JMXNotification'
JNDI_NAME = 'JNDIName'
JNDI_PROPERTY = 'JNDIProperty'
JPA = 'JPA'
JTA = 'JTA'
JTA_PARTITION = 'JtaPartition'
JTA_MIGRATABLE_TARGET = 'JTAMigratableTarget'
JOLT_CONNECTION_POOL = 'JoltConnectionPool'
KEY = 'Key'
KUBERNETES = 'kubernetes'
LDAP_AUTHENTICATOR = 'LDAPAuthenticator'
LDAP_X509_IDENTITY_ASSERTER = 'LDAPX509IdentityAsserter'
LIBRARY = 'Library'
LOAD_BALANCING_PARAMS = 'LoadBalancingParams'
LOG = 'Log'
LOG_FILTER = 'LogFilter'
LOG_ACTION = 'LogAction'
MACHINE = 'Machine'
MACHINES = 'Machines'
MAIL_SESSION = 'MailSession'
MAIL_SESSION_OVERRIDE = 'MailSessionOverride'
MAIL_SESSION_PROPERTIES = 'Properties'
MANAGED_EXECUTOR_SERVICE_TEMPLATE = 'ManagedExecutorServiceTemplate'
MANAGED_SCHEDULED_EXECUTOR_SERVICE = 'ManagedScheduledExecutorService'
MANAGED_THREAD_FACTORY_TEMPLATE = 'ManagedThreadFactoryTemplate'
MAX_DYNAMIC_SERVER_COUNT = 'MaximumDynamicServerCount'
MAX_THREADS_CONSTRAINT = 'MaxThreadsConstraint'
MIGRATABLE_TARGET = 'MigratableTarget'
MIN_THREADS_CONSTRAINT = 'MinThreadsConstraint'
MESSAGE_LOGGING_PARAMS = 'MessageLoggingParams'
MESSAGING_BRIDGE = 'MessagingBridge'
METHOD = 'Method'
MODULE_TYPE = 'ModuleType'
MULTICAST = 'Multicast'
MULTICAST_ADDRESS = 'MulticastAddress'
MULTICAST_PORT = 'MulticastPort'
NEGOTIATE_IDENTITY_ASSERTER = 'NegotiateIdentityAsserter'
NETWORK_ACCESS_POINT = 'NetworkAccessPoint'
NM_PROPERTIES = 'NMProperties'
NM_TYPE = 'NMType'
NODE_MANAGER = 'NodeManager'
NODE_MANAGER_PW_ENCRYPTED = 'NodeManagerPasswordEncrypted'
NODE_MANAGER_USER_NAME = 'NodeManagerUsername'
NOVELL_AUTHENTICATOR = 'NovellAuthenticator'
ODL_CONFIGURATION = 'ODLConfiguration'
OHS = 'OHS'
OPEN_LDAP_AUTHENTICATOR = 'OpenLDAPAuthenticator'
OPSS_INITIALIZATION = 'OPSSInitialization'
# deprecated field name in 4.0
OPSS_SECRETS = 'OPSSSecrets'
OPSS_WALLET_PASSPHRASE = 'OPSSWalletPassphrase'
OPTIONAL_FEATURE = 'OptionalFeature'
OPTIONAL_FEATURE_DEPLOYMENT = 'OptionalFeatureDeployment'
ORACLE_DATABASE_CONNECTION_TYPE = 'oracle_database_connection_type'
ORACLE_OID_AUTHENTICATOR = 'OracleInternetDirectoryAuthenticator'
ORACLE_OUD_AUTHENTICATOR = 'OracleUnifiedDirectoryAuthenticator'
ORACLE_OVD_AUTHENTICATOR = 'OracleVirtualDirectoryAuthenticator'
OVERLOAD_PROTECTION = 'OverloadProtection'
PARTITION = 'Partition'
PARTITION_SYSTEM_FILE = 'SystemFileSystem'
PARTITION_USER_FILE = 'UserFileSystem'
PARTITION_WORK_MANAGER = 'PartitionWorkManager'
PASSWORD_DIGEST_ENABLED = 'PasswordDigestEnabled'
PASSWORD_VALIDATOR = 'PasswordValidator'
PATH = 'Path'
PATH_SERVICE = 'PathService'
PASSWORD_ENCRYPTED = 'PasswordEncrypted'
PERSISTENT_STORE = 'PersistentStore'
PKI_CREDENTIAL_MAPPER = 'PKICredentialMapper'
PLAN_DIR = 'PlanDir'
PLAN_PATH = 'PlanPath'
POLICY = 'Policy'
PREPEND = 'prepend'
PROPERTIES = 'Properties'
PRODUCTION_MODE_ENABLED = 'ProductionModeEnabled'
PROTOCOL = 'Protocol'
QUEUE = 'Queue'
QUOTA = 'Quota'
REALM = 'Realm'
RECOVER_ONLY_ONCE = 'RecoverOnlyOnce'
RCU_ADMIN_PASSWORD = 'rcu_admin_password'
RCU_ADMIN_USER = 'rcu_admin_user'
RCU_COMP_INFO = 'compInfoXMLLocation'
RCU_DATABASE_TYPE = 'rcu_database_type'
RCU_DB_CONN_STRING = 'rcu_db_conn_string'
RCU_DB_INFO = 'RCUDbInfo'
RCU_DEFAULT_TABLESPACE = 'rcu_default_tablespace'
RCU_EDITION = 'rcu_edition'
RCU_PREFIX = 'rcu_prefix'
RCU_SCHEMA_PASSWORD = 'rcu_schema_password'
RCU_STG_INFO = 'storageXMLLocation'
RCU_TEMP_TBLSPACE = 'rcu_temp_tablespace'
RCU_UNICODE_SUPPORT = 'rcu_unicode_support'
RCU_VARIABLES = 'rcu_variables'
REMOTE_CONSOLE_HELPER = 'RemoteConsoleHelper'
REMOTE_DOMAIN = 'RemoteDomain'
REMOTE_HOST = 'RemoteHost'
REMOTE_PASSWORD = 'RemotePassword'
REMOTE_PORT = 'RemotePort'
REMOTE_RESOURCE = 'RemoteResource'
REMOTE_USER = 'RemoteUser'
REPLACE = 'replace'
RESOURCE_GROUP = 'ResourceGroup'
RESOURCE_GROUP_TEMPLATE = 'ResourceGroupTemplate'
RESOURCE_ID = 'ResourceID'
RESOURCES = 'resources'
RESOURCE_MANAGEMENT = 'ResourceManagement'
RESOURCE_MANAGER = 'ResourceManager'
RESPONSE_TIME_REQUEST_CLASS = 'ResponseTimeRequestClass'
RESTFUL_MANAGEMENT_SERVICES = 'RestfulManagementServices'
REST_NOTIFICATION = 'RestNotification'
RO_SQL_AUTHENTICATOR = 'ReadOnlySQLAuthenticator'
ROLE_MAPPER = 'RoleMapper'
SAF_AGENT = 'SAFAgent'
SAF_ERROR_DESTINATION = 'SafErrorDestination'
SAF_ERROR_HANDLING = 'SAFErrorHandling'
SAF_IMPORTED_DESTINATION = 'SAFImportedDestinations'
SAF_LOGIN_CONTEXT = 'SAFLoginContext'
SAF_MESSAGE_LOG_FILE = 'JmssafMessageLogFile'
SAF_QUEUE = 'SAFQueue'
SAF_REMOTE_CONTEXT = 'SAFRemoteContext'
SAF_TOPIC = 'SAFTopic'
SAML_AUTHENTICATOR = 'SAMLAuthenticator'
SAML_CREDENTIAL_MAPPER_V2 = 'SAMLCredentialMapperV2'
SAML_IDENTITY_ASSERTER_V2 = 'SAML2IdentityAsserterV2'
SAML2_CREDENTIAL_MAPPER = 'SAML2CredentialMapper'
SAML2_IDENTITY_ASSERTER = 'SAML2IdentityAsserter'
SCRIPT_ACTION = 'ScriptAction'
SECURE_MODE = 'SecureMode'
SECURE_MODE_ENABLED = 'SecureModeEnabled'
SECURITY = 'Security'
SECURITY_CONFIGURATION = 'SecurityConfiguration'
SECURITY_CONFIGURATION_CD_ENABLED = 'CrossDomainSecurityEnabled'
SECURITY_CONFIGURATION_PASSWORD = 'CredentialEncrypted'
SECURITY_CONFIGURATION_NM_PASSWORD = 'NodeManagerPasswordEncrypted'
SECURITY_PARAMS = 'SecurityParams'
SELF_TUNING = 'SelfTuning'
SERVER = 'Server'
SERVER_FAILURE_TRIGGER = 'ServerFailureTrigger'
SERVER_GROUP_TARGETING_LIMITS = 'ServerGroupTargetingLimits'
SERVER_NAME_PREFIX = 'ServerNamePrefix'
SERVER_NAME_START_IDX = 'ServerNameStartingIndex'
SERVER_START = 'ServerStart'
SERVER_START_MODE = 'ServerStartMode'
SERVER_TEMPLATE = 'ServerTemplate'
SHUTDOWN_CLASS = 'ShutdownClass'
SINGLETON_SERVICE = 'SingletonService'
SMTP_NOTIFICATION = 'SMTPNotification'
SNMP_NOTIFICATION = 'SNMPNotification'
SOURCE_DESTINATION = 'SourceDestination'
SQL_AUTHENTICATOR = 'SQLAuthenticator'
SSL = 'SSL'
STARTUP_CLASS = 'StartupClass'
STORE = 'Store'
SUB_DEPLOYMENT = 'SubDeployment'
SUB_DEPLOYMENT_NAME = 'SubDeploymentName'
SUB_MODULE_TARGETS = 'subModuleTargets'
SYSTEM_COMPONENT = 'SystemComponent'
SYSTEM_PASSWORD_VALIDATOR = 'SystemPasswordValidator'
TARGET = 'Target'
TARGET_DESTINATION = 'TargetDestination'
TARGET_KEY = 'TargetKey'
TEMPLATE = 'Template'
THREAD_DUMP_ACTION = 'ThreadDumpAction'
THRESHOLDS = 'Thresholds'
TNS_ENTRY = 'tns.alias'
TOPIC = 'Topic'
TOPOLOGY = 'topology'
TRANSACTION_LOG_JDBC_STORE = 'TransactionLogJDBCStore'
TRANSACTION_PARAMS = 'TransactionParams'
TRIGGER = 'Trigger'
UNIFORM_DISTRIBUTED_QUEUE = 'UniformDistributedQueue'
UNIFORM_DISTRIBUTED_TOPIC = 'UniformDistributedTopic'
UNIX_MACHINE = 'UnixMachine'
UNIX_MACHINE_ATTRIBUTE = 'PostBindGID'
UPDATE_MODE = 'UpdateMode'
USE_ATP = 'useATP'
USER = 'User'
USER_ATTRIBUTES = 'UserAttribute'
USE_SAMPLE_DATABASE = 'UseSampleDatabase'
USE_SSL = "useSSL"
VERRAZZANO = "verrazzano"
VIRTUAL_HOST = 'VirtualHost'
VIRTUAL_TARGET = 'VirtualTarget'
VIRTUAL_USER_AUTHENTICATOR = 'VirtualUserAuthenticator'
WATCH = 'Watch'
WATCH_NOTIFICATION = 'WatchNotification'
WEBAPP_CONTAINER = 'WebAppContainer'
WEB_SERVER = 'WebServer'
WEB_SERVER_LOG = 'WebServerLog'
WEB_SERVICE = 'WebService'
WEB_SERVICE_BUFFERING = 'WebServiceBuffering'
WEB_SERVICE_LOGICAL_STORE = 'WebServiceLogicalStore'
WEB_SERVICE_PERSISTENCE = 'WebServicePersistence'
WEB_SERVICE_PHYSICAL_STORE = 'WebServicePhysicalStore'
WEB_SERVICE_REQUEST_BUFFERING_QUEUE = 'WebServiceRequestBufferingQueue'
WEB_SERVICE_RESPONSE_BUFFERING_QUEUE = 'WebServiceResponseBufferingQueue'
WEB_SERVICE_SECURITY = 'WebserviceSecurity'
WEBLOGIC_CERT_PATH_PROVIDER = 'WebLogicCertPathProvider'
WORK_MANAGER = "WorkManager"
WLDF_INSTRUMENTATION_MONITOR = "WLDFInstrumentationMonitor"
WLDF_RESOURCE = "WLDFResource"
WLDF_SYSTEM_RESOURCE = "WLDFSystemResource"
WLS_POLICIES = "WLSPolicies"
WLS_ROLES = "WLSRoles"
WLS_USER_PASSWORD_CREDENTIAL_MAPPINGS = 'WLSUserPasswordCredentialMappings'
WLS_DEFAULT_AUTHENTICATION = 'WLSDefaultAuthentication'
WS_RELIABLE_DELIVERY_POLICY = 'WSReliableDeliveryPolicy'
WTC_SERVER = 'WTCServer'
XACML_AUTHORIZER = 'XACMLAuthorizer'
XACML_DOCUMENT = 'XacmlDocument'
XACML_ROLE_MAPPER = 'XACMLRoleMapper'
XACML_STATUS = 'XacmlStatus'
XML_ENTITY_CACHE = 'XMLEntityCache'
XML_REGISTRY = 'XMLRegistry'

# names of attributes, alphabetically

ABSOLUTE_PLAN_PATH = 'AbsolutePlanPath'
ABSOLUTE_SOURCE_PATH = 'AbsoluteSourcePath'
ACTION = 'Action'
ACTIVE_TYPE = 'ActiveType'
ARGUMENTS = 'Arguments'
AUTO_MIGRATION_ENABLED = 'AutoMigrationEnabled'
CANDIDATE_MACHINE = 'CandidateMachine'
CANDIDATE_MACHINES_FOR_MIGRATABLE_SERVER = 'CandidateMachinesForMigratableServer'
COMPONENT_TYPE = 'ComponentType'
CONSTRAINED_CANDIDATE_SERVER = 'ConstrainedCandidateServer'
CUSTOM_IDENTITY_KEYSTORE_FILE = 'CustomIdentityKeyStoreFileName'
CUSTOM_TRUST_KEYSTORE_FILE = 'CustomTrustKeyStoreFileName'
DATABASE_LESS_LEASING_BASIS = 'DatabaseLessLeasingBasis'
DEPLOYMENT_ORDER = 'DeploymentOrder'
DESTINATION_SERVER = 'DestinationServer'
DRIVER_NAME = 'DriverName'
DRIVER_PARAMS_PROPERTY_VALUE = 'Value'
DRIVER_PARAMS_PROPERTY_VALUE_ENCRYPTED = 'EncryptedValueEncrypted'
DRIVER_PARAMS_PROPERTY_SYS_PROP_VALUE = 'SysPropValue'
DRIVER_PARAMS_USER_PROPERTY = 'user'
DRIVER_PARAMS_TRUSTSTORE_PROPERTY = 'javax.net.ssl.trustStore'
DRIVER_PARAMS_KEYSTORE_PROPERTY = 'javax.net.ssl.keyStore'
DRIVER_PARAMS_TRUSTSTORETYPE_PROPERTY = 'javax.net.ssl.trustStoreType'
DRIVER_PARAMS_KEYSTORETYPE_PROPERTY = 'javax.net.ssl.keyStoreType'
DRIVER_PARAMS_TRUSTSTOREPWD_PROPERTY = 'javax.net.ssl.trustStorePassword'
DRIVER_PARAMS_KEYSTOREPWD_PROPERTY = 'javax.net.ssl.keyStorePassword'
DRIVER_PARAMS_NET_SERVER_DN_MATCH_PROPERTY = 'oracle.net.ssl_server_dn_match'
DRIVER_PARAMS_NET_SSL_VERSION = 'oracle.net.ssl_version'
DRIVER_PARAMS_NET_SSL_VERSION_VALUE = '1.2'
DRIVER_PARAMS_NET_TNS_ADMIN = 'oracle.net.tns_admin'
DRIVER_PARAMS_NET_FAN_ENABLED = 'oracle.jdbc.fanEnabled'
DYNAMIC_CLUSTER_SIZE = 'DynamicClusterSize'
ENABLED = 'Enabled'
HARVESTED_ATTRIBUTE = 'HarvestedAttribute'
HARVESTED_INSTANCE = 'HarvestedInstance'
HOSTING_SERVER = 'HostingServer'
INSTALL_DIR = 'InstallDir'
LISTEN_ADDRESS = 'ListenAddress'
LISTEN_PORT = 'ListenPort'
MASKED_PASSWORD = '<Masked>'
MIGRATION_BASIS = 'MigrationBasis'
MIME_MAPPING_FILE = 'MimeMappingFile'
NAME = 'Name'
NOTIFICATION = 'Notification'
PASSWORD = 'Password'
PATH_TO_SCRIPT = 'PathToScript'
PLAN_STAGING_MODE = 'PlanStagingMode'
SECURITY_DD_MODEL = 'SecurityDDModel'
SET_OPTION_APP_DIR = 'AppDir'
SET_OPTION_DOMAIN_NAME = 'DomainName'
SET_OPTION_JAVA_HOME = 'JavaHome'
SET_OPTION_SERVER_START_MODE = 'ServerStartMode'
SOURCE_PATH = 'SourcePath'
STAGE_MODE = 'StagingMode'
TAGS = 'Tags'
TARGETS = 'Targets'
URL = 'URL'
USER_PREFERRED_SERVER = 'UserPreferredServer'

# Default Security Provider names and types
DEFAULT_ADJUDICATOR_NAME = 'DefaultAdjudicator'
DEFAULT_ADJUDICATOR_TYPE = DEFAULT_ADJUDICATOR
DEFAULT_AUDITOR_NAME = None
DEFAULT_AUDITOR_TYPE = DEFAULT_AUDITOR
DEFAULT_AUTHENTICATOR_NAME = 'DefaultAuthenticator'
DEFAULT_AUTHENTICATOR_TYPE = DEFAULT_AUTHENTICATOR
DEFAULT_IDENTITY_ASSERTER_NAME = 'DefaultIdentityAsserter'
DEFAULT_IDENTITY_ASSERTER_TYPE = DEFAULT_IDENTITY_ASSERTER
DEFAULT_AUTHORIZER_NAME = 'XACMLAuthorizer'
DEFAULT_AUTHORIZER_TYPE = XACML_AUTHORIZER
DEFAULT_CERT_PATH_PROVIDER_NAME = 'WebLogicCertPathProvider'
DEFAULT_CERT_PATH_PROVIDER_TYPE = WEBLOGIC_CERT_PATH_PROVIDER
DEFAULT_CREDENTIAL_MAPPER_NAME = 'DefaultCredentialMapper'
DEFAULT_CREDENTIAL_MAPPER_TYPE = DEFAULT_CREDENTIAL_MAPPER
DEFAULT_PASSWORD_VALIDATOR_NAME = 'SystemPasswordValidator'
DEFAULT_PASSWORD_VALIDATOR_TYPE = SYSTEM_PASSWORD_VALIDATOR
DEFAULT_ROLE_MAPPER_NAME = 'XACMLRoleMapper'
DEFAULT_ROLE_MAPPER_TYPE = XACML_ROLE_MAPPER

# SSL store types
STORE_TYPE_SSO = 'SSO'

KNOWN_TOPLEVEL_MODEL_SECTIONS = [
    DOMAIN_INFO,
    TOPOLOGY,
    RESOURCES,
    APP_DEPLOYMENTS,
    KUBERNETES,
    VERRAZZANO
]

# the contents of these sections are based on CRD schemas
CRD_MODEL_SECTIONS = [
    KUBERNETES,
    VERRAZZANO
]

# these domain attributes have special processing in create,
# and should be skipped in regular attribute processing.
CREATE_ONLY_DOMAIN_ATTRIBUTES = [
    DOMAIN_NAME,
    ADMIN_SERVER_NAME
]

# these JDBC driver param properties are paths, and may reference the archive.
# there is special processing to discover and deploy them.
DRIVER_PARAMS_PATH_PROPERTIES = [
    DRIVER_PARAMS_KEYSTORE_PROPERTY,
    DRIVER_PARAMS_NET_TNS_ADMIN,
    DRIVER_PARAMS_TRUSTSTORE_PROPERTY
]

# Model Path constants
PATH_TO_RCU_DB_CONN = '%s:/%s/%s' % (DOMAIN_INFO, RCU_DB_INFO, RCU_DB_CONN_STRING)
PATH_TO_RCU_PREFIX = '%s:/%s/%s' % (DOMAIN_INFO, RCU_DB_INFO, RCU_PREFIX)
PATH_TO_RCU_ADMIN_PASSWORD = '%s:/%s/%s' % (DOMAIN_INFO, RCU_DB_INFO, RCU_ADMIN_PASSWORD)
PATH_TO_RCU_SCHEMA_PASSWORD = '%s:/%s/%s' % (DOMAIN_INFO, RCU_DB_INFO, RCU_SCHEMA_PASSWORD)

# Constants to define the scope of discovering security provider data
ALL = 'ALL'
DISCOVER_SECURITY_PROVIDER_TYPES = [
    ALL,
    DEFAULT_AUTHENTICATOR,
    DEFAULT_CREDENTIAL_MAPPER,
    XACML_AUTHORIZER,
    XACML_ROLE_MAPPER
]

DISCOVER_SECURITY_PROVIDER_TYPES_LOWER_CASE = []
for type in DISCOVER_SECURITY_PROVIDER_TYPES:
    DISCOVER_SECURITY_PROVIDER_TYPES_LOWER_CASE.append(type.lower())

DEFAULT_AUTHENTICATOR_USER_ATTRIBUTE_KEYS = [
    'c',
    'departmentnumber',
    'displayname',
    'employeenumber',
    'employeetype',
    'facsimiletelephonenumber',
    'givenname',
    'homephone',
    'homepostaladdress',
    'l',
    'mail',
    'mobile',
    'pager',
    'postaladdress',
    'postofficebox',
    'preferredlanguage',
    'st',
    'street',
    'telephonenumber',
    'title'
]
