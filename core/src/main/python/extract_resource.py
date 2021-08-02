"""
Copyright (c) 2020, 2021, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.

The entry point for the extractDomainResource tool.
"""
import sys

from oracle.weblogic.deploy.deploy import DeployException
from oracle.weblogic.deploy.util import CLAException
from oracle.weblogic.deploy.util import WebLogicDeployToolingVersion

# Jython tools don't require sys.path modification

# imports from local packages start here
from wlsdeploy.aliases.aliases import Aliases
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.extract.domain_resource_extractor import DomainResourceExtractor
from wlsdeploy.tool.util import model_context_helper
from wlsdeploy.util import cla_helper
from wlsdeploy.util import tool_exit
from wlsdeploy.util.cla_utils import CommandLineArgUtil
from wlsdeploy.util.cla_utils import TOOL_TYPE_EXTRACT
from wlsdeploy.util.model import Model
from wlsdeploy.util.weblogic_helper import WebLogicHelper

_program_name = 'extractDomainResource'
_class_name = 'extract_resource'
__logger = PlatformLogger('wlsdeploy.extract')
__wls_helper = WebLogicHelper(__logger)
__wlst_mode = WlstModes.OFFLINE

__required_arguments = [
    CommandLineArgUtil.ORACLE_HOME_SWITCH,
    CommandLineArgUtil.DOMAIN_HOME_SWITCH,
    CommandLineArgUtil.DOMAIN_RESOURCE_FILE_SWITCH
]

__optional_arguments = [
    # Used by shell script to locate WLST
    CommandLineArgUtil.DOMAIN_TYPE_SWITCH,
    CommandLineArgUtil.ARCHIVE_FILE_SWITCH,
    CommandLineArgUtil.MODEL_FILE_SWITCH,
    CommandLineArgUtil.VARIABLE_FILE_SWITCH,
    CommandLineArgUtil.USE_ENCRYPTION_SWITCH,
    CommandLineArgUtil.PASSPHRASE_SWITCH,
]


def __process_args(args):
    """
    Process the command-line arguments and prompt the user for any missing information
    :param args: the command-line arguments list
    :raises CLAException: if an error occurs while validating and processing the command-line arguments
    """
    cla_util = CommandLineArgUtil(_program_name, __required_arguments, __optional_arguments)
    cla_util.set_allow_multiple_models(True)
    argument_map = cla_util.process_args(args, TOOL_TYPE_EXTRACT)

    cla_helper.validate_optional_archive(_program_name, argument_map)

    # determine if the model file was passed separately or requires extraction from the archive.
    cla_helper.validate_model_present(_program_name, argument_map)
    cla_helper.validate_variable_file_exists(_program_name, argument_map)
    cla_helper.process_encryption_args(argument_map)

    argument_map[CommandLineArgUtil.VALIDATION_METHOD] = CommandLineArgUtil.LAX_VALIDATION_METHOD
    model_context = model_context_helper.create_context(_program_name, argument_map)
    model_context.set_ignore_missing_archive_entries(True)
    return model_context


def __extract_resource(model, model_context):
    """
    Offline deployment orchestration
    :param model: the model
    :param model_context: the model context
    :raises: DeployException: if an error occurs
    """
    _method_name = '__extract_resource'

    resource_extractor = DomainResourceExtractor(model, model_context, __logger)
    resource_extractor.extract()
    return 0


def main(args):
    """
    The python entry point for extractDomainResource.
    :param args: the command-line arguments
    """
    _method_name = 'main'

    __logger.entering(args[0], class_name=_class_name, method_name=_method_name)
    for index, arg in enumerate(args):
        __logger.finer('sys.argv[{0}] = {1}', str(index), str(arg), class_name=_class_name, method_name=_method_name)

    exit_code = CommandLineArgUtil.PROG_OK_EXIT_CODE

    try:
        model_context = __process_args(args)
    except CLAException, ex:
        exit_code = ex.getExitCode()
        if exit_code != CommandLineArgUtil.HELP_EXIT_CODE:
            __logger.severe('WLSDPLY-20008', _program_name, ex.getLocalizedMessage(), error=ex,
                            class_name=_class_name, method_name=_method_name)
        cla_helper.clean_up_temp_files()

        # create a minimal model for summary logging
        model_context = model_context_helper.create_exit_context(_program_name)
        tool_exit.end(model_context, exit_code)

    aliases = Aliases(model_context, wlst_mode=__wlst_mode)

    model_dictionary = cla_helper.load_model(_program_name, model_context, aliases, "extract", __wlst_mode)

    try:
        model = Model(model_dictionary)
        exit_code = __extract_resource(model, model_context)
    except DeployException, ex:
        __logger.severe('WLSDPLY-09015', _program_name, ex.getLocalizedMessage(), error=ex,
                        class_name=_class_name, method_name=_method_name)
        cla_helper.clean_up_temp_files()
        tool_exit.end(model_context, CommandLineArgUtil.PROG_ERROR_EXIT_CODE)

    cla_helper.clean_up_temp_files()

    tool_exit.end(model_context, exit_code)
    return


if __name__ == '__main__' or __name__ == 'main':
    WebLogicDeployToolingVersion.logVersionInfo(_program_name)
    main(sys.argv)
