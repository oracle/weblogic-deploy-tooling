"""
Copyright (c) 2019, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""
import com.oracle.cie.domain.script.jython.WLSTException as WLSTException
import oracle.weblogic.deploy.util.StringUtils as StringUtils

from wlsdeploy.exception import exception_helper
from wlsdeploy.logging.platform_logger import PlatformLogger

_logger = PlatformLogger('wlsdeploy.wlst')
_class_name = 'wlst_extended'

wlst_functions = None
wlst_state = None


def apply_jrf(jrf_target, domain_home=None, should_update=False):
    """
    For installs that need to connect extension template server groups to servers

    :param jrf_target: entity (cluster, server) to target JRF applications and service
    :param domain_home: the domain home directory
    :param should_update: If true, update the domain - it will check if in online or offline mode
    :raises: PyWLSTException: if a WLST error occurs
    """
    _method_name = 'apply_jrf'
    _logger.entering(jrf_target, domain_home, should_update, class_name=_class_name, method_name=_method_name)
    _logger.fine('WLSDPLY-00073', jrf_target, domain_home, should_update, 
                 class_name=_class_name, method_name=_method_name)
    applyJRF = _load_global('applyJRF')
    try:
        applyJRF(jrf_target, domain_home, should_update)
    except (WLSTException, Exception), e:
        raise exception_helper.create_pywlst_exception('WLSDPLY-00071', jrf_target, domain_home, should_update,
                                                       _format_exception(e), error=e)
    _logger.exiting(class_name=_class_name, method_name=_method_name)
    return


def apply_jrf_global_updates(online, jrf_targets, admin_user=None, admin_pass=None, admin_url=None, domain_home=None):
    """
    For installs that will control locally any updates from the apply_jrf
    :param online: True if the tool session is in online mode
    :param jrf_targets: the list target for the JRF resources
    :param admin_user: admin user if online session
    :param admin_pass: admin password if online session
    :param admin_url: admin url if online session
    :param domain_home: domain home if offline session
    :return:
    """
    _method_name = 'apply_jrf_global_updates'
    _logger.entering(StringUtils.stringForBoolean(online), jrf_targets, domain_home,
                     class_name=_class_name, method_name=_method_name)

    session_start(online, jrf_targets, admin_user, admin_pass, admin_url, domain_home)
    for jrf_target in jrf_targets:
        apply_jrf(jrf_target, domain_home, False)

    session_end(online, jrf_targets)

    _logger.exiting(class_name=_class_name, method_name=_method_name)
    return

def session_start(online, jrf_targets, admin_user, admin_pass, admin_url, domain_home):
    """
    Start the edit session in the global context
    :param online: True if the tool session is in online mode
    :param jrf_targets: the list target for the JRF resources
    :param admin_user: admin user if online session
    :param admin_pass: admin password if online session
    :param admin_url: admin url if online session
    :param domain_home: domain home if offline session
    """
    _method_name = 'session_start'
    _logger.entering(online, jrf_targets, admin_user, admin_url, domain_home,
                     class_name=_class_name, method_name=_method_name)
    if online:
        __online_session_start(jrf_targets, admin_user, admin_pass, admin_url)
    else:
        __offline_session_start(jrf_targets, domain_home)
    _logger.exiting(class_name=_class_name, method_name=_method_name)
    return
    

def session_end(online, jrf_targets):
    """
    End the edit session in the global context
    :param online: True if the tool session is in online mode
    :param jrf_targets: the list target for the JRF resources
    """
    _method_name = 'session_end'
    _logger.entering(online, jrf_targets, class_name=_class_name, method_name=_method_name)
    if online:
        __online_session_end(jrf_targets)
    else:
        __offline_session_end(jrf_targets)
    _logger.exiting(class_name=_class_name, method_name=_method_name)
    
            
def __online_session_start(jrf_target, admin_user, admin_pass, admin_url):
    _method_name = 'online_session_start'
    _logger.entering(jrf_target, admin_user, admin_url, class_name=_class_name, method_name=_method_name)

    global_connect(admin_user, admin_pass, admin_url)
    global_edit()
    global_start_edit()

    _logger.exiting(class_name=_class_name, method_name=_method_name)
    return


def global_connect(user, upass, url):
    _method_name = 'global_connect'
    _logger.entering(class_name=_class_name, method_name=_method_name)

    connect = _load_global('connect')
    try:
        connect(user, upass, url)
    except (WLSTException, Exception), e:
        connect_string = 'connect(' + user + ', password hidden, ' + url + ')'
        raise exception_helper.create_pywlst_exception('WLSDPLY-00086', connect_string, _format_exception(e), error=e)

    _logger.exiting(class_name=_class_name, method_name=_method_name)


def global_edit():
    _method_name = 'global_edit'
    _logger.entering(class_name=_class_name, method_name=_method_name)

    edit = _load_global('edit')
    try:
        edit()
    except (WLSTException, Exception), e:
        raise exception_helper.create_pywlst_exception('WLSDPLY-00086', 'edit()', _format_exception(e), error=e)
    _logger.exiting(class_name=_class_name, method_name=_method_name)


def global_start_edit():
    _method_name = 'global_start_edit'
    _logger.entering(class_name=_class_name, method_name=_method_name)

    startEdit = _load_global('startEdit')
    try:
        startEdit()
    except (WLSTException, Exception), e:
        raise exception_helper.create_pywlst_exception('WLSDPLY-00086', 'startEdit()', _format_exception(e), error=e)
    _logger.exiting(class_name=_class_name, method_name=_method_name)


def __offline_session_start(jrf_targets, domain_home):
    _method_name = '__offline_session_start'
    _logger.entering(jrf_targets, domain_home, class_name=_class_name, method_name=_method_name)

    _logger.finest('WLSDPLY-00082', jrf_targets, class_name=_class_name, method_name=_method_name)
    global_read_domain(domain_home)

    _logger.exiting(class_name=_class_name, method_name=_method_name)


def global_read_domain(domain_home):
    _method_name = 'global_read_domain'
    _logger.entering(class_name=_class_name, method_name=_method_name)
    readDomain = _load_global('readDomain')
    try:
        readDomain(domain_home)
    except (WLSTException, Exception), e:
        read_string = 'readDomain(' + domain_home + ')'
        raise exception_helper.create_pywlst_exception('WLSDPLY-00086', read_string, _format_exception(e), error=e)
    _logger.exiting(class_name=_class_name, method_name=_method_name)


def __online_session_end(jrf_target):
    _method_name = '__online_session_end'
    _logger.entering(jrf_target, class_name=_class_name, method_name=_method_name)

    _logger.finest('WLSDPLY-00085', jrf_target, class_name=_class_name, method_name=_method_name)
    cmgr = get_config_manager()
    if is_editor(cmgr):
        global_save()
        global_activate()
    global_disconnect()

    _logger.exiting(class_name=_class_name, method_name=_method_name)


def global_save():
    _method_name = 'global_save'
    _logger.entering(class_name=_class_name, method_name=_method_name)

    save = _load_global('save')
    try:
        save()
    except (WLSTException, Exception), e:
        raise exception_helper.create_pywlst_exception('WLSDPLY-00086', 'save()', _format_exception(e), error=e)
    _logger.exiting(class_name=_class_name, method_name=_method_name)


def global_activate():
    _method_name = 'global_activate'
    _logger.entering(class_name=_class_name, method_name=_method_name)

    activate = _load_global('activate')
    try:
        activate()
    except (WLSTException, Exception), e:
        raise exception_helper.create_pywlst_exception('WLSDPLY-00086', 'activate()', _format_exception(e), error=e)
    _logger.exiting(class_name=_class_name, method_name=_method_name)


def global_disconnect():
    _method_name = 'global_disconnect'
    _logger.entering(class_name=_class_name, method_name=_method_name)

    disconnect = _load_global('disconnect')
    try:
        disconnect()
    except (WLSTException, Exception), e:
        raise exception_helper.create_pywlst_exception('WLSDPLY-00086', 'disconnect()', _format_exception(e), error=e)
    _logger.exiting(class_name=_class_name, method_name=_method_name)


def __offline_session_end(jrf_target):
    _method_name = '__offline_session_end'
    _logger.entering(jrf_target, class_name=_class_name, method_name=_method_name)

    _logger.finest('WLSDPLY-00085', jrf_target, class_name=_class_name, method_name=_method_name)
    global_update_domain()
    global_close_domain()

    _logger.exiting(class_name=_class_name, method_name=_method_name)


def global_update_domain():
    _method_name = 'global_update_domain'
    _logger.entering(class_name=_class_name, method_name=_method_name)
    updateDomain = _load_global('updateDomain')
    try:
        updateDomain()
    except (WLSTException, Exception), e:
        raise exception_helper.create_pywlst_exception('WLSDPLY-00086', 'updateDomain()', _format_exception(e), error=e)
    _logger.exiting(class_name=_class_name, method_name=_method_name)


def global_close_domain():
    _method_name = 'global_close_domain'
    _logger.entering(class_name=_class_name, method_name=_method_name)

    closeDomain = _load_global('closeDomain')
    try:
        closeDomain()
    except (WLSTException, Exception), e:
        raise exception_helper.create_pywlst_exception('WLSDPLY-00086', 'closeDomain()', _format_exception(e), error=e)
    _logger.exiting(class_name=_class_name, method_name=_method_name)


def get_config_manager():
    """
    Return the online configuration manager
    :return: configuration manager
    :raises: PyWLSTException: if a WLST error occurs
    """
    _method_name = 'get_config_manager'
    _logger.entering(class_name=_class_name, method_name=_method_name)

    getConfigManager = _load_global('getConfigManager')
    try:
        result = getConfigManager()
    except (WLSTException, Exception), e:
        pwe = exception_helper.create_pywlst_exception('WLSDPLY-00086', 'getConfigManager()',  _format_exception(e),
                                                       error=e)
        _logger.throwing(class_name=_class_name, method_name=_method_name, error=pwe)
        raise pwe

    _logger.exiting(class_name=_class_name, method_name=_method_name, result=result)
    return result


def get_current_editor(cmgr):
    """
    Return current editor
    :param cmgr: configuration manager
    :return: current editor of the domain
    :raises: PyWLSTException: if a WLST error occurs
    """
    _method_name = 'get_current_editor'
    _logger.entering(cmgr, class_name=_class_name, method_name=_method_name)

    try:
        result = cmgr.getCurrentEditor()
    except (WLSTException, Exception), e:
        pwe = exception_helper.create_pywlst_exception('WLSDPLY-00086', 'cmgr.getCurrentEditor()',
                                                       _format_exception(e), error=e)
        _logger.throwing(class_name=_class_name, method_name=_method_name, error=pwe)
        raise pwe

    _logger.exiting(class_name=_class_name, method_name=_method_name, result=result)
    return result


def is_editor(cmgr):
    """
    Determine if an edit is in progress and if this context is the current editor.
    :param cmgr: current configuration manager
    :return: True if context is current editor
    """
    _method_name = 'is_editor'
    _logger.entering(class_name=_class_name, method_name=_method_name)

    try:
        result = cmgr.isEditor()
    except WLSTException, e:
        pwe = exception_helper.create_pywlst_exception('WLSDPLY-00094', _format_exception(e), error=e)
        _logger.throwing(class_name=_class_name, method_name=_method_name, error=pwe)
        raise pwe
    _logger.exiting(class_name=_class_name, method_name=_method_name, result=StringUtils.stringForBoolean(result))
    return result


def have_unactivated_changes(cmgr):
    """
    Return True if there is any unactivated changes in the domain
    :param cmgr: configuration manager
    :return: True if there is any unactivated changes in the domain
    :raises: PyWLSTException: if a WLST error occurs
    """
    _method_name = 'have_unactivated_changes'
    _logger.entering(cmgr, class_name=_class_name, method_name=_method_name)

    try:
        result = cmgr.haveUnactivatedChanges()
    except (WLSTException, Exception), e:
        pwe = exception_helper.create_pywlst_exception('WLSDPLY-00086', 'cmgr.haveUnactivatedChanges()',
                                                       _format_exception(e), error=e)
        _logger.throwing(class_name=_class_name, method_name=_method_name, error=pwe)
        raise pwe

    _logger.exiting(class_name=_class_name, method_name=_method_name, result=result)
    return result


def _load_global(global_name):
    member = None
    if wlst_functions is not None and global_name in wlst_functions:
        member = wlst_functions[global_name]

    if member is None:
        raise exception_helper.create_pywlst_exception('WLSDPLY-00087', global_name)
    return member


def _format_exception(e):
    """
    Format the exception
    :param e: the exception
    :return: the formmated exception message
    """
    if isinstance(e, WLSTException):
        message = e.getLocalizedMessage()
        #
        # Try to find a message that is not empty
        #
        if message is None:
            cause = e.getCause()
            while message is None and cause is not None:
                message = cause.getLocalizedMessage()
                cause = cause.getCause()
        return message
    return str(e)
