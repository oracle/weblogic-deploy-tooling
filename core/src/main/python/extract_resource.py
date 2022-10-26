"""
Copyright (c) 2020, 2022, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.

The entry point for the extractDomainResource tool.
"""
import sys

from oracle.weblogic.deploy.deploy import DeployException

# Jython tools don't require sys.path modification

# imports from local packages start here
from wlsdeploy.aliases.aliases import Aliases
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception import exception_helper
from wlsdeploy.exception.expection_types import ExceptionType
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.extract.domain_resource_extractor import DomainResourceExtractor
from wlsdeploy.tool.util import model_context_helper
from wlsdeploy.util import cla_helper
from wlsdeploy.util import tool_main
from wlsdeploy.util import validate_configuration
from wlsdeploy.util.cla_utils import CommandLineArgUtil
from wlsdeploy.util.cla_utils import TOOL_TYPE_EXTRACT
from wlsdeploy.util.exit_code import ExitCode
from wlsdeploy.util.model import Model
from wlsdeploy.util.weblogic_helper import WebLogicHelper

_program_name = 'extractDomainResource'
_class_name = 'extract_resource'
__logger = PlatformLogger('wlsdeploy.extract')
__wls_helper = WebLogicHelper(__logger)
__wlst_mode = WlstModes.OFFLINE

__required_arguments = [
    CommandLineArgUtil.ORACLE_HOME_SWITCH
]

__optional_arguments = [
    # Used by shell script to locate WLST
    CommandLineArgUtil.DOMAIN_TYPE_SWITCH,
    CommandLineArgUtil.DOMAIN_HOME_SWITCH,
    CommandLineArgUtil.ARCHIVE_FILE_SWITCH,
    CommandLineArgUtil.MODEL_FILE_SWITCH,
    CommandLineArgUtil.TARGET_SWITCH,
    CommandLineArgUtil.VARIABLE_FILE_SWITCH,
    CommandLineArgUtil.USE_ENCRYPTION_SWITCH,
    CommandLineArgUtil.PASSPHRASE_SWITCH,
    CommandLineArgUtil.PASSPHRASE_FILE_SWITCH,
    CommandLineArgUtil.PASSPHRASE_ENV_SWITCH,
    CommandLineArgUtil.OUTPUT_DIR_SWITCH,  # move to __required_arguments once DOMAIN_RESOURCE_FILE_SWITCH is removed
    CommandLineArgUtil.DOMAIN_RESOURCE_FILE_SWITCH  # deprecated, only this program uses it
]


def __process_args(args):
    """
    Process the command-line arguments and prompt the user for any missing information
    :param args: the command-line arguments list
    :raises CLAException: if an error occurs while validating and processing the command-line arguments
    """
    _method_name = '__process_args'

    # if no target type was specified, use wko
    if CommandLineArgUtil.TARGET_SWITCH not in args:
        args.append(CommandLineArgUtil.TARGET_SWITCH)
        args.append('wko')

    cla_util = CommandLineArgUtil(_program_name, __required_arguments, __optional_arguments)
    cla_util.set_allow_multiple_models(True)
    argument_map = cla_util.process_args(args, TOOL_TYPE_EXTRACT)

    cla_helper.validate_optional_archive(_program_name, argument_map)

    # determine if the model file was passed separately or requires extraction from the archive.
    cla_helper.validate_model_present(_program_name, argument_map)
    cla_helper.validate_variable_file_exists(_program_name, argument_map)
    cla_helper.process_encryption_args(argument_map)

    # allow unresolved tokens and archive entries
    argument_map[CommandLineArgUtil.VALIDATION_METHOD] = validate_configuration.LAX_METHOD

    # warn about deprecated -domain_resource_file argument.
    # not needed once -domain_resource_file is removed and -output_dir moves to __required_arguments.
    if CommandLineArgUtil.DOMAIN_RESOURCE_FILE_SWITCH in argument_map:
        __logger.warning('WLSDPLY-10040', CommandLineArgUtil.DOMAIN_RESOURCE_FILE_SWITCH,
                         CommandLineArgUtil.OUTPUT_DIR_SWITCH, class_name=_class_name, method_name=_method_name)
    elif CommandLineArgUtil.OUTPUT_DIR_SWITCH not in argument_map:
        ex = exception_helper.create_cla_exception(ExitCode.USAGE_ERROR, 'WLSDPLY-20005',
                                                   _program_name, CommandLineArgUtil.OUTPUT_DIR_SWITCH,
                                                   class_name=_class_name, method_name=_method_name)
        __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
        raise ex

    return model_context_helper.create_context(_program_name, argument_map)


def __extract_resource(model, model_context, aliases):
    """
    Offline deployment orchestration
    :param model: the model
    :param model_context: the model context
    :param aliases: the aliases object
    :raises: DeployException: if an error occurs
    """
    _method_name = '__extract_resource'

    resource_extractor = DomainResourceExtractor(model, model_context, aliases, __logger)
    resource_extractor.extract()
    return 0


def main(model_context):
    """
    The python entry point for extractDomainResource.
    :param model_context: the model context object
    """
    _method_name = 'main'
    __logger.entering(class_name=_class_name, method_name=_method_name)

    _exit_code = ExitCode.OK

    try:
        aliases = Aliases(model_context, wlst_mode=__wlst_mode, exception_type=ExceptionType.DEPLOY)
        model_dictionary = cla_helper.load_model(_program_name, model_context, aliases, "extract", __wlst_mode)
        model = Model(model_dictionary)
        _exit_code = __extract_resource(model, model_context, aliases)
    except DeployException, ex:
        _exit_code = ExitCode.ERROR
        __logger.severe('WLSDPLY-09015', _program_name, ex.getLocalizedMessage(), error=ex,
                        class_name=_class_name, method_name=_method_name)

    __logger.exiting(class_name=_class_name, method_name=_method_name, result=_exit_code)
    return _exit_code


if __name__ == '__main__' or __name__ == 'main':
    tool_main.run_tool(main, __process_args, sys.argv, _program_name, _class_name, __logger)
