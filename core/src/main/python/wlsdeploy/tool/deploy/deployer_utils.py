"""
Copyright (c) 2017, 2022, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import os

from sets import Set

from java.io import IOException
from java.io import PrintStream
from java.lang import System
from java.net import URI
from java.net import URISyntaxException
from java.security import NoSuchAlgorithmException

from oracle.weblogic.deploy.deploy import DeployException
from oracle.weblogic.deploy.util import FileUtils
from oracle.weblogic.deploy.util import StringUtils
from oracle.weblogic.deploy.util import PyWLSTException
from oracle.weblogic.deploy.util import WLSDeployArchive

from oracle.weblogic.deploy.exception import BundleAwareException

from wlsdeploy.aliases import alias_utils
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import APPLICATION
from wlsdeploy.aliases.model_constants import APP_DEPLOYMENTS
from wlsdeploy.aliases.model_constants import CLUSTER
from wlsdeploy.aliases.model_constants import DYNAMIC_CLUSTER_SIZE
from wlsdeploy.aliases.model_constants import DYNAMIC_SERVERS
from wlsdeploy.aliases.model_constants import FILE_URI
from wlsdeploy.aliases.model_constants import JDBC_RESOURCE
from wlsdeploy.aliases.model_constants import JDBC_DATASOURCE_PARAMS
from wlsdeploy.aliases.model_constants import JDBC_DRIVER_PARAMS
from wlsdeploy.aliases.model_constants import JDBC_SYSTEM_RESOURCE
from wlsdeploy.aliases.model_constants import JDBC_CONNECTION_POOL_PARAMS
from wlsdeploy.aliases.model_constants import JDBC_DRIVER_PARAMS_PROPERTIES
from wlsdeploy.aliases.model_constants import JDBC_ORACLE_PARAMS
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_PROPERTY_VALUE
from wlsdeploy.aliases.model_constants import LIBRARY
from wlsdeploy.aliases.model_constants import MAX_DYNAMIC_SERVER_COUNT
from wlsdeploy.aliases.model_constants import SERVER
from wlsdeploy.aliases.model_constants import SERVER_NAME_PREFIX
from wlsdeploy.aliases.model_constants import SERVER_NAME_START_IDX
from wlsdeploy.aliases.model_constants import TARGET
from wlsdeploy.aliases.validation_codes import ValidationCodes
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception import exception_helper
from wlsdeploy.exception.expection_types import ExceptionType
from wlsdeploy.logging import platform_logger
from wlsdeploy.tool.util.string_output_stream import StringOutputStream
from wlsdeploy.tool.util.wlst_helper import WlstHelper
from wlsdeploy.util import dictionary_utils
from wlsdeploy.util import model_helper
import wlsdeploy.util.unicode_helper as str_helper
from wlsdeploy.util.exit_code import ExitCode

from wlsdeploy.aliases.model_constants import RESOURCE_GROUP
from wlsdeploy.aliases.model_constants import RESOURCE_GROUP_TEMPLATE

_class_name = "deployer_utils"
_logger = platform_logger.PlatformLogger('wlsdeploy.deploy.utils')
_wlst_helper = WlstHelper(ExceptionType.DEPLOY)


def get_existing_object_list(location, aliases):
    """
    Get a list of the existing names at the specified location.
    :param location: the location to be examined, for example, location MACHINE returns names under /Machines
    :param aliases: the alias helper used to determine path names
    """
    method_name = 'get_existing_object_list'
    list_path = aliases.get_wlst_list_path(location)
    existing_names = _wlst_helper.get_existing_object_list(list_path)
    _logger.finer("WLSDPLY-09100", existing_names, class_name=_class_name, method_name=method_name)
    return existing_names


def create_and_cd(location, existing_names, aliases):
    """
    Create the directories specified by location (if they do not exist), then CD to the attributes path for the
    location.
    :param location: the location of the directory to be created
    :param existing_names: names that already exist at the specified location
    :param aliases: the alias helper used to determine path names
    """
    method_name = 'create_and_cd'
    _logger.entering(str_helper.to_string(location), existing_names, _class_name, method_name)

    mbean_name = get_mbean_name(location, existing_names, aliases)
    create_path = aliases.get_wlst_create_path(location)
    _wlst_helper.cd(create_path)

    create_if_not_exist(mbean_name,
                        aliases.get_wlst_mbean_type(location),
                        existing_names)
    wlst_path = aliases.get_wlst_attributes_path(location)
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
        _logger.finer('WLSDPLY-09101', object_name, object_type, class_name=_class_name, method_name=_method_name)
        result = _wlst_helper.create(object_name, object_type)
    _logger.exiting(class_name=_class_name, method_name=_method_name, result=result)
    return result


def get_mbean_name(location, existing_names, aliases):
    """
    Return the mbean name for the specified location.
    For unpredictable single folders:
      1. if an existing folder name is present, use that name as the mbean name.
      2. set the location's token to the mbean name.
    :param location: the location to examine
    :param existing_names: a list of existing names at the location
    :param aliases: the alias helper to use for name and path resolution
    """
    mbean_name = aliases.get_wlst_mbean_name(location)

    if aliases.requires_unpredictable_single_name_handling(location):
        if len(existing_names) > 0:
            mbean_name = existing_names[0]
        token = aliases.get_name_token(location)
        location.add_name_token(token, mbean_name)

    return mbean_name


def set_single_folder_token(location, aliases):
    """
    Determine the name of the MBean at the specified WLST location, and set the corresponding token.
    :param location: the single-folder location to be updated
    :param aliases: the aliases object to use for name and path resolution
    """
    exception_type = aliases.get_exception_type()
    wlst_helper = WlstHelper(exception_type)
    list_path = aliases.get_wlst_list_path(location)
    existing_names = wlst_helper.get_existing_object_list(list_path)
    if len(existing_names) > 0:
        mbean_name = existing_names[0]
        token = aliases.get_name_token(location)
        location.add_name_token(token, mbean_name)


def set_flattened_folder_token(location, aliases):
    """
    If the specified model location contains a flattened folder,
    add the corresponding token to the location with the MBean name.
    :param location: the location to be checked
    """
    flattened_folder_info = aliases.get_wlst_flattened_folder_info(location)
    if flattened_folder_info is not None:
        path_token = flattened_folder_info.get_path_token()
        mbean_name = flattened_folder_info.get_mbean_name()
        location.add_name_token(path_token, mbean_name)


def check_flattened_folder(location, aliases):
    """
    The paths for a location may contain a flattened folder - a type/name level that is not reflected in the model.
    For these cases, create the required type/name directory pair.
    :param location: the location to examine
    :param aliases: the alias helper to use for name and path resolution
    """
    flattened_folder_info = aliases.get_wlst_flattened_folder_info(location)
    if flattened_folder_info is not None:
        create_path = aliases.get_wlst_flattened_folder_create_path(location)
        existing_types = _wlst_helper.get_existing_object_list(create_path)

        mbean_type = flattened_folder_info.get_mbean_type()
        mbean_name = flattened_folder_info.get_mbean_name()
        if mbean_type not in existing_types:
            _wlst_helper.cd(create_path)
            create_if_not_exist(mbean_name, mbean_type, [])

        path_token = flattened_folder_info.get_path_token()
        location.add_name_token(path_token, mbean_name)


def get_jdbc_driver_params_location(ds_name, aliases):
    """
    Return the JDBC_DRIVER_PARAMS location for the specified datasource name.
    :param ds_name: the name of the datasource
    :param aliases: the alias helper to use for name and token resolution
    :return: the resulting location
    """
    location = LocationContext()
    location.append_location(JDBC_SYSTEM_RESOURCE)
    token_name = aliases.get_name_token(location)
    location.add_name_token(token_name, ds_name)

    location.append_location(JDBC_RESOURCE)
    set_single_folder_token(location, aliases)
    location.append_location(JDBC_DRIVER_PARAMS)
    set_single_folder_token(location, aliases)
    return location


def get_domain_token(aliases):
    """
    Returns the domain token required by some root-level WLST elements.
    :return: the domain token
    """
    return "DOMAIN"


def is_in_resource_group_or_template(location):
    """
    Determine if the specified location is in a resource group of template.
    :return: True if the location is in a resource group of template, otherwise false
    """
    folders = location.get_model_folders()
    is_in = (RESOURCE_GROUP in folders) or (RESOURCE_GROUP_TEMPLATE in folders)
    return is_in


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
        if type(existing_list) in [str, unicode]:
            existing_set = Set(existing_list.split(separator))
        else:
            existing_set = Set(existing_list)
    else:
        existing_set = Set()

    if model_list is not None and len(model_list) > 0:
        if type(model_list) in [str, unicode]:
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


def delete_named_element(location, delete_name, existing_names, aliases):
    """
    Delete the specified named element if present. If the name is not present, log a warning and return.
    :param location: the location of the element to be deleted
    :param delete_name: the name of the element to be deleted, assumed to include the "!" prefix
    :param existing_names: a list of names to check against
    :param aliases: alias helper for lookups
    """
    _method_name = 'delete_named_element'

    name = model_helper.get_delete_item_name(delete_name)
    type_name = aliases.get_wlst_mbean_type(location)

    if name not in existing_names:
        _logger.warning('WLSDPLY-09109', type_name, name, class_name=_class_name, method_name=_method_name)
    else:
        _logger.info('WLSDPLY-09110', type_name, name, class_name=_class_name, method_name=_method_name)
        type_path = aliases.get_wlst_create_path(location)
        _wlst_helper.cd(type_path)
        _wlst_helper.delete(name, type_name)
        existing_names.remove(name)


def ensure_no_uncommitted_changes_or_edit_sessions(ignore_edit_session_check=False):
    """
    Ensure that the domain does not contain any uncommitted changes and there is no existing edit session.
    :param ignore_edit_session_check: whether to ignore edit session state checks
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
            ex = exception_helper.create_deploy_exception('WLSDPLY-09102', len(tasks))
            _logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex

        if unactivated_changes and not ignore_edit_session_check:
            ex = exception_helper.create_deploy_exception('WLSDPLY-09103')
            _logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex

        if current_editor is not None and not ignore_edit_session_check:
            ex = exception_helper.create_deploy_exception('WLSDPLY-09104', str_helper.to_string(current_editor))
            _logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex
    except PyWLSTException, e:
        ex = exception_helper.create_deploy_exception('WLSDPLY-09105', e.getLocalizedMessage(), error=e)
        _logger.throwing(ex, class_name=_class_name, method_name=_method_name)
        raise ex
    _logger.exiting(class_name=_class_name, method_name=_method_name)


def discard_current_edit():
    """
    Undo any current edit that may have left.
    :raises: DeployException: if there are any wlst errors
    """
    _method_name = 'discard_current_edit'

    _logger.entering(class_name=_class_name, method_name=_method_name)
    try:
        cmgr = _wlst_helper.get_config_manager()
        unactivated_changes = _wlst_helper.have_unactivated_changes(cmgr)

        if unactivated_changes:
            _logger.info("WLSDPLY-09016")
            cmgr.undoUnactivatedChanges()

    except PyWLSTException, e:
        ex = exception_helper.create_deploy_exception('WLSDPLY-09112', e.getLocalizedMessage(), error=e)
        _logger.throwing(ex, class_name=_class_name, method_name=_method_name)
        raise ex
    _logger.exiting(class_name=_class_name, method_name=_method_name)


def extract_from_uri(model_context, path_value):
    """
    If the MBean path attribute has a URI file scheme, look past the scheme and
    resolve any global tokens. If the filename contains non-standard RFC 2936 and
    does not represent a file but rather a future file.

    :param model_context: current context containing job information
    :param path_value: MBean attribute path
    :return: fully resolved URI path, or the path_value if not a URI scheme
    """
    _method_name = 'extract_from_uri'
    try:
        uri = URI(path_value)
        if uri.getScheme() == 'file':
            return FILE_URI + model_context.replace_token_string(uri.getPath()[1:])
    except URISyntaxException, use:
        _logger.fine('WLSDPLY-09113', path_value, use, class_name=_class_name, method_name=_method_name)
    return path_value


def get_rel_path_from_uri(model_context, path_value):
    """
    If the MBean attribute is a URI. To extract it from the archive, need to make
    it into a relative path. If it contains non-standard RF 2396 characters, assume
    it is not a file name in the archive.
    :param model_context: current context containing run information
    :param path_value: the full value of the path attribute
    :return: The relative value of the path attribute
    """
    _method_name = 'get_rel_path_from_uri'
    try:
        uri = URI(path_value)
        if uri.getScheme() == 'file':
            value = model_context.tokenize_path(uri.getPath())
            if value.startswith(model_context.DOMAIN_HOME_TOKEN):
                # point past the token and first slash
                value = value[len(model_context.DOMAIN_HOME_TOKEN)+1:]
            return value
    except URISyntaxException, use:
        _logger.fine('WLSDPLY-09113', path_value, use, class_name=_class_name, method_name=_method_name)
    return path_value


def is_path_into_archive(path):
    """
    Is the path specified a path into the archive file?
    :param path: the path to test
    :return: True if the path is into the archive file, False otherwise
    """
    _method_name = 'is_path_into_archive'

    _logger.entering(path, class_name=_class_name, method_name=_method_name)
    result = WLSDeployArchive.isPathIntoArchive(path)
    _logger.exiting(class_name=_class_name, method_name=_method_name, result=result)
    return result


def get_library_name_components(name, wlst_mode=WlstModes.OFFLINE):
    """
    Helper method for application deployer to decompose a shared library name into its components.
    :param name: the name
    :param wlst_mode: the WLST mode
    :return: a tuple of the name components
    """
    _method_name = '__get_library_name_components'

    _logger.entering(name, class_name=_class_name, method_name=_method_name)
    items = name.split('#')
    name_tuple = [items[0]]
    if len(items) == 2:
        ver_items = items[1].split('@')
        name_tuple.append(ver_items[0])
        if len(ver_items) == 2:
            name_tuple.append(ver_items[1])
        elif len(ver_items) == 1:
            # no implementation version specified...
            pass
        else:
            ex = exception_helper.create_deploy_exception('WLSDPLY-09106', name, len(ver_items) - 1)
            _logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex
    elif len(items) != 1:
        ex = exception_helper.create_deploy_exception('WLSDPLY-09107', name, len(items) - 1)
        _logger.throwing(ex, class_name=_class_name, method_name=_method_name)
        raise ex
    _logger.exiting(class_name=_class_name, method_name=_method_name, result=name_tuple)
    return name_tuple


def get_file_hash(file_name):
    """
    Compute the Base64-encoded hash value for the specified file.
    :param file_name: the file name
    :return: the Base64-encoded hash value
    :raise: DeployException: if an error occurs
    """
    _method_name = 'get_file_hash'

    _logger.entering(file_name, class_name=_class_name, method_name=_method_name)
    try:
        result = FileUtils.computeHash(file_name)
    except (IOException, NoSuchAlgorithmException), e:
        ex = exception_helper.create_deploy_exception('WLSDPLY-09108', file_name, e.getLocalizedMessage(), error=e)
        _logger.throwing(ex, class_name=_class_name, method_name=_method_name)
        raise ex
    _logger.exiting(class_name=_class_name, method_name=_method_name, result=result)
    return result


def get_cluster_for_server(server_name, aliases):
    """
    Get the Cluster name for the existing server name for additional information to mine for the update action.
    :param server_name: name of the server
    :param aliases: alias context instance
    :return: cluster name: name of the cluster the server belongs to, or None if stand-alone or server does not exist
    """
    _method_name = 'get_cluster_for_server'
    _logger.entering(server_name, class_name=_class_name, method_name=_method_name)
    location = LocationContext()
    location.append_location(SERVER)
    name_token = aliases.get_name_token(location)
    location.add_name_token(name_token, server_name)
    attr_path = aliases.get_wlst_attributes_path(location)
    cluster_name = None
    try:
        _wlst_helper.cd(attr_path)
        cluster_name = _wlst_helper.get(CLUSTER)
    except DeployException, de:
        _logger.fine('WLSDPLY-09205', server_name, str_helper.to_string(location), de.getLocalizedMessage,
                     SERVER, class_name=_class_name, method_name=_method_name)
    _logger.exiting(result=cluster_name, class_name=_class_name, method_name=_method_name)
    return cluster_name


def list_restarts(model_context, exit_code):
    """
    Get the list of restarts and save this list in format to restart.file
    in the -output_dirs location. If the output_dirs is not included, bypass
    writing to the restart file.
    :param model_context: instance of the tool model context
    :param exit_code: current exit code for online restarts
    """
    _method_name = 'list_restarts'
    _logger.entering(model_context.get_output_dir(), class_name=_class_name, method_name=_method_name)
    restart_list = get_list_of_restarts()
    output_dirs = model_context.get_output_dir()
    result = exit_code
    if len(restart_list) == 0:
        result = 0
    elif output_dirs is not None:
        file_name = os.path.join(output_dirs, 'restart.file')
        pw = FileUtils.getPrintWriter(file_name)
        for entry in restart_list:
            line = '%s:%s:%s:%s' % (entry[0], entry[1], entry[2], entry[3])
            _logger.finer('WLSDPLY-09208', line, class_name=_class_name, method_name=_method_name)
            pw.println(line)
        pw.close()
    _logger.exiting(class_name=_class_name, method_name=_method_name, result=result)
    return result


def list_non_dynamic_changes(model_context, non_dynamic_changes_string):
    """
    If output dir is present in the model context, write the restart data to the output dir as non_dynamic_changes.file.
    :param model_context: Current context with the run parameters.
    :param non_dynamic_changes_string: java.lang.String of changes that were non dynamic
    """
    _method_name = 'list_non_dynamic_changes'
    _logger.entering(class_name=_class_name, method_name=_method_name)
    output_dir = model_context.get_output_dir()
    if len(str_helper.to_string(non_dynamic_changes_string)) > 0 and output_dir is not None:
        file_name = os.path.join(output_dir, 'non_dynamic_changes.file')
        pw = FileUtils.getPrintWriter(file_name)
        pw.println(non_dynamic_changes_string)
        pw.close()


def get_list_of_restarts():
    """
    Return the restart checklist from the online domain instance. Log each instance of the restart checklist
    :return: String buffer of restart information
    """
    _method_name = 'get_list_of_restarts'
    restart_list = []
    _wlst_helper.cd('/')
    cmo = _wlst_helper.get_cmo()
    for server in _wlst_helper.get_server_runtimes():
        resources = server.getPendingRestartSystemResources()
        is_restart = server.isRestartRequired()
        if len(resources) > 0 or is_restart:
            server_name = server.getName()
            cluster = server.getClusterRuntime()
            cluster_name = ''
            if cluster is not None:
                cluster_name = cluster.getName()
            prt_cluster = cluster_name
            if cluster_name == '':
                prt_cluster = 'standalone'
            for resource in resources:
                line = list()
                line.append(cluster_name)
                line.append(server_name)
                line.append(resource)
                value = cmo.lookupSystemResource(resource)
                res_type = ''
                if value is not None:
                    res_type = value.getType()
                line.append(res_type)
                restart_list.append(line)
                _logger.warning('WLSDPLY-09207', resource, res_type, server_name, prt_cluster,
                                class_name=_class_name, method_name=_method_name)
            if is_restart:
                line = list()
                line.append(cluster_name)
                line.append(server_name)
                line.append('')
                line.append('')
                restart_list.append(line)
                _logger.warning('WLSDPLY-09206', server_name, prt_cluster,
                                class_name=_class_name, method_name=_method_name)
    return restart_list


def online_check_save_activate(model_context):
    """
    For online update and deploy, check if restart is required, then cancel or save and activate.
    :param model_context: used to perform checks
    :return: the exit code for the tool
    :raises BundleAwareException: if an error occurs during the process
    """
    exit_code = 0

    try:
        # First we enable the stdout again and then redirect the stdoout to a string output stream
        # call isRestartRequired to get the output, capture the string and then silence wlst output again

        _wlst_helper.enable_stdout()
        sostream = StringOutputStream()
        System.setOut(PrintStream(sostream))
        restart_required = _wlst_helper.is_restart_required()
        is_restartreq_output = sostream.get_string()
        _wlst_helper.silence()
        if model_context.is_cancel_changes_if_restart_required() and restart_required:
            _wlst_helper.cancel_edit()
            _logger.warning('WLSDPLY-09018', is_restartreq_output)
            exit_code = ExitCode.CANCEL_CHANGES_IF_RESTART
            list_non_dynamic_changes(model_context, is_restartreq_output)
        else:
            _wlst_helper.save()
            _wlst_helper.activate(model_context.get_model_config().get_activate_timeout())
            if restart_required:
                exit_code = ExitCode.RESTART_REQUIRED
                list_non_dynamic_changes(model_context, is_restartreq_output)
                exit_code = list_restarts(model_context, exit_code)

    except BundleAwareException, ex:
        release_edit_session_and_disconnect()
        raise ex

    return exit_code


def release_edit_session_and_disconnect():
    """
    An online error recovery method.
    """
    _method_name = 'release_edit_session_and_disconnect'
    try:
        _wlst_helper.undo()
        _wlst_helper.stop_edit()
        _wlst_helper.disconnect()
    except BundleAwareException, ex:
        # This method is only used for cleanup after an error so don't mask
        # the original problem by throwing yet another exception...
        _logger.warning('WLSDPLY-09012', ex.getLocalizedMessage(), error=ex,
                        class_name=_class_name, method_name=_method_name)


def check_if_dynamic_cluster(server_name, cluster_name, aliases):
    """
    Determine if the server is part of a dynamic cluster.
    :param server_name: Name of the server to check
    :param cluster_name: Name of the cluster the server belongs to, or None if stand-alone
    :param aliases: aliases context instance
    :return: True if part of a dynamic cluster
    """
    _method_name = 'check_if_dynamic_cluster'
    # check wls version first either here or before caller. preferably here
    location = LocationContext()
    location.append_location(CLUSTER)
    location.add_name_token(aliases.get_name_token(location), cluster_name)
    attr_path = aliases.get_wlst_attributes_path(location)

    try:
        _wlst_helper.cd(attr_path)
    except DeployException, de:
        _logger.fine('WLSDPLY-09205', cluster_name, str_helper.to_string(location), de.getLocalizedMessage,
                     CLUSTER, class_name=_class_name, method_name=_method_name)
        return True
    location.append_location(DYNAMIC_SERVERS)
    location.add_name_token(aliases.get_name_token(location), cluster_name)
    attr_path = aliases.get_wlst_attributes_path(location)
    try:
        _wlst_helper.cd(attr_path)
    except DeployException:
        return False
    present, __ = aliases.is_valid_model_attribute_name(location, DYNAMIC_CLUSTER_SIZE)
    if present == ValidationCodes.VALID:
        attr_name = aliases.get_wlst_attribute_name(location, DYNAMIC_CLUSTER_SIZE)
    else:
        attr_name = aliases.get_wlst_attribute_name(location, MAX_DYNAMIC_SERVER_COUNT)
    dynamic_size = _wlst_helper.get(attr_name)
    attr_name = aliases.get_wlst_attribute_name(location, SERVER_NAME_PREFIX)
    prefix = _wlst_helper.get(attr_name)
    starting = 1
    present, __ = aliases.is_valid_model_attribute_name(location, SERVER_NAME_START_IDX)
    if present == ValidationCodes.VALID:
        attr_name = aliases.get_model_attribute_name(location, SERVER_NAME_START_IDX)
        starting = _wlst_helper.get(attr_name)
    if dynamic_size > 0 and prefix is not None and server_name.startswith(prefix):
        split_it = server_name.split(prefix)
        if len(split_it) == 2:
            number = StringUtils.stringToInteger(split_it[1].strip())
            if number is not None and starting <= number < (dynamic_size + starting):
                return True
    return False


def delete_online_deployment_targets(model, aliases, wlst_mode):
    """
    For online deploy and update, remove any deleted targets from existing apps and libraries.
    This step needs to occur during the WLST edit session, before regular app/library deployment.
    :param model: the model to be examined
    :param aliases: to resolve WLST paths
    :param wlst_mode: to check for online mode
    """
    if wlst_mode == WlstModes.ONLINE:
        app_deployments = dictionary_utils.get_dictionary_element(model.get_model(), APP_DEPLOYMENTS)
        __delete_online_targets(app_deployments, APPLICATION, aliases)
        __delete_online_targets(app_deployments, LIBRARY, aliases)


def __delete_online_targets(app_deployments, model_type, aliases):
    """
    For online deploy and update, remove any deleted targets from existing objects of the specified type.
    Objects may be applications or libraries.
    :param app_deployments: the APP_DEPLOYMENTS dictionary from the model
    :param model_type: map of library targets to be deleted
    :param aliases: the parent location of the apps and libraries
    """
    _method_name = '__delete_online_targets'

    location = LocationContext().append_location(model_type)
    wlst_path = aliases.get_wlst_list_path(location)
    wlst_names = _wlst_helper.get_existing_object_list(wlst_path)
    name_token = aliases.get_name_token(location)

    deploy_dict = dictionary_utils.get_dictionary_element(app_deployments, model_type)
    for deploy_name in deploy_dict.keys():
        if deploy_name in wlst_names:
            value_dict = deploy_dict[deploy_name]

            delete_names = []
            model_targets = dictionary_utils.get_element(value_dict, TARGET)
            targets = alias_utils.create_list(model_targets, 'WLSDPLY-08000')
            for target in targets:
                if model_helper.is_delete_name(target):
                    delete_names.append(model_helper.get_delete_item_name(target))

            location.add_name_token(name_token, deploy_name)
            mbean_path = aliases.get_wlst_attributes_path(location)
            mbean = _wlst_helper.get_mbean_for_wlst_path(mbean_path)
            mbean_targets = mbean.getTargets()
            for mbean_target in mbean_targets:
                mbean_name = mbean_target.getName()
                if mbean_name in delete_names:
                    _logger.info('WLSDPLY-09114', mbean_name, model_type, deploy_name, class_name=_class_name,
                                 method_name=_method_name)
                    mbean.removeTarget(mbean_target)

def __copy_templated_ds_attributes(src_location, target_location, aliases):
    src_ds_wlst_path = aliases.get_wlst_attributes_path(src_location)
    _wlst_helper.cd(src_ds_wlst_path)

    attributes = _wlst_helper.lsa()
    for attribute in attributes:

        if attribute in ['Tag', 'Id', 'Name', 'JNDIName', 'DescriptorFileName']:
            continue
        if attribute == 'Target' and attributes[attribute] is None:
            continue

        _wlst_helper.cd(aliases.get_wlst_attributes_path(target_location))
        wlst_name, wlst_value = \
            aliases.get_wlst_attribute_name_and_value(target_location, attribute,
                                                      attributes[attribute])
        _wlst_helper.set_if_needed(wlst_name, wlst_value)

def __add_token_at_location(aliases, location, value):
    token = aliases.get_name_token(location)
    if token:
        location.add_name_token(token, value)

def __get_jdbc_system_resource_location(ds_name, aliases):
    ds_location = LocationContext()
    ds_location.append_location(JDBC_SYSTEM_RESOURCE)
    __add_token_at_location(aliases, ds_location, ds_name)
    return ds_location

def get_jdbc_datasource_location(ds_name, aliases):
    ds_location = __get_jdbc_system_resource_location(ds_name, aliases)
    ds_location.append_location(JDBC_RESOURCE)
    __add_token_at_location(aliases, ds_location, ds_name)
    return ds_location

def __get_jdbc_datasource_params_location(ds_name, aliases):
    ds_location = get_jdbc_datasource_location(ds_name, aliases)
    ds_location.append_location(JDBC_DATASOURCE_PARAMS)
    __add_token_at_location(aliases, ds_location, 'NO_NAME_0')
    return ds_location

def get_jdbc_datasource_oracleparams_location(ds_name, aliases):
    ds_location = get_jdbc_datasource_location(ds_name, aliases)
    ds_location.append_location(JDBC_ORACLE_PARAMS)
    __add_token_at_location(aliases, ds_location, 'NO_NAME_0')
    return ds_location

def __get_jdbc_driver_params_location(ds_name, aliases):
    ds_location = get_jdbc_datasource_location(ds_name, aliases)
    ds_location.append_location(JDBC_DRIVER_PARAMS)
    __add_token_at_location(aliases, ds_location, 'NO_NAME_0')
    return ds_location

def get_jdbc_driver_params_properties_location(ds_name, aliases):
    ds_location = __get_jdbc_driver_params_location(ds_name, aliases)
    __add_token_at_location(aliases, ds_location, 'NO_NAME_0')
    ds_location.append_location(JDBC_DRIVER_PARAMS_PROPERTIES)
    ds_location.add_name_token('PROPERTIES', 'NO_NAME_0')
    return ds_location

def __get_jdbc_connection_pool_params_location(ds_name, aliases):
    ds_location = get_jdbc_datasource_location(ds_name, aliases)
    ds_location.append_location(JDBC_CONNECTION_POOL_PARAMS)
    __add_token_at_location(aliases, ds_location, 'NO_NAME_0')
    return ds_location

def __update_templated_ds_datasource_params(aliases, src_name, target_name):
    target_ds_location = __get_jdbc_datasource_params_location(target_name, aliases)
    src_ds_location = __get_jdbc_datasource_params_location(src_name, aliases)

    __copy_templated_ds_attributes(src_ds_location, target_ds_location, aliases)

def __update_templated_ds_driver_params(aliases, src_name, target_name):
    target_ds_location = __get_jdbc_driver_params_location(target_name, aliases)
    src_ds_location = __get_jdbc_driver_params_location(src_name, aliases)

    __copy_templated_ds_attributes(src_ds_location, target_ds_location, aliases)

    # copy properties
    src_property_path = aliases.get_wlst_attributes_path(src_ds_location)  + '/Properties/NO_NAME_0/Property'
    target_properties_path = aliases.get_wlst_attributes_path(target_ds_location)  + '/Properties/NO_NAME_0'
    properties = _wlst_helper.lsc(src_property_path)

    src_ds_location.append_location(JDBC_DRIVER_PARAMS_PROPERTIES)
    set_flattened_folder_token(src_ds_location, aliases)
    target_ds_location.append_location(JDBC_DRIVER_PARAMS_PROPERTIES)
    set_flattened_folder_token(target_ds_location, aliases)

    if properties is not None:
        for property in properties:
            token_name = aliases.get_name_token(src_ds_location)

            if token_name is not None:
                src_ds_location.add_name_token(token_name, property)

            property_wlst_path = aliases.get_wlst_attributes_path(src_ds_location)
            _wlst_helper.cd(property_wlst_path)
            property_value = _wlst_helper.get('Value')
            _wlst_helper.cd(target_properties_path)
            _wlst_helper.create(property, 'Property')
            target_ds_location.add_name_token(token_name, property)
            property_wlst_path = aliases.get_wlst_attributes_path(target_ds_location)
            _wlst_helper.cd(property_wlst_path)
            wlst_name, wlst_value = \
                aliases.get_wlst_attribute_name_and_value(target_ds_location, DRIVER_PARAMS_PROPERTY_VALUE,
                                                          property_value)
            _wlst_helper.set_if_needed(wlst_name, wlst_value)


def __update_templated_ds_connpool_params(aliases, src_name, target_name):
    target_ds_location = __get_jdbc_connection_pool_params_location(target_name, aliases)
    src_ds_location = __get_jdbc_connection_pool_params_location(src_name, aliases)
    __copy_templated_ds_attributes(src_ds_location, target_ds_location, aliases)

def __update_datasource_toplevel_params(aliases, src_name, target_name):

    target_ds_location = __get_jdbc_system_resource_location(target_name, aliases)
    src_ds_location = __get_jdbc_system_resource_location(src_name, aliases)

    create_and_cd(target_ds_location, [], aliases)
    _wlst_helper.cd('JdbcResource/' + target_name)
    _wlst_helper.create('NO_NAME_0', 'JDBCDriverParams', None)
    _wlst_helper.create('NO_NAME_0', 'JDBCConnectionPoolParams', None)
    _wlst_helper.create('NO_NAME_0', 'JDBCDataSourceParams', None)
    _wlst_helper.cd('JDBCDriverParams/NO_NAME_0')
    _wlst_helper.create('NO_NAME_0', 'Properties')

    src_ds_wlst_path = aliases.get_wlst_attributes_path(src_ds_location)
    _wlst_helper.cd(src_ds_wlst_path)

    __copy_templated_ds_attributes(src_ds_location, target_ds_location, aliases)


def clone_templated_data_source(src_name, multi_data_source, aliases):
    adjusted_names = []
    urls = {}
    # Create each physical datasource,
    for target_name in multi_data_source:
        new_target_name = src_name + '-' + target_name
        adjusted_names.append(new_target_name)
        urls[new_target_name] = { 'url': multi_data_source[target_name]['url']}

        __update_datasource_toplevel_params(aliases, src_name, new_target_name)
        __update_templated_ds_datasource_params(aliases, src_name, new_target_name)
        __update_templated_ds_driver_params(aliases, src_name, new_target_name)
        __update_templated_ds_connpool_params(aliases, src_name, new_target_name)

    return adjusted_names, urls

def convert_templated_ds_to_mds(ds_name,  multi_data_source, aliases):
    ds_location = get_jdbc_datasource_location(ds_name, aliases)
    ds_wlst_path = aliases.get_wlst_attributes_path(ds_location)
    _wlst_helper.cd(ds_wlst_path)
    wlst_name, wlst_value = \
        aliases.get_wlst_attribute_name_and_value(ds_location, 'DatasourceType', 'MDS')
    _wlst_helper.set_if_needed(wlst_name, wlst_value)

    # Note:  in order for JRF cie code to work,  JDBCDriverParams and JDBCConnectionPoolParams must be present
    #  do not delete the mbeans.

    ds_location = __get_jdbc_datasource_params_location(ds_name, aliases)
    ds_wlst_path = aliases.get_wlst_attributes_path(ds_location)
    _wlst_helper.cd(ds_wlst_path)

    wlst_name, wlst_value = \
        aliases.get_wlst_attribute_name_and_value(ds_location, 'AlgorithmType', 'Failover')
    _wlst_helper.set_if_needed(wlst_name, wlst_value)
    mds_list = list(multi_data_source)
    wlst_name, wlst_value = \
        aliases.get_wlst_attribute_name_and_value(ds_location, 'DataSourceList', mds_list)
    _wlst_helper.set_if_needed(wlst_name, wlst_value)

def set_datasource_type(ds_name, ds_type, aliases):
    ds_location = get_jdbc_datasource_location(ds_name, aliases)
    ds_wlst_path = aliases.get_wlst_attributes_path(ds_location)
    _wlst_helper.cd(ds_wlst_path)
    wlst_name, wlst_value = \
        aliases.get_wlst_attribute_name_and_value(ds_location, 'DatasourceType', ds_type)
    _wlst_helper.set_if_needed(wlst_name, wlst_value)
