"""
Copyright (c) 2019, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""
from com.oracle.cie.domain.script.jython import WLSTState as WLSTState
import com.oracle.cie.domain.script.jython.WLSTException as offlineWLSTException
import oracle.weblogic.deploy.util.StringUtils as StringUtils
import wlstModule as wlst

from wlsdeploy.exception import exception_helper
from wlsdeploy.logging.platform_logger import PlatformLogger

_logger = PlatformLogger('wlsdeploy.wlst')
_class_name = 'wlst_extended'

wlst_functions = None
applyJRF = None


def apply_jrf(jrf_target, domain_home=None, should_update=False):
    """
    For installs that need to connect extension template server groups to servers

    :param jrf_target: entity (cluster, server) to target JRF applications and service
    :param domain_home: the domain home directory
    :param should_update: If true, update the domain - it will check if in online or offline mode
    :raises: PyWLSTException: if a WLST error occurs
    """
    global applyJRF
    _method_name = 'apply_jrf'
    _logger.entering(jrf_target, domain_home, should_update, class_name=_class_name, method_name=_method_name)
    _logger.fine('WLSDPLY-00073', jrf_target, domain_home, should_update, class_name=_class_name, method_name=_method_name)
    applyJRF = _load_global('applyJRF')
    try:
        readDomain = _load_global('readDomain')
        readDomain(domain_home)
        mycmo = _load_global('cmo')
        print '***** ', mycmo

        applyJRF(jrf_target, None, False)

        updateDomain = _load_global('updateDomain')
        closeDomain = _load_global('closeDomain')
        updateDomain()
        closeDomain()
    except (wlst.WLSTException, offlineWLSTException, Exception), e:
        raise exception_helper.create_pywlst_exception('WLSDPLY-00071', jrf_target, domain_home, should_update,
                                                       _format_exception(e), error=e)
    _logger.exiting(class_name=_class_name, method_name=_method_name)
    return


def _load_global(global_name):
    _method_name = '_load_global'
    member = None
    if wlst_functions is not None and global_name in wlst_functions:
        member = wlst_functions[global_name]
    else:
        print 'Member not found ', global_name
        if wlst_functions is not None:
            sorted=list()
            for item in wlst_functions:
                sorted.append(item)
            sorted.sort()
            for item in sorted:
                print ' ** ', item
        raise exception_helper.create_pywlst_exception('WLSDPLY-00072', global_name, _get_exception_mode(0))
    return member


def _get_exception_mode(e):
    """
    Return a text value dependent on online or offline mode. The wlst exception messages differ between offline
    and online, and this can provide clarity to our exception. This value is not internationalized.
    :param e: The exception instance. The class of this instance determines whether the exception was thrown
                in offline or online mode
    :return: The text value online, offline or unknown
    """
    if isinstance(e, wlst.WLSTException):
        return 'online'
    if isinstance(e, offlineWLSTException):
        return 'offline'
    return 'unknown'


def _format_exception(e):
    """
    Format the exception
    :param e: the exception
    :return: the formmated exception message
    """
    print '********* ', type(e)
    if isinstance(e, offlineWLSTException):
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
