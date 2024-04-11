"""
Copyright (c) 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import os

from wlsdeploy.aliases.model_constants import POLICY
from wlsdeploy.aliases.model_constants import RESOURCE_ID
from wlsdeploy.aliases.model_constants import WLS_POLICIES
from wlsdeploy.exception.exception_types import ExceptionType
from wlsdeploy.util import dictionary_utils
from wlsdeploy.util.weblogic_policies_helper import WebLogicPoliciesHelper

_DOMAIN_SECURITY_SUBDIR = 'security'
_WL_HOME_AUTHORIZER_LDIFT_FILE = os.path.join('server', 'lib', 'XACMLAuthorizerInit.ldift')


class WLSPolicies(object):
    __class_name = 'WLSPolicies'

    def __init__(self, domain_info, model_context, logger, exception_type=ExceptionType.CREATE, validation_policies_map=None):
        self._domain_info = domain_info
        self._model_context = model_context
        self._logger = logger
        self._exception_type = exception_type
        self._wls_policies_map = validation_policies_map
        self._weblogic_policy_helper = None

        if domain_info is not None and WLS_POLICIES in domain_info:
            if not dictionary_utils.is_empty_dictionary_element(domain_info, WLS_POLICIES):
                self._wls_policies_map = domain_info[WLS_POLICIES]
                self._weblogic_policy_helper = WebLogicPoliciesHelper(self._model_context, self._logger, self._exception_type)

    def validate_policies(self):
        _method_name = 'validate_policies'
        self._logger.entering(class_name=self.__class_name, method_name=_method_name)
        if self._wls_policies_map is not None and len(self._wls_policies_map) > 0:
            # dictionary keyed by policy resource ID with the value being the artificial name that defined it
            policy_resource_map = dict()
            for key, value in self._wls_policies_map.iteritems():
                if not self.__validate_policy_object_fields_present(key, value):
                    continue

                resource_id = dictionary_utils.get_element(value, RESOURCE_ID)
                if resource_id in policy_resource_map:
                    self._logger.severe('WLSDPLY-12602', key, RESOURCE_ID, resource_id, policy_resource_map[resource_id],
                                        class_name=self.__class_name, method_name=_method_name)
                else:
                    policy_resource_map[resource_id] = key

        self._logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def process_policies(self):
        _method_name = 'process_policies'
        self._logger.entering(class_name=self.__class_name, method_name=_method_name)

        if self._wls_policies_map is not None:
            wls_helper = self._model_context.get_weblogic_helper()
            if wls_helper is not None and wls_helper.is_weblogic_version_or_above('12.2.1'):
                self._weblogic_policy_helper.update_xacml_authorizer(self._wls_policies_map)
            else:
                self._logger.warning('WLSDPLY-12603', '12.2.1.0.0', self._model_context.get_local_wls_version(),
                                     class_name=self.__class_name, method_name=_method_name)

        self._logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def __validate_policy_object_fields_present(self, policy_name, policy_dict):
        _method_name = '__validate_policy_object_fields_present'
        self._logger.entering(policy_name, policy_dict, class_name=self.__class_name, method_name=_method_name)

        is_valid = True
        resource_id = dictionary_utils.get_element(policy_dict, RESOURCE_ID)
        policy = dictionary_utils.get_element(policy_dict, POLICY)
        if not isinstance(resource_id, (str, unicode)) or len(resource_id) == 0:
            is_valid = False
            self._logger.severe('WLSDPLY-12600', policy_name, RESOURCE_ID,
                                class_name=self.__class_name, method_name=_method_name)
        if not isinstance(policy, (str, unicode)) or len(policy) == 0:
            is_valid = False
            self._logger.severe('WLSDPLY-12600', policy_name, POLICY,
                                class_name=self.__class_name, method_name=_method_name)
        self._logger.exiting(class_name=self.__class_name, method_name=_method_name, result=is_valid)
        return is_valid


def get_wls_policies_validator(policies_map, model_context, logger):
    return WLSPolicies(None, model_context, logger, exception_type=ExceptionType.CREATE, validation_policies_map=policies_map)
