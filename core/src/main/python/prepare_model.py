# Copyright (c) 2020, 2022, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
#
# ------------
# Description:
# ------------
#
#   This code prepare a list of models for deploying to WebLogic Kubernetes Operator Environment.

import sys

from oracle.weblogic.deploy.prepare import PrepareException
from oracle.weblogic.deploy.util import CLAException
from oracle.weblogic.deploy.util import PyWLSTException

from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.prepare.model_preparer import ModelPreparer
from wlsdeploy.util import target_configuration_helper
from wlsdeploy.util import tool_main
from wlsdeploy.util.cla_utils import CommandLineArgUtil
from wlsdeploy.util.exit_code import ExitCode
from wlsdeploy.util.model_context import ModelContext

_program_name = 'prepareModel'
_class_name = 'prepare_model'
__logger = PlatformLogger('wlsdeploy.prepare_model')

__required_arguments = [
    CommandLineArgUtil.ORACLE_HOME_SWITCH,
    CommandLineArgUtil.MODEL_FILE_SWITCH,
    CommandLineArgUtil.OUTPUT_DIR_SWITCH,
    CommandLineArgUtil.TARGET_SWITCH
]

__optional_arguments = [
    CommandLineArgUtil.VARIABLE_FILE_SWITCH,
    CommandLineArgUtil.ARCHIVE_FILE_SWITCH
]


def __process_args(args):
    """
    Process the command-line arguments.
    :param args: the command-line arguments list
    :raises CLAException: if an error occurs while validating and processing the command-line arguments
    """
    _method_name = '__process_args'

    cla_util = CommandLineArgUtil(_program_name, __required_arguments, __optional_arguments)
    cla_util.set_allow_multiple_models(True)
    argument_map = cla_util.process_args(args)

    target_configuration_helper.process_target_arguments(argument_map)

    model_context = ModelContext(_program_name, argument_map)
    if model_context.get_archive_file_name() is None:
        # override this check, if archive file is not supplied
        model_context.get_validate_configuration().set_allow_unresolved_archive_references(True)
    return model_context


def main(model_context):
    """
    The main entry point for the modelHelp tool.
    :param model_context: the model context object
    """
    _method_name = 'main'
    __logger.entering(class_name=_class_name, method_name=_method_name)

    _exit_code = ExitCode.OK
    _output_dir = None

    try:
        _output_dir = model_context.get_output_dir()
        model_files = model_context.get_model_file()

        obj = ModelPreparer(model_files, model_context, _output_dir)
        obj.prepare_models()
    except CLAException, ex:
        _exit_code = ex.getExitCode()
        __logger.severe('WLSDPLY-20008', _program_name, ex.getLocalizedMessage(), error=ex,
                        class_name=_class_name, method_name=_method_name)
    except (PrepareException, PyWLSTException), ex:
        _exit_code = ExitCode.ERROR
        __logger.severe('WLSDPLY-05801', ex.getLocalizedMessage(), error=ex, class_name=_class_name,
                        method_name=_method_name)

    __logger.exiting(class_name=_class_name, method_name=_method_name, result=_exit_code)
    return _exit_code


if __name__ == "__main__" or __name__ == 'main':
    tool_main.run_tool(main, __process_args, sys.argv, _program_name, _class_name, __logger)
