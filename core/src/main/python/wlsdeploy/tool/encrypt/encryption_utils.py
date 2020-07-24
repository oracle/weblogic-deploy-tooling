"""
Copyright (c) 2017, 2020, Oracle Corporation and/or its affiliates.  All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
from java.lang import String
from oracle.weblogic.deploy.encrypt import EncryptionUtils

from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import DOMAIN_INFO
from wlsdeploy.exception import exception_helper
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.util import model
from wlsdeploy.util import variables as variable_helper


class _ModelEncrypter(object):
    """
    Enables encryption of the password fields in a model dictionary.
    The methods in this class are not thread safe, and it should be accessed only through the static methods at
    the end of this file.
    """
    _class_name = '_ModelEncrypter'
    _logger = PlatformLogger('wlsdeploy.encrypt')

    def __init__(self, passphrase, aliases, variables=None):
        """
        Initialize variables for use throughout.
        :param passphrase: the passphrase used to encrypt/decrypt the passwords
        :param aliases: the alias helper for the tool
        :param variables: the variables property object
        :raises EncryptionException if an error occurs
        """
        self.passphrase = passphrase
        self.aliases = aliases
        self.variables = variables
        self.model_changes = 0
        self.variable_changes = 0

    def encrypt_model_dictionary(self, model_dict):
        """
        Encrypt the model dictionary (and referenced variables, if provided) using the specified passphrase.
        :param model_dict: the model dictionary
        :return: the number of model elements encrypted, and the number of variables encrypted
        :raises EncryptionException if an error occurs
        """

        if model.get_model_domain_info_key() in model_dict:
            domain_info_dict = model_dict[model.get_model_domain_info_key()]
            self._encrypt_info_nodes(domain_info_dict)

        if model.get_model_topology_key() in model_dict:
            top_folder_names = self.aliases.get_model_topology_top_level_folder_names()
            topology_nodes = model_dict[model.get_model_topology_key()]
            location = LocationContext()
            self._encrypt_nodes(location, topology_nodes, top_folder_names)

        if model.get_model_resources_key() in model_dict:
            top_folder_names = self.aliases.get_model_resources_top_level_folder_names()
            resources_nodes = model_dict[model.get_model_resources_key()]
            location = LocationContext()
            self._encrypt_nodes(location, resources_nodes, top_folder_names)

        if model.get_model_deployments_key() in model_dict:
            top_folder_names = self.aliases.get_model_app_deployments_top_level_folder_names()
            deployments_nodes = model_dict[model.get_model_deployments_key()]
            location = LocationContext()
            self._encrypt_nodes(location, deployments_nodes, top_folder_names)

        return self.model_changes, self.variable_changes

    def _encrypt_info_nodes(self, info_nodes):
        """
        Encrypt a set of nodes from the domainInfo section of the model.
        :param info_nodes: the model nodes
        """
        info_location = self.aliases.get_model_section_attribute_location(DOMAIN_INFO)
        password_attribute_names = self.aliases.get_model_password_type_attribute_names(info_location)

        subfolder_names = self.aliases.get_model_section_top_level_folder_names(DOMAIN_INFO)

        for node in info_nodes:
            if node in subfolder_names:
                child_location = LocationContext().append_location(node)
                child_nodes = info_nodes[node]
                self._encrypt_nodes(child_location, child_nodes)

            elif node in password_attribute_names:
                self._encrypt_attribute(DOMAIN_INFO, info_nodes, node)

    def _encrypt_nodes(self, location, model_nodes, subfolder_names=None):
        """
        Encrypt a set of nodes corresponding to the specified location.
        :param location: the location of the model nodes
        :param model_nodes: the model nodes
        :param subfolder_names: the valid sub-folders of the location. If not specified, derive from location
        """
        _method_name = '_encrypt_nodes'

        folder_name = location.get_folder_path()

        password_attribute_names = self.aliases.get_model_password_type_attribute_names(location)

        if subfolder_names is None:
            subfolder_names = self.aliases.get_model_subfolder_names(location)

        for node in model_nodes:
            if node in subfolder_names:
                child_location = LocationContext(location).append_location(node)

                # check artificial type first, those locations will cause error in other checks
                has_multiple = (not self.aliases.is_artificial_type_folder(child_location)) and \
                               (self.aliases.requires_artificial_type_subfolder_handling(child_location) or
                                self.aliases.supports_multiple_mbean_instances(child_location))

                if has_multiple:
                    name_nodes = model_nodes[node]
                    for name_node in name_nodes:
                        child_nodes = name_nodes[name_node]
                        self._encrypt_nodes(child_location, child_nodes)
                else:
                    child_nodes = model_nodes[node]
                    self._encrypt_nodes(child_location, child_nodes)

            elif (not self.aliases.is_artificial_type_folder(location)) and \
                    self.aliases.requires_artificial_type_subfolder_handling(location):
                # if a child of a security provider type is not a known subfolder, possibly a custom provider
                self._logger.info('WLSDPLY-04108', node, folder_name,
                                  class_name=self._class_name, method_name=_method_name)

            elif node in password_attribute_names:
                self._encrypt_attribute(folder_name, model_nodes, node)

    def _encrypt_attribute(self, folder_name, model_nodes, key):
        """
        Encrypt a specific attribute that was flagged as password type.
        If the attribute value uses a variable, encrypt the variable and replace the value,
        otherwise replace the value in the dictionary with the encrypted value.
        :param folder_name: text describing the folder location, used for logging
        :param model_nodes: the dictionary containing the attribute
        :param key: the key of the model attribute
        """
        _method_name = '_encrypt_attribute'

        value = model_nodes[key]
        variable_names = variable_helper.get_variable_names(value)
        if len(variable_names) == 0:
            if not EncryptionUtils.isEncryptedString(value):
                encrypted_value = EncryptionUtils.encryptString(value, String(self.passphrase).toCharArray())
                model_nodes[key] = encrypted_value
                self._logger.fine('WLSDPLY-04103', folder_name, key,
                                  class_name=self._class_name, method_name=_method_name)
                self.model_changes += 1
            else:
                self._logger.fine('WLSDPLY-04104', folder_name, key,
                                  class_name=self._class_name, method_name=_method_name)
        elif len(variable_names) == 1:
            self._encrypt_variable_value(folder_name, key, variable_names[0])
        else:
            self._logger.warning('WLSDPLY-04105', folder_name, key, len(variable_names), variable_names,
                                 class_name=self._class_name, method_name=_method_name)

    def _encrypt_variable_value(self, folder_name, field_name, var_name):
        """
        Encrypt the variable value, and replace it in the variable set.
        :param folder_name: text describing the folder location, used for logging
        :param field_name: the attribute name
        :param var_name: the variable name
        :return: the number of variable changes
        """
        _method_name = '_encrypt_variable_value'

        # if variables file was not specified, don't try to encrypt
        if self.variables is None:
            return

        # Do not encrypt already encrypted to match model encryption: Don't encrypt encrypted value
        if var_name in self.variables:
            var_value = self.variables[var_name]
            if len(var_value) > 0:

                # don't encrypt an already encrypted variable. Matches logic in model
                if EncryptionUtils.isEncryptedString(var_value):
                    self._logger.fine('WLSDPLY-04109', folder_name, field_name, var_name)
                    return

                encrypted_value = EncryptionUtils.encryptString(var_value, String(self.passphrase).toCharArray())
                self.variables[var_name] = encrypted_value
                self.variable_changes += 1
                self._logger.fine('WLSDPLY-04106', folder_name, field_name, var_name,
                                  class_name=self._class_name, method_name=_method_name)
        else:
            ex = exception_helper.create_encryption_exception('WLSDPLY-04107', var_name, field_name, folder_name)
            self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex


def encrypt_model_dictionary(passphrase, model_dict, aliases, variables):
    """
    Encrypt password attributes and replace them in the specified model.
    :param passphrase: the password to use for encryption
    :param model_dict: the model dictionary
    :param aliases: the alias helper for the tool
    :param variables: the variables property object
    :return: the number of model elements encrypted, and the number of variables encrypted
    :raises EncryptionException if an error occurs
    """
    encrypter = _ModelEncrypter(passphrase, aliases, variables)
    return encrypter.encrypt_model_dictionary(model_dict)


def encrypt_one_password(passphrase, text):
    """
    Encrypt the text provided using the specified passphrase.
    :param passphrase: the password to use for encryption
    :param text: the text to encrypt
    :return: the encrypted text
    :raises EncryptionException if an error occurs
    """
    return EncryptionUtils.encryptString(text, passphrase.toCharArray())
