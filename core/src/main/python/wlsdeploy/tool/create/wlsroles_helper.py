"""
Copyright (c) 2019, 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
from java.io import File

from oracle.weblogic.deploy.json import JsonException
from oracle.weblogic.deploy.json import JsonStreamTranslator
from oracle.weblogic.deploy.util import FileUtils

from wlsdeploy.aliases.model_constants import APPEND
from wlsdeploy.aliases.model_constants import EXPRESSION
from wlsdeploy.aliases.model_constants import PREPEND
from wlsdeploy.aliases.model_constants import REPLACE
from wlsdeploy.aliases.model_constants import UPDATE_MODE
from wlsdeploy.aliases.model_constants import WLS_ROLES
from wlsdeploy.exception import exception_helper
from wlsdeploy.util import dictionary_utils
from wlsdeploy.util import string_utils
from wlsdeploy.util.weblogic_roles_helper import WebLogicRolesHelper

WLS_GLOBAL_ROLES = None
WLS_ROLE_UPDATE_OPERAND = '|'

class WLSRoles(object):
    """
    Handle the WLSRoles section from the model domainInfo
    """
    __class_name = 'WLSRoles'
    __DEFAULT_ROLES_PATH = 'oracle/weblogic/deploy/security/XACMLRoleMapperDefaults/'

    def __init__(self, domain_info, domain_home, wls_helper, exception_type, logger, validation_roles_map = None):
        global WLS_GLOBAL_ROLES

        self.logger = logger
        self._wls_helper = wls_helper
        self._wls_roles_map = None
        self._domain_security_folder = None
        self._validation_roles_map = validation_roles_map

        if WLS_GLOBAL_ROLES is None:
            default_roles = self._load_default_roles()
            if default_roles:
                WLS_GLOBAL_ROLES = default_roles

        if domain_info is not None:
            if not dictionary_utils.is_empty_dictionary_element(domain_info, WLS_ROLES):
                self._wls_roles_map = domain_info[WLS_ROLES]
                self._domain_security_folder = File(domain_home, 'security').getPath()
                self._weblogic_roles_helper = WebLogicRolesHelper(logger, exception_type, self._domain_security_folder)

    def process_roles(self):
        """
        Process the WebLogic roles contained in the domainInfo section of the model when specified.
        """
        _method_name = 'process_roles'
        self.logger.entering(self._domain_security_folder, self._wls_roles_map, class_name=self.__class_name, method_name=_method_name)
        if self._wls_roles_map is not None:
            role_expressions = self._process_roles_map(self._wls_roles_map)
            if role_expressions is not None and len(role_expressions) > 0:
                self.logger.info('WLSDPLY-12500', role_expressions.keys(), class_name=self.__class_name, method_name=_method_name)
                self._update_xacml_role_mapper(role_expressions)
        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def validate_roles(self):
        """
        Validate WLSRoles section of the domainInfo independent of any domain home location
        """
        _method_name = 'validate_roles'
        self.logger.entering(self._validation_roles_map, class_name=self.__class_name, method_name=_method_name)
        if self._validation_roles_map is not None and len(self._validation_roles_map) > 0:
            self._validate_update_mode(self._validation_roles_map)
            self._process_roles_map(self._validation_roles_map)
        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def _process_roles_map(self, roles_map):
        """
        Loop through the WebLogic roles listed in the domainInfo and create a map of the role to the expression 
        """
        global WLS_GLOBAL_ROLES

        _method_name = '_process_roles_map'
        self.logger.entering(class_name=self.__class_name, method_name=_method_name)

        result = {}
        for role in roles_map.keys():
            # Get the role expression and if the role should be an update to the default set of roles
            expression = self._get_role_expression(role, roles_map)
            if string_utils.is_empty(expression):
                self.logger.warning('WLSDPLY-12501', role, class_name=self.__class_name, method_name=_method_name)
                continue
            update_role = self._is_role_update_mode(role, roles_map)
            if update_role and role not in WLS_GLOBAL_ROLES:
                self.logger.warning('WLSDPLY-12502', role, class_name=self.__class_name, method_name=_method_name)
                update_role = False
            # Add the role and expression to the map of roles to be processed 
            if update_role:
                expression = self._update_role_epression(role, expression, roles_map)
            result[role] = expression

        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return result

    def _update_xacml_role_mapper(self, role_expression_map):
        """
        Update the XACML role mapper based on the supplied map of WebLogic roles with expressions
        """
        _method_name = '_update_xacml_role_mapper'
        self.logger.entering(role_expression_map, class_name=self.__class_name, method_name=_method_name)
        self._weblogic_roles_helper.update_xacml_role_mapper(role_expression_map)
        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def _get_role_expression(self, role_name, roles_map):
        """
        Determine if the role has an expression defined in the model
        :return: the expression if the model value is present
        """
        result = None
        role_map = roles_map[role_name]
        if EXPRESSION in role_map:
            result = role_map[EXPRESSION]
        return result

    def _is_role_update_mode(self, role_name, roles_map):
        """
        Determine if the role update mode indicates that a role update is specified
        :return: True if the update mode value is present and set to append or prepend mode
        """
        result = False
        role_map = roles_map[role_name]
        if UPDATE_MODE in role_map:
            mode = role_map[UPDATE_MODE]
            if not string_utils.is_empty(mode):
                mode = mode.lower()
                if APPEND == mode or PREPEND == mode:
                    result = True
        return result

    def _update_role_epression(self, role_name, expression_value, roles_map):
        """
        Lookup the default role definition and logically OR the expression
        Based on the update mode the expression is appended or prepended
        :return: the updated role expression
        """
        global WLS_GLOBAL_ROLES

        result = expression_value
        role_map = roles_map[role_name]
        if UPDATE_MODE in role_map:
            mode = role_map[UPDATE_MODE]
            if not string_utils.is_empty(mode):
                mode = mode.lower()
                if APPEND == mode:
                    result = WLS_GLOBAL_ROLES[role_name] + WLS_ROLE_UPDATE_OPERAND + expression_value
                elif PREPEND == mode:
                    result = expression_value + WLS_ROLE_UPDATE_OPERAND + WLS_GLOBAL_ROLES[role_name]
        return result

    def _validate_update_mode(self, roles_map):
        """
        Check that the UpdateMode value of a role is one of append, prepend or replace
        Provide a warning for other values as these will be treated as the default of replace
        """
        _method_name = '_validate_update_mode'
        self.logger.entering(class_name=self.__class_name, method_name=_method_name)

        for role_name in roles_map.keys():
            role_map = roles_map[role_name]
            if UPDATE_MODE in role_map:
                mode = role_map[UPDATE_MODE]
                if not string_utils.is_empty(mode):
                    mode = mode.lower()
                    if APPEND == mode or PREPEND == mode or REPLACE == mode:
                        continue
                    self.logger.warning('WLSDPLY-12503', role_name, class_name=self.__class_name,
                                        method_name=_method_name)

        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def _load_default_roles(self):
        _method_name = '_load_default_roles'

        if self._wls_helper is not None:
            if self._wls_helper.is_weblogic_version_or_above('12.2.1'):
                file_name = '1412.json'
            else:
                file_name = '1213.json'
        else:
            # unit tests...
            file_name = '1412.json'

        defaults_file_path = '%s%s' % (self.__DEFAULT_ROLES_PATH, file_name)
        defaults_input_stream = FileUtils.getResourceAsStream(defaults_file_path)
        if defaults_input_stream is None:
            ex = exception_helper.create_create_exception('WLSDPLY-07106', 'XACMLRoleMapper', defaults_file_path)
            self.logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex

        try:
            json_translator = JsonStreamTranslator('%s/%s' % ('XACMLRoleMapper', file_name), defaults_input_stream)
            result = json_translator.parse()
        except JsonException, jex:
            ex = exception_helper.create_create_exception('WLSDPLY-07124', 'XACMLRoleMapper',
                                                   defaults_file_path, jex.getLocalizedMessage(), error=jex)
            self.logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex

        self.logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result


def get_wls_roles_validator(roles_map, logger):
    """
    Obtain a WLSRoles helper only for the validation of the WLSRoles section
    """
    return WLSRoles(None, None, None, None, logger, validation_roles_map = roles_map)
