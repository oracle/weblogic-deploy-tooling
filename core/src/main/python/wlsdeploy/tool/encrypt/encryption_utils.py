"""
Copyright (c) 2017, 2019, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""
from java.lang import String
from oracle.weblogic.deploy.encrypt import EncryptionUtils

from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import DOMAIN_INFO
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_KEYSTOREPWD_PROPERTY
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_TRUSTSTOREPWD_PROPERTY
from wlsdeploy.aliases.model_constants import RCU_ADMIN_PASSWORD
from wlsdeploy.aliases.model_constants import RCU_DB_INFO
from wlsdeploy.aliases.model_constants import RCU_SCHEMA_PASSWORD
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

    # these elements in the domainInfo/RCUDbInfo section are passwords,
    # and may need to be encrypted.
    _rcu_password_attributes = [
        RCU_ADMIN_PASSWORD,
        RCU_SCHEMA_PASSWORD,
        DRIVER_PARAMS_KEYSTOREPWD_PROPERTY,
        DRIVER_PARAMS_TRUSTSTOREPWD_PROPERTY
    ]

    def __init__(self, passphrase, alias_helper, variables=None):
        """
        Initialize variables for use throughout.
        :param passphrase: the passphrase used to encrypt/decrypt the passwords
        :param alias_helper: the alias helper for the tool
        :param variables: the variables property object
        :raises EncryptionException if an error occurs
        """
        self.passphrase = passphrase
        self.alias_helper = alias_helper
        self.variables = variables
        self.model_changes = 0
        self.variables_changed = []

    def encrypt_model_dictionary(self, model_dict):
        """
        Encrypt the model dictionary (and referenced variables, if provided) using the specified passphrase.
        :param model_dict: the model dictionary
        :return: the number of model elements encrypted, and the number of variables encrypted
        :raises EncryptionException if an error occurs
        """

        if model.get_model_domain_info_key() in model_dict:
            info_name_map = self.alias_helper.get_model_domain_info_attribute_names_and_types()
            domain_info_dict = model_dict[model.get_model_domain_info_key()]
            self._encrypt_info_nodes(domain_info_dict, info_name_map)

        if model.get_model_topology_key() in model_dict:
            top_folder_names = self.alias_helper.get_model_topology_top_level_folder_names()
            topology_nodes = model_dict[model.get_model_topology_key()]
            location = LocationContext()
            self._encrypt_nodes(location, topology_nodes, top_folder_names)

        if model.get_model_resources_key() in model_dict:
            top_folder_names = self.alias_helper.get_model_resources_top_level_folder_names()
            resources_nodes = model_dict[model.get_model_resources_key()]
            location = LocationContext()
            self._encrypt_nodes(location, resources_nodes, top_folder_names)

        if model.get_model_deployments_key() in model_dict:
            top_folder_names = self.alias_helper.get_model_app_deployments_top_level_folder_names()
            deployments_nodes = model_dict[model.get_model_deployments_key()]
            location = LocationContext()
            self._encrypt_nodes(location, deployments_nodes, top_folder_names)

        return self.model_changes, len(self.variables_changed)

    def _encrypt_info_nodes(self, info_nodes, info_name_map):
        """
        Encrypt a set of nodes from the domainInfo section of the model.
        :param info_nodes: the model nodes
        :param info_name_map: a map of model key names to type
        """
        for key in info_nodes:
            if key in info_name_map:
                attribute_type = info_name_map[key]
                if attribute_type == 'password':
                    self._encrypt_attribute(DOMAIN_INFO, info_nodes, key)

        if RCU_DB_INFO in info_nodes:
            rcu_nodes = info_nodes[RCU_DB_INFO]
            folder_name = DOMAIN_INFO + '/' + RCU_DB_INFO
            for key in rcu_nodes:
                if key in self._rcu_password_attributes:
                    self._encrypt_attribute(folder_name, rcu_nodes, key)

    def _encrypt_nodes(self, location, model_nodes, subfolder_names=None):
        """
        Encrypt a set of nodes corresponding to the specified location.
        :param location: the location of the model nodes
        :param model_nodes: the model nodes
        :param subfolder_names: the valid sub-folders of the location. If not specified, derive from location
        """
        _method_name = '_encrypt_nodes'

        folder_name = location.get_folder_path()

        password_attribute_names = self.alias_helper.get_model_password_type_attribute_names(location)

        if subfolder_names is None:
            subfolder_names = self.alias_helper.get_model_subfolder_names(location)

        for node in model_nodes:
            if node in subfolder_names:
                child_location = LocationContext(location).append_location(node)

                # check artificial type first, those locations will cause error in other checks
                has_multiple = (not self.alias_helper.is_artificial_type_folder(child_location)) and \
                               (self.alias_helper.requires_artificial_type_subfolder_handling(child_location) or
                                self.alias_helper.supports_multiple_mbean_instances(child_location))

                if has_multiple:
                    name_nodes = model_nodes[node]
                    for name_node in name_nodes:
                        child_nodes = name_nodes[name_node]
                        self._encrypt_nodes(child_location, child_nodes)
                else:
                    child_nodes = model_nodes[node]
                    self._encrypt_nodes(child_location, child_nodes)

            elif (not self.alias_helper.is_artificial_type_folder(location)) and \
                    self.alias_helper.requires_artificial_type_subfolder_handling(location):
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

        # this variable may have been encrypted for another attribute
        if var_name in self.variables_changed:
            return

        if var_name in self.variables:
            var_value = self.variables[var_name]
            if len(var_value) > 0:
                encrypted_value = EncryptionUtils.encryptString(var_value, String(self.passphrase).toCharArray())
                self.variables[var_name] = encrypted_value
                self.variables_changed.append(var_name)
                self._logger.fine('WLSDPLY-04106', folder_name, field_name, var_name,
                                  class_name=self._class_name, method_name=_method_name)
        else:
            ex = exception_helper.create_encryption_exception('WLSDPLY-04107', var_name, field_name, folder_name)
            self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex


def encrypt_model_dictionary(passphrase, model_dict, alias_helper, variables):
    """
    Encrypt password attributes and replace them in the specified model.
    :param passphrase: the password to use for encryption
    :param model_dict: the model dictionary
    :param alias_helper: the alias helper for the tool
    :param variables: the variables property object
    :return: the number of model elements encrypted, and the number of variables encrypted
    :raises EncryptionException if an error occurs
    """
    encrypter = _ModelEncrypter(passphrase, alias_helper, variables)
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
