"""
Copyright (c) 2017, 2018, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0

The main module for the WLSDeploy tool to create empty domains.
"""
import os
import sys

import java.io.IOException as IOException
import java.lang.IllegalArgumentException as IllegalArgumentException
import java.lang.IllegalStateException as IllegalStateException
import java.lang.String as String

import oracle.weblogic.deploy.create.CreateException as CreateException
import oracle.weblogic.deploy.deploy.DeployException as DeployException
import oracle.weblogic.deploy.util.CLAException as CLAException
import oracle.weblogic.deploy.util.FileUtils as FileUtils
import oracle.weblogic.deploy.util.TranslateException as TranslateException
import oracle.weblogic.deploy.util.VariableException as VariableException
import oracle.weblogic.deploy.util.WLSDeployArchive as WLSDeployArchive
import oracle.weblogic.deploy.util.WLSDeployArchiveIOException as WLSDeployArchiveIOException

sys.path.append(os.path.dirname(os.path.realpath(sys.argv[0])))

# imports from local packages start here
import wlsdeploy.exception.exception_helper as exception_helper
import wlsdeploy.util.getcreds as getcreds
import wlsdeploy.util.variables as variables
import wlsdeploy.util.wlst_helper as wlst_helper
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.create.domain_creator import DomainCreator
from wlsdeploy.tool.create.domain_typedef import DomainTypedef
from wlsdeploy.util.cla_utils import CommandLineArgUtil
from wlsdeploy.util.model_context import ModelContext
from wlsdeploy.util.model_translator import FileToPython

_program_name = 'createDomain'
_class_name = 'create'
__logger = PlatformLogger('wlsdeploy.create')
__wlst_mode = WlstModes.OFFLINE
__tmp_model_dir = None

__required_arguments = [
    CommandLineArgUtil.ORACLE_HOME_SWITCH,
    CommandLineArgUtil.DOMAIN_PARENT_SWITCH,
    CommandLineArgUtil.DOMAIN_TYPE_SWITCH
]

__optional_arguments = [
    CommandLineArgUtil.ARCHIVE_FILE_SWITCH,
    CommandLineArgUtil.JAVA_HOME_SWITCH,
    CommandLineArgUtil.MODEL_FILE_SWITCH,
    CommandLineArgUtil.RUN_RCU_SWITCH,
    CommandLineArgUtil.RCU_SYS_PASS_SWITCH,
    CommandLineArgUtil.RCU_DB_SWITCH,
    CommandLineArgUtil.RCU_PREFIX_SWITCH,
    CommandLineArgUtil.RCU_SCHEMA_PASS_SWITCH,
    CommandLineArgUtil.VARIABLE_FILE_SWITCH,
    CommandLineArgUtil.USE_ENCRYPTION_SWITCH,
    CommandLineArgUtil.PASSPHRASE_SWITCH
]

def __process_args(args):
    """
    Process the command-line arguments and prompt the user for any missing information
    :param args: the command-line arguments list
    :raises CLAException: if an error occurs while validating and processing the command-line arguments
    """
    cla_util = CommandLineArgUtil(_program_name, __required_arguments, __optional_arguments)
    required_arg_map, optional_arg_map = cla_util.process_args(args)

    __verify_required_args_present(required_arg_map)
    __process_java_home_arg(optional_arg_map)
    __process_model_args(optional_arg_map)

    #
    # Verify that the domain type is a known type and load its typedef.
    #
    domain_type = required_arg_map[CommandLineArgUtil.DOMAIN_TYPE_SWITCH]
    domain_typedef = DomainTypedef(_program_name, domain_type)
    optional_arg_map[CommandLineArgUtil.DOMAIN_TYPEDEF] = domain_typedef

    __process_rcu_args(optional_arg_map, domain_type, domain_typedef)
    __process_encryption_args(optional_arg_map)

    combined_arg_map = optional_arg_map.copy()
    combined_arg_map.update(required_arg_map)
    model_context = ModelContext(_program_name, combined_arg_map)
    domain_typedef.set_model_context(model_context)
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
            ex = exception_helper.create_cla_exception('WLSDPLY-12400', _program_name, req_arg)
            ex.setExitCode(CommandLineArgUtil.USAGE_ERROR_EXIT_CODE)
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex
    return

def __process_java_home_arg(optional_arg_map):
    """
    Verify that java_home is set.  If not, set it.
    :param optional_arg_map: the optional arguments map
    :raises CLAException: if the java home argument is not valid
    """
    _method_name = '__process_java_home_arg'

    if CommandLineArgUtil.JAVA_HOME_SWITCH not in optional_arg_map:
        java_home_name = os.environ.get('JAVA_HOME')
        try:
            java_home = FileUtils.validateExistingDirectory(java_home_name)
        except IllegalArgumentException, iae:
            ex = exception_helper.create_cla_exception('WLSDPLY-12401', _program_name, java_home_name,
                                                       iae.getLocalizedMessage(), error=iae)
            ex.setExitCode(CommandLineArgUtil.ARG_VALIDATION_ERROR_EXIT_CODE)
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex
        optional_arg_map[CommandLineArgUtil.JAVA_HOME_SWITCH] = java_home.getAbsolutePath()
    return

def __process_model_args(optional_arg_map):
    """
    Verify that either the model_file or archive_file was provided and exists.
    Extract the model file if only the archive_file was provided.
    :param optional_arg_map: the optional arguments map
    :raises CLAException: if the arguments are invalid or an error occurs extracting the model from the archive
    """
    _method_name = '__process_model_args'
    global __tmp_model_dir

    if CommandLineArgUtil.MODEL_FILE_SWITCH in optional_arg_map:
        model_file_name = optional_arg_map[CommandLineArgUtil.MODEL_FILE_SWITCH]

        try:
            FileUtils.validateExistingFile(model_file_name)
        except IllegalArgumentException, iae:
            ex = exception_helper.create_cla_exception('WLSDPLY-12402', _program_name, model_file_name,
                                                       iae.getLocalizedMessage(), error=iae)
            ex.setExitCode(CommandLineArgUtil.ARG_VALIDATION_ERROR_EXIT_CODE)
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex
    elif CommandLineArgUtil.ARCHIVE_FILE_SWITCH in optional_arg_map:
        archive_file_name = optional_arg_map[CommandLineArgUtil.ARCHIVE_FILE_SWITCH]

        try:
            archive_file = WLSDeployArchive(archive_file_name)
            __tmp_model_dir = FileUtils.createTempDirectory(_program_name)
            tmp_model_file = archive_file.extractModel(__tmp_model_dir)
        except (IllegalArgumentException, IllegalStateException, WLSDeployArchiveIOException), archex:
            ex = exception_helper.create_cla_exception('WLSDPLY-12403', _program_name, archive_file_name,
                                                       archex.getLocalizedMessage(), error=archex)
            ex.setExitCode(CommandLineArgUtil.ARG_VALIDATION_ERROR_EXIT_CODE)
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex
        optional_arg_map[CommandLineArgUtil.MODEL_FILE_SWITCH] = tmp_model_file
    else:
        ex = exception_helper.create_cla_exception('WLSDPLY-12404', _program_name, CommandLineArgUtil.MODEL_FILE_SWITCH,
                                                   CommandLineArgUtil.ARCHIVE_FILE_SWITCH)
        ex.setExitCode(CommandLineArgUtil.USAGE_ERROR_EXIT_CODE)
        __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
        raise ex
    return

def __process_rcu_args(optional_arg_map, domain_type, domain_typedef):
    """
    Determine if the RCU is needed and validate/prompt for any missing information
    :param optional_arg_map: the optional arguments map
    :param domain_type:      the domain type
    :param domain_typedef:   the domain_typedef data structure
    :raises CLAException:    if an error occurs getting the passwords from the user or arguments are missing
    """
    _method_name = '__process_rcu_args'

    rcu_schema_count = len(domain_typedef.get_rcu_schemas())
    run_rcu = False
    if CommandLineArgUtil.RUN_RCU_SWITCH in optional_arg_map:
        run_rcu = optional_arg_map[CommandLineArgUtil.RUN_RCU_SWITCH]
        if rcu_schema_count == 0:
            __logger.info('WLSDPLY-12405', _program_name, CommandLineArgUtil.RUN_RCU_SWITCH, domain_type)
            del optional_arg_map[CommandLineArgUtil.RUN_RCU_SWITCH]
            run_rcu = False
            return

    if rcu_schema_count > 0:
        if CommandLineArgUtil.RCU_DB_SWITCH in optional_arg_map:
            if CommandLineArgUtil.RCU_PREFIX_SWITCH in optional_arg_map:
                if run_rcu and CommandLineArgUtil.RCU_SYS_PASS_SWITCH not in optional_arg_map:
                    try:
                        password = getcreds.getpass('WLSDPLY-12406')
                    except IOException, ioe:
                        ex = exception_helper.create_cla_exception('WLSDPLY-12407', ioe.getLocalizedMessage(),
                                                                   error=ioe)
                        ex.setExitCode(CommandLineArgUtil.ARG_VALIDATION_ERROR_EXIT_CODE)
                        __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
                        raise ex
                    optional_arg_map[CommandLineArgUtil.RCU_SYS_PASS_SWITCH] = String(password)
                if CommandLineArgUtil.RCU_SCHEMA_PASS_SWITCH not in optional_arg_map:
                    try:
                        password = getcreds.getpass('WLSDPLY-12408')
                    except IOException, ioe:
                        ex = exception_helper.create_cla_exception('WLSDPLY-12409', ioe.getLocalizedMessage(),
                                                                   error=ioe)
                        ex.setExitCode(CommandLineArgUtil.ARG_VALIDATION_ERROR_EXIT_CODE)
                        __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
                        raise ex
                    optional_arg_map[CommandLineArgUtil.RCU_SCHEMA_PASS_SWITCH] = String(password)
            else:
                ex = exception_helper.create_cla_exception('WLSDPLY-12410', _program_name,
                                                           CommandLineArgUtil.RCU_DB_SWITCH,
                                                           CommandLineArgUtil.RCU_PREFIX_SWITCH)
                ex.setExitCode(CommandLineArgUtil.USAGE_ERROR_EXIT_CODE)
                __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
                raise ex
        else:
            ex = exception_helper.create_cla_exception('WLSDPLY-12411', domain_type, rcu_schema_count,
                                                       CommandLineArgUtil.RCU_DB_SWITCH,
                                                       CommandLineArgUtil.RCU_PREFIX_SWITCH)
            ex.setExitCode(CommandLineArgUtil.USAGE_ERROR_EXIT_CODE)
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex
    return

def __process_encryption_args(optional_arg_map):
    """
    Determine if the user is using our encryption and if so, get the passphrase.
    :param optional_arg_map: the optional arguments map
    :raises CLAException: if getting the passphrase from the user fails
    """
    _method_name = '__process_encryption_args'

    if CommandLineArgUtil.USE_ENCRYPTION_SWITCH in optional_arg_map and \
            CommandLineArgUtil.PASSPHRASE_SWITCH not in optional_arg_map:
        try:
            passphrase = getcreds.getpass('WLSDPLY-12412')
        except IOException, ioe:
            ex = exception_helper.create_cla_exception('WLSDPLY-12413', ioe.getLocalizedMessage(),
                                                       error=ioe)
            ex.setExitCode(CommandLineArgUtil.ARG_VALIDATION_ERROR_EXIT_CODE)
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex
        optional_arg_map[CommandLineArgUtil.PASSPHRASE_SWITCH] = String(passphrase)
    return

def __clean_up_temp_files():
    """
    If a temporary directory was created to extract the model from the archive, delete the directory and its contents.
    """
    global __tmp_model_dir

    if __tmp_model_dir is not None:
        FileUtils.deleteDirectory(__tmp_model_dir)
        __tmp_model_dir = None

def main():
    """
    The entry point for the create domain tool.
    """
    _method_name = 'main'

    __logger.entering(sys.argv[0], class_name=_class_name, method_name=_method_name)
    for index, arg in enumerate(sys.argv):
        __logger.finer('sys.argv[{0}] = {1}', str(index), str(arg), class_name=_class_name, method_name=_method_name)

    wlst_helper.silence()

    try:
        model_context = __process_args(sys.argv)
    except CLAException, ex:
        exit_code = ex.getExitCode()
        if exit_code != CommandLineArgUtil.HELP_EXIT_CODE:
            __logger.severe('WLSDPLY-12414', _program_name, ex.getLocalizedMessage(), error=ex,
                            class_name=_class_name, method_name=_method_name)
        __clean_up_temp_files()
        sys.exit(exit_code)

    model_file = model_context.get_model_file()
    try:
        model = FileToPython(model_file, True).parse()
    except TranslateException, te:
        __logger.severe('WLSDPLY-03162', _program_name, model_file, te.getLocalizedMessage(), error=te,
                        class_name=_class_name, method_name=_method_name)
        __clean_up_temp_files()
        sys.exit(CommandLineArgUtil.PROG_ERROR_EXIT_CODE)

    if model_context.get_variable_file():
        try:
            variable_map = variables.load_variables(model_context.get_variable_file())
            variables.substitute(model, variable_map)
        except VariableException, ex:
            __logger.severe('WLSDPLY-12416', _program_name, ex.getLocalizedMessage(), error=ex,
                            class_name=_class_name, method_name=_method_name)
            __clean_up_temp_files()
            sys.exit(CommandLineArgUtil.PROG_ERROR_EXIT_CODE)

    try:
        creator = DomainCreator(model, model_context)
        creator.create()
    except CreateException, ex:
        __logger.severe('WLSDPLY-12417', _program_name, ex.getLocalizedMessage(), error=ex,
                        class_name=_class_name, method_name=_method_name)
        __clean_up_temp_files()
        sys.exit(CommandLineArgUtil.PROG_ERROR_EXIT_CODE)
    except DeployException, ex:
        __logger.severe('WLSDPLY-12418', _program_name, ex.getLocalizedMessage(), error=ex,
                        class_name=_class_name, method_name=_method_name)
        __clean_up_temp_files()
        sys.exit(CommandLineArgUtil.PROG_ERROR_EXIT_CODE)

    __clean_up_temp_files()
    return

if __name__ == "main":
    main()
