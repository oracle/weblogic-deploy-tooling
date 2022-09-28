"""
Copyright (c) 2017, 2022, Oracle Corporation and/or its affiliates.  All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.

The main module for the WLSDeploy tool to encrypt passwords.
"""
import exceptions
import sys

from java.io import IOException
from java.lang import String, System

from oracle.weblogic.deploy.encrypt import EncryptionException
from oracle.weblogic.deploy.util import CLAException
from oracle.weblogic.deploy.util import TranslateException
from oracle.weblogic.deploy.util import VariableException

# Jython tools don't require sys.path modification

# imports from local packages start here
from wlsdeploy.aliases.aliases import Aliases
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception import exception_helper
from wlsdeploy.exception.expection_types import ExceptionType
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.encrypt import encryption_utils
from wlsdeploy.util import cla_utils
from wlsdeploy.util import getcreds
from wlsdeploy.util import tool_main
from wlsdeploy.util import variables as variable_helper
from wlsdeploy.util.cla_utils import CommandLineArgUtil
from wlsdeploy.util.exit_code import ExitCode
from wlsdeploy.util.model_context import ModelContext
from wlsdeploy.util.model_translator import FileToPython
from wlsdeploy.util.model_translator import PythonToFile

_program_name = 'encryptModel'
_class_name = 'encrypt'
__logger = PlatformLogger('wlsdeploy.encrypt')

__required_arguments = [
    CommandLineArgUtil.ORACLE_HOME_SWITCH,
]

__optional_arguments = [
    CommandLineArgUtil.DOMAIN_TYPE_SWITCH,
    CommandLineArgUtil.MODEL_FILE_SWITCH,
    CommandLineArgUtil.VARIABLE_FILE_SWITCH,
    CommandLineArgUtil.PASSPHRASE_SWITCH,
    CommandLineArgUtil.PASSPHRASE_FILE_SWITCH,
    CommandLineArgUtil.PASSPHRASE_ENV_SWITCH,
    CommandLineArgUtil.ENCRYPT_MANUAL_SWITCH,
    CommandLineArgUtil.ONE_PASS_SWITCH
]


def __process_args(args):
    """
    Process the command-line arguments and prompt the user for any missing information
    :param args: the command-line arguments list
    :raises CLAException: if an error occurs while validating and processing the command-line arguments
    """
    _method_name = '__process_args'

    cla_util = CommandLineArgUtil(_program_name, __required_arguments, __optional_arguments)
    cla_util.set_allow_multiple_models(True)
    argument_map = cla_util.process_args(args)

    __validate_mode_args(argument_map)
    __process_passphrase_arg(argument_map)

    #
    # Prompt for the password to encrypt if the -manual switch was specified
    #
    if CommandLineArgUtil.ENCRYPT_MANUAL_SWITCH in argument_map and \
            CommandLineArgUtil.ONE_PASS_SWITCH not in argument_map:
        try:
            pwd = getcreds.getpass('WLSDPLY-04200')
        except IOException, ioe:
            ex = exception_helper.create_encryption_exception('WLSDPLY-04201', ioe.getLocalizedMessage(), error=ioe)
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex
        argument_map[CommandLineArgUtil.ONE_PASS_SWITCH] = String(pwd)

    model_context = ModelContext(_program_name, argument_map)
    return model_context


def __validate_mode_args(optional_arg_map):
    """
    Verify that either the model_file or the manual switch was specified.
    :param optional_arg_map: the optional arguments map
    :raises CLAException: if the arguments are not valid
    """
    _method_name = '__validate_mode_args'

    if CommandLineArgUtil.MODEL_FILE_SWITCH not in optional_arg_map \
            and CommandLineArgUtil.ENCRYPT_MANUAL_SWITCH not in optional_arg_map:
        ex = exception_helper.create_cla_exception(ExitCode.USAGE_ERROR,
                                                   'WLSDPLY-04202', _program_name, CommandLineArgUtil.MODEL_FILE_SWITCH,
                                                   CommandLineArgUtil.ENCRYPT_MANUAL_SWITCH)
        __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
        raise ex


def __process_passphrase_arg(optional_arg_map):
    """
    Prompt for the passphrase.
    :param optional_arg_map: the optional arguments map
    :raises CLAException: if an error occurs reading the passphrase input from the user
    """
    _method_name = '__process_passphrase_arg'

    if CommandLineArgUtil.PASSPHRASE_SWITCH not in optional_arg_map:
        got_matching_passphrases = False
        while not got_matching_passphrases:
            try:
                passphrase = getcreds.getpass('WLSDPLY-04203')
                passphrase2 = getcreds.getpass('WLSDPLY-04204')
            except IOException, ioe:
                ex = exception_helper.create_encryption_exception('WLSDPLY-04205', ioe.getLocalizedMessage(), error=ioe)
                __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
                raise ex

            if passphrase == passphrase2:
                got_matching_passphrases = True
                optional_arg_map[CommandLineArgUtil.PASSPHRASE_SWITCH] = String(passphrase)
            else:
                # if it is script mode do not prompt again
                if System.console() is None:
                    ex = exception_helper.create_cla_exception(ExitCode.ERROR, 'WLSDPLY-04213')
                    __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
                    raise ex


def __encrypt_model_and_variables(model_context):
    """
    Encrypt the model and variables file, if provided.
    :param model_context: the model context object containing the processed command-line arguments
    :return: the exit code that should be used to exit the program
    """
    _method_name = '__encrypt_model_and_variables'

    model_files = cla_utils.get_model_files(model_context.get_model_file())
    models = dict()
    for model_file in model_files:
        try:
            models[model_file] = FileToPython(model_file, True).parse()
        except TranslateException, te:
            __logger.severe('WLSDPLY-04206', _program_name, model_file, te.getLocalizedMessage(), error=te,
                            class_name=_class_name, method_name=_method_name)
            return ExitCode.ERROR

    variable_file = model_context.get_variable_file()
    variables = None
    if variable_file is not None:
        try:
            variables = variable_helper.load_variables(variable_file)
        except VariableException, ve:
            __logger.severe('WLSDPLY-04207', _program_name, variable_file, ve.getLocalizedMessage(), error=ve,
                            class_name=_class_name, method_name=_method_name)
            return ExitCode.ERROR

    aliases = Aliases(model_context, wlst_mode=WlstModes.OFFLINE, exception_type=ExceptionType.ENCRYPTION)

    for model_file, model in models.iteritems():
        try:
            passphrase = model_context.get_encryption_passphrase()
            model_change_count, variable_change_count = \
                encryption_utils.encrypt_model_dictionary(passphrase, model, aliases, variables)
        except EncryptionException, ee:
            __logger.severe('WLSDPLY-04208', _program_name, ee.getLocalizedMessage(), error=ee,
                            class_name=_class_name, method_name=_method_name)
            return ExitCode.ERROR

        if variable_change_count > 0:
            try:
                variable_helper.write_variables(_program_name, variables, variable_file)
                __logger.info('WLSDPLY-04209', _program_name, variable_change_count, variable_file,
                              class_name=_class_name, method_name=_method_name)
            except VariableException, ve:
                __logger.severe('WLSDPLY-20007', _program_name, variable_file, ve.getLocalizedMessage(), error=ve,
                                class_name=_class_name, method_name=_method_name)
                return ExitCode.ERROR

        if model_change_count > 0:
            try:
                model_writer = PythonToFile(model)
                model_writer.write_to_file(model_file)
                __logger.info('WLSDPLY-04210', _program_name, model_change_count, model_file,
                              class_name=_class_name, method_name=_method_name)
            except TranslateException, te:
                __logger.severe('WLSDPLY-04211', _program_name, model_file, te.getLocalizedMessage(), error=te,
                                class_name=_class_name, method_name=_method_name)
                return ExitCode.ERROR

    return ExitCode.OK


#  Factored out for unit testing...
def _process_request(args, model_context=None):
    """
    Performs the work for the encryptModel tool.

    :param args: the command-line arguments list
    :return: the exit code that should be used to exit the program
    """
    _method_name = '_process_request'

    __logger.entering(args[0], class_name=_class_name, method_name=_method_name)
    if model_context is None:
        try:
            model_context = __process_args(args)
        except CLAException, ex:
            exit_code = ex.getExitCode()
            if exit_code != ExitCode.HELP:
                __logger.severe('WLSDPLY-20008', _program_name, ex.getLocalizedMessage(), error=ex,
                                class_name=_class_name, method_name=_method_name)
            __logger.exiting(class_name=_class_name, method_name=_method_name, result=exit_code)
            return exit_code

    if model_context.is_encryption_manual():
        try:
            passphrase = model_context.get_encryption_passphrase()
            encrypted_password = encryption_utils.encrypt_one_password(passphrase, model_context.get_encrypt_one_pass())
            print ""
            print encrypted_password
            exit_code = ExitCode.OK
        except EncryptionException, ee:
            exit_code = ExitCode.ERROR
            __logger.severe('WLSDPLY-04212', _program_name, ee.getLocalizedMessage(), error=ee,
                            class_name=_class_name, method_name=_method_name)
    else:
        exit_code = __encrypt_model_and_variables(model_context)

    __logger.exiting(class_name=_class_name, method_name=_method_name, result=exit_code)
    return exit_code


def main(model_context):
    """
    The main entry point for the encryptModel tool.

    :param model_context:
    :return:
    """
    _method_name = 'main'
    __logger.entering(sys.argv[0], class_name=_class_name, method_name=_method_name)

    exit_code = _process_request(sys.argv, model_context=model_context)

    __logger.exiting(class_name=_class_name, method_name=_method_name, result=exit_code)
    return exit_code


if __name__ == '__main__' or __name__ == 'main':
    tool_main.run_tool(main, __process_args, sys.argv, _program_name, _class_name, __logger)
