"""
Copyright (c) 2017, 2022, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.

The WLS Deploy tooling entry point for the validateModel tool.
"""
import copy
import sys

from java.util.logging import Level

from oracle.weblogic.deploy.logging import WLSDeployLogEndHandler
from oracle.weblogic.deploy.util import CLAException
from oracle.weblogic.deploy.util import TranslateException
from oracle.weblogic.deploy.util import VariableException
from oracle.weblogic.deploy.validate import ValidateException

# Jython tools don't require sys.path modification

# imports from local packages start here
from wlsdeploy.aliases.aliases import Aliases
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception import exception_helper
from wlsdeploy.exception.expection_types import ExceptionType
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.util import filter_helper
from wlsdeploy.tool.util import model_context_helper
from wlsdeploy.tool.validate.validator import Validator
from wlsdeploy.util import cla_helper
from wlsdeploy.util import dictionary_utils
from wlsdeploy.util import tool_main
from wlsdeploy.util import validate_configuration
from wlsdeploy.util import variables
from wlsdeploy.util.cla_utils import CommandLineArgUtil
from wlsdeploy.util.exit_code import ExitCode
from wlsdeploy.util.weblogic_helper import WebLogicHelper


_program_name = 'validateModel'
_class_name = 'validate'
__logger = PlatformLogger('wlsdeploy.validate')
__wls_helper = WebLogicHelper(__logger)
__wlst_mode = WlstModes.OFFLINE

__required_arguments = [
    CommandLineArgUtil.ORACLE_HOME_SWITCH
]

__optional_arguments = [
    CommandLineArgUtil.DOMAIN_TYPE_SWITCH,  # Used by shell script to locate WLST
    CommandLineArgUtil.MODEL_FILE_SWITCH,
    CommandLineArgUtil.ARCHIVE_FILE_SWITCH,
    CommandLineArgUtil.VARIABLE_FILE_SWITCH,
    CommandLineArgUtil.TARGET_SWITCH,
    CommandLineArgUtil.TARGET_VERSION_SWITCH,
    CommandLineArgUtil.TARGET_MODE_SWITCH,
    CommandLineArgUtil.VALIDATION_METHOD
]


def __process_args(args):
    """
    Process the command-line arguments and prompt the user for any missing information
    :param args: the command-line arguments list
    :raises CLAException: if an error occurs while validating and processing the command-line arguments
    """
    cla_util = CommandLineArgUtil(_program_name, __required_arguments, __optional_arguments)
    cla_util.set_allow_multiple_models(True)
    argument_map = cla_util.process_args(args)

    __process_model_args(argument_map)

    return model_context_helper.create_context(_program_name, argument_map)


def __process_model_args(argument_map):
    """
    Determine if the model file was passed separately or requires extraction from the archive.
    :param argument_map: the arguments map
    :raises CLAException: if the arguments were not valid or an error occurred extracting the model from the archive
    """
    _method_name = '__process_model_args'

    cla_helper.validate_optional_archive(_program_name, argument_map)

    try:
        cla_helper.validate_model_present(_program_name, argument_map)
    except CLAException, ce:
        # in lax validation mode, if no model is found, log at INFO and exit
        method = dictionary_utils.get_element(argument_map, CommandLineArgUtil.VALIDATION_METHOD)
        if method == validate_configuration.LAX_METHOD:
            __logger.info('WLSDPLY-20032', _program_name, class_name=_class_name, method_name=_method_name)
            ex = exception_helper.create_cla_exception(ExitCode.OK, 'WLSDPLY-20032', _program_name)
            raise ex
        raise ce


def __perform_model_file_validation(model_file_name, model_context):
    """

    :param model_file_name:
    :param model_context:
    :return:
    :raises ValidationException:
    """

    _method_name = '__perform_model_file_validation'

    __logger.entering(model_file_name,
                      class_name=_class_name, method_name=_method_name)

    try:
        wlst_mode = model_context.get_target_wlst_mode()
        aliases = Aliases(model_context=model_context, wlst_mode=wlst_mode, exception_type=ExceptionType.VALIDATE)
        model_validator = Validator(model_context, aliases, logger=__logger)
        variable_map = model_validator.load_variables(model_context.get_variable_file())
        model_dictionary = cla_helper.merge_model_files(model_file_name, variable_map)

        if cla_helper.check_persist_model():
            persist_model_dict = copy.deepcopy(model_dictionary)
            variables.substitute(persist_model_dict, variable_map, model_context)
            cla_helper.persist_model(model_context, persist_model_dict)

        model_validator.validate_in_standalone_mode(model_dictionary, variable_map,
                                                    model_context.get_archive_file_name())

        # substitute variables before filtering
        variables.substitute(model_dictionary, variable_map, model_context)
        # apply filters to merged model
        if filter_helper.apply_filters(model_dictionary, "validate", model_context):
            # persist model after filtering
            cla_helper.persist_model(model_context, model_dictionary)

            # validate model changes after filtering
            model_validator.validate_in_standalone_mode(model_dictionary, variable_map,
                                                        model_context.get_archive_file_name())

    except (TranslateException, VariableException), te:
        ex = exception_helper.create_validate_exception(te.getLocalizedMessage(), error=te)
        __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
        raise ex

    __logger.exiting(class_name=_class_name, method_name=_method_name)


def main(model_context):
    """
    The main entry point for the validateModel tool.

    :param model_context: the model context object
    :return: exit code
    """
    _method_name = 'main'
    __logger.entering(class_name=_class_name, method_name=_method_name)

    _exit_code = ExitCode.OK
    model_file_name = model_context.get_model_file()

    try:
        if model_file_name is not None:
            __perform_model_file_validation(model_file_name, model_context)

            summary_handler = WLSDeployLogEndHandler.getSummaryHandler()
            if summary_handler is not None:
                summary_level = summary_handler.getMaximumMessageLevel()
                if summary_level == Level.SEVERE:
                    _exit_code = ExitCode.ERROR
                elif summary_level == Level.WARNING:
                    _exit_code = ExitCode.WARNING

    except ValidateException, ve:
        _exit_code = ExitCode.ERROR
        __logger.severe('WLSDPLY-20000', _program_name, ve.getLocalizedMessage(), error=ve,
                        class_name=_class_name, method_name=_method_name)

    __logger.exiting(class_name=_class_name, method_name=_method_name, result=_exit_code)
    return _exit_code


if __name__ == '__main__' or __name__ == 'main':
    tool_main.run_tool(main, __process_args, sys.argv, _program_name, _class_name, __logger)
