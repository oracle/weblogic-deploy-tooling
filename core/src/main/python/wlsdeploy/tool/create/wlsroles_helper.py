"""
Copyright (c) 2019, 2022, Oracle Corporation and/or its affiliates.  All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
from java.io import File
from wlsdeploy.aliases.model_constants import APPEND
from wlsdeploy.aliases.model_constants import EXPRESSION
from wlsdeploy.aliases.model_constants import PREPEND
from wlsdeploy.aliases.model_constants import REPLACE
from wlsdeploy.aliases.model_constants import UPDATE_MODE
from wlsdeploy.aliases.model_constants import WLS_ROLES
from wlsdeploy.util import dictionary_utils
from wlsdeploy.util import string_utils
from wlsdeploy.util.weblogic_roles_helper import WebLogicRolesHelper

WLS_GLOBAL_ROLES = {
    'Admin': '?weblogic.entitlement.rules.AdministrativeGroup(Administrators)',
    'Deployer': '?weblogic.entitlement.rules.AdministrativeGroup(Deployers)',
    'Operator': '?weblogic.entitlement.rules.AdministrativeGroup(Operators)',
    'Monitor': '?weblogic.entitlement.rules.AdministrativeGroup(Monitors)',
    'Anonymous': 'Grp(everyone)',
    'AppTester': '?weblogic.entitlement.rules.OwnerIDDGroup(AppTesters)',
    'CrossDomainConnector': '?weblogic.entitlement.rules.OwnerIDDGroup(CrossDomainConnectors)',
    'AdminChannelUser': '?weblogic.entitlement.rules.OwnerIDDGroup(AdminChannelUsers)'
}
WLS_ROLE_UPDATE_OPERAND = '|'


class WLSRoles(object):
    """
    Handle the WLSRoles section from the model domainInfo
    """
    __class_name = 'WLSRoles'

    def __init__(self, domain_info, domain_home, wls_helper, exception_type, logger, validation_roles_map = None):
        self.logger = logger
        self._wls_helper = wls_helper
        self._wls_roles_map = None
        self._domain_security_folder = None
        self._validation_roles_map = validation_roles_map
        
        if domain_info is not None:
            if not dictionary_utils.is_empty_dictionary_element(domain_info, WLS_ROLES):
               self._wls_roles_map = domain_info[WLS_ROLES]
               self._domain_security_folder = File(domain_home, 'security').getPath()
               self._weblogic_roles_helper = WebLogicRolesHelper(logger, exception_type, self._domain_security_folder)

    def process_roles(self):
        """
        Process the WebLogic roles contained in the domainInfo section of the model when specified
        Support for the WebLogic roles handling is when using WebLogic Server 12.2.1 or greater
        """
        _method_name = 'process_roles'
        self.logger.entering(self._domain_security_folder, self._wls_roles_map, class_name=self.__class_name, method_name=_method_name)
        if self._wls_roles_map is not None:
            # Process the WLSRoles section after checking for proper version support
            if self._wls_helper is not None and not self._wls_helper.is_weblogic_version_or_above('12.2.1'):
                self.logger.warning('WLSDPLY-12504', self._wls_helper.get_actual_weblogic_version(), class_name=self.__class_name, method_name=_method_name)
            else:
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


def validator(roles_map, logger):
    """
    Obtain a WLSRoles helper only for the validation of the WLSRoles section
    """
    return WLSRoles(None, None, None, None, logger, validation_roles_map = roles_map)
