"""
Copyright (c) 2019, Oracle and/or its affiliates. All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl.
"""
from java.io import File
from wlsdeploy.aliases import alias_utils
from wlsdeploy.aliases.model_constants import EXPRESSION
from wlsdeploy.aliases.model_constants import UPDATE
from wlsdeploy.aliases.model_constants import WLS_ROLES
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

    def __init__(self, domain_info, domain_home, exception_type, logger):
        self.logger = logger
        self._wls_roles_map = None
        self._domain_security_folder = None
        
        if domain_info is not None:
            if WLS_ROLES in domain_info:
               self._wls_roles_map = domain_info[WLS_ROLES]
               self._domain_security_folder = File(domain_home, 'security').getPath()
               self._weblogic_roles_helper = WebLogicRolesHelper(logger, exception_type, self._domain_security_folder)

    def process_roles(self):
        """
        Process the WebLogic roles contained in the domainInfo section of the model when specified 
        """
        _method_name = 'process_roles'
        self.logger.entering(self._domain_security_folder, self._wls_roles_map, class_name=self.__class_name, method_name=_method_name)
        if self._wls_roles_map is not None:
            role_expressions = self._process_roles_map()
            if role_expressions is not None:
                self.logger.info('The WebLogic role mapper will be updated with the roles: {0}', role_expressions.keys(), class_name=self.__class_name, method_name=_method_name)
                self._update_xacml_role_mapper(role_expressions)
        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def _process_roles_map(self):
        """
        Loop through the WebLogic roles listed in the domainInfo and create a map of the role to the expression 
        """
        _method_name = '_process_roles_map'
        self.logger.entering(class_name=self.__class_name, method_name=_method_name)
        result = {}
        role_list = self._wls_roles_map.keys()
        for role in role_list:
            # Get the role expression and if the role should be an update to the default set of roles
            expression = self._get_role_expression(role)
            if expression is None:
                self.logger.warning('The role {0} has no specified expression value', role, class_name=self.__class_name, method_name=_method_name)
                continue
            update_role = self._is_role_updated(role)
            if update_role and role not in WLS_GLOBAL_ROLES:
                self.logger.warning('The role {0} is not a WebLogic global role and will use the expression as specified', role, class_name=self.__class_name, method_name=_method_name)
                update_role = False
            # Add the role and expression to the map of roles to be processed 
            if update_role:
                expression = self._update_role_epression(role, expression)
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

    def _get_role_expression(self, role_name):
        """
        Determine if the role has an expression defined in the model
        :return: the expression if the model value is present
        """
        result = None
        role_map = self._wls_roles_map[role_name]
        if EXPRESSION in role_map:
            result = role_map[EXPRESSION]
        return result

    def _is_role_updated(self, role_name):
        """
        Determine if the role is to be updated with the default definition
        :return: True if the model value is present and indicates true, False otherwise
        """
        role_map = self._wls_roles_map[role_name]
        if UPDATE in role_map:
            value = alias_utils.convert_to_type('boolean', role_map[UPDATE])
            return value == 'true'
        return False

    def _update_role_epression(self, role_name, expression_value):
        """
        Lookup the default role definition and logically OR the expressions
        :return: the updated role expression
        """
        return WLS_GLOBAL_ROLES[role_name] + WLS_ROLE_UPDATE_OPERAND + expression_value
