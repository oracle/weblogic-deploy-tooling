"""
Copyright (c) 2017, 2019, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0

These constants are internal to the aliases module and should not be used, as they are not part of the public API.
"""
from wlsdeploy.util.enum import Enum

ACCESS = 'access'
ATTRIBUTES = 'attributes'
CHILD_FOLDERS_TYPE = 'child_folders_type'
CONTAINS = 'contains'
DEFAULT = 'default'
DEFAULT_NAME_VALUE = 'default_name_value'
FLATTENED_FOLDER_DATA = 'flattened_folder_data'
FOLDERS = 'folders'
FOLDER_PARAMS = 'folder_params'
GET_MBEAN_TYPE = 'get_mbean_type'
GET_METHOD = 'get_method'
MERGE = 'merge'
MODEL_NAME = 'model_name'
NAME_VALUE = 'name_value'
PASSWORD_TOKEN = "--FIX ME--"
PREFERRED_MODEL_TYPE = 'preferred_model_type'
RESTART_REQUIRED = 'restart_required'
SET_MBEAN_TYPE = 'set_mbean_type'
SET_METHOD = 'set_method'
UNRESOLVED_ATTRIBUTES_MAP = '__unresolved_attributes__'
UNRESOLVED_FOLDERS_MAP = '__unresolved_folders__'
USES_PATH_TOKENS = 'uses_path_tokens'
VALUE = 'value'
# VERSION is used for folder versioning
VERSION = 'version'
# VERSION_RAGE is used for attribute versioning
VERSION_RANGE = 'version'
WLST_ATTRIBUTES_PATH = 'wlst_attributes_path'
WLST_CREATE_PATH = 'wlst_create_path'
WLST_LIST_PATH = 'wlst_list_path'
WLST_MODE = 'wlst_mode'
WLST_NAME = 'wlst_name'
WLST_NAMES_MAP = '__wlst_names__'
WLST_PATH = 'wlst_path'
WLST_PATHS = 'wlst_paths'
WLST_READ_TYPE = 'wlst_read_type'
WLST_SKIP_NAMES = '__wlst_skip_names__'
WLST_SUBFOLDERS_PATH = 'wlst_subfolders_path'
WLST_TYPE = 'wlst_type'

# CHILD_FOLDER_TYPES
MULTIPLE = 'multiple'
MULTIPLE_WITH_TYPE_SUBFOLDER = 'multiple_with_type_subfolder'
NONE_CHILD_FOLDERS_TYPE = 'none'
SINGLE = 'single'
SINGLE_UNPREDICTABLE = 'single_unpredictable'

ChildFoldersTypes = Enum(['MULTIPLE', 'MULTIPLE_WITH_TYPE_SUBFOLDER', 'NONE', 'SINGLE', 'SINGLE_UNPREDICTABLE'])

# get_method values
GET = 'GET'
LSA = 'LSA'
NONE = 'NONE'

# set_method values
MBEAN = 'MBEAN'

# attribute wlst_type values
BOOLEAN = 'boolean'
COMMA_DELIMITED_STRING = 'delimited_string[comma]'
CREDENTIAL = 'credential'
DELIMITED_STRING = 'delimited_string'
DICTIONARY = 'dict'
DOUBLE = 'double'
INTEGER = 'integer'
JARRAY = 'jarray'
JAVA_LANG_BOOLEAN = 'java.lang.Boolean'
LIST = 'list'
LONG = 'long'
OBJECT = 'object'
PASSWORD = 'password'
PATH_SEPARATOR_DELIMITED_STRING = 'delimited_string[path_separator]'
PROPERTIES = 'properties'
SEMI_COLON_DELIMITED_STRING = 'delimited_string[semicolon]'
SPACE_DELIMITED_STRING = 'delimited_string[space]'
STRING = 'string'

ALIAS_DELIMITED_TYPES = [
    COMMA_DELIMITED_STRING,
    DELIMITED_STRING,
    PATH_SEPARATOR_DELIMITED_STRING,
    SEMI_COLON_DELIMITED_STRING,
    SPACE_DELIMITED_STRING
]

ALIAS_LIST_TYPES = [
    COMMA_DELIMITED_STRING,
    DELIMITED_STRING,
    JARRAY,
    LIST,
    PATH_SEPARATOR_DELIMITED_STRING,
    SEMI_COLON_DELIMITED_STRING,
    SPACE_DELIMITED_STRING
]
ALIAS_MAP_TYPES = [PROPERTIES, DICTIONARY]

ALIAS_PRIMITIVE_DATA_TYPES = [
    BOOLEAN,
    CREDENTIAL,
    DOUBLE,
    INTEGER,
    JAVA_LANG_BOOLEAN,
    LONG,
    PASSWORD,
    STRING
]

ALIAS_DATA_TYPES = list()
ALIAS_DATA_TYPES.extend(ALIAS_PRIMITIVE_DATA_TYPES)
ALIAS_DATA_TYPES.extend(ALIAS_LIST_TYPES)
ALIAS_DATA_TYPES.extend(ALIAS_MAP_TYPES)


def __build_security_provider_data_structures(name_map, base_path):
    """
    Populate the security provider data structures for the given provider type.
    :param name_map: the provider name map
    :param base_path: the provider base path
    """
    for key, value in name_map.iteritems():
        SECURITY_PROVIDER_FOLDER_PATHS.append(base_path + '/' + key)
        SECURITY_PROVIDER_NAME_MAP[key] = value
        mbean_name = value + 'MBean'
        SECURITY_PROVIDER_MBEAN_NAME_MAP[mbean_name] = key
    return


ADJUDICATION_PROVIDER_NAME_MAP = {
    'DefaultAdjudicator': 'weblogic.security.providers.authorization.DefaultAdjudicator'
}

AUDIT_PROVIDER_NAME_MAP = {
    'DefaultAuditor': 'weblogic.security.providers.audit.DefaultAuditor'
}

AUTHENTICATION_PROVIDER_NAME_MAP = {
    'SAML2IdentityAsserter': 'com.bea.security.saml2.providers.SAML2IdentityAsserter',
    'ActiveDirectoryAuthenticator': 'weblogic.security.providers.authentication.ActiveDirectoryAuthenticator',
    'CustomDBMSAuthenticator': 'weblogic.security.providers.authentication.CustomDBMSAuthenticator',
    'DefaultAuthenticator': 'weblogic.security.providers.authentication.DefaultAuthenticator',
    'DefaultIdentityAsserter': 'weblogic.security.providers.authentication.DefaultIdentityAsserter',
    'IPlanetAuthenticator': 'weblogic.security.providers.authentication.IPlanetAuthenticator',
    'LDAPAuthenticator': 'weblogic.security.providers.authentication.LDAPAuthenticator',
    'LDAPX509IdentityAsserter': 'weblogic.security.providers.authentication.LDAPX509IdentityAsserter',
    'NegotiateIdentityAsserter': 'weblogic.security.providers.authentication.NegotiateIdentityAsserter',
    'NovellAuthenticator': 'weblogic.security.providers.authentication.NovellAuthenticator',
    'OpenLDAPAuthenticator': 'weblogic.security.providers.authentication.OpenLDAPAuthenticator',
    'OracleInternetDirectoryAuthenticator':
        'weblogic.security.providers.authentication.OracleInternetDirectoryAuthenticator',
    'OracleUnifiedDirectoryAuthenticator':
        'weblogic.security.providers.authentication.OracleUnifiedDirectoryAuthenticator',
    'OracleVirtualDirectoryAuthenticator':
        'weblogic.security.providers.authentication.OracleVirtualDirectoryAuthenticator',
    'ReadOnlySQLAuthenticator': 'weblogic.security.providers.authentication.ReadOnlySQLAuthenticator',
    'SQLAuthenticator': 'weblogic.security.providers.authentication.SQLAuthenticator',
    'VirtualUserAuthenticator': 'weblogic.security.providers.authentication.VirtualUserAuthenticator',
    'SAMLAuthenticator': 'weblogic.security.providers.saml.SAMLAuthenticator',
    'SAMLIdentityAsserterV2': 'weblogic.security.providers.saml.SAMLIdentityAsserterV2',
    'TrustServiceIdentityAsserter': 'oracle.security.jps.wls.providers.trust.TrustServiceIdentityAsserter',
}

AUTHORIZATION_PROVIDER_NAME_MAP = {
    'DefaultAuthorizer': 'weblogic.security.providers.authorization.DefaultAuthorizer',
    'XACMLAuthorizer': 'weblogic.security.providers.xacml.authorization.XACMLAuthorizer'
}

CERT_PATH_PROVIDER_NAME_MAP = {
    'CertificateRegistry': 'weblogic.security.providers.pk.CertificateRegistry',
    'WebLogicCertPathProvider': 'weblogic.security.providers.pk.WebLogicCertPathProvider'
}

CREDENTIAL_MAPPING_PROVIDER_NAME_MAP = {
    'SAML2CredentialMapper': 'com.bea.security.saml2.providers.SAML2CredentialMapper',
    'DefaultCredentialMapper': 'weblogic.security.providers.credentials.DefaultCredentialMapper',
    'PKICredentialMapper': 'weblogic.security.providers.credentials.PKICredentialMapper',
    'SAMLCredentialMapperV2': 'weblogic.security.providers.saml.SAMLCredentialMapperV2'
}

PASSWORD_VALIDATION_PROVIDER_NAME_MAP = {
    'SystemPasswordValidator': 'com.bea.security.providers.authentication.passwordvalidator.SystemPasswordValidator'
}

ROLE_MAPPING_PROVIDER_NAME_MAP = {
    'DefaultRoleMapper': 'weblogic.security.providers.authorization.DefaultRoleMapper',
    'XACMLRoleMapper': 'weblogic.security.providers.xacml.authorization.XACMLRoleMapper'
}

REALM_FOLDER_PATH = '/SecurityConfiguration/Realm'
ADJUDICATION_PROVIDER_PARENT_FOLDER_PATH = REALM_FOLDER_PATH + '/Adjudicator'
AUDIT_PROVIDER_PARENT_FOLDER_PATH = REALM_FOLDER_PATH + '/Auditor'
AUTHENTICATION_PROVIDER_PARENT_FOLDER_PATH = REALM_FOLDER_PATH + '/AuthenticationProvider'
AUTHORIZATION_PROVIDER_PARENT_FOLDER_PATH = REALM_FOLDER_PATH + '/Authorizer'
CERT_PATH_PROVIDER_PARENT_FOLDER_PATH = REALM_FOLDER_PATH + '/CertPathProvider'
CREDENTIAL_MAPPING_PROVIDER_PARENT_FOLDER_PATH = REALM_FOLDER_PATH + '/CredentialMapper'
PASSWORD_VALIDATION_PROVIDER_PARENT_FOLDER_PATH = REALM_FOLDER_PATH + '/PasswordValidator'
ROLE_MAPPING_PROVIDER_PARENT_FOLDER_PATH = REALM_FOLDER_PATH + '/RoleMapper'

SECURITY_PROVIDER_FOLDER_PATHS = list()
SECURITY_PROVIDER_NAME_MAP = dict()
SECURITY_PROVIDER_MBEAN_NAME_MAP = dict()
__build_security_provider_data_structures(ADJUDICATION_PROVIDER_NAME_MAP, ADJUDICATION_PROVIDER_PARENT_FOLDER_PATH)
__build_security_provider_data_structures(AUDIT_PROVIDER_NAME_MAP, AUDIT_PROVIDER_PARENT_FOLDER_PATH)
__build_security_provider_data_structures(AUTHENTICATION_PROVIDER_NAME_MAP, AUTHENTICATION_PROVIDER_PARENT_FOLDER_PATH)
__build_security_provider_data_structures(AUTHORIZATION_PROVIDER_NAME_MAP, AUTHORIZATION_PROVIDER_PARENT_FOLDER_PATH)
__build_security_provider_data_structures(CERT_PATH_PROVIDER_NAME_MAP, CERT_PATH_PROVIDER_PARENT_FOLDER_PATH)
__build_security_provider_data_structures(CREDENTIAL_MAPPING_PROVIDER_NAME_MAP,
                                          CREDENTIAL_MAPPING_PROVIDER_PARENT_FOLDER_PATH)
__build_security_provider_data_structures(PASSWORD_VALIDATION_PROVIDER_NAME_MAP,
                                          PASSWORD_VALIDATION_PROVIDER_PARENT_FOLDER_PATH)
__build_security_provider_data_structures(ROLE_MAPPING_PROVIDER_NAME_MAP, ROLE_MAPPING_PROVIDER_PARENT_FOLDER_PATH)
