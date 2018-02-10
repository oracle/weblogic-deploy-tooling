"""
Copyright (c) 2017, 2018, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""
from java.lang import String

from oracle.weblogic.deploy.encrypt import EncryptionUtils
from oracle.weblogic.deploy.json import JsonException
from oracle.weblogic.deploy.json import JsonStreamTranslator
from oracle.weblogic.deploy.util import FileUtils

import wlsdeploy.exception.exception_helper as exception_helper
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.util import model
from wlsdeploy.util import variables as variable_helper

_class_name = 'encryption_utils'
_password_field_names = None
_password_field_names_file = 'oracle/weblogic/deploy/util/ModelPasswordFieldNames.json'
_logger = PlatformLogger('wlsdeploy.encrypt')


def encrypt_model_dictionary(passphrase, model_dict, variables=None):
    """
    Encrypt the model dictionary (and referenced variables, if provided) using the specified passphrase.
    :param passphrase: the passphrase used to encrypt/decrypt the passwords
    :param model_dict: the model dictionary
    :param variables: the variables property object
    :raises EncryptionException if an error occurs
    """
    _initialize_password_field_names()
    model_changes = 0
    variable_changes = 0

    if model.get_model_domain_info_key() in model_dict:
        domain_info_dict = model_dict[model.get_model_domain_info_key()]
        _model_changes, _variable_changes = \
            _search_and_replace_passwords(passphrase, model.get_model_domain_info_key(), domain_info_dict, variables)
        model_changes += _model_changes
        variable_changes += _variable_changes

    if model.get_model_topology_key() in model_dict:
        topology_dict = model_dict[model.get_model_topology_key()]
        _model_changes, _variable_changes = \
            _search_and_replace_passwords(passphrase, model.get_model_topology_key(), topology_dict, variables)
        model_changes += _model_changes
        variable_changes += _variable_changes

    if model.get_model_resources_key() in model_dict:
        resources_dict = model_dict[model.get_model_resources_key()]
        _model_changes, _variable_changes = \
            _search_and_replace_passwords(passphrase, model.get_model_resources_key(), resources_dict, variables)
        model_changes += _model_changes
        variable_changes += _variable_changes

    if model.get_model_deployments_key() in model_dict:
        deployments_dict = model_dict[model.get_model_deployments_key()]
        _model_changes, _variable_changes = \
            _search_and_replace_passwords(passphrase, model.get_model_deployments_key(), deployments_dict, variables)
        model_changes += _model_changes
        variable_changes += _variable_changes

    return model_changes, variable_changes

def encrypt_one_password(passphrase, password):
    """
    Encrypt the password provided using the specified passphrase.
    :param passphrase: the password to use for encryption/decryption
    :param password: the password to encrypt
    :return: the encrypted password
    :raises EncryptionException if an error occurs
    """
    return EncryptionUtils.encryptString(password, passphrase.toCharArray())

def _initialize_password_field_names():
    """
    Initialize the password field names structure.
    :raises: EncryptionException: if an error occurs while loading and parsing the password field names file
    """
    global _password_field_names
    _method_name = '_initialize_password_field_names'

    if _password_field_names is None:
        password_field_names_stream = FileUtils.getResourceAsStream(_password_field_names_file)
        if password_field_names_stream is None:
            ex = exception_helper.create_encryption_exception('WLSDPLY-03124', _password_field_names_file)
            _logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex

        try:
            password_field_names_dict = \
                JsonStreamTranslator(_password_field_names_file, password_field_names_stream).parse()
        except JsonException, je:
            ex = exception_helper.create_encryption_exception('WLSDPLY-03125', _password_field_names_file,
                                                              je.getLocalizedMessage(), error=je)
            _logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex

        if password_field_names_dict is not None and 'passwordFieldNames' in password_field_names_dict:
            _password_field_names = password_field_names_dict['passwordFieldNames']
        else:
            ex = exception_helper.create_encryption_exception('WLSDPLY-03126', _password_field_names_file)
            _logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex
    return

def _search_and_replace_passwords(passphrase, dict_name, model_dict, variables):
    """
    Search the model file for password fields and replace the value with its encrypted value.
    :param passphrase: the encryption passphrase to use
    :param dict_name: the name of the model element represented by the dictionary
    :param model_dict: the model dictionary to search
    :param variables: the variables to use with the model
    :return: the number of changes to the model dictionary, the number of changes to the variables
    """
    _method_name = '_search_and_replace_passwords'

    model_changes = 0
    variable_changes = 0
    if model_dict is None or len(model_dict) == 0:
        return model_changes, variable_changes

    for key in model_dict:
        value = model_dict[key]
        if isinstance(value, dict):
            _model_changes, _variable_changes = _search_and_replace_passwords(passphrase, key, value, variables)
            model_changes += _model_changes
            variable_changes += _variable_changes
        elif type(value) is str and key in _password_field_names:
            variable_names = variable_helper.get_variable_names(value)
            if len(variable_names) == 0:
                if not EncryptionUtils.isEncryptedString(value):
                    encrypted_value = EncryptionUtils.encryptString(value, String(passphrase).toCharArray())
                    model_dict[key] = encrypted_value
                    _logger.fine('WLSDPLY-03129', dict_name, key, class_name=_class_name, method_name=_method_name)
                    model_changes += 1
                else:
                    _logger.fine('WLSDPLY-03134', dict_name, key, class_name=_class_name, method_name=_method_name)
            elif len(variable_names) == 1:
                _variable_changes = _encrypt_variable_value(passphrase, dict_name, key, variable_names[0], variables)
                variable_changes += _variable_changes
            else:
                _logger.warning('WLSDPLY-03130', dict_name, key, len(variable_names), variable_names,
                                class_name=_class_name, method_name=_method_name)
    return model_changes, variable_changes


def _encrypt_variable_value(passphrase, dict_name, field_name, var_name, variables):
    """
    Encrypt the variable value.
    :param passphrase: the encryption passphrase
    :param dict_name: the model element name
    :param field_name: the attribute name
    :param var_name: the variable name
    :param variables: the variables
    :return: the number of variable changes
    """
    _method_name = '_encrypt_variable_value'

    variable_changes = 0
    if variables is None:
        return variable_changes

    if var_name in variables:
        var_value = variables[var_name]
        if len(var_value) > 0:
            encrypted_value = EncryptionUtils.encryptString(var_value, String(passphrase).toCharArray())
            variables[var_name] = encrypted_value
            _logger.fine('WLSDPLY-03128', dict_name, field_name, var_name,
                         class_name=_class_name, method_name=_method_name)
            variable_changes = 1
    else:
        ex = exception_helper.create_encryption_exception('WLSDPLY-03127', var_name, field_name, dict_name)
        _logger.throwing(ex, class_name=_class_name, method_name=_method_name)
        raise ex

    return variable_changes
