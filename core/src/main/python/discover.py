"""
Copyright (c) 2017, 2019, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0

The entry point for the discoverDomain tool.
"""
import javaos as os
import sys

from java.io import File
from java.io import IOException
from java.lang import IllegalArgumentException
from java.lang import IllegalStateException
from java.lang import String
from oracle.weblogic.deploy.aliases import AliasException
from oracle.weblogic.deploy.discover import DiscoverException
from oracle.weblogic.deploy.util import CLAException
from oracle.weblogic.deploy.util import FileUtils
from oracle.weblogic.deploy.util import PyWLSTException
from oracle.weblogic.deploy.util import TranslateException
from oracle.weblogic.deploy.util import WLSDeployArchive
from oracle.weblogic.deploy.util import WLSDeployArchiveIOException
from oracle.weblogic.deploy.util import WebLogicDeployToolingVersion
from oracle.weblogic.deploy.validate import ValidateException

sys.path.append(os.path.dirname(os.path.realpath(sys.argv[0])))

from wlsdeploy.aliases import model_constants
from wlsdeploy.aliases.aliases import Aliases
from wlsdeploy.aliases.location_context import LocationContext
import wlsdeploy.tool.util.variable_injector as variable_injector

from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception import exception_helper
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.create.domain_typedef import DomainTypedef
from wlsdeploy.tool.discover import discoverer
from wlsdeploy.tool.discover.deployments_discoverer import DeploymentsDiscoverer
from wlsdeploy.tool.discover.domain_info_discoverer import DomainInfoDiscoverer
from wlsdeploy.tool.discover.multi_tenant_discoverer import MultiTenantDiscoverer
from wlsdeploy.tool.discover.resources_discoverer import ResourcesDiscoverer
from wlsdeploy.tool.discover.topology_discoverer import TopologyDiscoverer
from wlsdeploy.tool.util import filter_helper
from wlsdeploy.tool.util.variable_injector import VariableInjector
from wlsdeploy.tool.validate.validator import Validator
from wlsdeploy.util import dictionary_utils
from wlsdeploy.util import getcreds
from wlsdeploy.util import model_translator
from wlsdeploy.util import tool_exit
from wlsdeploy.util import wlst_extended
from wlsdeploy.util import wlst_helper
from wlsdeploy.util.cla_utils import CommandLineArgUtil
from wlsdeploy.util.model import Model
from wlsdeploy.util.model_context import ModelContext
from wlsdeploy.util.weblogic_helper import WebLogicHelper

wlst_extended.wlst_functions = globals()

_program_name = 'discoverDomain'
_class_name = 'discover'
__logger = PlatformLogger(discoverer.get_discover_logger_name())
__wlst_mode = WlstModes.OFFLINE

__required_arguments = [
    CommandLineArgUtil.ORACLE_HOME_SWITCH,
    CommandLineArgUtil.DOMAIN_HOME_SWITCH,
    CommandLineArgUtil.ARCHIVE_FILE_SWITCH
]

__optional_arguments = [
    # Used by shell script to locate WLST
    CommandLineArgUtil.MODEL_FILE_SWITCH,
    CommandLineArgUtil.DOMAIN_TYPE_SWITCH,
    CommandLineArgUtil.VARIABLE_PROPERTIES_FILE_SWITCH,
    CommandLineArgUtil.ADMIN_URL_SWITCH,
    CommandLineArgUtil.ADMIN_USER_SWITCH,
    CommandLineArgUtil.ADMIN_PASS_SWITCH,
    CommandLineArgUtil.TARGET_MODE_SWITCH
]


def __process_args(args):
    """
    Process the command-line arguments and prompt the user for any missing information
    :param args: the command-line arguments list
    :raises CLAException: if an error occurs while validating and processing the command-line arguments
    """
    global __wlst_mode

    cla_util = CommandLineArgUtil(_program_name, __required_arguments, __optional_arguments)
    required_arg_map, optional_arg_map = cla_util.process_args(args)

    domain_type = dictionary_utils.get_element(optional_arg_map, CommandLineArgUtil.DOMAIN_TYPE_SWITCH)
    if domain_type is None:
        domain_type = 'WLS'
    domain_typedef = DomainTypedef(_program_name, domain_type)
    optional_arg_map[CommandLineArgUtil.DOMAIN_TYPEDEF] = domain_typedef

    __verify_required_args_present(required_arg_map)
    __wlst_mode = __process_online_args(optional_arg_map)
    __process_archive_filename_arg(required_arg_map)
    __process_variable_filename_arg(optional_arg_map)

    combined_arg_map = optional_arg_map.copy()
    combined_arg_map.update(required_arg_map)

    return ModelContext(_program_name, combined_arg_map)


def __verify_required_args_present(required_arg_map):
    """
    Verify that the required args are present.
    :param required_arg_map: the required arguments map
    :raises CLAException: if one or more of the required arguments are missing
    """
    _method_name = '__verify_required_args_present'

    for req_arg in __required_arguments:
        if req_arg not in required_arg_map:
            ex = exception_helper.create_cla_exception('WLSDPLY-20005', _program_name, req_arg)
            ex.setExitCode(CommandLineArgUtil.USAGE_ERROR_EXIT_CODE)
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex
    return


def __process_online_args(optional_arg_map):
    """
    Determine if we are discover in online mode and if so, validate/prompt for the necessary parameters.
    :param optional_arg_map: the optional arguments map
    :return: the WLST mode
    :raises CLAException: if an error occurs reading input from the user
    """
    _method_name = '__process_online_args'

    mode = WlstModes.OFFLINE
    if CommandLineArgUtil.ADMIN_URL_SWITCH in optional_arg_map:
        if CommandLineArgUtil.ADMIN_USER_SWITCH not in optional_arg_map:
            try:
                username = getcreds.getuser('WLSDPLY-06016')
            except IOException, ioe:
                ex = exception_helper.create_cla_exception('WLSDPLY-06017', ioe.getLocalizedMessage(), error=ioe)
                ex.setExitCode(CommandLineArgUtil.ARG_VALIDATION_ERROR_EXIT_CODE)
                __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
                raise ex
            optional_arg_map[CommandLineArgUtil.ADMIN_USER_SWITCH] = username

        if CommandLineArgUtil.ADMIN_PASS_SWITCH not in optional_arg_map:
            try:
                password = getcreds.getpass('WLSDPLY-06018')
            except IOException, ioe:
                ex = exception_helper.create_cla_exception('WLSDPLY-06019', ioe.getLocalizedMessage(), error=ioe)
                ex.setExitCode(CommandLineArgUtil.ARG_VALIDATION_ERROR_EXIT_CODE)
                __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
                raise ex
            optional_arg_map[CommandLineArgUtil.ADMIN_PASS_SWITCH] = String(password)

        mode = WlstModes.ONLINE
        optional_arg_map[CommandLineArgUtil.TARGET_MODE_SWITCH] = 'online'
    return mode


def __process_archive_filename_arg(required_arg_map):
    """
    Validate the archive file name and load the archive file object.
    :param required_arg_map: the required arguments map
    :raises CLAException: if a validation error occurs while loading the archive file object
    """
    _method_name = '__process_archive_filename_arg'

    archive_file_name = required_arg_map[CommandLineArgUtil.ARCHIVE_FILE_SWITCH]
    try:
        archive_file = WLSDeployArchive(archive_file_name)
    except (IllegalArgumentException, IllegalStateException), ie:
        ex = exception_helper.create_cla_exception('WLSDPLY-06013', _program_name, archive_file_name,
                                                   ie.getLocalizedMessage(), error=ie)
        __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
        raise ex
    required_arg_map[CommandLineArgUtil.ARCHIVE_FILE] = archive_file
    return


def __process_variable_filename_arg(optional_arg_map):
    """
    If the variable filename argument is present, the required model variable injector json file must exist in
    the WLSDEPLOY lib directory.
    :param optional_arg_map: containing the variable file name
    :raises: CLAException: if this argument is present but the model variable injector json does not exist
    """
    _method_name = '__process_variable_filename_arg'

    if CommandLineArgUtil.VARIABLE_PROPERTIES_FILE_SWITCH in optional_arg_map:
        variable_injector_file_name = variable_injector.get_default_variable_injector_file_name()
        try:
            FileUtils.validateExistingFile(variable_injector_file_name)
        except IllegalArgumentException, ie:
            ex = exception_helper.create_cla_exception('WLSDPLY-06021', optional_arg_map[
                CommandLineArgUtil.VARIABLE_PROPERTIES_FILE_SWITCH], variable_injector_file_name,
                                                       ie.getLocalizedMessage(), error=ie)
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex
    return


def __discover(model_context, aliases):
    """
    Populate the model from the domain.
    :param model_context: the model context
    :return: the fully-populated model
    :raises DiscoverException: if an error occurred while discover the domain
    """
    _method_name = '__discover'
    model = Model()
    base_location = LocationContext()
    __connect_to_domain(model_context)
    try:
        _add_domain_name(base_location, aliases)
        DomainInfoDiscoverer(model_context, model.get_model_domain_info(), base_location, wlst_mode=__wlst_mode,
                             aliases=aliases).discover()
        TopologyDiscoverer(model_context, model.get_model_topology(), base_location, wlst_mode=__wlst_mode,
                           aliases=aliases).discover()
        ResourcesDiscoverer(model_context, model.get_model_resources(), base_location, wlst_mode=__wlst_mode,
                            aliases=aliases).discover()
        DeploymentsDiscoverer(model_context, model.get_model_app_deployments(), base_location, wlst_mode=__wlst_mode,
                              aliases=aliases).discover()
        __discover_multi_tenant(model, model_context, base_location, aliases)
    except AliasException, ae:
        wls_version = WebLogicHelper(__logger).get_actual_weblogic_version()
        wlst_mode = WlstModes.from_value(__wlst_mode)
        ex = exception_helper.create_discover_exception('WLSDPLY-06000', model_context.get_domain_name(),
                                                        model_context.get_domain_home(), wls_version, wlst_mode,
                                                        ae.getLocalizedMessage(), error=ae)
        __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
        raise ex

    __disconnect_domain()
    return model


def _add_domain_name(location, aliases):
    _method_name = '_get_domain_name'
    try:
        wlst_helper.cd('/')
        domain_name = wlst_helper.get(model_constants.DOMAIN_NAME)
    except PyWLSTException, pe:
        de = exception_helper.create_discover_exception('WLSDPLY-06020', pe.getLocalizedMessage())
        __logger.throwing(class_name=_class_name, method_name=_method_name, error=de)
        raise de
    if domain_name is not None:
        location.add_name_token(aliases.get_name_token(location), domain_name)
        __logger.info('WLSDPLY-06022', domain_name, class_name=_class_name, method_name=_method_name)
    else:
        de = exception_helper.create_discover_exception('WLSDPLY-WLSDPLY-06023')
        __logger.throwing(class_name=_class_name, method_name=_method_name, error=de)
        raise de


def __discover_multi_tenant(model, model_context, base_location, aliases):
    """
    Discover the multi-tenant-related parts of the domain, if they exist.
    :param model: the model object to populate
    :param model_context: the model context object
    :raises DiscoverException: if an error occurs during discovery
    """
    MultiTenantDiscoverer(model, model_context, base_location, wlst_mode=__wlst_mode, aliases=aliases).discover()
    return


def __connect_to_domain(model_context):
    """
    Connects WLST to the domain by either connecting to the Admin Server or reading the domain from disk.
    :param model_context: the model context
    :raises DiscoverException: if a WLST error occurs while connecting to or reading the domain
    """
    _method_name = '__connect_to_domain'

    __logger.entering(class_name=_class_name, method_name=_method_name)
    if __wlst_mode == WlstModes.ONLINE:
        try:
            wlst_helper.connect(model_context.get_admin_user(), model_context.get_admin_password(),
                                model_context.get_admin_url())
        except PyWLSTException, wlst_ex:
            ex = exception_helper.create_discover_exception('WLSDPLY-06001', model_context.get_admin_url(),
                                                            model_context.get_admin_user(),
                                                            wlst_ex.getLocalizedMessage(), error=wlst_ex)
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex
    else:
        try:
            wlst_helper.read_domain(model_context.get_domain_home())
        except PyWLSTException, wlst_ex:
            wls_version = WebLogicHelper(__logger).get_actual_weblogic_version()
            ex = exception_helper.create_discover_exception('WLSDPLY-06002', model_context.get_domain_home(),
                                                            wls_version, wlst_ex.getLocalizedMessage(), error=wlst_ex)
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex

    __logger.exiting(class_name=_class_name, method_name=_method_name)
    return


def __clear_archive_file(model_context):
    """
    Remove any binaries already in the archive file.
    :param model_context: the model context
    :raises DiscoverException: if an error occurs while removing the binaries
    """
    _method_name = '__clear_archive_file'
    __logger.entering(class_name=_class_name, method_name=_method_name)

    archive_file = model_context.get_archive_file()

    if archive_file is None:
        de = exception_helper.create_discover_exception('WLSDPLY-06004', model_context.get_archive_file_name())
        __logger.throwing(class_name=_class_name, method_name=_method_name, error=de)
        raise de

    try:
        archive_file.removeAllBinaries()
    except WLSDeployArchiveIOException, wioe:
        de = exception_helper.create_discover_exception('WLSDPLY-06005', wioe.getLocalizedMessage())
        __logger.throwing(class_name=_class_name, method_name=_method_name, error=de)
        raise de

    return


def __close_archive(model_context):
    """
    Close the archive object
    :param model_context: the model context
    """
    _method_name = '__close_archive'

    __logger.entering(_class_name=_class_name, method_name=_method_name)
    archive_file = model_context.get_archive_file()
    archive_file.close()
    __logger.exiting(class_name=_class_name, method_name=_method_name)
    return


def __disconnect_domain():
    """
    Disconnects WLST from the domain by either disconnecting from the Admin Server or closing the domain read from disk.
    :raises DiscoverException: if a WLST error occurred while disconnecting or closing the domain
    """
    _method_name = '__disconnect_domain'

    __logger.entering(class_name=_class_name, method_name=_method_name)
    if __wlst_mode == WlstModes.ONLINE:
        try:
            wlst_helper.disconnect()
        except PyWLSTException, wlst_ex:
            ex = exception_helper.create_discover_exception('WLSDPLY-06006',
                                                            wlst_ex.getLocalizedMessage(), error=wlst_ex)
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex
    else:
        try:
            wlst_helper.close_domain()
        except PyWLSTException, wlst_ex:
            ex = exception_helper.create_discover_exception('WLSDPLY-06007',
                                                            wlst_ex.getLocalizedMessage(), error=wlst_ex)
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex

    __logger.exiting(class_name=_class_name, method_name=_method_name)
    return


def __persist_model(model, model_context):
    """
    Save the model to the specified model file name or to the archive if the file name was not specified.
    :param model: the model to save
    :param model_context: the model context
    :raises DiscoverException: if an error occurs while create a temporary file for the model
                               or while adding it to the archive
    :raises TranslateException: if an error occurs while serializing the model or writing it to disk
    """
    _method_name = '__persist_model'

    __logger.entering(class_name=_class_name, method_name=_method_name)

    add_to_archive = False
    model_file_name = model_context.get_model_file()
    if model_file_name is None:
        add_to_archive = True
        try:
            domain_name = model_context.get_domain_name()
            model_file = File.createTempFile(domain_name, '.yaml').getCanonicalFile()
            model_file_name = model_context.get_domain_name() + '.yaml'
        except (IllegalArgumentException, IOException), ie:
            ex = exception_helper.create_discover_exception('WLSDPLY-06008', ie.getLocalizedMessage(), error=ie)
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex
    else:
        model_file = FileUtils.getCanonicalFile(File(model_file_name))

    try:
        model_translator.PythonToFile(model.get_model()).write_to_file(model_file.getAbsolutePath())
    except TranslateException, ex:
        # Jython 2.2.1 does not support finally so use this like a finally block...
        if add_to_archive and not model_file.delete():
            model_file.deleteOnExit()
        raise ex

    if add_to_archive:
        try:
            archive_file = model_context.get_archive_file()
            archive_file.addModel(model_file, model_file_name)
            if not model_file.delete():
                model_file.deleteOnExit()
        except (WLSDeployArchiveIOException, IllegalArgumentException), arch_ex:
            ex = exception_helper.create_discover_exception('WLSDPLY-20023', model_file.getAbsolutePath(),
                                                            model_file_name, arch_ex.getLocalizedMessage(),
                                                            error=arch_ex)
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            if not model_file.delete():
                model_file.deleteOnExit()
            raise ex

    __logger.exiting(class_name=_class_name, method_name=_method_name)
    return


def __check_and_customize_model(model, model_context, aliases):
    """
    Customize the model dictionary before persisting. Validate the model after customization for informational
    purposes. Any validation errors will not stop the discovered model to be persisted.
    :param model: completely discovered model
    """
    _method_name = '__check_and_customize_model'
    __logger.entering(class_name=_class_name, method_name=_method_name)

    if filter_helper.apply_filters(model.get_model(), "discover"):
        __logger.info('WLSDPLY-06014', _class_name=_class_name, method_name=_method_name)

    inserted, variable_model, variable_file_name = VariableInjector(_program_name, model.get_model(), model_context,
                                                                    WebLogicHelper(
                                                                        __logger).get_actual_weblogic_version()).\
        inject_variables_keyword_file()
    if inserted:
        model = Model(variable_model)
    try:
        validator = Validator(model_context, wlst_mode=__wlst_mode, aliases=aliases)

        # no variables are generated by the discover tool
        validator.validate_in_tool_mode(model.get_model(), variables_file_name=variable_file_name,
                                        archive_file_name=model_context.get_archive_file_name())
    except ValidateException, ex:
        __logger.warning('WLSDPLY-06015', ex.getLocalizedMessage(), class_name=_class_name, method_name=_method_name)
    return model


def __log_and_exit(model_context, exit_code, class_name, method_name):
    """
    Helper method to log the exiting message and call sys.exit()
    :param exit_code: the exit code to use
    :param class_name: the class name to pass  to the logger
    :param method_name: the method name to pass to the logger
    """
    __logger.exiting(result=exit_code, class_name=class_name, method_name=method_name)

    tool_exit.end(model_context, exit_code)


def main(args):
    """
    The main entry point for the discoverDomain tool.

    :param args:
    :return:
    """
    _method_name = 'main'

    __logger.entering(class_name=_class_name, method_name=_method_name)
    for index, arg in enumerate(args):
        __logger.finer('sys.argv[{0}] = {1}', str(index), str(arg), class_name=_class_name, method_name=_method_name)

    wlst_helper.silence()

    exit_code = CommandLineArgUtil.PROG_OK_EXIT_CODE

    model_context = None
    try:
        model_context = __process_args(args)
    except CLAException, ex:
        exit_code = ex.getExitCode()
        if exit_code != CommandLineArgUtil.HELP_EXIT_CODE:
            __logger.severe('WLSDPLY-20008', _program_name, ex.getLocalizedMessage(), error=ex,
                            class_name=_class_name, method_name=_method_name)
        __log_and_exit(None, exit_code, _class_name, _method_name)

    try:
        __clear_archive_file(model_context)
    except DiscoverException, ex:
        __logger.severe('WLSDPLY-06010', _program_name, model_context.get_archive_file_name(),
                        ex.getLocalizedMessage(), error=ex, class_name=_class_name, method_name=_method_name)
        __log_and_exit(model_context, CommandLineArgUtil.PROG_ERROR_EXIT_CODE, _class_name, _method_name)

    aliases = Aliases(model_context, wlst_mode=__wlst_mode)
    model = None
    try:
        model = __discover(model_context, aliases)
    except DiscoverException, ex:
        __logger.severe('WLSDPLY-06011', _program_name, model_context.get_domain_name(),
                        model_context.get_domain_home(), ex.getLocalizedMessage(),
                        error=ex, class_name=_class_name, method_name=_method_name)
        __log_and_exit(model_context, CommandLineArgUtil.PROG_ERROR_EXIT_CODE, _class_name, _method_name)
        
    model = __check_and_customize_model(model, model_context, aliases)
    
    try:
        __persist_model(model, model_context)

    except TranslateException, ex:
        __logger.severe('WLSDPLY-20024', _program_name, model_context.get_archive_file_name(), ex.getLocalizedMessage(),
                        error=ex, class_name=_class_name, method_name=_method_name)
        __log_and_exit(model_context, CommandLineArgUtil.PROG_ERROR_EXIT_CODE, _class_name, _method_name)

    __close_archive(model_context)

    __log_and_exit(model_context, exit_code, _class_name, _method_name)

if __name__ == 'main':
    WebLogicDeployToolingVersion.logVersionInfo(_program_name)
    main(sys.argv)
