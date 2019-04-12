"""
Copyright (c) 2017, 2019, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0

The main module for the WLSDeploy tool to encrypt passwords.
"""
import javaos as os
import sys

from java.io import IOException
from java.lang import IllegalArgumentException
from java.lang import String

from oracle.weblogic.deploy.encrypt import EncryptionException
from oracle.weblogic.deploy.util import CLAException
from oracle.weblogic.deploy.util import FileUtils
from oracle.weblogic.deploy.util import TranslateException
from oracle.weblogic.deploy.util import VariableException
from oracle.weblogic.deploy.util import WebLogicDeployToolingVersion

sys.path.append(os.path.dirname(os.path.realpath(sys.argv[0])))

# imports from local packages start here
from wlsdeploy.aliases.aliases import Aliases
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception import exception_helper
from wlsdeploy.exception.expection_types import ExceptionType
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.encrypt import encryption_utils
from wlsdeploy.tool.util.alias_helper import AliasHelper
from wlsdeploy.util import getcreds
from wlsdeploy.util import variables as variable_helper
from wlsdeploy.util import wlst_helper
from wlsdeploy.util.cla_utils import CommandLineArgUtil
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
    required_arg_map, optional_arg_map = cla_util.process_args(args)

    __verify_required_args_present(required_arg_map)
    __validate_mode_args(optional_arg_map)
    __process_passphrase_arg(optional_arg_map)

    #
    # Prompt for the password to encrypt if the -manual switch was specified
    #
    if CommandLineArgUtil.ENCRYPT_MANUAL_SWITCH in optional_arg_map and \
            CommandLineArgUtil.ONE_PASS_SWITCH not in optional_arg_map:
        try:
            pwd = getcreds.getpass('WLSDPLY-04200')
        except IOException, ioe:
            ex = exception_helper.create_encryption_exception('WLSDPLY-04201', ioe.getLocalizedMessage(), error=ioe)
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex
        optional_arg_map[CommandLineArgUtil.ONE_PASS_SWITCH] = String(pwd)

    combined_arg_map = optional_arg_map.copy()
    combined_arg_map.update(required_arg_map)
    model_context = ModelContext(_program_name, combined_arg_map)
    return model_context


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


def __validate_mode_args(optional_arg_map):
    """
    Verify that either the model_file or the manual switch was specified.
    :param optional_arg_map: the optional arguments map
    :raises CLAException: if the arguments are not valid
    """
    _method_name = '__validate_mode_args'

    if CommandLineArgUtil.MODEL_FILE_SWITCH in optional_arg_map:
        model_file_name = optional_arg_map[CommandLineArgUtil.MODEL_FILE_SWITCH]
        try:
            FileUtils.validateExistingFile(model_file_name)
        except IllegalArgumentException, iae:
            ex = exception_helper.create_cla_exception('WLSDPLY-20006', _program_name, model_file_name,
                                                       iae.getLocalizedMessage(), error=iae)
            ex.setExitCode(CommandLineArgUtil.ARG_VALIDATION_ERROR_EXIT_CODE)
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex
    elif CommandLineArgUtil.ENCRYPT_MANUAL_SWITCH not in optional_arg_map:
        ex = exception_helper.create_cla_exception('WLSDPLY-04202', _program_name, CommandLineArgUtil.MODEL_FILE_SWITCH,
                                                   CommandLineArgUtil.ENCRYPT_MANUAL_SWITCH)
        ex.setExitCode(CommandLineArgUtil.USAGE_ERROR_EXIT_CODE)
        __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
        raise ex
    return


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
    return


def __encrypt_model_and_variables(model_context):
    """
    Encrypt the model and variables file, if provided.
    :param model_context: the model context object containing the processed command-line arguments
    :return: the exit code that should be used to exit the program
    """
    _method_name = '__encrypt_model_and_variables'

    model_file = model_context.get_model_file()
    try:
        model = FileToPython(model_file, True).parse()
    except TranslateException, te:
        __logger.severe('WLSDPLY-04206', _program_name, model_file, te.getLocalizedMessage(), error=te,
                        class_name=_class_name, method_name=_method_name)
        return CommandLineArgUtil.PROG_ERROR_EXIT_CODE

    variable_file = model_context.get_variable_file()
    variables = None
    if variable_file is not None:
        try:
            variables = variable_helper.load_variables(variable_file)
        except VariableException, ve:
            __logger.severe('WLSDPLY-04207', _program_name, variable_file, ve.getLocalizedMessage(), error=ve,
                            class_name=_class_name, method_name=_method_name)
            return CommandLineArgUtil.PROG_ERROR_EXIT_CODE

    aliases = Aliases(model_context, wlst_mode=WlstModes.OFFLINE)
    alias_helper = AliasHelper(aliases, __logger, ExceptionType.ENCRYPTION)

    try:
        passphrase = model_context.get_encryption_passphrase()
        model_change_count, variable_change_count = \
            encryption_utils.encrypt_model_dictionary(passphrase, model, alias_helper, variables)
    except EncryptionException, ee:
        __logger.severe('WLSDPLY-04208', _program_name, ee.getLocalizedMessage(), error=ee,
                        class_name=_class_name, method_name=_method_name)
        return CommandLineArgUtil.PROG_ERROR_EXIT_CODE

    if variable_change_count > 0:
        try:
            variable_helper.write_variables(_program_name, variables, variable_file)
            __logger.info('WLSDPLY-04209', _program_name, variable_change_count, variable_file,
                          class_name=_class_name, method_name=_method_name)
        except VariableException, ve:
            __logger.severe('WLSDPLY-20007', _program_name, variable_file, ve.getLocalizedMessage(), error=ve,
                            class_name=_class_name, method_name=_method_name)
            return CommandLineArgUtil.PROG_ERROR_EXIT_CODE

    if model_change_count > 0:
        try:
            model_writer = PythonToFile(model)
            model_writer.write_to_file(model_file)
            __logger.info('WLSDPLY-04210', _program_name, model_change_count, model_file,
                          class_name=_class_name, method_name=_method_name)
        except TranslateException, te:
            __logger.severe('WLSDPLY-04211', _program_name, model_file, te.getLocalizedMessage(), error=te,
                            class_name=_class_name, method_name=_method_name)
            return CommandLineArgUtil.PROG_ERROR_EXIT_CODE

    return CommandLineArgUtil.PROG_OK_EXIT_CODE


#  Factored out for unit testing...
def _process_request(args):
    """
    Performs the work for the encryptModel tool.

    :param args: the command-line arguments list
    :return: the exit code that should be used to exit the program
    """
    _method_name = '_process_request'

    __logger.entering(args[0], class_name=_class_name, method_name=_method_name)
    try:
        model_context = __process_args(args)
    except CLAException, ex:
        exit_code = ex.getExitCode()
        if exit_code != CommandLineArgUtil.HELP_EXIT_CODE:
            __logger.severe('WLSDPLY-20008', _program_name, ex.getLocalizedMessage(), error=ex,
                            class_name=_class_name, method_name=_method_name)
        return exit_code

    if model_context.is_encryption_manual():
        try:
            passphrase = model_context.get_encryption_passphrase()
            encrypted_password = encryption_utils.encrypt_one_password(passphrase, model_context.get_encrypt_one_pass())
            print ""
            print encrypted_password
            exit_code = CommandLineArgUtil.PROG_OK_EXIT_CODE
        except EncryptionException, ee:
            exit_code = CommandLineArgUtil.PROG_ERROR_EXIT_CODE
            __logger.severe('WLSDPLY-04212', _program_name, ee.getLocalizedMessage(), error=ee,
                            class_name=_class_name, method_name=_method_name)
    else:
        exit_code = __encrypt_model_and_variables(model_context)

    __logger.exiting(class_name=_class_name, method_name=_method_name, result=exit_code)
    return exit_code


def main(args):
    """
    The main entry point for the encryptModel tool.

    :param args:
    :return:
    """
    _method_name = 'main'

    __logger.entering(args[0], class_name=_class_name, method_name=_method_name)
    for index, arg in enumerate(args):
        __logger.finer('sys.argv[{0}] = {1}', str(index), str(arg), class_name=_class_name, method_name=_method_name)

    wlst_helper.silence()
    exit_code = _process_request(args)
    __logger.exiting(class_name=_class_name, method_name=_method_name, result=exit_code)
    sys.exit(exit_code)


if __name__ == "main":
    WebLogicDeployToolingVersion.logVersionInfo(_program_name)
    main(sys.argv)
