"""
Copyright (c) 2017, 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import sys
import traceback

from java.lang import Throwable as JThrowable

import oracle.weblogic.deploy.aliases.AliasException as AliasException
import oracle.weblogic.deploy.compare.CompareException as CompareException
import oracle.weblogic.deploy.create.CreateException as CreateException
import oracle.weblogic.deploy.deploy.DeployException as DeployException
import oracle.weblogic.deploy.discover.DiscoverException as DiscoverException
import oracle.weblogic.deploy.encrypt.EncryptionException as JEncryptionException
import oracle.weblogic.deploy.exception.ExceptionHelper as ExceptionHelper
import oracle.weblogic.deploy.exception.PyAttributeErrorException as PyAttributeErrorException
import oracle.weblogic.deploy.exception.PyBaseException as PyBaseException
import oracle.weblogic.deploy.exception.PyIOErrorException as PyIOErrorException
import oracle.weblogic.deploy.exception.PyKeyErrorException as PyKeyErrorException
import oracle.weblogic.deploy.exception.PyTypeErrorException as PyTypeErrorException
import oracle.weblogic.deploy.exception.PyValueErrorException as PyValueErrorException
import oracle.weblogic.deploy.json.JsonException as JJsonException
import oracle.weblogic.deploy.prepare.PrepareException as PrepareException
import oracle.weblogic.deploy.util.CLAException as JCLAException
import oracle.weblogic.deploy.util.PyWLSTException as PyWLSTException
import oracle.weblogic.deploy.util.SSHException as SSHException
import oracle.weblogic.deploy.util.TranslateException as JTranslateException
import oracle.weblogic.deploy.util.VariableException as JVariableException
import oracle.weblogic.deploy.util.WLSDeployArchiveIOException as JWLSDeployArchiveIOException
import oracle.weblogic.deploy.validate.ValidateException as ValidateException
import oracle.weblogic.deploy.yaml.YamlException as JYamlException

from wlsdeploy.exception.exception_types import ExceptionType
from wlsdeploy.util import unicode_helper as str_helper
from wlsdeploy.util.exit_code import ExitCode

_EXCEPTION_TYPE_MAP = {
    ExceptionType.ALIAS:                 'create_alias_exception',
    ExceptionType.CLA:                   '_create_cla_type_exception',
    ExceptionType.COMPARE:               'create_compare_exception',
    ExceptionType.CREATE:                'create_create_exception',
    ExceptionType.DEPLOY:                'create_deploy_exception',
    ExceptionType.DISCOVER:              'create_discover_exception',
    ExceptionType.ENCRYPTION:            'create_encryption_exception',
    ExceptionType.JSON:                  'create_json_exception',
    ExceptionType.PREPARE:               'create_prepare_exception',
    ExceptionType.PY_WLST:               'create_pywlst_exception',
    ExceptionType.SSH:                   'create_ssh_exception',
    ExceptionType.TRANSLATE:             'create_translate_exception',
    ExceptionType.VALIDATE:              'create_validate_exception',
    ExceptionType.VARIABLE:              'create_variable_exception',
    ExceptionType.WLS_DEPLOY_ARCHIVE_IO: 'create_archive_ioexception',
    ExceptionType.YAML:                  'create_yaml_exception'
}

_PROGRAM_NAME_TO_EXCEPTION_TYPE_MAP = {
    'compareModel':          ExceptionType.COMPARE,
    'createDomain':          ExceptionType.CREATE,
    'deployApps':            ExceptionType.DEPLOY,
    'discoverDomain':        ExceptionType.DISCOVER,
    'encryptModel':          ExceptionType.ENCRYPTION,
    'extractDomainResource': ExceptionType.DEPLOY,
    'injectVariables':       ExceptionType.TRANSLATE,
    'modelHelp':             ExceptionType.CLA,
    'prepareModel':          ExceptionType.PREPARE,
    'updateDomain':          ExceptionType.DEPLOY,
    'validateModel':         ExceptionType.VALIDATE,
    'verifySSH':             ExceptionType.SSH
}


def get_exception_type_from_program_name(program_name):
    if program_name in _PROGRAM_NAME_TO_EXCEPTION_TYPE_MAP:
        exception_type = _PROGRAM_NAME_TO_EXCEPTION_TYPE_MAP[program_name]
    else:
        raise TypeError(str_helper.to_string('Unknown program name: %s' % program_name))
    return exception_type

def get_exception_class(exception_type):
    ex = create_exception(exception_type, 'Find the class')
    return ex.getClass()


def create_exception(exception_type, key, *args, **kwargs):
    """
    Create an exception of the specified type.
    :param exception_type: the exception type
    :param key: key to the message in resource bundler or the message itself
    :param args: list of parameters for the parameters or empty if none needed for the message
    :param kwargs: contains Throwable or instance if present
    :return: BundleAwareException: an exception of the specified type which is a subclass of BundleAwareException
    """
    if exception_type in _EXCEPTION_TYPE_MAP:
        method_name = _EXCEPTION_TYPE_MAP[exception_type]
    else:
        raise TypeError(str_helper.to_string('Unknown exception type: ') + str_helper.to_string(exception_type))

    return globals()[method_name](key, *args, **kwargs)


def get_message(key, *args):
    """
    Get the formatted message from the resource bundle.

    :param key: the message key
    :param args: the token values
    :return: the formatted message string
    """
    return ExceptionHelper.getMessage(key, list(args))


def create_create_exception(key, *args, **kwargs):
    """
    Create a CreateException from a message id, list of message parameters and Throwable error.
    :param key: key to the message in resource bundler or the message itself
    :param args: list of parameters for the parameters or empty if none needed for the message
    :param kwargs: contains Throwable or instance if present
    :return: CreateException encapsulating the exception information
    """
    arg_list, error = _return_exception_params(*args, **kwargs)
    arg_len = len(arg_list)
    if error is not None:
        if not isinstance(error, JThrowable):
            error = convert_error_to_exception()
        if arg_len > 0:
            # Jython 2.7.1 in 14.1.1 is broken when it comes to binding varargs
            # Java methods.  Calling the CreateException(key, error, arg_list) is
            # binding to the CreateException(String key, Object... params) constructor
            # instead of CreateException(String key, Throwable cause, Object...params).
            #
            ex = CreateException(key, arg_list)
            ex.initCause(error)
        else:
            ex = CreateException(key, error)
    else:
        if arg_len > 0:
            ex = CreateException(key, arg_list)
        else:
            ex = CreateException(key)
    return ex


def create_deploy_exception(key, *args, **kwargs):
    """
    Create a DeployException from a message id, list of message parameters and Throwable error.
    :param key: key to the message in resource bundler or the message itself
    :param args: list of parameters for the parameters or empty if none needed for the message
    :param kwargs: contains Throwable or instance if present
    :return: DeployException encapsulating the exception information
    """
    arg_list, error = _return_exception_params(*args, **kwargs)
    arg_len = len(arg_list)
    if error is not None:
        if isinstance(error, JThrowable) is False:
            error = convert_error_to_exception()

        if arg_len > 0:
            # Jython 2.7.1 in 14.1.1 is broken when it comes to binding varargs
            # Java methods.  Calling the DeployException(key, error, arg_list) is
            # binding to the DeployException(String key, Object... params) constructor
            # instead of DeployException(String key, Throwable cause, Object...params).
            #
            ex = DeployException(key, arg_list)
            ex.initCause(error)
        else:
            ex = DeployException(key, error)
    else:
        if arg_len > 0:
            ex = DeployException(key, arg_list)
        else:
            ex = DeployException(key)
    return ex


def create_discover_exception(key, *args, **kwargs):
    """
    Create a DiscoverException from a message id, list of message parameters and Throwable error.
    :param key: key to the message in resource bundler or the message itself
    :param args: list of parameters for the parameters or empty if none needed for the message
    :param kwargs: contains Throwable or instance if present
    :return: DiscoverException encapsulating the exception information
    """
    arg_list, error = _return_exception_params(*args, **kwargs)
    arg_len = len(arg_list)
    if error is not None:
        if isinstance(error, JThrowable) is False:
            error = convert_error_to_exception()
        if arg_len > 0:
            # Jython 2.7.1 in 14.1.1 is broken when it comes to binding varargs
            # Java methods.  Calling the DiscoverException(key, error, arg_list) is
            # binding to the DiscoverException(String key, Object... params) constructor
            # instead of DiscoverException(String key, Throwable cause, Object...params).
            #
            ex = DiscoverException(key, arg_list)
            ex.initCause(error)
        else:
            ex = DiscoverException(key, error)
    else:
        if arg_len > 0:
            ex = DiscoverException(key, arg_list)
        else:
            ex = DiscoverException(key)
    return ex


def create_alias_exception(key, *args, **kwargs):
    """
    Create a AliasException from a message id, list of message parameters and Throwable error.
    :param key: key to the message in resource bundler or the message itself
    :param args: list of parameters for the parameters or empty if none needed for the message
    :param kwargs: contains Throwable or instance if present
    :return: AliasException encapsulating the exception information
    """
    arg_list, error = _return_exception_params(*args, **kwargs)
    arg_len = len(arg_list)
    if error is not None:
        if arg_len > 0:
            # Jython 2.7.1 in 14.1.1 is broken when it comes to binding varargs
            # Java methods.  Calling the AliasException(key, error, arg_list) is
            # binding to the AliasException(String key, Object... params) constructor
            # instead of AliasException(String key, Throwable cause, Object...params).
            #
            ex = AliasException(key, arg_list)
            ex.initCause(error)
        else:
            ex = AliasException(key, error)
    else:
        if arg_len > 0:
            ex = AliasException(key, arg_list)
        else:
            ex = AliasException(key)
    return ex


def create_validate_exception(key, *args, **kwargs):
    """
    Create a ValidateException from a message id, list of message parameters and Throwable error.
    :param key: key to the message in resource bundler or the message itself
    :param args: list of parameters for the parameters or empty if none needed for the message
    :param kwargs: contains Throwable or instance if present
    :return: ValidateException encapsulating the exception information
    """
    arg_list, error = _return_exception_params(*args, **kwargs)
    arg_len = len(arg_list)
    if error is not None:
        if arg_len > 0:
            # Jython 2.7.1 in 14.1.1 is broken when it comes to binding varargs
            # Java methods.  Calling the ValidateException(key, error, arg_list) is
            # binding to the ValidateException(String key, Object... params) constructor
            # instead of ValidateException(String key, Throwable cause, Object...params).
            #
            ex = ValidateException(key, arg_list)
            ex.initCause(error)
        else:
            ex = ValidateException(key, error)
    else:
        if arg_len > 0:
            ex = ValidateException(key, arg_list)
        else:
            ex = ValidateException(key)
    return ex


def create_compare_exception(key, *args, **kwargs):
    """
    Create a ComapareException from a message id, list of message parameters and Throwable error.
    :param key: key to the message in resource bundler or the message itself
    :param args: list of parameters for the parameters or empty if none needed for the message
    :param kwargs: contains Throwable or instance if present
    :return: ValidateException encapsulating the exception information
    """
    arg_list, error = _return_exception_params(*args, **kwargs)
    arg_len = len(arg_list)
    if error is not None:
        if arg_len > 0:
            # Jython 2.7.1 in 14.1.1 is broken when it comes to binding varargs
            # Java methods.  Calling the CompareException(key, error, arg_list) is
            # binding to the CompareException(String key, Object... params) constructor
            # instead of CompareException(String key, Throwable cause, Object...params).
            #
            ex = CompareException(key, arg_list)
            ex.initCause(error)
        else:
            ex = CompareException(key, error)
    else:
        if arg_len > 0:
            ex = CompareException(key, arg_list)
        else:
            ex = CompareException(key)
    return ex


def create_prepare_exception(key, *args, **kwargs):
    """
    Create a PrepareException from a message id, list of message parameters and Throwable error.
    :param key: key to the message in resource bundler or the message itself
    :param args: list of parameters for the parameters or empty if none needed for the message
    :param kwargs: contains Throwable or instance if present
    :return: ValidateException encapsulating the exception information
    """
    arg_list, error = _return_exception_params(*args, **kwargs)
    arg_len = len(arg_list)
    if error is not None:
        if arg_len > 0:
            # Jython 2.7.1 in 14.1.1 is broken when it comes to binding varargs
            # Java methods.  Calling the PrepareException(key, error, arg_list) is
            # binding to the PrepareException(String key, Object... params) constructor
            # instead of PrepareException(String key, Throwable cause, Object...params).
            #
            ex = PrepareException(key, arg_list)
            ex.initCause(error)
        else:
            ex = PrepareException(key, error)
    else:
        if arg_len > 0:
            ex = PrepareException(key, arg_list)
        else:
            ex = PrepareException(key)
    return ex


def create_pywlst_exception(key, *args, **kwargs):
    """
    Create a PyWLSTException from a message id, list of message parameters and Throwable error.
    :param key: key to the message in resource bundler or the message itself
    :param args: list of parameters for the parameters or empty if none needed for the message
    :param kwargs: contains Throwable or instance if present
    :return: PyWLSTException encapsulating the exception information
    """
    arg_list, error = _return_exception_params(*args, **kwargs)
    arg_len = len(arg_list)
    if error is not None:
        if isinstance(error, JThrowable) is False:
            error = convert_error_to_exception()
        if arg_len > 0:
            # Jython 2.7.1 in 14.1.1 is broken when it comes to binding varargs
            # Java methods.  Calling the PyWLSTException(key, error, arg_list) is
            # binding to the PyWLSTException(String key, Object... params) constructor
            # instead of PyWLSTException(String key, Throwable cause, Object...params).
            #
            ex = PyWLSTException(key, arg_list)
            ex.initCause(error)
        else:
            ex = PyWLSTException(key, error)
    else:
        if arg_len > 0:
            ex = PyWLSTException(key, arg_list)
        else:
            ex = PyWLSTException(key)
    return ex


def create_ssh_exception(key, *args, **kwargs):
    """
    Create a Java SSHException from a message id, list of message parameters and Throwable error.
    :param key: key to the message in resource bundler or the message itself
    :param args: list of parameters for the parameters or empty if none needed for the message
    :param kwargs: contains Throwable or instance if present
    :return: SSHException encapsulating the exception information
    """
    arg_list, error = _return_exception_params(*args, **kwargs)
    if error is not None:
        if len(arg_list) > 0:
            # Jython 2.7.1 in 14.1.1 is broken when it comes to binding varargs
            # Java methods.  Calling the SSHException(key, error, arg_list) is
            # binding to the SSHException(String key, Object... params) constructor
            # instead of SSHException(String key, Throwable cause, Object...params).
            #
            ex = SSHException(key, arg_list)
            ex.initCause(error)
        else:
            ex = SSHException(key, error)
    elif len(arg_list) > 0:
        ex = SSHException(key, arg_list)
    else:
        ex = SSHException(key)
    return ex


def create_yaml_exception(key, *args, **kwargs):
    """
    Create a Java YamlException from a message id, list of message parameters and Throwable error.
    :param key: key to the message in resource bundler or the message itself
    :param args: list of parameters for the parameters or empty if none needed for the message
    :param kwargs: contains Throwable or instance if present
    :return: YamlException encapsulating the exception information
    """
    arg_list, error = _return_exception_params(*args, **kwargs)
    if error is not None:
        if len(arg_list) > 0:
            # Jython 2.7.1 in 14.1.1 is broken when it comes to binding varargs
            # Java methods.  Calling the JYamlException(key, error, arg_list) is
            # binding to the JYamlException(String key, Object... params) constructor
            # instead of JYamlException(String key, Throwable cause, Object...params).
            #
            ex = JYamlException(key, arg_list)
            ex.initCause(error)
        else:
            ex = JYamlException(key, error)
    elif len(arg_list) > 0:
        ex = JYamlException(key, arg_list)
    else:
        ex = JYamlException(key)
    return ex


def create_json_exception(key, *args, **kwargs):
    """
    Create a Java JsonException from a message id, list of message parameters and Throwable error.
    :param key: key to the message in resource bundler or the message itself
    :param args: list of parameters for the parameters or empty if none needed for the message
    :param kwargs: contains Throwable or instance if present
    :return: JsonException encapsulating the exception information
    """
    arg_list, error = _return_exception_params(*args, **kwargs)
    if error is not None:
        if len(arg_list) > 0:
            # Jython 2.7.1 in 14.1.1 is broken when it comes to binding varargs
            # Java methods.  Calling the JJsonException(key, error, arg_list) is
            # binding to the JJsonException(String key, Object... params) constructor
            # instead of JJsonException(String key, Throwable cause, Object...params).
            #
            ex = JJsonException(key, arg_list)
            ex.initCause(error)
        else:
            ex = JJsonException(key, error)
    elif len(arg_list) > 0:
        ex = JJsonException(key, arg_list)
    else:
        ex = JJsonException(key)
    return ex


def create_translate_exception(key, *args, **kwargs):
    """
    Create a Java TranslateException from a message id, list of message parameters and Throwable error.
    :param key: key to the message in resource bundle or the message itself
    :param args: list of parameters for the parameters or empty if none needed for the message
    :param kwargs: contains Throwable or instance if present
    :return: TranslateException encapsulating the exception information
    """
    arg_list, error = _return_exception_params(*args, **kwargs)
    if error is not None:
        if len(arg_list) > 0:
            # Jython 2.7.1 in 14.1.1 is broken when it comes to binding varargs
            # Java methods.  Calling the JTranslateException(key, error, arg_list) is
            # binding to the JTranslateException(String key, Object... params) constructor
            # instead of JTranslateException(String key, Throwable cause, Object...params).
            #
            ex = JTranslateException(key, arg_list)
            ex.initCause(error)
        else:
            ex = JTranslateException(key, error)
    elif len(arg_list) > 0:
        ex = JTranslateException(key, arg_list)
    else:
        ex = JTranslateException(key)
    return ex


def _create_cla_type_exception(key, *args, **kwargs):
    """
    Create a Java CLAException from a message id, list of message parameters and Throwable error.
    This internal wrapper method provides a matching signature for _EXCEPTION_TYPE_MAP.
    :param key: key to the message in resource bundle or the message itself
    :param args: list of parameters for the message or empty if none needed
    :param kwargs: contains Throwable or instance if present
    :return: CLAException encapsulating the exception information
    """
    return create_cla_exception(ExitCode.ERROR, key, *args, **kwargs)


def create_cla_exception(exit_code, key, *args, **kwargs):
    """
    Create a Java CLAException from a message id, list of message parameters and Throwable error.
    :param exit_code: exit code to return from the tool
    :param key: key to the message in resource bundle or the message itself
    :param args: list of parameters for the parameters or empty if none needed for the message
    :param kwargs: contains Throwable or instance if present
    :return: CLAException encapsulating the exception information
    """
    arg_list, error = _return_exception_params(*args, **kwargs)
    if error is not None:
        if len(arg_list) > 0:
            # Jython 2.7.1 in 14.1.1 is broken when it comes to binding varargs
            # Java methods.  Calling the JCLAException(key, error, arg_list) is
            # binding to the JCLAException(String key, Object... params) constructor
            # instead of JCLAException(String key, Throwable cause, Object...params).
            #
            ex = JCLAException(exit_code, key, arg_list)
            ex.initCause(error)
        else:
            ex = JCLAException(exit_code, key, error)
    elif len(arg_list) > 0:
        ex = JCLAException(exit_code, key, arg_list)
    else:
        ex = JCLAException(exit_code, key)
    return ex


def create_variable_exception(key, *args, **kwargs):
    """
    Create a Java VariableException from a message id, list of message parameters and Throwable error.
    :param key: key to the message in resource bundle or the message itself
    :param args: list of parameters for the parameters or empty if none needed for the message
    :param kwargs: contains Throwable or instance if present
    :return: VariableException encapsulating the exception information
    """
    arg_list, error = _return_exception_params(*args, **kwargs)
    if error is not None:
        if len(arg_list) > 0:
            # Jython 2.7.1 in 14.1.1 is broken when it comes to binding varargs
            # Java methods.  Calling the JVariableException(key, error, arg_list) is
            # binding to the JVariableException(String key, Object... params) constructor
            # instead of JVariableException(String key, Throwable cause, Object...params).
            #
            ex = JVariableException(key, arg_list)
            ex.initCause(error)
        else:
            ex = JVariableException(key, error)
    elif len(arg_list) > 0:
        ex = JVariableException(key, arg_list)
    else:
        ex = JVariableException(key)
    return ex


def create_archive_ioexception(key, *args, **kwargs):
    """
    Create a Java WLSDeployArchiveIOException from a message id, list of message parameters and Throwable error.
    :param key: key to the message in resource bundle or the message itself
    :param args: list of parameters for the parameters or empty if none needed for the message
    :param kwargs: contains Throwable or instance if present
    :return: WLSDeployArchiveIOException encapsulating the exception information
    """
    arg_list, error = _return_exception_params(*args, **kwargs)
    if error is not None:
        if len(arg_list) > 0:
            # Jython 2.7.1 in 14.1.1 is broken when it comes to binding varargs
            # Java methods.  Calling the JWLSDeployArchiveIOException(key, error, arg_list) is
            # binding to the JWLSDeployArchiveIOException(String key, Object... params) constructor
            # instead of JWLSDeployArchiveIOException(String key, Throwable cause, Object...params).
            #
            ex = JWLSDeployArchiveIOException(key, arg_list)
            ex.initCause(error)
        else:
            ex = JWLSDeployArchiveIOException(key, error)
    elif len(arg_list) > 0:
        ex = JWLSDeployArchiveIOException(key, arg_list)
    else:
        ex = JWLSDeployArchiveIOException(key)
    return ex


def create_encryption_exception(key, *args, **kwargs):
    """
    Create a Java EncryptionException from a message id, list of message parameters and Throwable error.
    :param key: key to the message in resource bundler or the message itself
    :param args: list of parameters for the parameters or empty if none needed for the message
    :param kwargs: contains Throwable or instance if present
    :return: EncryptionException encapsulating the exception information
    """
    arg_list, error = _return_exception_params(*args, **kwargs)
    if error is not None:
        if len(arg_list) > 0:
            # Jython 2.7.1 in 14.1.1 is broken when it comes to binding varargs
            # Java methods.  Calling the JEncryptionException(key, error, arg_list) is
            # binding to the JEncryptionException(String key, Object... params) constructor
            # instead of JEncryptionException(String key, Throwable cause, Object...params).
            #
            ex = JEncryptionException(key, arg_list)
            ex.initCause(error)
        else:
            ex = JEncryptionException(key, error)
    elif len(arg_list) > 0:
        ex = JEncryptionException(key, arg_list)
    else:
        ex = JEncryptionException(key)
    return ex


def convert_error_to_exception():
    """
    Convert a Python built-in error to a proper bundle-aware Java exception
    :return: the bundle-aware Java exception
    """
    exc_type, exc_obj, exc_tb = sys.exc_info()
    ex_strings = traceback.format_exception(exc_type, exc_obj, exc_tb)
    exception_message = ex_strings[-1]
    for ex_string in ex_strings:
        exception_message += ex_string

    exception_type = str_helper.to_string(exc_type)

    if exception_type.find("exceptions.IOError") == 0:
        custom_exception = PyIOErrorException(exception_message)
    elif exception_type.find("exceptions.KeyError") == 0:
        custom_exception = PyKeyErrorException(exception_message)
    elif exception_type.find("exceptions.ValueError") == 0:
        custom_exception = PyValueErrorException(exception_message)
    elif exception_type.find("exceptions.TypeError") == 0:
        custom_exception = PyTypeErrorException(exception_message)
    elif exception_type.find("exceptions.AttributeError") == 0:
        custom_exception = PyAttributeErrorException(exception_message)
    else:
        custom_exception = PyBaseException(exception_message)

    custom_exception.setStackTrace(exception_message)
    return custom_exception


def get_error_message_from_exception(ex):
    if isinstance(ex, JThrowable):
        message =  ex.getLocalizedMessage()
    else:
        message = ex.to_string()
    return message


def _return_exception_params(*args, **kwargs):
    """
    Get the exception parameters from the list
    :param args: input args
    :param kwargs: input names args
    :return: the args and error for the exception
    """
    arg_list = list(args)
    error = kwargs.pop('error', None)
    return arg_list, error
