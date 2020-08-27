"""
Copyright (c) 2020, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""

import oracle.weblogic.deploy.util.PyOrderedDict as OrderedDict
from wlsdeploy.aliases.alias_constants import CREDENTIAL
from wlsdeploy.aliases.alias_constants import PASSWORD
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

_class_name = 'CredentialInjector'
_logger = PlatformLogger('wlsdeploy.tool.util')


class CredentialInjector(VariableInjector):
    """
    A specialized variable injector for use with the tokenizing of credential attributes.
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

    def check_and_tokenize(self, dictionary, location, model_param, model_value):
        """
        If the specified attribute is a security credential, add it to the injector,
        and replace the value in the model dictionary with the token.
        :param dictionary: the model dictionary containing the attribute
        :param location: the location of the attribute
        :param model_param: the name of the attribute
        :param model_value: the value of the attribute
        """
        aliases = self.get_aliases()
        attribute_type = aliases.get_model_attribute_type(location, model_param)
        folder_path = '.'.join(location.get_model_folders())

        if attribute_type == CREDENTIAL:
            injector_commands = OrderedDict()
            injector_commands.update({VARIABLE_VALUE: model_value})
            self.custom_injection(dictionary, model_param, location, injector_commands)

        elif attribute_type == PASSWORD:
            # STANDARD_PASSWORD_INJECTOR provides an empty value for the mapping
            self.custom_injection(dictionary, model_param, location, STANDARD_PASSWORD_INJECTOR)

        elif folder_path.endswith(self.JDBC_PROPERTIES_PATH):
            token = aliases.get_name_token(location)
            property_name = location.get_name_for_token(token)
            if (property_name == DRIVER_PARAMS_USER_PROPERTY) and (model_param == DRIVER_PARAMS_PROPERTY_VALUE):
                injector_commands = OrderedDict()
                injector_commands.update({VARIABLE_VALUE: model_value})
                self.custom_injection(dictionary, model_param, location, injector_commands)

        elif folder_path.endswith(MAIL_SESSION) and (model_param == PROPERTIES):
            # users and passwords are property assignments
            value = dictionary[model_param]
            is_string = isinstance(value, str)

            # for discover, value is a string at this point
            if is_string:
                dictionary[model_param] = OrderedDict()
                split = value.split(';')
                for assign in split:
                    halves = assign.split('=')
                    dictionary[model_param][halves[0]] = halves[1]

            self.custom_injection(dictionary, model_param, location, self.USER_COMMANDS)
            self.custom_injection(dictionary, model_param, location, self.PASSWORD_COMMANDS)

            if is_string:
                properties = dictionary[model_param]
                assigns = []
                for key in properties:
                    assigns.append('%s=%s' % (key, properties[key]))
                dictionary[model_param] = ';'.join(assigns)
