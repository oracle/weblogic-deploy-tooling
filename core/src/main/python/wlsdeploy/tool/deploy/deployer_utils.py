"""
Copyright (c) 2017, 2018, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""
from sets import Set

from oracle.weblogic.deploy.util import PyWLSTException

from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import SECURITY_CONFIGURATION
from wlsdeploy.exception import exception_helper
from wlsdeploy.exception.expection_types import ExceptionType
from wlsdeploy.logging import platform_logger
from wlsdeploy.tool.util.wlst_helper import WlstHelper

_class_name = "deployer_utils"
_logger = platform_logger.PlatformLogger('wlsdeploy.deploy.utils')
_wlst_helper = WlstHelper(_logger, ExceptionType.DEPLOY)


def set_attribute(location, model_key, model_value, alias_helper, use_raw_value=False):
    """
    Set a single attribute to the specified value.
    :param location: the location of the attribute to be set
    :param model_key: the key of the attribute to be set
    :param model_value: the value of the attribute to be set
    :param alias_helper: the alias helper to use for name resolution
    :param use_raw_value: apply passed value directly if true (example: mbean)
    """
    method_name = 'set_attribute'

    if use_raw_value:
        wlst_param = alias_helper.get_wlst_attribute_name(location, model_key)
        wlst_value = model_value
    else:
        wlst_param, wlst_value = alias_helper.get_wlst_attribute_name_and_value(location, model_key, model_value)

    if wlst_param is None:
        _logger.info('WLSDPLY-09001', model_key, class_name=_class_name, method_name=method_name)
        return

    if wlst_value is None:
        _logger.info('WLSDPLY-09002', model_key, str(model_value), class_name=_class_name, method_name=method_name)
        return

    _wlst_helper.set(wlst_param, wlst_value)


def tokenize_attribute(attribute_key, nodes, model_context):
    if attribute_key in nodes:
        model_context.replace_tokens_in_path(attribute_key, nodes)


def append_model_path(path, subpath):
    return path + "/" + subpath


def get_existing_object_list(location, alias_helper):
    """
    Get a list of the existing names at the specified location.
    :param location: the location to be examined, for example, location MACHINE returns names under /Machines
    :param alias_helper: the alias helper used to determine path names
    """
    method_name = 'get_existing_object_list'
    list_path = alias_helper.get_wlst_list_path(location)
    existing_names = _wlst_helper.get_existing_object_list(list_path)
    _logger.finer("WLSDPLY-09032", existing_names, class_name=_class_name, method_name=method_name)
    return existing_names


def create_and_cd(location, existing_names, alias_helper):
    """
    Create the directories specified by location (if they do not exist), then CD to the attributes path for the
    location.
    :param location: the location of the directory to be created
    :param existing_names: names that already exist at the specified location
    :param alias_helper: the alias helper used to determine path names
    """
    method_name = 'create_and_cd'
    _logger.entering(str(location), existing_names, _class_name, method_name)

    mbean_name = get_mbean_name(location, existing_names, alias_helper)
    create_path = alias_helper.get_wlst_create_path(location)
    _wlst_helper.cd(create_path)

    create_if_not_exist(mbean_name,
                        alias_helper.get_wlst_mbean_type(location),
                        existing_names)

    wlst_path = alias_helper.get_wlst_attributes_path(location)
    _logger.exiting(_class_name, method_name, wlst_path)
    return _wlst_helper.cd(wlst_path)


def create_if_not_exist(object_name, object_type, existing_names):
    """
    If the provided object name does not exist in the provided list of object names, create the object
    at the current location.
    :param object_name: name of the new mbean object
    :param object_type: type of the mbean to create
    :param existing_names: list of existing mbean object names of the mbean object type
    :return: the return value of WLST create() or None if the object already existed and create() was not called
    """
    _method_name = 'create_if_not_exist'
    _logger.entering(object_name, object_type, existing_names, class_name=_class_name, method_name=_method_name)

    result = None
    if object_name not in existing_names:
        _logger.finer('WLSDPLY-00047', object_name, object_type, class_name=_class_name, method_name=_method_name)
        result = _wlst_helper.create(object_name, object_type)
    _logger.exiting(class_name=_class_name, method_name=_method_name, result=result)
    return result


def get_mbean_name(location, existing_names, alias_helper):
    mbean_name = alias_helper.get_wlst_mbean_name(location)

    # for unpredictable single folders:
    #   if an existing folder name is present, use that name as the mbean name.
    #   set the location's token to the mbean name
    if alias_helper.requires_unpredictable_single_name_handling(location):
        if len(existing_names) > 0:
            mbean_name = existing_names[0]
        token = alias_helper.get_name_token(location)
        location.add_name_token(token, mbean_name)

    return mbean_name


def check_flattened_folder(location, alias_helper):
    """
    The paths for a location may contain a flattened folder - a type/name level that is not reflected in the model.
    For these cases, create the required type/name directory pair.
    :param location: the location to examine
    :param alias_helper: the alias helper to use for name and path resolution
    """
    if alias_helper.is_flattened_folder(location):
        create_path = alias_helper.get_wlst_flattened_folder_create_path(location)
        existing_types = _wlst_helper.get_existing_object_list(create_path)

        mbean_type = alias_helper.get_wlst_flattened_mbean_type(location)
        if mbean_type not in existing_types:
            mbean_name = alias_helper.get_wlst_flattened_mbean_name(location)
            _wlst_helper.cd(create_path)
            create_if_not_exist(mbean_name, mbean_type, [])
    return


def get_domain_token(alias_helper):
    """
    Returns the domain token required by some root-level WLST elements.
    :return: the domain token
    """
    # determine the domain token by checking security configuration
    security_location = LocationContext().append_location(SECURITY_CONFIGURATION)
    return alias_helper.get_name_token(security_location)


def merge_lists(existing_list, model_list, separator=',', return_as_string=True):
    """
    Merge two lists into one list of unique elements.  This method understands both
    delimited string and lists and can handle the two list arguments in different formats.
    :param existing_list: the existing list
    :param model_list: the list from the model
    :param separator: the separator for any string list and the return list, if returning as a string, default is comma
    :param return_as_string: whether or not to return the resulting list as a string, dault if True
    :return: the merged list of unique elements
    """
    method_name = 'merge_lists'
    _logger.entering(existing_list, model_list, separator, return_as_string, _class_name, method_name)
    if existing_list is not None and len(existing_list) > 0:
        if type(existing_list) is str:
            existing_set = Set(existing_list.split(separator))
        else:
            existing_set = Set(existing_list)
    else:
        existing_set = Set()

    if model_list is not None and len(model_list) > 0:
        if type(model_list) is str:
            model_set = Set(model_list.split(separator))
        else:
            model_set = Set(model_list)
    else:
        model_set = Set()

    existing_set.union(model_set)
    if return_as_string:
        result = separator.join(existing_set)
    else:
        result = list(existing_set)
    _logger.exiting(_class_name, method_name, result)
    return result


def ensure_no_uncommitted_changes_or_edit_sessions():
    """
    Ensure that the domain does not contain any uncommitted changes and there is no existing edit session.
    :raises: DeployException: if there are any uncommitted changes, existing edit sessions, or a WLST error occurs
    """
    _method_name = 'ensure_no_uncommitted_changes_or_edit_sessions'

    _logger.entering(class_name=_class_name, method_name=_method_name)
    try:
        cmgr = _wlst_helper.get_config_manager()
        tasks = _wlst_helper.get_active_activation_tasks(cmgr)
        current_editor = _wlst_helper.get_current_editor(cmgr)
        unactivated_changes = _wlst_helper.have_unactivated_changes(cmgr)

        if len(tasks) > 0:
            ex = exception_helper.create_deploy_exception('WLSDPLY-09029', len(tasks))
            _logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex

        if unactivated_changes:
            ex = exception_helper.create_deploy_exception('WLSDPLY-09030')
            _logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex

        if current_editor is not None:
            ex = exception_helper.create_deploy_exception('WLSDPLY-09031', str(current_editor))
            _logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex
    except PyWLSTException, e:
        ex = exception_helper.create_deploy_exception('WLSDPLY-09105', e.getLocalizedMessage(), error=e)
        _logger.throwing(ex, class_name=_class_name, method_name=_method_name)
        raise ex
    _logger.exiting(class_name=_class_name, method_name=_method_name)
    return
