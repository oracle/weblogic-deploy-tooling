"""
Copyright (c) 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at https://oss.oracle.com/licenses/upl.

Module that contains the class for working with XACMLAuthorizer LDIFT files.
"""
from com.bea.security.xacml.cache.resource import ResourcePolicyIdUtil
from oracle.weblogic.deploy.util import PyOrderedDict as OrderedDict
from oracle.weblogic.deploy.util import XACMLException
from oracle.weblogic.deploy.util import XACMLUtil

from wlsdeploy.aliases.model_constants import POLICY
from wlsdeploy.aliases.model_constants import RESOURCE_ID
from wlsdeploy.aliases.model_constants import XACML_AUTHORIZER
from wlsdeploy.exception.exception_types import ExceptionType
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.util.ldift_helper import LdiftBase
from wlsdeploy.util.ldift_helper import LdiftLine

_logger = PlatformLogger('wlsdeploy.ldift')


class XacmlAuthorizerLdiftEntry(object):
    __class_name = 'XacmlAuthorizerLdiftEntry'
    __escaper = ResourcePolicyIdUtil.getEscaper()

    def __init__(self, lines=None, exception_type=ExceptionType.DISCOVER):
        self._lines = list()
        self._exception_type = exception_type
        self._is_header_element = True

        if lines is not None:
            for line in lines:
                ldift_line = LdiftLine(line)
                if ldift_line.get_key() == 'cn':
                    self._is_header_element = False
                self._lines.append(LdiftLine(line))

    def is_policy_entry(self):
        return not self._is_header_element

    def get_resource_id(self):
        _method_name = 'get_resource_id'
        _logger.entering(class_name=self.__class_name, method_name=_method_name)

        result = None
        if not self._is_header_element:
            for line in self._lines:
                if line.get_key() == 'cn':
                    result = self.__escaper.unescapeString(line.get_value())
                    last_colon_index = result.rfind(':')
                    if last_colon_index != -1:
                        result = result[last_colon_index + 1:]
                        result = self.__escaper.unescapeString(result)
                    break

        _logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result

    def get_entitlement_policy(self):
        _method_name = 'get_entitlement_policy'
        _logger.entering(class_name=self.__class_name, method_name=_method_name)

        result = None
        if not self._is_header_element:
            value = None
            for line in self._lines:
                if line.get_key() == 'xacmlDocument':
                    value = line.get_value()
                    break

            if value is not None:
                try:
                    xacml_parser = XACMLUtil(value)
                    result = xacml_parser.getPolicyEntitlementExpression()
                except XACMLException, xe:
                    _logger.warning('WLSDPLY-07103',xe.getLocalizedMessage(), error=xe,
                                    class_name=self.__class_name, method_name=_method_name)

        _logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result


class XacmlAuthorizerLdift(LdiftBase):
    __class_name = 'XacmlAuthorizerLdift'
    __policy_name_pattern = 'WLSPolicy-%s'
    __DEFAULT_POLICIES_DICT = None

    def __init__(self, ldift_file_name, model_context, exception_type=ExceptionType.DISCOVER):
        LdiftBase.__init__(self, model_context, exception_type)

        self._ldift_file_name = ldift_file_name
        self._weblogic_helper = model_context.get_weblogic_helper()
        self._ldift_entries = self.read_ldift_file(ldift_file_name)


    # Override
    def read_ldift_file(self, ldift_file_name):
        _method_name = 'read_ldift_file'
        _logger.entering(ldift_file_name, class_name=self.__class_name, method_name=_method_name)

        entries = list()
        string_entries = LdiftBase.read_ldift_file(self, ldift_file_name)
        for string_entry in string_entries:
            entries.append(XacmlAuthorizerLdiftEntry(string_entry, self._exception_type))

        _logger.exiting(class_name=self.__class_name, method_name=_method_name, result=entries)
        return entries

    def get_policies_dictionary(self, filter_defaults=True):
        _method_name = 'get_policies_dictionary'
        _logger.entering(filter_defaults, class_name=self.__class_name, method_name=_method_name)

        count = 1
        result = OrderedDict()
        for ldift_entry in self._ldift_entries:
            if ldift_entry.is_policy_entry():
                policy_name = self.__policy_name_pattern % count
                policy = OrderedDict()

                policy[RESOURCE_ID] = ldift_entry.get_resource_id()
                if policy[RESOURCE_ID] is None:
                    _logger.warning('WLSDPLY-07122', RESOURCE_ID,
                                    class_name=self.__class_name, method_name=_method_name)
                    continue

                policy[POLICY] = ldift_entry.get_entitlement_policy()
                if policy[POLICY] is None:
                    # warning logged inside get_entitlement_policy() function
                    continue

                if filter_defaults:
                    if not self._is_default_policy(policy):
                        result[policy_name] = policy
                        count += 1
                    else:
                        _logger.fine('WLSDPLY-07104', RESOURCE_ID, policy[RESOURCE_ID], POLICY,
                                     policy[POLICY], class_name=self.__class_name, method_name=_method_name)
                else:
                    result[policy_name] = policy
                    count += 1

        _logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result

    def _get_default_policy_file_name(self):
        _method_name = '_get_default_policy_file_name'
        wls_version = self._model_context.get_remote_wls_version()
        if wls_version is None:
            wls_version = self._model_context.get_local_wls_version()
        _logger.entering(wls_version, class_name=self.__class_name, method_name=_method_name)

        if self._weblogic_helper.is_weblogic_version_or_above('14.1.2'):
            file_name = '1412.json'
        elif self._weblogic_helper.is_weblogic_version_or_above('14.1.1'):
            file_name = '1411.json'
        elif self._weblogic_helper.is_weblogic_version_or_above('12.2.1.3'):
            file_name = '12214.json'
        elif self._weblogic_helper.is_weblogic_version_or_above('12.2.1'):
            file_name = '12212.json'
        elif self._weblogic_helper.is_weblogic_version_or_above('12.1.3'):
            file_name = '1213.json'
        elif self._weblogic_helper.is_weblogic_version_or_above('12.1.2'):
            file_name = '1212.json'
        elif self._weblogic_helper.is_weblogic_version_or_above('12.1.1'):
            file_name = '1211.json'
        else:
            file_name = '1036.json'

        _logger.exiting(class_name=self.__class_name, method_name=_method_name, result=file_name)
        return file_name

    def _get_default_policies(self):
        _method_name = '_get_default_policies'
        _logger.entering(class_name=self.__class_name, method_name=_method_name)

        if self.__DEFAULT_POLICIES_DICT is None:
            file_name = self._get_default_policy_file_name()
            self.__DEFAULT_POLICIES_DICT = self.load_provider_defaults_file(XACML_AUTHORIZER, file_name)
            _logger.info('WLSDPLY-07107', file_name, class_name=self.__class_name, method_name=_method_name)

        _logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return self.__DEFAULT_POLICIES_DICT

    # This function is potentially called thousands of times in 14.1.2+
    # so don't log unless the FINEST level is enabled.
    #
    def _is_default_policy(self, policy_dict):
        _method_name = '_is_default_policy'
        if _logger.is_finest_enabled():
            _logger.entering(policy_dict, class_name=self.__class_name, method_name=_method_name)

        result = False
        defaults = self._get_default_policies()
        if policy_dict[RESOURCE_ID] in defaults:
            _logger.finest('WLSDPLY-07108', RESOURCE_ID, policy_dict[RESOURCE_ID],
                           class_name=self.__class_name, method_name=_method_name)
            if defaults[policy_dict[RESOURCE_ID]] == policy_dict[POLICY]:
                result = True

        if _logger.is_finest_enabled():
            _logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result
