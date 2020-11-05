"""
Copyright (c) 2017, 2020, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.

The entry point for the discoverDomain tool.
"""
import os
import sys

from java.io import File
from java.io import IOException
from java.lang import IllegalArgumentException
from java.lang import IllegalStateException
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

sys.path.insert(0, os.path.dirname(os.path.realpath(sys.argv[0])))

from wlsdeploy.aliases import model_constants
from wlsdeploy.aliases.aliases import Aliases
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception import exception_helper
from wlsdeploy.exception.expection_types import ExceptionType
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.discover import discoverer
from wlsdeploy.tool.discover.deployments_discoverer import DeploymentsDiscoverer
from wlsdeploy.tool.discover.domain_info_discoverer import DomainInfoDiscoverer
from wlsdeploy.tool.discover.multi_tenant_discoverer import MultiTenantDiscoverer
from wlsdeploy.tool.discover.resources_discoverer import ResourcesDiscoverer
from wlsdeploy.tool.discover.topology_discoverer import TopologyDiscoverer
from wlsdeploy.tool.util import filter_helper
from wlsdeploy.tool.util import model_context_helper
from wlsdeploy.tool.util.credential_injector import CredentialInjector
from wlsdeploy.tool.util.variable_injector import VariableInjector
from wlsdeploy.tool.util import wlst_helper
from wlsdeploy.tool.util.wlst_helper import WlstHelper
from wlsdeploy.tool.validate.validator import Validator
from wlsdeploy.util import cla_helper
from wlsdeploy.util import model_translator
from wlsdeploy.util import path_utils
from wlsdeploy.util import tool_exit
from wlsdeploy.util.cla_utils import CommandLineArgUtil
from wlsdeploy.util.model import Model
from wlsdeploy.util.weblogic_helper import WebLogicHelper
from wlsdeploy.util import target_configuration_helper

wlst_helper.wlst_functions = globals()

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
    CommandLineArgUtil.JAVA_HOME_SWITCH,
    CommandLineArgUtil.VARIABLE_FILE_SWITCH,
    CommandLineArgUtil.ADMIN_URL_SWITCH,
    CommandLineArgUtil.ADMIN_USER_SWITCH,
    CommandLineArgUtil.ADMIN_PASS_SWITCH,
    CommandLineArgUtil.TARGET_MODE_SWITCH,
    CommandLineArgUtil.OUTPUT_DIR_SWITCH,
    CommandLineArgUtil.TARGET_SWITCH
]


def __process_args(args):
    """
    Process the command-line arguments and prompt the user for any missing information
    :param args: the command-line arguments list
    :raises CLAException: if an error occurs while validating and processing the command-line arguments
    """
    global __wlst_mode

    cla_util = CommandLineArgUtil(_program_name, __required_arguments, __optional_arguments)
    argument_map = cla_util.process_args(args)

    __wlst_mode = cla_helper.process_online_args(argument_map)
    target_configuration_helper.process_target_arguments(argument_map)
    __process_archive_filename_arg(argument_map)
    __process_variable_filename_arg(argument_map)
    __process_java_home(argument_map)

    return model_context_helper.create_context(_program_name, argument_map)


def __process_archive_filename_arg(required_arg_map):
    """
    Validate the archive file name and load the archive file object.
    :param required_arg_map: the required arguments map
    :raises CLAException: if a validation error occurs while loading the archive file object
    """
    _method_name = '__process_archive_filename_arg'

    archive_file_name = required_arg_map[CommandLineArgUtil.ARCHIVE_FILE_SWITCH]
    archive_dir_name = path_utils.get_parent_directory(archive_file_name)
    if os.path.exists(archive_dir_name) is False:
        ex = exception_helper.create_cla_exception('WLSDPLY-06026', archive_file_name)
        __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
        raise ex
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

    if CommandLineArgUtil.VARIABLE_FILE_SWITCH in optional_arg_map:
        variable_injector_file_name = optional_arg_map[CommandLineArgUtil.VARIABLE_FILE_SWITCH]
        try:
            FileUtils.validateWritableFile(variable_injector_file_name)
        except IllegalArgumentException, ie:
            ex = exception_helper.create_cla_exception('WLSDPLY-06021', optional_arg_map[
                CommandLineArgUtil.VARIABLE_FILE_SWITCH], variable_injector_file_name,
                                                       ie.getLocalizedMessage(), error=ie)
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex
    return


def __process_java_home(optional_arg_map):
    _method_name = '__process_java_home'
    if CommandLineArgUtil.JAVA_HOME_SWITCH in optional_arg_map:
        java_home_name = optional_arg_map[CommandLineArgUtil.JAVA_HOME_SWITCH]
    else:
        java_home_name = os.environ.get('JAVA_HOME')

    try:
        FileUtils.validateExistingDirectory(java_home_name)
    except IllegalArgumentException, iae:
        # this value is used for java home global token in attributes.
        # If this was passed as command line, it might no longer exist.
        # The JAVA_HOME environment variable was validated by script.
        __logger.info('WLSDPLY-06027', java_home_name, iae.getLocalizedMessage(),
                      class_name=_class_name, method_name=_method_name)


def __discover(model_context, aliases, credential_injector, helper):
    """
    Populate the model from the domain.
    :param model_context: the model context
    :param aliases: aliases instance for discover
    :param credential_injector: credential injector instance
    :param helper: wlst_helper instance
    :return: the fully-populated model
    :raises DiscoverException: if an error occurred while discover the domain
    """
    _method_name = '__discover'
    model = Model()
    base_location = LocationContext()
    __connect_to_domain(model_context, helper)
    try:
        _add_domain_name(base_location, aliases, helper)
        DomainInfoDiscoverer(model_context, model.get_model_domain_info(), base_location, wlst_mode=__wlst_mode,
                             aliases=aliases, credential_injector=credential_injector).discover()
        TopologyDiscoverer(model_context, model.get_model_topology(), base_location, wlst_mode=__wlst_mode,
                           aliases=aliases, credential_injector=credential_injector).discover()
        ResourcesDiscoverer(model_context, model.get_model_resources(), base_location, wlst_mode=__wlst_mode,
                            aliases=aliases, credential_injector=credential_injector).discover()
        DeploymentsDiscoverer(model_context, model.get_model_app_deployments(), base_location, wlst_mode=__wlst_mode,
                              aliases=aliases, credential_injector=credential_injector).discover()
        __discover_multi_tenant(model, model_context, base_location, aliases, credential_injector)
    except AliasException, ae:
        wls_version = WebLogicHelper(__logger).get_actual_weblogic_version()
        wlst_mode = WlstModes.from_value(__wlst_mode)
        ex = exception_helper.create_discover_exception('WLSDPLY-06000', model_context.get_domain_name(),
                                                        model_context.get_domain_home(), wls_version, wlst_mode,
                                                        ae.getLocalizedMessage(), error=ae)
        __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
        raise ex

    __disconnect_domain(helper)
    return model


def _add_domain_name(location, aliases, helper):
    _method_name = '_get_domain_name'
    try:
        helper.cd('/')
        domain_name = helper.get(model_constants.DOMAIN_NAME)
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


def __discover_multi_tenant(model, model_context, base_location, aliases, injector):
    """
    Discover the multi-tenant-related parts of the domain, if they exist.
    :param model: the model object to populate
    :param model_context: the model context object
    :raises DiscoverException: if an error occurs during discovery
    """
    MultiTenantDiscoverer(model, model_context, base_location,
                          wlst_mode=__wlst_mode, aliases=aliases, credential_injector=injector).discover()
    return


def __connect_to_domain(model_context, helper):
    """
    Connects WLST to the domain by either connecting to the Admin Server or reading the domain from disk.
    :param model_context: the model context
    :param helper: wlst helper instance
    :raises DiscoverException: if a WLST error occurs while connecting to or reading the domain
    """
    _method_name = '__connect_to_domain'

    __logger.entering(class_name=_class_name, method_name=_method_name)
    if __wlst_mode == WlstModes.ONLINE:
        try:
            helper.connect(model_context.get_admin_user(), model_context.get_admin_password(),
                           model_context.get_admin_url(), model_context.get_model_config().get_connect_timeout())
        except PyWLSTException, wlst_ex:
            ex = exception_helper.create_discover_exception('WLSDPLY-06001', model_context.get_admin_url(),
                                                            model_context.get_admin_user(),
                                                            wlst_ex.getLocalizedMessage(), error=wlst_ex)
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex
    else:
        try:
            helper.read_domain(model_context.get_domain_home())
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


def __disconnect_domain(helper):
    """
    Disconnects WLST from the domain by either disconnecting from the Admin Server or closing the domain read from disk.
    :param helper: wlst_helper instance
    :raises DiscoverException: if a WLST error occurred while disconnecting or closing the domain
    """
    _method_name = '__disconnect_domain'

    __logger.entering(class_name=_class_name, method_name=_method_name)
    if __wlst_mode == WlstModes.ONLINE:
        try:
            helper.disconnect()
        except PyWLSTException, wlst_ex:
            ex = exception_helper.create_discover_exception('WLSDPLY-06006',
                                                            wlst_ex.getLocalizedMessage(), error=wlst_ex)
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex
    else:
        try:
            helper.close_domain()
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


def __check_and_customize_model(model, model_context, aliases, credential_injector):
    """
    Customize the model dictionary before persisting. Validate the model after customization for informational
    purposes. Any validation errors will not stop the discovered model to be persisted.
    :param model: completely discovered model, before any tokenization
    :param model_context: configuration from command-line
    :param aliases: used for validation if model changes are made
    :param credential_injector: injector created to collect and tokenize credentials, possibly None
    """
    _method_name = '__check_and_customize_model'
    __logger.entering(class_name=_class_name, method_name=_method_name)

    if filter_helper.apply_filters(model.get_model(), "discover", model_context):
        __logger.info('WLSDPLY-06014', _class_name=_class_name, method_name=_method_name)

    # target config always present in model context, default config if not declared
    target_configuration = model_context.get_target_configuration()

    # if target config declared, use the validation method it contains (lax, etc.)
    if model_context.is_targetted_config():
        validation_method = target_configuration.get_validation_method()
        model_context.set_validation_method(validation_method)

    credential_cache = None
    if credential_injector is not None:
        # filter variables or secrets that are no longer in the model
        credential_injector.filter_unused_credentials(model.get_model())

        credential_cache = credential_injector.get_variable_cache()

        # Generate k8s create secret script
        if target_configuration.uses_credential_secrets():
            target_configuration_helper.generate_k8s_script(model_context, credential_cache, model.get_model())

        # create additional output after filtering, but before variables have been inserted
        if model_context.is_targetted_config():
            target_configuration_helper.create_additional_output(model, model_context, aliases, credential_injector,
                                                                 ExceptionType.DISCOVER)

        # if target handles credential configuration, clear property cache to keep out of variables file.
        if model_context.get_target_configuration().manages_credentials():
            credential_cache.clear()

    # Apply the injectors specified in model_variable_injector.json, or in the target configuration.
    # Include the variable mappings that were collected in credential_cache.
    variable_injector = VariableInjector(_program_name, model.get_model(), model_context,
                                         WebLogicHelper(__logger).get_actual_weblogic_version(), credential_cache)

    inserted, variable_model, variable_file_name = variable_injector.inject_variables_keyword_file()

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

    helper = WlstHelper(ExceptionType.DISCOVER)
    helper.silence()

    exit_code = CommandLineArgUtil.PROG_OK_EXIT_CODE

    try:
        model_context = __process_args(args)
    except CLAException, ex:
        exit_code = ex.getExitCode()
        if exit_code != CommandLineArgUtil.HELP_EXIT_CODE:
            __logger.severe('WLSDPLY-20008', _program_name, ex.getLocalizedMessage(), error=ex,
                            class_name=_class_name, method_name=_method_name)

        # create a minimal model for summary logging
        model_context = model_context_helper.create_exit_context(_program_name)
        __log_and_exit(model_context, exit_code, _class_name, _method_name)

    try:
        __clear_archive_file(model_context)
    except DiscoverException, ex:
        __logger.severe('WLSDPLY-06010', _program_name, model_context.get_archive_file_name(),
                        ex.getLocalizedMessage(), error=ex, class_name=_class_name, method_name=_method_name)
        __log_and_exit(model_context, CommandLineArgUtil.PROG_ERROR_EXIT_CODE, _class_name, _method_name)

    aliases = Aliases(model_context, wlst_mode=__wlst_mode, exception_type=ExceptionType.DISCOVER)
    model = None
    credential_injector = None
    if model_context.get_variable_file() is not None:
        credential_injector = CredentialInjector(_program_name, dict(), model_context,
                                                 WebLogicHelper(__logger).get_actual_weblogic_version())

        __logger.info('WLSDPLY-06025', class_name=_class_name, method_name=_method_name)
    else:
        __logger.info('WLSDPLY-06024', class_name=_class_name, method_name=_method_name)

    try:
        model = __discover(model_context, aliases, credential_injector, helper)

        model = __check_and_customize_model(model, model_context, aliases, credential_injector)

    except DiscoverException, ex:
        __logger.severe('WLSDPLY-06011', _program_name, model_context.get_domain_name(),
                        model_context.get_domain_home(), ex.getLocalizedMessage(),
                        error=ex, class_name=_class_name, method_name=_method_name)
        __log_and_exit(model_context, CommandLineArgUtil.PROG_ERROR_EXIT_CODE, _class_name, _method_name)

    try:
        __persist_model(model, model_context)

    except TranslateException, ex:
        __logger.severe('WLSDPLY-20024', _program_name, model_context.get_archive_file_name(), ex.getLocalizedMessage(),
                        error=ex, class_name=_class_name, method_name=_method_name)
        __log_and_exit(model_context, CommandLineArgUtil.PROG_ERROR_EXIT_CODE, _class_name, _method_name)

    __close_archive(model_context)

    __log_and_exit(model_context, exit_code, _class_name, _method_name)


if __name__ == '__main__' or __name__ == 'main':
    WebLogicDeployToolingVersion.logVersionInfo(_program_name)
    main(sys.argv)
