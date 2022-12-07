"""
Copyright (c) 2021, 2022, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import re

import java.lang.Boolean as Boolean
import java.util.Map as Map

import com.oracle.cie.domain.script.jython.WLSTException as offlineWLSTException

import java.lang.ClassCastException as ClassCastException
import java.lang.NoSuchMethodException as NoSuchMethodException

from wlsdeploy.logging.platform_logger import PlatformLogger

CREDENTIAL_FIELD_NAME_MARKERS = ['Password', 'PassPhrase', 'Credential', 'Encrypted', 'Secret']
CREDENTIAL_FIELD_EXCEPTIONS = [
    'ClearTextCredentialAccessEnabled'.lower(),
    'CORSAllowedCredentials'.lower(),
    'CredentialGenerated'.lower(),
    'CredentialMappingDeploymentEnabled'.lower(),
    'CredentialMappingEnabled'.lower(),
    'CredentialPolicy'.lower(),
    'DebugSecurityPasswordPolicy'.lower(),
    'DefaultCredentialProviderSTSURI'.lower(),
    'DeployCredentialMappingIgnored'.lower(),
    'EnforceValidBasicAuthCredentials'.lower(),
    'KeyEncrypted'.lower(),
    'MaxPasswordLength'.lower(),
    'MinimumPasswordLength'.lower(),
    'MinPasswordLength'.lower(),
    'PasswordAlgorithm'.lower(),
    'PasswordDigestEnabled'.lower(),
    'PasswordStyle'.lower(),
    'PasswordStyleRetained'.lower(),
    'PlaintextPasswordsEnabled'.lower(),
    'SQLGetUsersPassword'.lower(),
    'SQLSetUserPassword'.lower(),
    'UseDatabaseCredentials'.lower(),
    'UsePasswordIndirection'.lower(),
    'WarnOnUsernamePasswords'.lower()
]

PATH_ATTRIBUTE_NAME_ENDINGS = ['File', 'Directory', 'FileName', 'Home', 'DirectoryName', 'Path', 'Dir', 'Root']
PATH_ATTRIBUTE_NAME_EXCEPTIONS = [
    'AcceptContextPathInGetRealPath',
    'BasePath',
    'CacheInAppDirectory',
    'ConsoleContextPath',
    'DebugJMSMessagePath',
    'DebugSAFMessagePath',
    'DebugSecurityCertPath',
    'DefaultWebAppContextRoot',
    'ErrorPath',
    'OidRoot',
    'OracleEnableJavaNetFastPath',
    'UriPath',
    'UsingCustomClusterConfigurationFile'
]

PATH_SERVER_NAMES = ['AdminServer']
SERVER_NAME_PATTERN = r'Server[s]?-\d{3,5}'
PARTITION_NAME_PATTERN = r'Partition[s]?-\d{3,5}'
RESOURCE_GROUP_TEMPLATE_PATTERN = r'ResourceGroupTemplate[s]?-\d{3,5}'

DOMAIN_HOME_TOKEN = '@@DOMAIN_HOME@@'
WL_HOME_TOKEN = '@@WL_HOME@@'
ORACLE_HOME_TOKEN = '@@ORACLE_HOME@@'
JAVA_HOME_TOKEN = '@@JAVA_HOME@@'
CURRENT_DIRECTORY_TOKEN = '@@PWD@@'
TEMP_DIRECTORY_TOKEN = '@@TMP@@'

__logger = PlatformLogger('test.generate.wlst')
__class_name = 'generate_wlst'

wlst_functions = None


def wlst_silence():
    """
    Silence the chatter that wlst generates by default.
    """
    _method_name = 'wlst_silence'
    __logger.entering(class_name=__class_name, method_name=_method_name)

    local_wls = _load_global('WLS')
    local_wls_on = _load_global('WLS_ON')
    local_wls.setLogToStdOut(False)
    local_wls.setShowLSResult(False)
    local_wls_on.setlogToStandardOut(False)
    local_wls_on.setHideDumpStack('true')
    local_wls.getCommandExceptionHandler().setMode(True)
    local_wls.getCommandExceptionHandler().setSilent(True)

    __logger.exiting(class_name=__class_name, method_name=_method_name)


def connect(userid, password, url):
    """
    Connect to the domain admin server.
    :param userid: for the connection
    :param password: for the connection
    :param url: host and port for the connection
    :return: True if connected
    """
    _method_name = 'connect'
    __logger.entering(userid, url, class_name=__class_name, method_name=_method_name)

    online_wlst_exception = _load_global('WLSTException')
    try:
        __logger.finer('Connect to admin server at {0}', url, class_name=__class_name, method_name=_method_name)
        local_connect = _load_global('connect')

        local_connect(username=userid, password=password, url=url)
        is_connected = _load_global('connected')
        __logger.finer('Status of connect to admin server at url {0} is {1}', url, is_connected,
                       class_name=__class_name, method_name=_method_name)
        local_edit = _load_global('edit')
        local_edit()
        __logger.finer('Cancel outstanding edit sessions for admin server at {0}', url,
                       class_name=__class_name, method_name=_method_name)
        cancel_edit = _load_global('cancelEdit')
        cancel_edit('y')
        __logger.finer('Start edit session under admin server at {0}', url,
                       class_name=__class_name, method_name=_method_name)

        local_start_edit = _load_global('startEdit')
        local_start_edit()
    except online_wlst_exception, we:
        __logger.warning('Unable to connect to the domain at url {0} : {1}', url, str(we),
                         class_name=__class_name, method_name=_method_name)
    is_connected = _load_global('connected')

    __logger.exiting(result=is_connected, class_name=__class_name, method_name=_method_name)
    return is_connected


def disconnect():
    """
    Disconnect from the connected domain admin server.
    """
    _method_name = 'disconnect'

    online_wlst_exception = _load_global('WLSTException')
    __logger.entering(class_name=__class_name, method_name=_method_name)
    try:
        local_stop_edit = _load_global('stopEdit')
        local_stop_edit('y')
        local_disconnect = _load_global('disconnect')
        local_disconnect()
    except online_wlst_exception, we:
        __logger.warning('Unable to cancel edit session and disconnect : {0}', str(we),
                         class_name=__class_name, method_name=_method_name)

    __logger.exiting(class_name=__class_name, method_name=_method_name)


def get(attribute_name):
    _method_name = 'get'

    online_wlst_exception = _load_global('WLSTException')
    local_get = _load_global('get')
    get_value = None
    success = True
    try:
        get_value = local_get(attribute_name)
    except (online_wlst_exception, offlineWLSTException), we:
        success = False
        # We don't expect to be able to retrieve credential fields so don't log a warning for them.
        if is_credential_field(attribute_name):
            __logger.fine('Unable to get credential attribute {0} at location {1} : {2}',
                          attribute_name, current_path(), we.getLocalizedMessage(),
                          class_name=__class_name, method_name=_method_name)
        else:
            __logger.warning('Unable to get attribute {0} at location {1} : {2}', attribute_name, current_path(),
                             we.getLocalizedMessage(), class_name=__class_name, method_name=_method_name)

    return success, get_value


def current_path():
    """
    Return the current mbean path from active wlst session.
    :return: path of current location in wlst
    """
    local_pwd = _load_global('pwd')
    original = local_pwd()
    start = original.find('/', 1)
    if start > 0:
        return original[start:]
    return '/'


def get_mbean_proxy(path=None):
    _method_name = 'get_mbean_proxy'
    __logger.entering(path, class_name=__class_name, method_name=_method_name)

    if path is None:
        path = current_path()
    local_cd = _load_global('cd')
    mbean_proxy = local_cd(path)
    if mbean_proxy is None:
        local_cmo = _load_global('cmo')
        mbean_proxy = local_cmo
        if mbean_proxy is None:
            update_cmo = _load_global('updateCmo')
            update_cmo()
            local_cmo = _load_global('cmo')
            mbean_proxy = local_cmo

    __logger.exiting(class_name=__class_name, method_name=_method_name, result=mbean_proxy)
    return mbean_proxy


def get_singleton_name(mbean_type):
    _method_name = 'get_singleton_name'

    online_wlst_exception = _load_global('WLSTException')
    local_ls = _load_global('ls')
    try:
        name_list = local_ls(mbean_type, returnMap='true')
    except(offlineWLSTException, online_wlst_exception), we:
        __logger.warning('Unable to ls({0}) at location {1} : {2}', mbean_type, current_path(), str(we),
                         class_name=__class_name, method_name=_method_name)
        return None
    if len(name_list) == 0:
        __logger.fine('No MBean instance found for {0} at location {1} and was not in listChildTypes',
                      mbean_type, current_path(), class_name=__class_name, method_name=_method_name)
        return None
    if len(name_list) > 1:
        __logger.warning('Singleton MBean {0} has more than one instance at location {1}', mbean_type, current_path(),
                         class_name=__class_name, method_name=_method_name)

    return name_list[0]


def read_domain(domain_home):
    """
    Read the domain using the provided domain home string.

    :param domain_home: to read into the wlst session
    :return: True if the domain was successfully read
    """
    _method_name = 'read_domain'
    __logger.entering(domain_home, class_name=__class_name, method_name=_method_name)

    online_wlst_exception = _load_global('WLSTException')
    try:
        local_read_domain = _load_global('readDomain')
        local_read_domain(domain_home)
        open_domain = True
    except (online_wlst_exception, offlineWLSTException), we:
        __logger.severe('Unable to read the domain {0}: {1}', domain_home, str(we),
                        class_name=__class_name, method_name=_method_name)
        open_domain = False

    __logger.exiting(result=open_domain, class_name=__class_name, method_name=_method_name)
    return open_domain


def can_get(mbean_type, attribute_name):
    _method_name = 'can_get'
    __logger.entering(mbean_type, attribute_name, class_name=__class_name, method_name=_method_name)

    online_wlst_exception = _load_global('WLSTException')
    local_get = _load_global('get')
    success = True
    try:
        local_get(attribute_name)
    except (online_wlst_exception, offlineWLSTException):
        success = False

    __logger.exiting(class_name=__class_name, method_name=_method_name, result=Boolean(success))
    return success


def close_domain():
    """
    Close the open domain.
    """
    local_close_domain = _load_global('closeDomain')
    local_close_domain()


def created(mbean_type, name):
    """
    Create the MBean with the provided name at the current wlst location. WLST Exceptions are caught and returned
    as False from the method.
    :param mbean_type: MBean type to create
    :param name: Name of the MBean to create
    :return: True if successfully created
    """
    _method_name = 'created'

    online_wlst_exception = _load_global('WLSTException')
    try:
        local_create = _load_global('create')
        local_create(name, mbean_type)
    except (online_wlst_exception, offlineWLSTException, ClassCastException, NoSuchMethodException), e:
        __logger.fine('Unable to create MBean {0} with name {1}  at location {2} : {3}', mbean_type, name,
                      current_path(), str(e), class_name=__class_name, method_name=_method_name)
        return False

    return True


def create_security_provider(name, mbean_subtype, mbean_type):
    """
    Create the MBean with the provided name at the current wlst location. WLST Exceptions are caught and returned
    as False from the method.
    :param mbean_type: MBean type to create
    :param name: Name of the MBean to create
    :param mbean_subtype: the subtype of the security provider to create
    :return: True if successfully created
    """
    _method_name = 'create_security_provider'
    __logger.entering(name, mbean_subtype, mbean_type, class_name=__class_name, method_name=_method_name)

    online_wlst_exception = _load_global('WLSTException')
    result = None
    try:
        local_create = _load_global('create')
        result = local_create(name, mbean_subtype, mbean_type)
    except (online_wlst_exception, offlineWLSTException, ClassCastException, NoSuchMethodException), e:
        __logger.fine('Unable to create MBean {0} with name {1} and provider subtype {2} at location {3} : {4}',
                      mbean_type, name, mbean_subtype, current_path(), str(e),
                      class_name=__class_name, method_name=_method_name)

    __logger.exiting(class_name=__class_name, method_name=_method_name, result=result)
    return result


def cd_proxy(bean_dir):
    _method_name = 'cd_proxy'
    __logger.entering(bean_dir, class_name=__class_name, method_name=_method_name)

    online_wlst_exception = _load_global('WLSTException')
    local_cd = _load_global('cd')
    proxy = None
    try:
        proxy = local_cd(bean_dir)
    except (online_wlst_exception, offlineWLSTException), we:
        __logger.warning('Failure on wlst.cd({0}) at location {1}: {2}', bean_dir, current_path(), we,
                         class_name=__class_name, method_name=_method_name)

    __logger.exiting(class_name=__class_name, method_name=_method_name, result=proxy)
    return proxy


def cd_mbean(bean_dir):
    _method_name = 'cd_mbean'
    __logger.entering(bean_dir, class_name=__class_name, method_name=_method_name)

    online_wlst_exception = _load_global('WLSTException')
    success = True
    try:
        _load_global('cd')(bean_dir)
    except (online_wlst_exception, offlineWLSTException), we:
        __logger.warning('Failure on wlst.cd({0}) at location {1}: {2}', bean_dir, current_path(),
                         we.getLocalizedMessage(), class_name=__class_name, method_name=_method_name)
        success = False

    __logger.exiting(class_name=__class_name, method_name=_method_name, result=Boolean(success))
    return success


def child_mbean_types():
    _method_name = 'child_mbean_types'
    __logger.entering(class_name=__class_name, method_name=_method_name)

    online_wlst_exception = _load_global('WLSTException')
    child_mbeans = None
    try:
        list_child_types = _load_global('listChildTypes')
        child_mbeans = list_child_types()
    except online_wlst_exception, we:
        __logger.warning('Unable to wlst.listChildTypes() at the current {0}: {1}', current_path(),
                         we.getLocalizedMessage(), class_name=__class_name, method_name=_method_name)

    __logger.exiting(class_name=__class_name, method_name=_method_name, result=child_mbeans)
    return child_mbeans


def ls_mbean_names(mbean_type):
    _method_name = 'ls_mbean_names'
    __logger.entering(mbean_type, class_name=__class_name, method_name=_method_name)

    online_wlst_exception = _load_global('WLSTException')
    local_ls = _load_global('ls')
    mbean_names_map = None
    try:
        mbean_names_map = local_ls(mbean_type, returnMap='true')
    except (online_wlst_exception, offlineWLSTException), we:
        __logger.warning('Unable wlst.ls({0}), returnMap=true) at location {1}: {2}', mbean_type, current_path(),
                         we.getLocalizedMessage(), class_name=__class_name, method_name=_method_name)

    __logger.exiting(class_name=__class_name, method_name=_method_name, result=mbean_names_map)
    return mbean_names_map


def ls_operations():
    _method_name = 'ls_operations'
    __logger.entering(class_name=__class_name, method_name=_method_name)

    online_wlst_exception = _load_global('WLSTException')
    local_ls = _load_global('ls')
    operations_list = list()
    try:
        operations_map = local_ls('o', returnMap='true')
        if operations_map is not None and not isinstance(operations_map, basestring):
            operations_list = [operation for operation in operations_map]
    except (online_wlst_exception, offlineWLSTException), we:
        __logger.warning('Unable wlst.ls(\'o\', returnMap=true) at location {0}: {1}', current_path(),
                         we.getLocalizedMessage(), class_name=__class_name, method_name=_method_name)

    __logger.exiting(class_name=__class_name, method_name=_method_name, result=operations_list)
    return operations_list


def lsa_string():
    _method_name = 'lsa_string'

    online_wlst_exception = _load_global('WLSTException')
    local_ls = _load_global('ls')
    attributes_str = None
    try:
        attributes_str = local_ls('a')
    except (online_wlst_exception, offlineWLSTException), we:
        __logger.warning('Cannot get attribute information for mbean at location {0}', current_path(),
                         we.getLocalizedMessage(), class_name=__class_name, method_name=_method_name)
    return attributes_str


def lsa_map():
    """
    Return a reformatted map of the attributes at the current MBean location.
     The reformatting converts to a valid dict and converts string none and null to None.
    :return: map of attributes at current location
    """
    make_dict = dict()
    result = lsa()
    if result and len(result) > 0:
        for entry in result.entrySet():
            key = entry.getKey()
            value = entry.getValue()
            if value and isinstance(value, basestring):
                new_value = value.rstrip()
                if new_value == 'null' or new_value == 'none':
                    make_dict[key] = None
                else:
                    make_dict[key] = new_value
            else:
                make_dict[key] = value

    return make_dict


def lsa_map_modified():
    """
    Return a reformatted map of the attributes at the current MBean location.
     The reformatting converts to a valid dict and converts string none and null to None.
    :return: map of attributes at current location
    """
    make_dict = dict()
    result = lsa_modified()
    if result and len(result) > 0:
        for entry in result.entrySet():
            key = entry.getKey()
            value = entry.getValue()
            if value and isinstance(value, basestring):
                new_value = value.rstrip()
                if new_value == 'null' or new_value == 'none':
                    make_dict[key] = None
                else:
                    make_dict[key] = new_value
            else:
                make_dict[key] = value

    return make_dict


def lsa():
    _method_name = 'lsa'

    online_wlst_exception = _load_global('WLSTException')
    local_lsa = _load_global('ls')
    mbean_map = None
    try:
        mbean_map = local_lsa(returnType='a', returnMap='true')
        if mbean_map and not isinstance(mbean_map, Map):
            __logger.fine('LSA at location {0} did not return an attribute map : {1}',
                          current_path(), mbean_map.getClass(), class_name=__class_name, method_name=_method_name)
            mbean_map = None
        else:
            __logger.finer('LSA map at location {0} : {1}', current_path(), mbean_map,
                           class_name=__class_name, method_name=_method_name)
    except (online_wlst_exception, offlineWLSTException), we:
        __logger.warning('Cannot get attribute information for mbean at location {0}', current_path(),
                         we.getLocalizedMessage(), class_name=__class_name, method_name=_method_name)

    return mbean_map


def lsa_modified():
    _method_name = 'lsa_modified'

    online_wlst_exception = _load_global('WLSTException')
    local_lsa = _load_global('ls')
    mbean_map = None
    try:
        mbean_map = local_lsa('a', returnMap='true')
        if mbean_map and not isinstance(mbean_map, Map):
            __logger.fine('LSA at location {0} did not return an attribute map : {1}',
                          current_path(), mbean_map.getClass(), class_name=__class_name, method_name=_method_name)
            mbean_map = None
        else:
            __logger.finer('LSA map at location {0} : {1}', current_path(), mbean_map,
                           class_name=__class_name, method_name=_method_name)
    except (online_wlst_exception, offlineWLSTException), we:
        __logger.warning('Cannot get attribute information for mbean at location {0}', current_path(),
                         we.getLocalizedMessage(), class_name=__class_name, method_name=_method_name)

    return mbean_map


def lsc():
    _method_name = 'lsc'

    online_wlst_exception = _load_global('WLSTException')
    local_lsc = _load_global('ls')
    mbean_list = list()
    try:
        mbean_list = local_lsc(returnType='c', returnMap='true')
    except (online_wlst_exception, offlineWLSTException), we:
        __logger.warning('Cannot get attribute information for mbean at location {0}', current_path(),
                         we.getLocalizedMessage(), class_name=__class_name, method_name=_method_name)

    return mbean_list


def lsc_modified():
    _method_name = 'lsc'
    online_wlst_exception = _load_global('WLSTException')
    local_lsc = _load_global('ls')
    mbean_list = list()
    try:
        mbean_list = local_lsc('c', returnMap='true')
    except (online_wlst_exception, offlineWLSTException), we:
        __logger.warning('Cannot get attribute information for mbean at location {0}', current_path(),
                         we.getLocalizedMessage(), class_name=__class_name, method_name=_method_name)
    return mbean_list


def get_mbi_info():
    _method_name = 'get_mbi_info'
    __logger.entering(class_name=__class_name, method_name=_method_name)

    mbi_info = None
    online_wlst_exception = _load_global('WLSTException')
    try:
        local_mbi = _load_global('getMBI')
        mbi_info = local_mbi()
        result = mbi_info.getMBeanDescriptor()
    except online_wlst_exception, we:
        __logger.warning('Unable to wlst.getMBI() at the current {0} : {1}', current_path(), we.getLocalizedMessage(),
                         class_name=__class_name, method_name='get_mbi_info')
        result = 'Not found'

    __logger.exiting(class_name=__class_name, method_name=_method_name, result=result)
    return mbi_info


def is_path_field(attribute_name):
    for name_ending in PATH_ATTRIBUTE_NAME_ENDINGS:
        if attribute_name.endswith(name_ending) and attribute_name not in PATH_ATTRIBUTE_NAME_EXCEPTIONS:
            return True

    return False


def tokenize_path_value(model_context, attribute_name, attribute_value):
    _method_name = 'tokenize_path_value'

    result = attribute_value
    if attribute_value is None:
        pass
    elif isinstance(attribute_value, basestring):
        if attribute_value.startswith(model_context.get_domain_home()):
            index = len(model_context.get_domain_home())
            result = '%s%s' % (DOMAIN_HOME_TOKEN, attribute_value[index:])
        elif attribute_value.startswith(model_context.get_wl_home()):
            index = len(model_context.get_wl_home())
            result = '%s%s' % (WL_HOME_TOKEN, attribute_value[index:])
        elif attribute_value.startswith(model_context.get_oracle_home()):
            index = len(model_context.get_oracle_home())
            result = '%s%s' % (ORACLE_HOME_TOKEN, attribute_value[index:])
        elif attribute_value.startswith(model_context.get_java_home()):
            index = len(model_context.get_java_home())
            result = '%s%s' % (JAVA_HOME_TOKEN, attribute_value[index:])

        for server_name in PATH_SERVER_NAMES:
            if server_name in result:
                result = result.replace(server_name, '%SERVER%')
        result = re.sub(SERVER_NAME_PATTERN, '%SERVER%', result)
        result = re.sub(PARTITION_NAME_PATTERN, '%PARTITION%', result)
        result = re.sub(RESOURCE_GROUP_TEMPLATE_PATTERN, '%RESOURCEGROUPTEMPLATE%', result)
    else:
        __logger.warning('Attribute {0} value {1} is not a string', attribute_name, attribute_value,
                         class_name=__class_name, method_name=_method_name)
    return result


def _load_global(global_name):
    member = None
    if wlst_functions is not None and global_name in wlst_functions:
        member = wlst_functions[global_name]

    if member is None:
        raise AttributeError(global_name)
    return member


def is_credential_field(attribute_name):
    for credential_marker in CREDENTIAL_FIELD_NAME_MARKERS:
        if credential_marker in attribute_name and attribute_name.lower() not in CREDENTIAL_FIELD_EXCEPTIONS:
            return True

    return False
