"""
Copyright (c) 2017, 2019, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""
import com.oracle.cie.domain.script.jython.WLSTException as offlineWLSTException
import oracle.weblogic.deploy.util.StringUtils as StringUtils
import weblogic.management.mbeanservers.edit.ValidationException as ValidationException
import wlstModule as wlst

from wlsdeploy.exception import exception_helper
from wlsdeploy.logging.platform_logger import PlatformLogger
from oracle.weblogic.deploy.util import PyWLSTException

_logger = PlatformLogger('wlsdeploy.wlst')
_class_name = 'wlst_helper'


def assign(source_type, source_name, target_type, target_name):
    """
    Assign target entity to source entity

    :param source_type: source entity type
    :param source_name: entity name
    :param target_type: target type
    :param target_name: target name
    :raises: PyWLSTException: if a WLST error occurs
    """

    _method_name = 'assign'
    _logger.finest('WLSDPLY-00001', source_type, source_name, target_type, target_name, class_name=_class_name,
                   method_name=_method_name)

    try:
        wlst.assign(source_type, source_name, target_type, target_name)
    except (wlst.WLSTException, offlineWLSTException), e:
        raise exception_helper.create_pywlst_exception('WLSDPLY-00002', source_type, source_name, target_type,
                                                       target_name, _get_exception_mode(e),
                                                       _format_exception(e), error=e)
    _logger.finest('WLSDPLY-00003', source_type, source_name, target_type, target_name, class_name=_class_name,
                   method_name=_method_name)
    return


def cd(path):
    """
    Change location to the provided path.

    :param path: wlst directory to which to change location
    :return: cmo object reference of the new location
    :raises: PyWLSTException: if a WLST error occurs
    """

    _method_name = 'cd'
    _logger.finest('WLSDPLY-00001', path, class_name=_class_name, method_name=_method_name)

    try:
        result = wlst.cd(path)
    except (wlst.WLSTException, offlineWLSTException), e:
        raise exception_helper.create_pywlst_exception('WLSDPLY-00002', path, _get_exception_mode(e),
                                                       _format_exception(e), error=e)
    _logger.finest('WLSDPLY-00003', path, result, class_name=_class_name, method_name=_method_name)
    return result


def get(attribute):
    """
    Return the value for the attribute at the current location

    :param attribute: name of the wlst attribute
    :return: value set for the attribute
    :raises: PyWLSTException: if a WLST error occurs
    """
    _method_name = 'get'
    _logger.finest('WLSDPLY-00004', attribute, class_name=_class_name, method_name=_method_name)

    try:
        result = wlst.get(attribute)
    except (wlst.WLSTException, offlineWLSTException), e:
        pwe = exception_helper.create_pywlst_exception('WLSDPLY-00005', attribute, _get_exception_mode(e),
                                                       _format_exception(e), error=e)
        _logger.throwing(class_name=_class_name, method_name=_method_name, error=pwe)
        raise pwe
    _logger.finest('WLSDPLY-00006', attribute, result, class_name=_class_name, method_name=_method_name)
    return result


def set(attribute, value):
    """
    Set the configuration for the indicated attribute to the provided value.

    :param attribute: attribute name at the current location
    :param value: to configure the attribute
    :raises: PyWLSTException: if a WLST error occurs
    """
    _method_name = 'set'
    _logger.finest('WLSDPLY-00007', attribute, value, class_name=_class_name, method_name=_method_name)
    try:
        wlst.set(attribute, value)
    except (wlst.WLSTException, offlineWLSTException), e:
        pwe = exception_helper.create_pywlst_exception('WLSDPLY-00008', attribute, value,
                                                       _get_exception_mode(e), _format_exception(e), error=e)
        _logger.throwing(class_name=_class_name, method_name=_method_name, error=pwe)
        raise pwe
    _logger.finest('WLSDPLY-00009', class_name=_class_name, method_name=_method_name)


def set_with_cmo(wlst_name, wlst_value, masked=False):
    """
    Set the specified attribute using the corresponding cmo set method (e.g., cmo.setListenPort()).
    :param wlst_name: the WLST attribute name
    :param wlst_value: the WLST value
    :param masked: whether or not to mask the wlst_value from the log files.
    :raises: PyWLSTException: if a WLST error occurs
    """
    _method_name = 'set_with_cmo'
    value = wlst_value
    if masked:
        value = '<masked>'

    _logger.finest('WLSDPLY-00010', wlst_name, value, class_name=_class_name, method_name=_method_name)

    set_method_name = 'set' + wlst_name
    _logger.finest('WLSDPLY-00011', set_method_name, class_name=_class_name, method_name=_method_name)

    current_cmo = get_cmo()
    if current_cmo is None:
        pwe = exception_helper.create_pywlst_exception('WLSDPLY-00012', set_method_name, value, _get_wlst_mode())
        _logger.throwing(class_name=_class_name, method_name=_method_name, error=pwe)
        raise pwe

    try:
        set_method = getattr(current_cmo, set_method_name)
        set_method(wlst_value)
    except AttributeError, e:
        pwe = exception_helper.create_pywlst_exception('WLSDPLY-00013', set_method_name, _get_exception_mode(e),
                                                       _format_exception(e), error=e)
        _logger.throwing(class_name=_class_name, method_name=_method_name, error=pwe)
        raise pwe
    except (wlst.WLSTException, offlineWLSTException), e:
        pwe = exception_helper.create_pywlst_exception('WLSDPLY-00014', set_method_name, value, _get_exception_mode(e),
                                                       _format_exception(e), error=e)
        _logger.throwing(class_name=_class_name, method_name=_method_name, error=pwe)
        raise pwe
    _logger.finest('WLSDPLY-00015', wlst_name, value, class_name=_class_name, method_name=_method_name)
    return


def create(name, folder, base_provider_type=None):
    """
    Create the mbean folder with the provided name at the current location.

    :param name: to create under the folder
    :param folder: name of the mbean folder
    :param base_provider_type: the name of the security provider base type
    :return: the MBean object returned by the underlying WLST create() method
    :raises: PyWLSTException: if a WLST error occurs
    """
    _method_name = 'create'
    _logger.finest('WLSDPLY-00016', name, folder, base_provider_type, class_name=_class_name, method_name=_method_name)

    try:
        if base_provider_type is None:
            result = wlst.create(name, folder)
        else:
            if not wlst.WLS_ON.isConnected():
                result = wlst.WLS.create(name, folder, base_provider_type)
            else:
                result = wlst.create(name, folder, base_provider_type)
    except (wlst.WLSTException, offlineWLSTException), e:
        pwe = exception_helper.create_pywlst_exception('WLSDPLY-00017', name, folder, base_provider_type,
                                                       _get_exception_mode(e), _format_exception(e), get_pwd(), error=e)
        _logger.throwing(class_name=_class_name, method_name=_method_name, error=pwe)
        raise pwe
    _logger.finest('WLSDPLY-00018', name, folder, base_provider_type, result,
                   class_name=_class_name, method_name=_method_name)
    return result


def delete(name, folder):
    """
    Delete an MBean of the specified name and type at the current location.
    :param name: the MBean name
    :param folder: the MBean type
    :raises: PyWLSTException: if a WLST error occurs
    """
    _method_name = 'delete'
    _logger.finest('WLSDPLY-00019', name, folder, class_name=_class_name, method_name=_method_name)

    try:
        wlst.delete(name, folder)
    except (wlst.WLSTException, offlineWLSTException), e:
        pwe = exception_helper.create_pywlst_exception('WLSDPLY-00020', name, folder, _get_exception_mode(e),
                                                       _format_exception(e), error=e)
        _logger.throwing(class_name=_class_name, method_name=_method_name, error=pwe)
        raise pwe
    _logger.finest('WLSDPLY-00021', name, folder, class_name=_class_name, method_name=_method_name)
    return


def get_database_defaults():
    """
    sets the database defaults indicated by RCU.
    :raises: PyWLSTException: if a WLST error occurs
    """
    _method_name = 'get_database_defaults'
    _logger.entering(class_name=_class_name, method_name=_method_name)
    try:
        wlst.getDatabaseDefaults()
    except offlineWLSTException, e:
        pwe = exception_helper.create_pywlst_exception('WLSDPLY-00022', e.getLocalizedMessage(), error=e)
        _logger.throwing(pwe, class_name=_class_name, method_name=_method_name)
        raise pwe
    _logger.exiting(class_name=_class_name, method_name=_method_name)


def set_server_groups(server, server_groups):
    """
    Sets the database defaults indicated by RCU.

    :param server: the name of the new server
    :param server_groups: the list of template-defined server groups to target to the server
    :raises: PyWLSTException: if a WLST error occurs
    """
    _method_name = 'set_server_groups'
    _logger.entering(server_groups, server, class_name=_class_name, method_name=_method_name)
    try:
        wlst.setServerGroups(server, server_groups)
    except (wlst.WLSTException, offlineWLSTException), e:
        pwe = exception_helper.create_pywlst_exception('WLSDPLY-00023', server_groups, server,
                                                       _format_exception(e), error=e)
        _logger.throwing(class_name=_class_name, method_name=_method_name, error=pwe)
        raise pwe
    _logger.exiting(class_name=_class_name, method_name=_method_name)


def set_option(option, value):
    """
    Set the configuration for the indicated option to the provided value.

    :param option: domain option to set
    :param value: to which to set the option
    :raises: PyWLSTException: if a WLST error occurs
    """
    _method_name = 'set_option'
    _logger.entering(option, value, class_name=_class_name, method_name=_method_name)
    try:
        wlst.setOption(option, value)
    except (wlst.WLSTException, offlineWLSTException), e:
        pwe = exception_helper.create_pywlst_exception('WLSDPLY-00024', option, _get_exception_mode(e),
                                                       _format_exception(e), error=e)
        _logger.throwing(class_name=_class_name, method_name=_method_name, error=pwe)
        raise pwe
    _logger.exiting(class_name=_class_name, method_name=_method_name)


def lsa(path=None, log_throwing=True):
    """
    Return a map of weblogic attributes found at the wlst path or the current path.

    In online mode, clean up the return values to strip off trailing spaces and
    convert the string 'null' into None.
    :param path: for which to return a map of attributes. If None, the current path is searched
    :param log_throwing: whether or not to log the throwing message if the path location is not found
    :return: map of weblogic attributes
    :raises: PyWLSTException: if a WLST error occurs
    """
    _method_name = 'lsa'
    result = _ls(_method_name, 'a', path, log_throwing)
    make_dict = dict()
    if result and len(result) > 0:
        for entry in result.entrySet():
            key = entry.getKey()
            value = entry.getValue()
            if value and type(value) is str:
                new_value = value.rstrip()
                if new_value == 'null' or new_value == 'none':
                    make_dict[key] = None
                else:
                    make_dict[key] = new_value
            else:
                make_dict[key] = value
    return make_dict


def lsc(path=None, log_throwing=True):
    """
    Return a map of weblogic folders found at the wlst path or the current path.
    :param path: for which to return a map of folders. If None, the current path is searched
    :param log_throwing: whether or not to log the throwing message if the path location is not found
    :return: list of weblogic folders
    :raises: PyWLSTException: if a WLST error occurs
    """
    _method_name = 'lsc'
    return _ls(_method_name, 'c', path, log_throwing)


def path_exists(path):
    """
    Determine if the provided path exists in the domain. This can be a path relative to the
    current location or a fully qualified path.
    :param path: path to validate.
    :return: True if path exists; false otherwise
    :raises: PyWLSTException: if a WLST error occurs
    """
    _method_name = 'path_exists'
    _logger.finest('WLSDPLY-00025', path, class_name=_class_name, method_name=_method_name)

    exists = True
    try:
        wlst.ls(path)
    except (wlst.WLSTException, offlineWLSTException), e:
        _logger.finest('WLSDPLY-00026', path, e.getLocalizedMessage(), class_name=_class_name, method_name=_method_name)
        exists = False
    _logger.finest('WLSDPLY-00027', path, exists, class_name=_class_name, method_name=_method_name)
    return exists


def _ls(method_name, ls_type, path=None, log_throwing=True):
    """
    Private helper method shared by various API methods
    :param method_name: calling method name
    :param ls_type: the WLST return type requested
    :param path: the path (default is the current path)
    :param log_throwing: whether or not to log the throwing message if the path location is not found
    :return: the result of the WLST ls(returnMap='true') call
    :raises: PyWLSTException: if a WLST error occurs
    """
    _method_name = method_name
    _logger.finest('WLSDPLY-00028', method_name, ls_type, path, class_name=_class_name, method_name=_method_name)

    if path is not None:
        # ls(path, returnMap='true') is busted in earlier versions of WLST so go ahead and
        # change directories to the specified path to workaround this
        current_path = get_pwd()
        cd(path)
        try:
            result = wlst.ls(ls_type, returnMap='true', returnType=ls_type)
        except (wlst.WLSTException, offlineWLSTException), e:
            pwe = exception_helper.create_pywlst_exception('WLSDPLY-00029', path, ls_type, _get_exception_mode(e),
                                                           _format_exception(e), error=e)
            if log_throwing:
                _logger.throwing(class_name=_class_name, method_name=_method_name, error=pwe)
            cd(current_path)
            raise pwe
        cd(current_path)
    else:
        current_path = get_pwd()
        try:
            result = wlst.ls(ls_type, returnMap='true', returnType=ls_type)
        except (wlst.WLSTException, offlineWLSTException), e:
            pwe = exception_helper.create_pywlst_exception('WLSDPLY-00029', current_path, ls_type,
                                                           _get_exception_mode(e), _format_exception(e), error=e)
            _logger.throwing(class_name=_class_name, method_name=_method_name, error=pwe)
            raise pwe
    _logger.finest('WLSDPLY-00030', method_name, ls_type, current_path, result,
                   class_name=_class_name, method_name=_method_name)
    return result


def get_singleton_name(path=None):
    """
    Return the name at the current location or at the provided path. This location represents
    the name of an MBean that is a singleton. None will be returned if a location is provided and
    it does not exist.
    :param path: location to retrieve the singleton name, or the current location if no path is provided
    :return: name of the MBean
    :throws: PyWLSTException: if there is either no name or more than one name found at the location
                              or if a WLST error occurs
    """
    _method_name = 'get_singleton_name'
    _logger.entering(class_name=_class_name, method_name=_method_name)

    mbean_name = None
    if path is None or path_exists(path):
        print_path = path
        if path is None:
            print_path = get_pwd()
        name_list = lsc(path)
        nbr_names = 0
        if name_list is not None:
            nbr_names = len(name_list)
        if not nbr_names == 1:
            pwe = exception_helper.create_pywlst_exception('WLSDPLY-00031', print_path, nbr_names, name_list)
            _logger.throwing(class_name=_class_name, method_name=_method_name, error=pwe)
            raise pwe
        mbean_name = name_list[0]
        _logger.finest('WLSDPLY-00032', print_path, mbean_name, class_name=_class_name, method_name=_method_name)

    _logger.exiting(class_name=_class_name, method_name=_method_name, result=mbean_name)
    return mbean_name


def get_pwd():
    """
    Return the current weblogic path. The domain name is stripped from this path.
    :return: path of current location.
    :raises: PyWLSTException: if a WLST error occurs
    """
    _method_name = 'get_pwd'
    _logger.finest('WLSDPLY-00033', class_name=_class_name, method_name=_method_name)
    try:
        path = wlst.pwd()[1:]
    except (wlst.WLSTException, offlineWLSTException), e:
        pwe = exception_helper.create_pywlst_exception('WLSDPLY-00034', _get_exception_mode(e),
                                                       _format_exception(e), error=e)
        _logger.throwing(class_name=_class_name, method_name=_method_name, error=pwe)
        raise pwe

    second_slash = path.find('/')
    if second_slash != -1:
        path = path[second_slash:]
    else:
        path = '/'
    _logger.finest('WLSDPLY-00035', path, class_name=_class_name, method_name=_method_name)
    return path


def get_cmo():
    """
    update the Current Management Object (cmo) to current mbean in wlst.
    :return: updated cmo
    :raises: PyWLSTException: if a WLST error occurs
    """
    _method_name = 'get_cmo'
    _logger.entering(class_name=_class_name, method_name=_method_name)

    if is_connected():
        if wlst.cmo is None:
            pwe = exception_helper.create_pywlst_exception('WLSDPLY-00070')
            _logger.throwing(class_name=_class_name, method_name=_method_name, error=pwe)
            raise pwe
    else:
        try:
            wlst.updateCmo()
        except (wlst.WLSTException, offlineWLSTException), e:
            pwe = exception_helper.create_pywlst_exception('WLSDPLY-00036', get_pwd(), _get_exception_mode(e),
                                                           _format_exception(e), error=e)
            _logger.throwing(class_name=_class_name, method_name='get_cmo', error=pwe)
            raise pwe
        _logger.exiting(class_name=_class_name, method_name=_method_name, result=wlst.cmo)
    return wlst.cmo


def is_connected():
    """
    Determine if wlst is currently connected to the admin server - from the WlstContext
    :return: Return True if currently connected
    """
    return wlst.connected == 'true'


def get_mbean_for_wlst_path(path):
    """
    Return the mbean object for the provided path.
    :param path: to return mbean object
    :return: mbean object
    :raises: PyWLSTException: if a WLST error occurs
    """
    _method_name = 'get_mbean_for_wlst_path'
    _logger.entering(path, class_name=_class_name, method_name=_method_name)

    current_dir = get_pwd()
    the_object = cd(path)
    cd(current_dir)
    _logger.exiting(_class_name, _method_name, the_object)
    return the_object


def read_template(template):
    """
    Read the server template into the weblogic domain for domain creation.
    :param template: name of the template to load for domain creation
    :raises: PyWLSTException: if a WLST error occurs
    """
    _method_name = 'read_template'
    _logger.entering(template, class_name=_class_name, method_name=_method_name)

    try:
        wlst.readTemplate(template)
    except offlineWLSTException, e:
        pwe = exception_helper.create_pywlst_exception('WLSDPLY-00037', template, e.getLocalizedMessage(), error=e)
        _logger.throwing(class_name=_class_name, method_name=_method_name, error=pwe)
        raise pwe
    _logger.exiting(class_name=_class_name, method_name=_method_name)


def add_template(template):
    """
    Extend the domain with the server template.
    :param template: name of the template to load for domain extension
    :raises: PyWLSTException: if a WLST error occurs
    """
    _method_name = 'add_template'
    _logger.entering(template, class_name=_class_name, method_name=_method_name)

    try:
        wlst.addTemplate(template)
    except offlineWLSTException, e:
        pwe = exception_helper.create_pywlst_exception('WLSDPLY-00038', template, e.getLocalizedMessage(), error=e)
        _logger.throwing(class_name=_class_name, method_name=_method_name, error=pwe)
        raise pwe
    _logger.exiting(class_name=_class_name, method_name=_method_name)


def close_template():
    """
    Close the template that is currently loaded for domain creation.
    :raises: PyWLSTException: if a WLST error occurs
    """
    _method_name = 'close_template'
    _logger.entering(class_name=_class_name, method_name=_method_name)

    try:
        wlst.closeTemplate()
    except offlineWLSTException, e:
        pwe = exception_helper.create_pywlst_exception('WLSDPLY-00039', e.getLocalizedMessage(), error=e)
        _logger.throwing(class_name=_class_name, method_name=_method_name, error=pwe)
        raise pwe
    _logger.exiting(class_name=_class_name, method_name=_method_name)


def select_template(template):
    """
    Select an existing domain template or application template for create a domain. This is
    available only in weblogic 12c versions
    :param template: to be selected and loaded into the current session
    :raises: PyWLSTException: if a WLST error occurs
    """
    _method_name = 'select_template'
    _logger.entering(template, class_name=_class_name, method_name=_method_name)

    try:
        wlst.selectTemplate(template)
    except offlineWLSTException, e:
        pwe = exception_helper.create_pywlst_exception('WLSDPLY-00040', template, e.getLocalizedMessage(), error=e)
        _logger.throwing(class_name=_class_name, method_name=_method_name, error=pwe)
        raise pwe
    _logger.exiting(class_name=_class_name, method_name=_method_name)


def load_templates():
    """
    Load all the selected templates.
    :raises: PyWLSTException: if a WLST error occurs
    """
    _method_name = 'load_templates'
    _logger.entering(class_name=_class_name, method_name=_method_name)

    try:
        wlst.loadTemplates()
    except offlineWLSTException, e:
        pwe = exception_helper.create_pywlst_exception('WLSDPLY-00041', e.getLocalizedMessage(), error=e)
        _logger.throwing(class_name=_class_name, method_name=_method_name, error=pwe)
        raise pwe
    _logger.exiting(class_name=_class_name, method_name=_method_name)


def read_domain(domain_home):
    """
    Read the domain indicated by the domain_home name in offline mode.
    :param domain_home: domain to read and load into the current offline session
    :raises: PyWLSTException: if a WLST error occurs
    """
    _method_name = 'read_domain'
    _logger.entering(domain_home, class_name=_class_name, method_name=_method_name)

    try:
        wlst.readDomain(domain_home)
    except offlineWLSTException, e:
        pwe = exception_helper.create_pywlst_exception('WLSDPLY-00042', domain_home, e.getLocalizedMessage(), error=e)
        _logger.throwing(class_name=_class_name, method_name=_method_name, error=pwe)
        raise pwe
    _logger.exiting(class_name=_class_name, method_name=_method_name)


def write_domain(domain_home):
    """
    Persist the newly created domain configuration to the provided location. This will automatically
    overwrite an existing domain at this location.
    :param domain_home: path location to write the domain and its configuration
    :raises: PyWLSTException: if a WLST error occurs
    """
    _method_name = 'write_domain'
    _logger.entering(domain_home, class_name=_class_name, method_name=_method_name)

    try:
        wlst.setOption('OverwriteDomain', 'true')
    except offlineWLSTException, e:
        pwe = exception_helper.create_pywlst_exception('WLSDPLY-00043', domain_home, e.getLocalizedMessage(), error=e)
        _logger.throwing(class_name=_class_name, method_name=_method_name, error=pwe)
        raise pwe

    try:
        wlst.writeDomain(domain_home)
    except offlineWLSTException, e:
        pwe = exception_helper.create_pywlst_exception('WLSDPLY-00044', domain_home, e.getLocalizedMessage(), error=e)
        _logger.throwing(class_name=_class_name, method_name=_method_name, error=pwe)
        raise pwe
    _logger.exiting(class_name=_class_name, method_name=_method_name)


def update_domain():
    """
    Update the existing domain configuration with the edits made during the offline session.
    :raises: PyWLSTException: if a WLST error occurs
    """
    _method_name = 'update_domain'
    _logger.entering(class_name=_class_name, method_name=_method_name)

    try:
        wlst.updateDomain()
    except offlineWLSTException, e:
        pwe = exception_helper.create_pywlst_exception('WLSDPLY-00045', e.getLocalizedMessage(), error=e)
        _logger.throwing(class_name=_class_name, method_name=_method_name, error=pwe)
        raise pwe
    _logger.exiting(class_name=_class_name, method_name=_method_name)


def close_domain():
    """
    Close the domain currently loaded into the offline wlst session.
    :raises: PyWLSTException: if a WLST error occurs
    """
    _method_name = 'close_domain'
    _logger.entering(class_name=_class_name, method_name=_method_name)

    try:
        wlst.closeDomain()
    except offlineWLSTException, e:
        pwe = exception_helper.create_pywlst_exception('WLSDPLY-00046', e.getLocalizedMessage(), error=e)
        _logger.throwing(class_name=_class_name, method_name=_method_name, error=pwe)
        raise pwe
    _logger.exiting(class_name=_class_name, method_name=_method_name)


def silence():
    """
    Performs the wlst commands to suppress stdout and stderr chatter.
    """
    wlst.WLS.setLogToStdOut(False)
    wlst.WLS.setShowLSResult(False)
    wlst.WLS_ON.setlogToStandardOut(False)
    wlst.WLS_ON.setHideDumpStack('true')
    wlst.WLS.getCommandExceptionHandler().setMode(True)
    wlst.WLS.getCommandExceptionHandler().setSilent(True)


def connect(username, password, url):
    """
    Connect WLST to a Weblogic Server instance at the provided url with the provided credentials.
    :param username: Weblogic user name
    :param password: Weblogic password
    :param url: Weblogic Server URL
    :raises: PyWLSTException: if a WLST error occurs
    """
    _method_name = 'connect'
    _logger.entering(username, url, class_name=_class_name, method_name=_method_name)

    try:
        wlst.connect(username=username, password=password, url=url)
    except (wlst.WLSTException, offlineWLSTException), e:
        pwe = exception_helper.create_pywlst_exception('WLSDPLY-00047', username, url, _get_exception_mode(e),
                                                       _format_exception(e), error=e)
        _logger.throwing(class_name=_class_name, method_name=_method_name, error=pwe)
        raise pwe
    _logger.exiting(class_name=_class_name, method_name=_method_name)


def disconnect():
    """
    Disconnects WLST from the current connected WebLogic Server instance.
    :raises: PyWLSTException: if a WLST error occurs
    """
    _method_name = 'disconnect'
    _logger.entering(class_name=_class_name, method_name=_method_name)

    try:
        wlst.disconnect()
    except wlst.WLSTException, e:
        pwe = exception_helper.create_pywlst_exception('WLSDPLY-00048', _format_exception(e), error=e)
        _logger.throwing(class_name=_class_name, method_name=_method_name, error=pwe)
        raise pwe
    _logger.exiting(class_name=_class_name, method_name=_method_name)


def edit():
    """
    Edit the current Weblogic Server configuration.
    :raises: PyWLSTException: if a WLST error occurs
    """
    _method_name = 'edit'
    _logger.entering(class_name=_class_name, method_name=_method_name)

    try:
        wlst.edit()
    except wlst.WLSTException, e:
        pwe = exception_helper.create_pywlst_exception('WLSDPLY-00049', _format_exception(e), error=e)
        _logger.throwing(class_name=_class_name, method_name=_method_name, error=pwe)
        raise pwe
    _logger.exiting(class_name=_class_name, method_name=_method_name)


def start_edit():
    """
    Start an edit session with the Weblogic Server for the currently connected user.
    :raises: PyWLSTException: if a WLST error occurs
    """
    _method_name = 'start_edit'
    _logger.entering(class_name=_class_name, method_name=_method_name)

    try:
        wlst.startEdit()
    except wlst.WLSTException, e:
        pwe = exception_helper.create_pywlst_exception('WLSDPLY-00050', _format_exception(e), error=e)
        _logger.throwing(class_name=_class_name, method_name=_method_name, error=pwe)
        raise pwe
    _logger.exiting(class_name=_class_name, method_name=_method_name)


def stop_edit():
    """
    Stop the current edit session and discard all unsaved changes.
    :raises: PyWLSTException: if a WLST error occurs
    """
    _method_name = 'stop_edit'
    _logger.entering(class_name=_class_name, method_name=_method_name)

    try:
        wlst.stopEdit('y')
    except wlst.WLSTException, e:
        pwe = exception_helper.create_pywlst_exception('WLSDPLY-00051', _format_exception(e), error=e)
        _logger.throwing(class_name=_class_name, method_name=_method_name, error=pwe)
        raise pwe
    _logger.exiting(class_name=_class_name, method_name=_method_name)


def undo():
    """
    Revert all unsaved or unactivated edits.
    :raises: PyWLSTException: if a WLST error occurs
    """
    _method_name = 'undo'
    _logger.entering(class_name=_class_name, method_name=_method_name)

    try:
        wlst.undo('true', 'y')
    except wlst.WLSTException, e:
        pwe = exception_helper.create_pywlst_exception('WLSDPLY-00069', _format_exception(e), error=e)
        _logger.throwing(class_name=_class_name, method_name=_method_name, error=pwe)
        raise pwe
    _logger.exiting(class_name=_class_name, method_name=_method_name)


def save():
    """
    Save the outstanding Weblogic Server configuration changes for the current edit session.
    :raises: PyWLSTException: if a WLST error occurs
    """
    _method_name = 'save'
    _logger.entering(class_name=_class_name, method_name=_method_name)

    try:
        wlst.save()
    except wlst.WLSTException, e:
        pwe = exception_helper.create_pywlst_exception('WLSDPLY-00052', _format_exception(e), error=e)
        _logger.throwing(class_name=_class_name, method_name=_method_name, error=pwe)
        raise pwe
    _logger.exiting(class_name=_class_name, method_name=_method_name)


def activate():
    """
    Activate changes saved during the current edit session but not yet deployed.
    :raises: PyWLSTException: if a WLST error occurs
    """
    _method_name = 'activate'
    _logger.entering(class_name=_class_name, method_name=_method_name)

    try:
        wlst.activate()
    except wlst.WLSTException, e:
        pwe = exception_helper.create_pywlst_exception('WLSDPLY-00053', _format_exception(e), error=e)
        _logger.throwing(class_name=_class_name, method_name=_method_name, error=pwe)
        raise pwe
    _logger.exiting(class_name=_class_name, method_name=_method_name)


def get_quoted_name_for_wlst(name):
    """
    Return a wlst required string for a name value in format ('<name>')
    :param name: to represent in the formatted string
    :return: formatted string
    """
    result = name
    if name is not None and '/' in name:
        result = '(' + name + ')'
    return result


def get_existing_object_list(wlst_objects_path):
    """
    Get the existing directory list at the provided WLST path.
    :param wlst_objects_path:
    :return: the list of directory objects
    """
    _method_name = 'get_existing_object_list'
    _logger.finest('WLSDPLY-00054', wlst_objects_path, class_name=_class_name, method_name=_method_name)
    current_dir = get_pwd()

    try:
        result = lsc(wlst_objects_path, log_throwing=False)
    except PyWLSTException:
        # if the ls() failed, directory does not exist
        result = []
    cd(current_dir)
    _logger.finest('WLSDPLY-00055', wlst_objects_path, result, class_name=_class_name, method_name=_method_name)
    return result


def subfolder_exists(wlst_objects_path, wlst_mbean_type):
    """
    Determine if the child exists in the current mbean.
    :param wlst_objects_path: if not None, the wlst mbean attributes path. Current path if none
    :param wlst_mbean_type: wlst child mbean to search for
    :return: True if the child folder exists under the wlst mbean
    """
    _method_name = 'subfolder_exists'
    child_folder_list = get_existing_object_list(wlst_objects_path)
    if child_folder_list is not None and wlst_mbean_type in child_folder_list:
        _logger.finest('WLSDPLY-00074', wlst_mbean_type, wlst_objects_path, class_name=_class_name,
                       _method_name=_method_name)
        exists = True
    else:
        _logger.finest('WLSDPLY-00075', wlst_mbean_type, wlst_objects_path, class_name=_class_name,
                       method_name=_method_name)
        exists = False
    return exists


def start_application(application_name, *args, **kwargs):
    """
    Start the application in the connected domain.
    :param application_name: the application name
    :param args: the positional arguments to the WLST function
    :param kwargs: the keywork arguments to the WLST function
    :return: progress object (depends on whether it is blocked)
    :raises: PyWLSTException: if a WLST error occurs
    """
    _method_name = 'start_application'
    _logger.entering(application_name, args, kwargs, class_name=_class_name, method_name=_method_name)

    try:
        result = wlst.startApplication(application_name, *args, **kwargs)
    except wlst.WLSTException, e:
        pwe = exception_helper.create_pywlst_exception('WLSDPLY-00056', application_name, args, kwargs,
                                                       _format_exception(e), error=e)
        _logger.throwing(class_name=_class_name, method_name=_method_name, error=pwe)
        raise pwe
    _logger.exiting(class_name=_class_name, method_name=_method_name, result=result)
    return result


def stop_application(application_name, *args, **kwargs):
    """
    Stop the application in the connected domain.
    :param application_name: the application name
    :param args: the positional arguments to the WLST function
    :param kwargs: the keywork arguments to the WLST function
    :return: progress object (depends on whether it is blocked)
    :raises: PyWLSTException: if a WLST error occurs
    """
    _method_name = 'stop_application'
    _logger.entering(application_name, args, kwargs, class_name=_class_name, method_name=_method_name)

    try:
        result = wlst.stopApplication(application_name, *args, **kwargs)
    except wlst.WLSTException, e:
        pwe = exception_helper.create_pywlst_exception('WLSDPLY-00057', application_name, args, kwargs,
                                                       _format_exception(e), error=e)
        _logger.throwing(class_name=_class_name, method_name=_method_name, error=pwe)
        raise pwe
    _logger.exiting(class_name=_class_name, method_name=_method_name, result=result)
    return result


def deploy_application(application_name, *args, **kwargs):
    """
    Deploy the application in the connected domain.
    :param application_name: the application name
    :param args: the positional arguments to the WLST function
    :param kwargs: the keywork arguments to the WLST function
    :return: progress object (depends on whether it is blocked)
    :raises: PyWLSTException: if a WLST error occurs
    """
    _method_name = 'deploy_application'
    _logger.entering(application_name, args, kwargs, class_name=_class_name, method_name=_method_name)

    try:
        result = wlst.deploy(application_name, *args, **kwargs)
    except wlst.WLSTException, e:
        pwe = exception_helper.create_pywlst_exception('WLSDPLY-00058', application_name, args, kwargs,
                                                       _format_exception(e), error=e)
        _logger.throwing(class_name=_class_name, method_name=_method_name, error=pwe)
        raise pwe
    _logger.exiting(class_name=_class_name, method_name=_method_name, result=result)
    return result


def undeploy_application(application_name, *args, **kwargs):
    """
    Undeploy the application in the connected domain.
    :param application_name: the application name
    :param args: the positional arguments to the WLST function
    :param kwargs: the keywork arguments to the WLST function
    :return: progress object (depends on whether it is blocked)
    :raises: PyWLSTException: if a WLST error occurs
    """
    _method_name = 'undeploy_application'
    _logger.entering(application_name, args, kwargs, class_name=_class_name, method_name=_method_name)

    try:
        result = wlst.undeploy(application_name, *args, **kwargs)
    except wlst.WLSTException, e:
        pwe = exception_helper.create_pywlst_exception('WLSDPLY-00059', application_name, args, kwargs,
                                                       _format_exception(e), error=e)
        _logger.throwing(class_name=_class_name, method_name=_method_name, error=pwe)
        raise pwe
    _logger.exiting(class_name=_class_name, method_name=_method_name, result=result)
    return result


def redeploy_application(application_name, *args, **kwargs):
    """
    Redeploy the application in the connected domain.
    :param application_name: the application name
    :param args: the positional arguments to the WLST function
    :param kwargs: the keywork arguments to the WLST function
    :return: progress object (depends on whether it is blocked)
    :raises: PyWLSTException: if a WLST error occurs
    """
    _method_name = 'redeploy_application'
    _logger.entering(application_name, args, kwargs, class_name=_class_name, method_name=_method_name)

    try:
        result = wlst.redeploy(application_name, *args, **kwargs)
    except wlst.WLSTException, e:
        pwe = exception_helper.create_pywlst_exception('WLSDPLY-00060', application_name, args, kwargs,
                                                       _format_exception(e), error=e)
        _logger.throwing(class_name=_class_name, method_name=_method_name, error=pwe)
        raise pwe
    _logger.exiting(class_name=_class_name, method_name=_method_name, result=result)
    return result


def get_config_manager():
    """
    Return the online configuration manager
    :return: configuration manager
    :raises: PyWLSTException: if a WLST error occurs
    """
    _method_name = 'get_config_manager'
    try:
        result = wlst.getConfigManager()
    except wlst.WLSTException, e:
        pwe = exception_helper.create_pywlst_exception('WLSDPLY-00061', _format_exception(e), error=e)
        _logger.throwing(class_name=_class_name, method_name=_method_name, error=pwe)
        raise pwe
    return result


def get_active_activation_tasks(cmgr):
    """
    Return list of active activation tasks
    :param cmgr: configuration manager
    :return: list of active activation tasks
    :raises: PyWLSTException: if a WLST error occurs
    """
    _method_name = 'get_active_activation_tasks'
    _logger.entering(cmgr, class_name=_class_name, method_name=_method_name)

    try:
        result = cmgr.getActiveActivationTasks()
    except wlst.WLSTException, e:
        pwe = exception_helper.create_pywlst_exception('WLSDPLY-00062', _format_exception(e), error=e)
        _logger.throwing(class_name=_class_name, method_name=_method_name, error=pwe)
        raise pwe
    _logger.exiting(class_name=_class_name, method_name=_method_name, result=result)
    return result


def is_editor(cmgr):
    """
    Determine if edit session is currently in progress, and if so, the WDT jvm is the current editor.
    :param cmgr: current configuration manager
    :return: True if edit session is in progress and editor is current WDT
    """
    _method_name = 'is_editor'
    _logger.entering(class_name=_class_name, method_name=_method_name)

    try:
        result = cmgr.isEditor()
    except wlst.WLSTException, e:
        pwe = exception_helper.create_pywlst_exception('WLSDPLY-00094', _format_exception(e), error=e)
        _logger.throwing(class_name=_class_name, method_name=_method_name, error=pwe)
        raise pwe
    _logger.exiting(class_name=_class_name, method_name=_method_name, result=StringUtils.stringForBoolean(result))
    return result


def get_current_editor(cmgr):
    """
    Return current editor
    :param cmgr: configuration manager
    :return: current editor of the domain
    :raises: PyWLSTException: if a WLST error occurs
    """
    _method_name = 'get_current_editor'

    try:
        result = cmgr.getCurrentEditor()
    except wlst.WLSTException, e:
        pwe = exception_helper.create_pywlst_exception('WLSDPLY-00063', _format_exception(e), error=e)
        _logger.throwing(class_name=_class_name, method_name=_method_name, error=pwe)
        raise pwe
    return result


def cm_save(cmgr):
    """
    Use the Configuration Manager to save the unsaved changes in online mode.
    :param cmgr: Current Configuration Manager
    :throws: PyWLSTException if unable to perform the online save
    """
    _method_name = 'cm_save'
    _logger.entering(class_name=_class_name, method_name=_method_name)
    try:
        cmgr.save()
    except (wlst.WLSTException, ValidationException), e:
        pwe = exception_helper.create_pywlst_exception('WLSDPLY-00090', _format_exception(e), error=e)
        _logger.throwing(class_name=_class_name, method_name=_method_name, error=pwe)
        raise pwe
    _logger.exiting(class_name=_class_name, method_name=_method_name)


def cm_activate(cmgr):
    """
    Use the configuration manager to activate the saved changes
    :param cmgr: current configuration manager
    :throws PyWLSTException: if in the wrong state to activate the changes
    """
    _method_name = 'cm_activate'
    _logger.entering(class_name=_class_name, method_name=_method_name)
    timeout = 300000L
    try:
        cmgr.activate(timeout)
    except wlst.WLSTException, e:
        pwe = exception_helper.create_pywlst_exception('WLSDPLY-00091', _format_exception(e), error=e)
        _logger.throwing(class_name=_class_name, method_name=_method_name, error=pwe)
        raise pwe
    _logger.exiting(class_name=_class_name, method_name=_method_name)


def cm_start_edit(cmgr):
    """
    Use the configuration manager to start an edit session
    :param cmgr: current configuration manager
    :throws PyWLSTException: in wrong state to start an edit session
    """
    _method_name = 'cm_edit'
    _logger.entering(class_name=_class_name, method_name=_method_name)

    try:
        cmgr.startEdit(0, -1, False)
    except wlst.WLSTException, e:
        pwe = exception_helper.create_pywlst_exception('WLSDPLY-00093', _format_exception(e), error=e)
        _logger.throwing(class_name=_class_name, method_name=_method_name, error=pwe)
        raise pwe

    _logger.exiting(class_name=_class_name, method_name=_method_name)


def get_unsaved_changes(cmgr):
    """
    Return the current edit session unsaved changes
    :param cmgr: current configuration manager
    :return: unsaved changes as Change[]
    """
    _method_name = 'get_changes'
    _logger.entering(class_name=_class_name, method_name=_method_name)
    try:
        changes = cmgr.getChanges()
    except wlst.WLSTException, e:
        pwe = exception_helper.create_pywlst_exception('WLSDPLY-00092', _format_exception(e), error=e)
        _logger.throwing(class_name=_class_name, method_name=_method_name, error=pwe)
        raise pwe

    _logger.exiting(class_name=_class_name, method_name=_method_name, result=len(changes))
    return changes


def have_unsaved_changes(cmgr):
    """
    Return true if the current edit session contains unsaved changes
    :param cmgr: Current Configuration Manager of the connected
    :throws PyWLSTException:
    """
    _method_name = 'have_unsaved_changes'
    _logger.entering(class_name=_class_name, method_name=_method_name)

    changes = get_unsaved_changes(cmgr)
    unsaved = changes is not None and len(changes) > 0
    _logger.exiting(class_name=_class_name, method_name=_method_name, result=StringUtils.stringForBoolean(unsaved))
    return unsaved


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
    except wlst.WLSTException, e:
        pwe = exception_helper.create_pywlst_exception('WLSDPLY-00064', _format_exception(e), error=e)
        _logger.throwing(class_name=_class_name, method_name=_method_name, error=pwe)
        raise pwe
    _logger.exiting(class_name=_class_name, method_name=_method_name, result=result)
    return result


def server_config():
    """
    Change to the serverConfig MBean tree.
    :raises: PyWLSTException: if a WLST error occurs
    """
    _method_name = 'server_config'
    try:
        wlst.serverConfig()
    except wlst.WLSTException, e:
        pwe = exception_helper.create_pywlst_exception('WLSDPLY-00065', _format_exception(e), error=e)
        _logger.throwing(class_name=_class_name, method_name=_method_name, error=pwe)
        raise pwe
    _logger.exiting(class_name=_class_name, method_name=_method_name)
    return


def domain_runtime():
    """
    Change to the domainRuntime MBean tree.
    :raises: PyWLSTException: if a WLST error occurs
    """
    _method_name = 'domain_runtime'
    try:
        wlst.domainRuntime()
    except wlst.WLSTException, e:
        pwe = exception_helper.create_pywlst_exception('WLSDPLY-00066', _format_exception(e), error=e)
        _logger.throwing(class_name=_class_name, method_name=_method_name, error=pwe)
        raise pwe
    _logger.exiting(class_name=_class_name, method_name=_method_name)
    return


def custom():
    """
    Change to the custom MBean tree.
    :raises: PyWLSTException: if a WLST error occurs
    """
    _method_name = 'custom'
    try:
        wlst.custom()
    except wlst.WLSTException, e:
        pwe = exception_helper.create_pywlst_exception('WLSDPLY-00067', _format_exception(e), error=e)
        _logger.throwing(class_name=_class_name, method_name=_method_name, error=pwe)
        raise pwe
    _logger.exiting(class_name=_class_name, method_name=_method_name)
    return


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


def _cd_back(return_directory):
    """
    Change directories back to the original directory, logging a warning if it fails
    :param return_directory: the directory to which to change
    """
    if return_directory is not None:
        try:
            wlst.cd(return_directory)
        except (wlst.WLSTException, offlineWLSTException), ex:
            _logger.warning('WLSDPLY-00068', return_directory, ex.getLocalizedMessage(), error=ex)


def _get_wlst_mode():
    """
    Get the text to describe the current WLST mode.
    :return: online, if connected, offline if not
    """
    if wlst.WLS_ON.isConnected():
        result = 'online'
    else:
        result = 'offline'
    return result


def get_mbi(path=None):
    """
    Get the MBeanInfo for the current or specifiec MBean location.
    :param path: optionally specify path to check
    :return: javax.management.modelmbean.ModelMBeanInfo instance for the current location
    """
    current_path = None
    if path is not None:
        current_path = get_pwd()
        cd(path)

    result = wlst.getMBI()

    if current_path is not None:
        cd(current_path)

    return result


def save_and_close_online():
    """
    Call this if necessary to save changes and disconnect from the domain
    midstream through the tool session. If not connected, do
    nothing.
    """
    _method_name = 'save_and_close_online'
    _logger.entering(class_name=_class_name, method_name=_method_name)
    if is_connected():
        _logger.fine('WLSDPLY-00077', class_name=_class_name, method_name=_method_name)
        save_and_activate_online()
        disconnect()
    else:
        _logger.fine('WLSDPLY-00076', class_name=_class_name, method_name=_method_name)
    _logger.exiting(class_name=_class_name, method_name=_method_name)


def save_and_close_offline():
    """
    Update the domain to save any active changes and close the domain. For use in middle of tool session.
    """
    _method_name = 'save_and_close_offline'
    _logger.entering(class_name=_class_name, method_name=_method_name)
    update_domain()
    close_domain()
    _logger.exiting(class_name=_class_name, method_name=_method_name)


def save_and_activate_online():
    """
    Call this if necessary to save changes midstream through the tool session. If not connected, do
    nothing.
    """
    _method_name = 'save_and_activate_online'
    _logger.entering(class_name=_class_name, method_name=_method_name)
    if is_connected():
        _logger.fine('WLSDPLY-00077', class_name=_class_name, method_name=_method_name)
        # The setServerGroups cmgr.reload() lost the saved and unactivated changes marker
        # Don't even check for outstanding changes or saved but not activated. Just
        # do this and hope for the best
        save()
        activate()
    else:
        _logger.fine('WLSDPLY-00076', class_name=_class_name, method_name=_method_name)
    _logger.exiting(class_name=_class_name, method_name=_method_name)


def save_and_activate_offline():
    """
    Update the domain to save any active changes. For use in middle of tool session.
    """
    _method_name = 'save_and_close_offline'
    _logger.fine('WLSDPLY-00078', class_name=_class_name, method_name=_method_name)
    update_domain()
    _logger.exiting(class_name=_class_name, method_name=_method_name)


def reopen_online(admin_user, admin_pass, admin_url):
    """
    Establish connection with the domain and start editing..
    :param admin_user: admin userid
    :param admin_pass: admin_password
    :param admin_url: url of the admin server
    """
    _method_name = 'reopen_online'
    _logger.entering(admin_user, admin_url, class_name=_class_name, method_name=_method_name)
    if not is_connected():
        _logger.fine('WLSDPLY-00080', class_name=_class_name, method_name=_method_name)
        connect(admin_user, admin_pass, admin_url)
    else:
        _logger.fine('WLSDPLY-00079', class_name=_class_name, method_name=_method_name)

    edit()
    start_edit()

    _logger.exiting(class_name=_class_name, method_name=_method_name)


def reopen_offline(domain_home):
    """
    Read the domain in offline.
    :param domain_home:
    """
    _method_name = 'reopen_offline'
    _logger.fine('WLSDPLY-00081', class_name=_class_name, method_name=_method_name)
    read_domain(domain_home)
    _logger.exiting(class_name=_class_name, method_name=_method_name)
