"""
Copyright (c) 2017, 2018, Oracle and/or its affiliates. All rights reserved.
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
GET_MBEAN_TYPE = 'get_mbean_type'
GET_METHOD = 'get_method'
MERGE = 'merge'
MODEL_NAME = 'model_name'
NAME_VALUE = 'name_value'
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
LIST = 'list'
LONG = 'long'
PASSWORD = 'password'
PATH_SEPARATOR_DELIMITED_STRING = 'delimited_string[path_separator]'
PROPERTIES = 'properties'
SEMI_COLON_DELIMITED_STRING = 'delimited_string[semicolon]'
SPACE_DELIMITED_STRING = 'delimited_string[space]'
STRING = 'string'

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
    LONG,
    PASSWORD,
    STRING
]

ALIAS_DATA_TYPES = list()
ALIAS_DATA_TYPES.extend(ALIAS_PRIMITIVE_DATA_TYPES)
ALIAS_DATA_TYPES.extend(ALIAS_LIST_TYPES)
ALIAS_DATA_TYPES.extend(ALIAS_MAP_TYPES)

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
    'SAMLIdentityAsserterV2': 'weblogic.security.providers.saml.SAMLIdentityAsserterV2'
}

AUTHENTICATION_PROVIDER_PARENT_FOLDER_PATH = '/SecurityConfiguration/Realm/AuthenticationProvider'

SECURITY_PROVIDER_FOLDER_PATHS = list()
for key in AUTHENTICATION_PROVIDER_NAME_MAP:
    SECURITY_PROVIDER_FOLDER_PATHS.append(AUTHENTICATION_PROVIDER_PARENT_FOLDER_PATH + '/' + key)


