"""
Copyright (c) 2017, 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at https://oss.oracle.com/licenses/upl.

The main module for the WLSDeploy tool to create empty domains.
"""
import os
import sys

from java.io import IOException
from java.lang import IllegalArgumentException
from java.lang import String
from oracle.weblogic.deploy.create import CreateException
from oracle.weblogic.deploy.deploy import DeployException
from oracle.weblogic.deploy.util import FileUtils
from oracle.weblogic.deploy.util import WLSDeployArchiveIOException
from oracle.weblogic.deploy.validate import ValidateException

sys.path.insert(0, os.path.dirname(os.path.realpath(sys.argv[0])))

# imports from local packages start here
from wlsdeploy.aliases.aliases import Aliases
from wlsdeploy.aliases.model_constants import DEFAULT_WLS_DOMAIN_NAME
from wlsdeploy.aliases.model_constants import DOMAIN_NAME
from wlsdeploy.aliases.model_constants import TOPOLOGY
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception import exception_helper
from wlsdeploy.exception.exception_types import ExceptionType
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.create.domain_creator import DomainCreator
from wlsdeploy.tool.util import model_context_helper
from wlsdeploy.tool.util.archive_helper import ArchiveList
from wlsdeploy.tool.util.wlst_helper import WlstHelper
from wlsdeploy.tool.util import wlst_helper
from wlsdeploy.tool.validate.create_content_validator import CreateDomainContentValidator
from wlsdeploy.util import cla_helper
from wlsdeploy.util import env_helper
from wlsdeploy.util import getcreds
from wlsdeploy.util import tool_main
from wlsdeploy.util.cla_utils import CommandLineArgUtil
from wlsdeploy.util.cla_utils import TOOL_TYPE_CREATE
from wlsdeploy.util.exit_code import ExitCode

wlst_helper.wlst_functions = globals()

_program_name = 'createDomain'

_class_name = 'create'
__logger = PlatformLogger('wlsdeploy.create')
__wlst_mode = WlstModes.OFFLINE

__required_arguments = [
    CommandLineArgUtil.MODEL_FILE_SWITCH,
    CommandLineArgUtil.ORACLE_HOME_SWITCH
]

__optional_arguments = [
    CommandLineArgUtil.ARCHIVE_FILE_SWITCH,
    CommandLineArgUtil.DOMAIN_HOME_SWITCH,
    CommandLineArgUtil.DOMAIN_PARENT_SWITCH,
    CommandLineArgUtil.DOMAIN_TYPE_SWITCH,
    CommandLineArgUtil.JAVA_HOME_SWITCH,
    CommandLineArgUtil.RUN_RCU_SWITCH,
    CommandLineArgUtil.VARIABLE_FILE_SWITCH,
    CommandLineArgUtil.PASSPHRASE_SWITCH,
    CommandLineArgUtil.PASSPHRASE_ENV_SWITCH,
    CommandLineArgUtil.PASSPHRASE_FILE_SWITCH,
    CommandLineArgUtil.OPSS_WALLET_SWITCH,
    CommandLineArgUtil.OPSS_WALLET_PASSPHRASE_SWITCH,
    CommandLineArgUtil.OPSS_WALLET_PASSPHRASE_FILE_SWITCH,
    CommandLineArgUtil.OPSS_WALLET_PASSPHRASE_ENV_SWITCH,
    CommandLineArgUtil.UPDATE_RCU_SCHEMA_PASS_SWITCH,
    CommandLineArgUtil.PASSPHRASE_PROMPT_SWITCH,
    # deprecated in 4.2.0
    CommandLineArgUtil.USE_ENCRYPTION_SWITCH
]


def __process_args(args, is_encryption_supported):
    """
    Process the command-line arguments and prompt the user for any missing information
    :param args: the command-line arguments list
    :param is_encryption_supported: whether WDT encryption is supported by the JVM
    :raises CLAException: if an error occurs while validating and processing the command-line arguments
    """
    cla_util = CommandLineArgUtil(_program_name, __required_arguments, __optional_arguments)
    cla_util.set_allow_multiple_models(True)
    argument_map = cla_util.process_args(args, TOOL_TYPE_CREATE)
    __process_java_home_arg(argument_map)
    __process_domain_location_args(argument_map)

    # don't verify that the archive is valid until it is needed.
    # this requirement is specific to create, other tools will verify it.
    cla_helper.validate_required_model(_program_name, argument_map)
    cla_helper.validate_variable_file_exists(_program_name, argument_map)

    #
    # Verify that the domain type is a known type and load its typedef.
    #
    domain_typedef = model_context_helper.create_typedef(_program_name, argument_map)

    __process_rcu_args(argument_map, domain_typedef.get_domain_type(), domain_typedef)
    cla_helper.process_encryption_args(argument_map, is_encryption_supported)
    __process_opss_args(argument_map)

    return model_context_helper.create_context(_program_name, argument_map, domain_typedef)


def __process_java_home_arg(optional_arg_map):
    """
    Verify that java_home is set.  If not, set it.
    :param optional_arg_map: the optional arguments map
    :raises CLAException: if the java home argument is not valid
    """
    _method_name = '__process_java_home_arg'

    if CommandLineArgUtil.JAVA_HOME_SWITCH not in optional_arg_map:
        java_home_name = env_helper.getenv('JAVA_HOME')
        try:
            java_home = FileUtils.validateExistingDirectory(java_home_name)
        except IllegalArgumentException, iae:
            ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR,
                                                       'WLSDPLY-12400', _program_name, java_home_name,
                                                       iae.getLocalizedMessage(), error=iae)
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex
        optional_arg_map[CommandLineArgUtil.JAVA_HOME_SWITCH] = java_home.getAbsolutePath()


def __process_domain_location_args(optional_arg_map):
    """
    Verify that either the domain_home or domain_parent was specified, and not both.
    Their values were already checked in the process_args call.
    :param optional_arg_map: the optional arguments map
    :raises CLAException: if the arguments are invalid or an error occurs extracting the model from the archive
    """
    _method_name = '__process_domain_location_args'

    has_home = CommandLineArgUtil.DOMAIN_HOME_SWITCH in optional_arg_map
    has_parent = CommandLineArgUtil.DOMAIN_PARENT_SWITCH in optional_arg_map

    if (has_home and has_parent) or (not has_home and not has_parent):
        ex = exception_helper.create_cla_exception(ExitCode.USAGE_ERROR,
                                                   'WLSDPLY-20025', _program_name,
                                                   CommandLineArgUtil.DOMAIN_PARENT_SWITCH,
                                                   CommandLineArgUtil.DOMAIN_HOME_SWITCH)
        __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
        raise ex


def __process_rcu_args(optional_arg_map, domain_type, domain_typedef):
    """
    Determine if the RCU is needed and validate/prompt for any missing information
    :param optional_arg_map: the optional arguments map
    :param domain_type:      the domain type
    :param domain_typedef:   the domain_typedef data structure
    """
    _method_name = '__process_rcu_args'

    rcu_schema_count = len(domain_typedef.get_rcu_schemas())
    if CommandLineArgUtil.RUN_RCU_SWITCH in optional_arg_map:
        if rcu_schema_count == 0:
            __logger.info('WLSDPLY-12402', _program_name, CommandLineArgUtil.RUN_RCU_SWITCH, domain_type)
            del optional_arg_map[CommandLineArgUtil.RUN_RCU_SWITCH]
            return


def __process_opss_args(optional_arg_map):
    """
    Determine if the user is using opss wallet and if so, get the passphrase.
    :param optional_arg_map: the optional arguments map
    :raises CLAException: if getting the passphrase from the user fails
    """
    _method_name = '__process_opss_args'

    if CommandLineArgUtil.OPSS_WALLET_SWITCH in optional_arg_map and \
            CommandLineArgUtil.OPSS_WALLET_PASSPHRASE_SWITCH not in optional_arg_map:
        try:
            passphrase = getcreds.getpass('WLSDPLY-20027')
        except IOException, ioe:
            ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR,
                                                       'WLSDPLY-20028', ioe.getLocalizedMessage(), error=ioe)
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex
        optional_arg_map[CommandLineArgUtil.OPSS_WALLET_PASSPHRASE_SWITCH] = str(String(passphrase))


def _get_domain_path(model_context, model):
    """
    Returns the domain home path.
    :param model_context: the model context
    :param model: the model
    :return: the domain path
    """
    domain_parent = model_context.get_domain_parent_dir()
    if domain_parent is None:
        return model_context.get_domain_home()
    elif TOPOLOGY in model and DOMAIN_NAME in model[TOPOLOGY]:
        return domain_parent + os.sep + model[TOPOLOGY][DOMAIN_NAME]
    else:
        return domain_parent + os.sep + DEFAULT_WLS_DOMAIN_NAME


def main(model_context):
    """
    The entry point for the createDomain tool.

    :param model_context: The model_context object
    :return: exit code
    """
    _method_name = 'main'
    __logger.entering(class_name=_class_name, method_name=_method_name)

    WlstHelper(ExceptionType.CREATE).silence()
    _exit_code = ExitCode.OK

    try:
        aliases = Aliases(model_context, wlst_mode=__wlst_mode, exception_type=ExceptionType.CREATE)
        model_dictionary = cla_helper.load_model(_program_name, model_context, aliases, "create", __wlst_mode,
                                                 validate_crd_sections=False)

        # set domain home result in model context, for use by deployers and helpers
        model_context.set_domain_home(_get_domain_path(model_context, model_dictionary))

        archive_helper = None
        archive_file_name = model_context.get_archive_file_name()
        if archive_file_name:
            archive_helper = ArchiveList(archive_file_name, model_context, ExceptionType.CREATE)

        # check for any content problems in the merged, substituted model
        content_validator = CreateDomainContentValidator(model_context, archive_helper, aliases)
        content_validator.validate_model(model_dictionary)

        if archive_helper:
            domain_path = _get_domain_path(model_context, model_dictionary)
            if not os.path.exists(os.path.abspath(domain_path)):
                os.mkdir(os.path.abspath(domain_path))

            archive_helper.extract_all_database_wallets()
            archive_helper.extract_custom_directory()
            archive_helper.extract_weblogic_remote_console_extension()

        creator = DomainCreator(model_dictionary, model_context, aliases)
        creator.create()

    except WLSDeployArchiveIOException, ex:
        _exit_code = ExitCode.ERROR
        __logger.severe('WLSDPLY-12409', _program_name, ex.getLocalizedMessage(), error=ex,
                        class_name=_class_name, method_name=_method_name)
    except ValidateException, ex:
        _exit_code = ExitCode.ERROR
        __logger.severe('WLSDPLY-12409', _program_name, ex.getLocalizedMessage(), error=ex,
                        class_name=_class_name, method_name=_method_name)
    except CreateException, ex:
        _exit_code = ExitCode.ERROR
        __logger.severe('WLSDPLY-12409', _program_name, ex.getLocalizedMessage(), error=ex,
                        class_name=_class_name, method_name=_method_name)
    except IOException, ex:
        _exit_code = ExitCode.ERROR
        __logger.severe('WLSDPLY-12409', _program_name, ex.getLocalizedMessage(), error=ex,
                        class_name=_class_name, method_name=_method_name)
    except DeployException, ex:
        _exit_code = ExitCode.ERROR
        __logger.severe('WLSDPLY-12410', _program_name, ex.getLocalizedMessage(), error=ex,
                        class_name=_class_name, method_name=_method_name)

    __logger.exiting(class_name=_class_name, method_name=_method_name, result=_exit_code)
    return _exit_code


if __name__ == '__main__' or __name__ == 'main':
    tool_main.run_tool(main, __process_args, sys.argv, _program_name, _class_name, __logger)
