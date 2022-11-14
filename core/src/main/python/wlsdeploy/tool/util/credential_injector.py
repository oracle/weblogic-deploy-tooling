"""
Copyright (c) 2020, 2022, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""

import oracle.weblogic.deploy.util.PyOrderedDict as OrderedDict
from wlsdeploy.aliases.alias_constants import CREDENTIAL
from wlsdeploy.aliases.alias_constants import PASSWORD
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import DOMAIN_INFO_ALIAS
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_PROPERTY_VALUE
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_USER_PROPERTY
from wlsdeploy.aliases.model_constants import JDBC_DRIVER_PARAMS
from wlsdeploy.aliases.model_constants import JDBC_RESOURCE
from wlsdeploy.aliases.model_constants import JDBC_SYSTEM_RESOURCE
from wlsdeploy.aliases.model_constants import MAIL_SESSION
from wlsdeploy.aliases.model_constants import PROPERTIES
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.util.variable_injector import REGEXP
from wlsdeploy.tool.util.variable_injector import REGEXP_PATTERN
from wlsdeploy.tool.util.variable_injector import REGEXP_SUFFIX
from wlsdeploy.tool.util.variable_injector import STANDARD_PASSWORD_INJECTOR
from wlsdeploy.tool.util.variable_injector import VARIABLE_VALUE
from wlsdeploy.tool.util.variable_injector import VariableInjector
from wlsdeploy.util import target_configuration_helper
import wlsdeploy.util.unicode_helper as str_helper
from wlsdeploy.util import variables
from wlsdeploy.util.target_configuration import CONFIG_OVERRIDES_SECRETS_METHOD
from wlsdeploy.util.target_configuration import SECRETS_METHOD
from wlsdeploy.util.target_configuration_helper import SECRET_PASSWORD_KEY
from wlsdeploy.util.target_configuration_helper import SECRET_USERNAME_KEY
from wlsdeploy.util.target_configuration_helper import WEBLOGIC_CREDENTIALS_SECRET_NAME

_class_name = 'CredentialInjector'
_logger = PlatformLogger('wlsdeploy.tool.util')


class CredentialInjector(VariableInjector):
    """
    A specialized variable injector for use with the tokenizing of credential attributes.
    Credential values are stored in the map with secret names like jdbc-generic1.password .
    """

    # used for user token search
    JDBC_PROPERTIES_PATH = '%s.%s.%s.%s' % (JDBC_SYSTEM_RESOURCE, JDBC_RESOURCE, JDBC_DRIVER_PARAMS, PROPERTIES)

    # regex for tokenizing MailSession.Properties passwords (blank the value)
    PASSWORD_COMMANDS = {
        VARIABLE_VALUE: '',
        REGEXP: [
            {REGEXP_PATTERN: "mail.imap.password", REGEXP_SUFFIX: "imap.password"},
            {REGEXP_PATTERN: "mail.pop3.password", REGEXP_SUFFIX: "pop3.password"},
            {REGEXP_PATTERN: "mail.smtp.password", REGEXP_SUFFIX: "smtp.password"}
        ]
    }

    # regex for tokenizing MailSession.Properties users
    USER_COMMANDS = {
        REGEXP: [
            {REGEXP_PATTERN: "mail.imap.user", REGEXP_SUFFIX: "imap.user"},
            {REGEXP_PATTERN: "mail.pop3.user", REGEXP_SUFFIX: "pop3.user"},
            {REGEXP_PATTERN: "mail.smtp.user", REGEXP_SUFFIX: "smtp.user"}
        ]
    }

    # keys that should not be filtered from cache, even if they are not in the model.
    # the model may reference admin credentials indirectly if the target type uses wls_credentials_name.
    NO_FILTER_KEYS = [
        WEBLOGIC_CREDENTIALS_SECRET_NAME + ":" + SECRET_PASSWORD_KEY,
        WEBLOGIC_CREDENTIALS_SECRET_NAME + ":" + SECRET_USERNAME_KEY
    ]

    def __init__(self, program_name, model, model_context, version=None, variable_dictionary=None):
        """
        Construct an instance of the credential injector.
        :param program_name: name of the calling tool
        :param model: to be updated with variables
        :param model_context: context with command line information
        :param version: of model if model context is not provided
        :param variable_dictionary: optional, a pre-populated map of variables
        """
        VariableInjector.__init__(self, program_name, model, model_context, version=version,
                                  variable_dictionary=variable_dictionary)
        self._model_context = model_context
        self._no_filter_keys_cache = []
        self._no_filter_keys_cache.append(self.NO_FILTER_KEYS)

    def check_and_tokenize(self, model_dict, attribute, location):
        """
        If the specified attribute is a security credential, add it to the injector,
        and replace the value in the model dictionary with the token.
        :param model_dict: the model dictionary containing the attribute
        :param attribute: the name of the attribute
        :param location: the location of the attribute
        """
        aliases = self.get_aliases()
        attribute_type = aliases.get_model_attribute_type(location, attribute)
        folder_path = '.'.join(location.get_model_folders())
        model_value = model_dict[attribute]

        if attribute_type == CREDENTIAL:
            injector_commands = OrderedDict()
            injector_commands.update({VARIABLE_VALUE: model_value})
            self.custom_injection(model_dict, attribute, location, injector_commands)

        elif attribute_type == PASSWORD:
            # STANDARD_PASSWORD_INJECTOR provides an empty value for the mapping
            self.custom_injection(model_dict, attribute, location, STANDARD_PASSWORD_INJECTOR)

        elif folder_path.endswith(self.JDBC_PROPERTIES_PATH):
            token = aliases.get_name_token(location)
            property_name = location.get_name_for_token(token)
            if (property_name == DRIVER_PARAMS_USER_PROPERTY) and (attribute == DRIVER_PARAMS_PROPERTY_VALUE):
                injector_commands = OrderedDict()
                injector_commands.update({VARIABLE_VALUE: model_value})
                self.custom_injection(model_dict, attribute, location, injector_commands)

        elif folder_path.endswith(MAIL_SESSION) and (attribute == PROPERTIES):
            # users and passwords are property assignments
            value = model_dict[attribute]
            is_string = isinstance(value, basestring)

            # for discover, value is a string at this point
            split_value = ';'
            if self._model_context.is_wlst_online():
                split_value = ','
            if is_string:
                model_dict[attribute] = OrderedDict()
                split = value.split(split_value)
                for assign in split:
                    halves = assign.split('=')
                    model_dict[attribute][halves[0]] = halves[1]

            self.custom_injection(model_dict, attribute, location, self.USER_COMMANDS)
            self.custom_injection(model_dict, attribute, location, self.PASSWORD_COMMANDS)

            if is_string:
                properties = model_dict[attribute]
                assigns = []
                for key in properties:
                    assigns.append('%s=%s' % (key, properties[key]))
                model_dict[attribute] = split_value.join(assigns)

    def injection_out_of_model(self, token, username=''):
        """
        This is for tokenizing variables that are not in the model but need to be in the variable file
        :param token: name for cache to create a token for
        :param username: usernames appear as part of property value
        :return: tokenized name
        """
        _method_name = 'injection_out_of_model'
        _logger.entering(token, class_name=_class_name, method_name=_method_name)
        result = self.get_variable_token(None, token)
        self.add_to_cache(token_name=token, token_value=username)

        self._no_filter_keys_cache.append(token)
        _logger.exiting(class_name=_class_name, method_name=_method_name, result=result)
        return result

    def get_variable_name(self, attribute_location, attribute, suffix=None):
        """
        Override method to possibly create secret token names instead of property names.
        :param attribute_location: the location to be used
        :param attribute: the attribute to be examined
        :param suffix: optional suffix for name
        :return: the derived name, such as jdbc-generic1.password
        """
        aliases = self.get_aliases()
        target_config = self._model_context.get_target_configuration()

        # domainInfo attributes have separate model and attribute locations
        model_location = attribute_location
        if model_location.get_current_model_folder() == DOMAIN_INFO_ALIAS:
            model_location = LocationContext()

        if target_config.uses_credential_secrets():
            # use the secret token name as variable name in the cache, such as jdbc-generic1.password .
            # secret name is the adjusted variable name, with the last element replaced with "username" or "password".

            attribute_type = aliases.get_model_attribute_type(attribute_location, attribute)
            variable_name = VariableInjector.get_variable_name(self, model_location, attribute)
            secret_name = target_configuration_helper.create_secret_name(variable_name, suffix)

            secret_key = SECRET_USERNAME_KEY
            if attribute_type == PASSWORD:
                secret_key = SECRET_PASSWORD_KEY

            # suffix such as map3.password in MailSession properties
            if suffix and suffix.endswith(".password"):
                secret_key = SECRET_PASSWORD_KEY

            return '%s:%s' % (secret_name, secret_key)

        return VariableInjector.get_variable_name(self, model_location, attribute, suffix=suffix)

    def get_variable_token(self, attribute, variable_name):
        """
        Override method to possibly create secret tokens instead of property token.
        :param attribute: the attribute to be examined
        :param variable_name: the variable name, such as JDBC.Generic1.PasswordEncrypted
        :return: the complete token name, such as @@SECRET:jdbc-generic1.password@@
        """
        target_config = self._model_context.get_target_configuration()
        credentials_method = target_config.get_credentials_method()

        if credentials_method == SECRETS_METHOD:
            return target_configuration_helper.format_as_secret_token(variable_name, target_config)
        elif credentials_method == CONFIG_OVERRIDES_SECRETS_METHOD:
            return target_configuration_helper.format_as_overrides_secret(variable_name)
        else:
            return VariableInjector.get_variable_token(self, attribute, variable_name)

    def get_property_token(self, attribute, variable_name):
        return VariableInjector.get_variable_token(self, attribute, variable_name)

    def _check_tokenized(self, attribute_value):
        """
        Override to return true if target uses credentials and the value is formatted like @@SECRET:xyz:abc@@.
        :param attribute_value: the value to be checked
        """
        target_uses_credentials = self._model_context.get_target_configuration().uses_credential_secrets()
        if target_uses_credentials:
            return variables.is_secret_string(attribute_value)
        else:
            return VariableInjector._check_tokenized(self, attribute_value)

    def filter_unused_credentials(self, model_dictionary):
        """
        Remove credentials from the cache that are no longer present in the model.
        Check for variables or secrets, depending on target configuration.
        :param model_dictionary: the model to be checked
        """
        _method_name = 'filter_unused_credentials'

        target_config = self._model_context.get_target_configuration()
        credentials_method = target_config.get_credentials_method()

        if credentials_method == CONFIG_OVERRIDES_SECRETS_METHOD:
            _logger.info("WLSDPLY-19650", credentials_method, class_name=_class_name, method_name=_method_name)
            return

        all_variables = []
        self._add_model_variables(model_dictionary, all_variables)

        cache_keys = self.get_variable_cache().keys()
        for key in cache_keys:
            if key in self._no_filter_keys_cache:
                continue

            if credentials_method == SECRETS_METHOD:
                variable_name = '@@SECRET:@@ENV:DOMAIN_UID@@-%s@@' % key
            else:
                variable_name = '@@PROP:%s@@' % key

            if variable_name not in all_variables:
                _logger.info("WLSDPLY-19651", variable_name, class_name=_class_name, method_name=_method_name)
                del self.get_variable_cache()[key]

    def _add_model_variables(self, model_dictionary, variables):
        """
        Add any variable values found in the model dictionary to the variables list
        :param model_dictionary: the dictionary to be examined
        :param variables: the list to be appended
        """
        for key in model_dictionary:
            value = model_dictionary[key]
            if isinstance(value, dict):
                self._add_model_variables(value, variables)
            else:
                text = str_helper.to_string(value)
                if text.startswith('@@'):
                    variables.append(text)
