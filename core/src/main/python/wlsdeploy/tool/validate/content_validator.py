"""
Copyright (c) 2023, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
from java.lang import Boolean
from java.lang import Integer
from java.util import HashMap

from oracle.weblogic.deploy.validate import PasswordValidator
from oracle.weblogic.deploy.validate import ValidateException

from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import ADMIN_PASSWORD
from wlsdeploy.aliases.model_constants import ADMIN_USERNAME
from wlsdeploy.aliases.model_constants import CLUSTER
from wlsdeploy.aliases.model_constants import DEFAULT_REALM
from wlsdeploy.aliases.model_constants import DOMAIN_INFO
from wlsdeploy.aliases.model_constants import DYNAMIC_SERVERS
from wlsdeploy.aliases.model_constants import PASSWORD
from wlsdeploy.aliases.model_constants import PASSWORD_VALIDATOR
from wlsdeploy.aliases.model_constants import REALM
from wlsdeploy.aliases.model_constants import SECURITY
from wlsdeploy.aliases.model_constants import SECURITY_CONFIGURATION
from wlsdeploy.aliases.model_constants import SERVER_TEMPLATE
from wlsdeploy.aliases.model_constants import SYSTEM_PASSWORD_VALIDATOR
from wlsdeploy.aliases.model_constants import TOPOLOGY
from wlsdeploy.aliases.model_constants import USER
from wlsdeploy.aliases import alias_utils
from wlsdeploy.exception import exception_helper
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.util import dictionary_utils


class ContentValidator(object):
    """
    Class for validating consistency and compatibility of model folders and attributes.
    These checks are done after alias folder and attribute checks.
    These checks should be performed against a complete, merged model.

    Dynamic clusters is currently the only validation.
    """
    _class_name = 'ContentValidator'
    _logger = PlatformLogger('wlsdeploy.validate')

    def __init__(self, model_context, aliases):
        self._model_context = model_context
        self._aliases = aliases

    def validate_model(self, model_dict):
        """
        Validate the contents of the specified model.
        :param model_dict: A Python dictionary of the model to be validated
        :raises ValidationException: if problems occur during validation
        """
        _method_name = 'validate_model'
        self._logger.entering(class_name=self._class_name, method_name=_method_name)
        self.validate_user_passwords(model_dict)
        self.validate_dynamic_clusters(model_dict)
        self._logger.exiting(class_name=self._class_name, method_name=_method_name)

    def validate_dynamic_clusters(self, model_dict):
        """
        Validate that dynamic clusters have a unique server template.
        :param model_dict: A Python dictionary of the model to be validated
        :raises ValidationException: if problems occur during validation
        """
        _method_name = 'validate_dynamic_clusters'

        server_templates = []
        topology_folder = dictionary_utils.get_dictionary_element(model_dict, TOPOLOGY)
        clusters_folder = dictionary_utils.get_dictionary_element(topology_folder, CLUSTER)
        for cluster_name, cluster_fields in clusters_folder.items():
            dynamic_folder = dictionary_utils.get_element(cluster_fields, DYNAMIC_SERVERS)
            if dynamic_folder:
                server_template = dictionary_utils.get_element(dynamic_folder, SERVER_TEMPLATE)

                if not server_template:
                    self._logger.warning('WLSDPLY-05200', cluster_name, SERVER_TEMPLATE,
                                         class_name=self._class_name, method_name=_method_name)

                elif server_template in server_templates:
                    self._logger.warning('WLSDPLY-05201', cluster_name, SERVER_TEMPLATE, server_template,
                                         class_name=self._class_name, method_name=_method_name)

                else:
                    server_templates.append(server_template)

    def validate_user_passwords(self, model_dict):
        """
        Validate user passwords in the model is password validation is enabled
        :param model_dict: the model dictionary
        :raises ValidationException: if validation errors are found
        """
        _method_name = 'validate_user_passwords'
        self._logger.entering(class_name=self._class_name, method_name=_method_name)

        enabled = self._model_context.get_model_config().get_enable_create_domain_password_validation()
        if not alias_utils.convert_boolean(enabled):
            self._logger.info('WLSDPLY-05210', class_name=self._class_name, method_name=_method_name)
            self._logger.exiting(class_name=self._class_name, method_name=_method_name)
            return

        password_validator_config_map = self._get_system_password_validator_config_map(model_dict)
        password_validator = PasswordValidator(password_validator_config_map)
        admin_username, admin_password = self._get_admin_credentials(model_dict)
        users_dict = self._get_users_dictionary(model_dict)

        found_errors = False
        try:
            if not password_validator.validate(admin_username, admin_password):
                found_errors = True
        except ValidateException, ex:
            self._logger.severe('WLSDPLY-05207', ex.getLocalizedMessage(),
                                error=ex, class_name=self._class_name, method_name=_method_name)
            ce = exception_helper.create_validate_exception('WLSDPLY-05207', ex.getLocalizedMessage(), error=ex)
            self._logger.throwing(error=ce, class_name=self._class_name, method_name=_method_name)
            raise ce

        if users_dict:
            for user_name, user_dict in users_dict.items():
                password = dictionary_utils.get_element(user_dict, PASSWORD)
                try:
                    if not password_validator.validate(user_name, password):
                        found_errors = True
                except ValidateException, ex:
                    self._logger.severe('WLSDPLY-05208', user_name, ex.getLocalizedMessage(),
                                        error=ex, class_name=self._class_name, method_name=_method_name)
                    ce = exception_helper.create_validate_exception('WLSDPLY-05207', ex.getLocalizedMessage(),
                                                                  error=ex)
                    self._logger.throwing(error=ce, class_name=self._class_name, method_name=_method_name)
                    raise ce

        if found_errors:
            ce = exception_helper.create_validate_exception('WLSDPLY-05209')
            self._logger.throwing(error=ce, class_name=self._class_name, method_name=_method_name)
            raise ce

        self._logger.exiting(class_name=self._class_name, method_name=_method_name)

    def _get_system_password_validator_config_map(self, model_dict):
        _method_name = '_get_system_password_validator_config_map'
        self._logger.entering(class_name=self._class_name, method_name=_method_name)

        model_system_password_validator_dict = self._get_system_password_validator_model_dict(model_dict)
        system_password_validator_defaults_map = self._get_default_system_password_validator_config_map()
        self._override_defaults_with_model_values(system_password_validator_defaults_map, model_system_password_validator_dict)
        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=system_password_validator_defaults_map)
        return system_password_validator_defaults_map

    def _get_system_password_validator_model_dict(self, model_dict):
        _method_name = '_get_system_password_validator_model_dict'
        self._logger.entering(class_name=self._class_name, method_name=_method_name)

        result = dict()
        topology_folder = dictionary_utils.get_dictionary_element(model_dict, TOPOLOGY)
        security_config_folder = dictionary_utils.get_dictionary_element(topology_folder, SECURITY_CONFIGURATION)
        realm_name = dictionary_utils.get_element(security_config_folder, DEFAULT_REALM)
        if realm_name is None:
            location = LocationContext()
            location.append_location(SECURITY_CONFIGURATION)
            realm_name = self._aliases.get_model_attribute_default_value(location, DEFAULT_REALM)

        realms_folder = dictionary_utils.get_dictionary_element(security_config_folder, REALM)
        realm_folder = dictionary_utils.get_dictionary_element(realms_folder, realm_name)
        password_validators_folder = dictionary_utils.get_dictionary_element(realm_folder, PASSWORD_VALIDATOR)
        for pv_name, pv_fields in password_validators_folder.items():
            if SYSTEM_PASSWORD_VALIDATOR in pv_fields:
                result = dictionary_utils.get_dictionary_element(pv_fields, SYSTEM_PASSWORD_VALIDATOR)
                break
        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=result)
        return result

    def _get_default_system_password_validator_config_map(self):
        _method_name = '_get_default_system_password_validator_config_map'
        self._logger.entering(class_name=self._class_name, method_name=_method_name)

        location = _get_system_password_validator_location()
        attr_map = self._get_alias_attribute_names_and_types(location)

        default_map = HashMap()
        for attr_name, attr_type in attr_map.items():
            default_value = self._aliases.get_model_attribute_default_value(location, attr_name)
            self._logger.finer('WLSDPLY-05205', attr_name, attr_type, default_value,
                               class_name=self._class_name, method_name=_method_name)

            # This filters out attributes that do not matter to the validation logic,
            # which are all string types.
            #
            converted_value = None
            if attr_type == 'integer':
                if default_value is not None:
                    converted_value = Integer(default_value)
            elif attr_type == 'boolean':
                converted_value = alias_utils.convert_boolean(default_value)
                if converted_value is not None:
                    converted_value = Boolean(converted_value)

            self._logger.finer('WLSDPLY-05206', attr_name, converted_value,
                               class_name=self._class_name, method_name=_method_name)
            if converted_value is not None:
                default_map.put(attr_name, converted_value)

        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=default_map)
        return default_map

    def _override_defaults_with_model_values(self, defaults_map, model_dict):
        _method_name = '_override_defaults_with_model_values'

        if model_dict:
            for attr_name, attr_value in model_dict.items():
                # defaults_map built from the aliases so if the model contains an
                # attribute name not in the defaults, skip it...
                #
                self._logger.finer('WLSWDPLY-05202', attr_name, attr_value,
                                   class_name=self._class_name, method_name=_method_name)
                if attr_name not in defaults_map:
                    self._logger.finer('WLSWDPLY-05203', attr_name,
                                       class_name=self._class_name, method_name=_method_name)
                    continue

                override_value = self._get_override_value(attr_name, attr_value)
                if override_value is not None:
                    self._logger.finer('WLSWDPLY-05204', attr_name, override_value,
                                       class_name=self._class_name, method_name=_method_name)
                    defaults_map.put(attr_name, override_value)

    def _get_override_value(self, attr_name, model_value):
        _method_name = '_get_override_value'
        self._logger.entering(attr_name, model_value,
                              class_name=self._class_name, method_name=_method_name)

        attr_map = self._get_alias_attribute_names_and_types()
        attr_type = attr_map[attr_name]

        result = model_value
        if attr_type == 'integer':
            result = Integer.valueOf('%s' % model_value)
        elif attr_type == 'boolean':
            result = alias_utils.convert_boolean(model_value)
            if result is not None:
                result = Boolean.valueOf(result)

        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=result)
        return result

    def _get_admin_credentials(self, model_dict):
        _method_name = '_get_admin_credentials'
        self._logger.entering(class_name=self._class_name, method_name=_method_name)

        domain_info_folder = dictionary_utils.get_dictionary_element(model_dict, DOMAIN_INFO)
        admin_username = dictionary_utils.get_element(domain_info_folder, ADMIN_USERNAME)
        admin_password = dictionary_utils.get_element(domain_info_folder, ADMIN_PASSWORD)

        self._logger.exiting(class_name=self._class_name, method_name=_method_name)
        return admin_username, admin_password

    def _get_users_dictionary(self, model_dict):
        _method_name = '_get_users_dictionary'
        self._logger.entering(class_name=self._class_name, method_name=_method_name)

        topology_folder = dictionary_utils.get_dictionary_element(model_dict, TOPOLOGY)
        security_folder = dictionary_utils.get_dictionary_element(topology_folder, SECURITY)
        users_folder = dictionary_utils.get_dictionary_element(security_folder, USER)

        self._logger.exiting(class_name=self._class_name, method_name=_method_name)
        return users_folder

    def _get_alias_attribute_names_and_types(self, location = None):
        if location is None:
            location = _get_system_password_validator_location()
        return self._aliases.get_model_attribute_names_and_types(location)

def _get_system_password_validator_location():
    location = LocationContext()
    location.append_location(SECURITY_CONFIGURATION, REALM, PASSWORD_VALIDATOR, SYSTEM_PASSWORD_VALIDATOR)
    return location
