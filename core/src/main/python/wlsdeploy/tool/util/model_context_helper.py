"""
Copyright (c) 2020, 2023, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
from wlsdeploy.tool.create.domain_typedef import DomainTypedef
from wlsdeploy.util import dictionary_utils
from wlsdeploy.util.cla_utils import CommandLineArgUtil
from wlsdeploy.util.model_context import ModelContext
from wlsdeploy.util import ssh_helper


def create_context(program_name, combined_arg_map, domain_typedef=None, exception_type=None, exit_context=False):
    """
    Create a model context object from the specified argument map, with the domain typedef set up correctly.
    If the domain_typedef is not specified, construct it from the argument map.
    :param program_name: the program name, used for logging
    :param combined_arg_map: all the arguments passed to the program
    :param domain_typedef: a domain typedef object to be used, or None
    :param exception_type: the exception type to add to the ssh_helper
    :param exit_context: whether the model context is being created for use as the exit model_context
    :return: the new model context object
    """
    if domain_typedef is None:
        domain_typedef = create_typedef(program_name, combined_arg_map, exit_context)

    combined_arg_map[CommandLineArgUtil.DOMAIN_TYPEDEF] = domain_typedef
    model_context = ModelContext(program_name, combined_arg_map)
    # domain_typedef.set_model_context(model_context)
    if not exit_context:
        if exception_type is None:
            ssh_helper.initialize_ssh(model_context, combined_arg_map)
        else:
            ssh_helper.initialize_ssh(model_context, combined_arg_map, exception_type)
    return model_context


def create_exit_context(program_name):
    """
    Create a minimal model context for use when a tool exits due to command-line parsing errors.
    This will provide some of the values needed for the summary logging.
    :param program_name: the program name, used for logging
    :return: the new, minimal model context object
    """
    # Oracle home switch is required for typedef template token resolution, for older WLS versions.
    return create_context(program_name, {CommandLineArgUtil.ORACLE_HOME_SWITCH: ""}, exit_context=True)


def create_typedef(program_name, argument_map, exit_context=False):
    """
    Create a domain typedef object for use with a model context.
    :param program_name: the program name, used for logging
    :param argument_map: the argument map that may contain a domain type
    :param exit_context: whether the typedef is being created only for an exit model_context.
    :return: a typedef object
    """
    domain_type = dictionary_utils.get_element(argument_map, CommandLineArgUtil.DOMAIN_TYPE_SWITCH)
    if domain_type is None:
        domain_type = 'WLS'
    return DomainTypedef(program_name, domain_type, exit_context=exit_context)
