"""
Copyright (c) 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import os
import re

from oracle.weblogic.deploy.util import WLSDeployArchive

from wlsdeploy.aliases.model_constants import POLICY
from wlsdeploy.aliases.model_constants import RESOURCE_ID
from wlsdeploy.aliases.model_constants import WLS_POLICIES
from wlsdeploy.aliases.model_constants import XACML_DOCUMENT
from wlsdeploy.aliases.model_constants import XACML_STATUS
from wlsdeploy.exception.exception_types import ExceptionType
from wlsdeploy.tool.util.archive_helper import ArchiveList
from wlsdeploy.util import dictionary_utils
from wlsdeploy.util import string_utils
from wlsdeploy.util import unicode_helper as str_helper
from wlsdeploy.util.weblogic_policies_helper import WebLogicPoliciesHelper

_DOMAIN_SECURITY_SUBDIR = 'security'
_WL_HOME_AUTHORIZER_LDIFT_FILE = os.path.join('server', 'lib', 'XACMLAuthorizerInit.ldift')
_XACML_STATUS_REGEX = re.compile(r'^[0-3]$')

class WLSPolicies(object):
    __class_name = 'WLSPolicies'

    def __init__(self, domain_info, model_context, logger, exception_type=ExceptionType.CREATE,
                 validation_policies_map=None, archive_helper=None):
        self._domain_info = domain_info
        self._model_context = model_context
        self._logger = logger
        self._exception_type = exception_type

        self._archive_helper = archive_helper
        if archive_helper is None:
            archive_file_name = model_context.get_archive_file_name()
            if archive_file_name is not None:
                self._archive_helper = ArchiveList(archive_file_name, model_context, self._exception_type)
        self._wls_policies_map = validation_policies_map
        self._weblogic_policy_helper = None

        if domain_info is not None and WLS_POLICIES in domain_info:
            if not dictionary_utils.is_empty_dictionary_element(domain_info, WLS_POLICIES):
                self._wls_policies_map = domain_info[WLS_POLICIES]
                self._weblogic_policy_helper = WebLogicPoliciesHelper(self._model_context, self._logger,
                                                                      self._exception_type, self._archive_helper)

    def validate_policies(self):
        _method_name = 'validate_policies'
        self._logger.entering(class_name=self.__class_name, method_name=_method_name)
        if self._wls_policies_map:
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

        if self._wls_policies_map:
            self._weblogic_policy_helper.update_xacml_authorizer(self._wls_policies_map)

        self._logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def __validate_policy_object_fields_present(self, policy_name, policy_dict):
        _method_name = '__validate_policy_object_fields_present'
        self._logger.entering(policy_name, policy_dict, class_name=self.__class_name, method_name=_method_name)

        resource_id = dictionary_utils.get_element(policy_dict, RESOURCE_ID)
        policy = dictionary_utils.get_element(policy_dict, POLICY)
        xacml_document = dictionary_utils.get_element(policy_dict, XACML_DOCUMENT)
        xacml_status = dictionary_utils.get_element(policy_dict, XACML_STATUS, '3')
        if not isinstance(xacml_status, (str, unicode)):
            xacml_status = str_helper.to_string(xacml_status)

        is_valid = True
        if not string_utils.is_empty(xacml_status) and _XACML_STATUS_REGEX.match(xacml_status) is None:
            self._logger.severe('WLSDPLY-12604', policy_name, XACML_STATUS, xacml_status,
                                class_name=self.__class_name, method_name=_method_name)
            is_valid = False

        if not isinstance(resource_id, (str, unicode)) or len(resource_id) == 0:
            is_valid = False
            self._logger.severe('WLSDPLY-12600', policy_name, RESOURCE_ID,
                                class_name=self.__class_name, method_name=_method_name)

        if isinstance(policy, (str, unicode)) and not string_utils.is_empty(policy):
            pass
        elif isinstance(xacml_document, (str, unicode)) and not string_utils.is_empty(xacml_document):
            # validate xacml_document
            if WLSDeployArchive.isPathIntoArchive(xacml_document) and \
                    (self._archive_helper is None or not self._archive_helper.contains_file(xacml_document)):

                # log level depends on validate configuration
                validate_configuration = self._model_context.get_validate_configuration()
                if validate_configuration.allow_unresolved_archive_references():
                    log_method = self._logger.info
                else:
                    log_method = self._logger.severe
                    is_valid = False

                log_method('WLSDPLY-12601', policy_name, XACML_DOCUMENT, xacml_document,
                           class_name=self.__class_name, method_name=_method_name)
        else:
            self._logger.severe('WLSDPLY-12603', policy_name, POLICY, XACML_DOCUMENT,
                                class_name=self.__class_name, method_name=_method_name)
            is_valid = False

        self._logger.exiting(class_name=self.__class_name, method_name=_method_name, result=is_valid)
        return is_valid


def get_wls_policies_validator(policies_map, model_context, logger):
    return WLSPolicies(None, model_context, logger, exception_type=ExceptionType.CREATE, validation_policies_map=policies_map)
