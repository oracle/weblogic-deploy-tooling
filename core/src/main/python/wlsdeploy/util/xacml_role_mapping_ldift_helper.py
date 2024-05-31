"""
Copyright (c) 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at https://oss.oracle.com/licenses/upl.

Module that contains the class for working with XACMLAuthorizer LDIFT files.
"""
from java.lang import IllegalArgumentException

from com.bea.security.xacml.cache.resource import ResourcePolicyIdUtil
from oracle.weblogic.deploy.util import PyOrderedDict as OrderedDict
from oracle.weblogic.deploy.util import WLSDeployArchiveIOException
from oracle.weblogic.deploy.util import XACMLException
from oracle.weblogic.deploy.util import XACMLUtil

from wlsdeploy.aliases.model_constants import EXPRESSION
from wlsdeploy.aliases.model_constants import UPDATE_MODE
from wlsdeploy.aliases.model_constants import XACML_DOCUMENT
from wlsdeploy.aliases.model_constants import XACML_ROLE_MAPPER
from wlsdeploy.aliases.model_constants import XACML_STATUS
from wlsdeploy.exception.exception_types import ExceptionType
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.util import string_utils
from wlsdeploy.util.cla_utils import CommandLineArgUtil
from wlsdeploy.util.ldift_helper import LdiftBase
from wlsdeploy.util.ldift_helper import LdiftLine

_logger = PlatformLogger('wlsdeploy.ldift')


class XacmlRoleMapperLdiftEntry(object):
    __class_name = 'XacmlRoleMapperLdiftEntry'
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

    def is_role_mapping_entry(self):
        return not self._is_header_element

    def get_role_name(self):
        _method_name = 'get_role_name'
        _logger.entering(class_name=self.__class_name, method_name=_method_name)

        result = None
        if not self._is_header_element:
            for line in self._lines:
                if line.get_key() == 'xacmlRole':
                    result = self.__escaper.unescapeString(line.get_value())
                    break

        _logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result

    def get_xacml_status(self):
        _method_name = 'get_xacml_status'
        _logger.entering(class_name=self.__class_name, method_name=_method_name)

        result = None
        if not self._is_header_element:
            for line in self._lines:
                if line.get_key() == 'xacmlStatus':
                    result = int(self.__escaper.unescapeString(line.get_value()))
                    break

        _logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result

    def get_role_mapping_expression(self, role_name):
        _method_name = 'get_role_mapping_expression'
        _logger.entering(role_name, class_name=self.__class_name, method_name=_method_name)

        success = True
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
                    result = xacml_parser.getRoleMappingEntitlementExpression()
                except XACMLException, xe:
                    _logger.warning('WLSDPLY-07116',role_name, xe.getLocalizedMessage(), error=xe,
                                    class_name=self.__class_name, method_name=_method_name)
                    success = False

        _logger.exiting(class_name=self.__class_name, method_name=_method_name, result=(success, result))
        return success, result

    def get_xacml_document(self, role_name):
        _method_name = 'get_xacml_document'
        _logger.entering(role_name, class_name=self.__class_name, method_name=_method_name)

        success = True
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
                    result = xacml_parser.getXACMLText()
                except XACMLException, xe:
                    _logger.warning('WLSDPLY-07116',role_name, xe.getLocalizedMessage(), error=xe,
                                    class_name=self.__class_name, method_name=_method_name)
                    success = False

        _logger.exiting(class_name=self.__class_name, method_name=_method_name, result=(success, result))
        return success, result


class XacmlRoleMapperLdift(LdiftBase):
    __class_name = 'XacmlRoleMapperLdift'
    __DEFAULT_ROLE_MAPPINGS_DICT = None

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
            entries.append(XacmlRoleMapperLdiftEntry(string_entry, self._exception_type))

        _logger.exiting(class_name=self.__class_name, method_name=_method_name, result=entries)
        return entries

    def get_role_mappings_dictionary(self, filter_defaults=True):
        _method_name = 'get_role_mappings_dictionary'
        _logger.entering(filter_defaults, class_name=self.__class_name, method_name=_method_name)

        result = OrderedDict()
        for ldift_entry in self._ldift_entries:
            if ldift_entry.is_role_mapping_entry():
                role_name = ldift_entry.get_role_name()
                if role_name is None:
                    _logger.warning('WLSDPLY-07123', class_name=self.__class_name, method_name=_method_name)
                    continue

                xacml_status = ldift_entry.get_xacml_status()
                if xacml_status is None:
                    _logger.warning('WLSDPLY-07134', XACML_STATUS, role_name,
                                    class_name=self.__class_name, method_name=_method_name)
                    xacml_status = 3
                if xacml_status != 3:
                    _logger.warning('WLSDPLY-07135', role_name, XACML_STATUS, xacml_status,
                                    class_name=self.__class_name, method_name=_method_name)

                xacml_document = None
                success, role_expression = ldift_entry.get_role_mapping_expression(role_name)
                if not success:
                    # warning already logged in get_role_mapping_expression()
                    continue

                if string_utils.is_empty(role_expression):
                    # Get the XACML document since the description field was empty.
                    success, xacml_document = ldift_entry.get_xacml_document(role_name)
                    if not success:
                        # warning already logged in get_xacml_document()
                        continue

                if not string_utils.is_empty(role_expression):
                    role_mapping = OrderedDict()
                    role_mapping[EXPRESSION] = role_expression
                    role_mapping[UPDATE_MODE] = 'replace'
                    role_mapping[XACML_STATUS] = xacml_status

                    if filter_defaults:
                        if not self._is_default_role_mapping(role_name, role_mapping):
                            result[role_name] = role_mapping
                        else:
                            _logger.fine('WLSDPLY-07117', role_name, EXPRESSION, role_mapping[EXPRESSION],
                                         class_name=self.__class_name, method_name=_method_name)
                    else:
                        result[role_name] = role_mapping
                elif not string_utils.is_empty(xacml_document):
                    if self._model_context.is_skip_archive():
                        _logger.notification('WLSDPLY-07126', role_name,
                                             CommandLineArgUtil.SKIP_ARCHIVE_FILE_SWITCH,
                                             class_name=self.__class_name, method_name=_method_name )
                        continue
                    elif self._model_context.is_remote():
                        _logger.todo('WLSDPLY-07127', role_name, '%s.xml' % role_name,
                                     class_name=self.__class_name, method_name=_method_name)
                        continue

                    archive_file = self._model_context.get_archive_file()
                    try:
                        role_mapping = OrderedDict()
                        role_mapping[XACML_DOCUMENT] = archive_file.addXACMLRoleFromText(role_name, xacml_document)
                        role_mapping[XACML_STATUS] = xacml_status
                        # There is no filtering when using a XACML Document directly...
                        result[role_name] = role_mapping
                    except (WLSDeployArchiveIOException, IllegalArgumentException), aex:
                        _logger.warning('WLSDPLY-07128', role_name, aex.getLocalizedMessage(), error=aex,
                                        class_name=self.__class_name, method_name=_method_name)
                else:
                    _logger.warning('WLSDPLY-07129', role_name, class_name=self.__class_name, method_name=_method_name)

        _logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result

    def _get_default_role_mapping_file_name(self):
        _method_name = '_get_default_role_mapping_file_name'
        wls_version = self._model_context.get_remote_wls_version()
        if wls_version is None:
            wls_version = self._model_context.get_local_wls_version()
        _logger.entering(wls_version, class_name=self.__class_name, method_name=_method_name)

        if self._weblogic_helper.is_weblogic_version_or_above('12.2.1'):
            file_name = '1412.json'
        else:
            file_name = '1213.json'

        _logger.exiting(class_name=self.__class_name, method_name=_method_name, result=file_name)
        return file_name

    def _get_default_role_mappings(self):
        _method_name = '_get_default_role_mappings'
        _logger.entering(class_name=self.__class_name, method_name=_method_name)

        if self.__DEFAULT_ROLE_MAPPINGS_DICT is None:
            file_name = self._get_default_role_mapping_file_name()
            self.__DEFAULT_ROLE_MAPPINGS_DICT = self.load_provider_defaults_file(XACML_ROLE_MAPPER, file_name)
            _logger.info('WLSDPLY-07125', file_name, class_name=self.__class_name, method_name=_method_name)

        _logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return self.__DEFAULT_ROLE_MAPPINGS_DICT

    def _is_default_role_mapping(self, role_name, role_mapping_dict):
        _method_name = '_is_default_role_mapping'
        _logger.entering(role_name, role_mapping_dict, class_name=self.__class_name, method_name=_method_name)

        result = False
        defaults = self._get_default_role_mappings()
        if role_name in defaults:
            _logger.finest('WLSDPLY-07118', role_name, class_name=self.__class_name, method_name=_method_name)
            if defaults[role_name] == role_mapping_dict[EXPRESSION]:
                result = True

        _logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result
