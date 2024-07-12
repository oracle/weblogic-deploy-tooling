"""
Copyright (c) 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at https://oss.oracle.com/licenses/upl.

Module that contains the class for working with DefaultCredentialMapper LDIFT files.
"""
from com.bea.security.xacml.cache.resource import ResourcePolicyIdUtil
from oracle.weblogic.deploy.encrypt import EncryptionException
from oracle.weblogic.deploy.util import PyOrderedDict as OrderedDict

from wlsdeploy.aliases.alias_constants import PASSWORD_TOKEN
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import CROSS_DOMAIN
from wlsdeploy.aliases.model_constants import METHOD
from wlsdeploy.aliases.model_constants import PATH
from wlsdeploy.aliases.model_constants import PROTOCOL
from wlsdeploy.aliases.model_constants import REMOTE_DOMAIN
from wlsdeploy.aliases.model_constants import REMOTE_HOST
from wlsdeploy.aliases.model_constants import REMOTE_PASSWORD
from wlsdeploy.aliases.model_constants import REMOTE_PORT
from wlsdeploy.aliases.model_constants import REMOTE_RESOURCE
from wlsdeploy.aliases.model_constants import REMOTE_USER
from wlsdeploy.aliases.model_constants import USER
from wlsdeploy.aliases.model_constants import WLS_USER_PASSWORD_CREDENTIAL_MAPPINGS
from wlsdeploy.exception.exception_types import ExceptionType
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.util import string_utils
from wlsdeploy.util.ldift_helper import LdiftBase
from wlsdeploy.util.ldift_helper import LdiftLine

_logger = PlatformLogger('wlsdeploy.ldift')


class DefaultCredentialMapperLdiftEntry(object):
    __class_name = 'DefaultCredentialMapperLdiftEntry'
    __escaper = ResourcePolicyIdUtil.getEscaper()
    __log_mask = '<redacted>'

    def __init__(self, lines=None, exception_type=ExceptionType.DISCOVER):
        self._lines = list()
        self._exception_type = exception_type
        self._is_credential_map_entry = False
        self._is_resource_map_entry = False

        if lines is not None:
            for line in lines:
                ldift_line = LdiftLine(line)
                # Either objectclass or objectClass
                if ldift_line.get_key().lower() == 'objectclass':
                    if ldift_line.get_value() == 'passwordCredentialMap':
                        self._is_credential_map_entry = True
                    elif ldift_line.get_value() == 'resourceMap':
                        self._is_resource_map_entry = True

                self._lines.append(LdiftLine(line))

    def is_credential_map_entry(self):
        return self._is_credential_map_entry

    def is_resource_map_entry(self):
        return self._is_resource_map_entry

    def get_credential_map_resource_name(self):
        _method_name = 'get_credential_map_resource_name'
        _logger.entering(class_name=self.__class_name, method_name=_method_name)

        result = None
        if self._is_credential_map_entry:
            result = self.__escaper.unescapeString(self._get_attribute_value('resourceName'))

        _logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result

    def get_credential_map_principal_name(self):
        _method_name = 'get_credential_map_principal_name'
        _logger.entering(class_name=self.__class_name, method_name=_method_name)

        result = None
        if self._is_credential_map_entry:
            result = self.__escaper.unescapeString(self._get_attribute_value('principalName'))

        _logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result

    def get_credential_map_principal_password(self):
        _method_name = 'get_credential_map_principal_password'
        _logger.entering(class_name=self.__class_name, method_name=_method_name)

        result = None
        if self._is_credential_map_entry:
            result = self.__escaper.unescapeString(self._get_attribute_value('principalPassword'))

        _logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result

    def get_credential_map_resource_name_map(self):
        _method_name = 'get_credential_map_principal_password'
        _logger.entering(class_name=self.__class_name, method_name=_method_name)

        result = OrderedDict()
        if self._is_credential_map_entry:
            resource_name = self.get_credential_map_resource_name()
            if not string_utils.is_empty(resource_name):
                result = self._get_resource_name_dict(resource_name)

        _logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result

    def is_credential_map_cross_domain(self):
        _method_name = 'is_credential_map_cross_domain'
        _logger.entering(class_name=self.__class_name, method_name=_method_name)

        result = False
        if self._is_credential_map_entry:
            resource_name = self.get_credential_map_resource_name()

            if resource_name is not None:
                resource_name_dict = self._get_resource_name_dict(resource_name)
                if 'protocol' in resource_name_dict and resource_name_dict['protocol'] == 'cross-domain-protocol':
                    result = True

        _logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result

    def is_credential_map_remote_resource(self):
        _method_name = 'is_credential_map_remote_resource'
        _logger.entering(class_name=self.__class_name, method_name=_method_name)

        result = not self.is_credential_map_cross_domain()

        _logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result

    def get_resource_map_resource_name(self):
        _method_name = 'get_resource_map_resource_name'
        _logger.entering(class_name=self.__class_name, method_name=_method_name)

        result = None
        if self._is_resource_map_entry:
            result = self.__escaper.unescapeString(self._get_attribute_value('resourceName'))

        _logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result

    def get_resource_map_principal_name(self):
        _method_name = 'get_resource_map_principal_name'
        _logger.entering(class_name=self.__class_name, method_name=_method_name)

        result = None
        if self._is_resource_map_entry:
            result = self.__escaper.unescapeString(self._get_attribute_value('principalName'))

        _logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result

    ###########################################################################
    #                         private helper methods                          #
    ###########################################################################

    def _get_attribute_value(self, attribute_key, mask_value_in_log=False):
        _method_name = '_get_attribute_value'
        _logger.entering(attribute_key, mask_value_in_log, class_name=self.__class_name, method_name=_method_name)

        result = None
        for line in self._lines:
            if line.get_key() == attribute_key:
                result = line.get_value()
                break

        log_result = result
        if mask_value_in_log:
            log_result = self.__log_mask

        _logger.exiting(class_name=self.__class_name, method_name=_method_name, result=log_result)
        return result

    def _get_resource_name_dict(self, resource_name):
        _method_name = '_get_resource_name_dict'
        _logger.entering(resource_name, class_name=self.__class_name, method_name=_method_name)

        result = OrderedDict()
        if not string_utils.is_empty(resource_name):
            resource_name_components = resource_name.split(', ')
            for resource_name_component in resource_name_components:
                name_components = resource_name_component.split('=')
                result[name_components[0].strip()] = name_components[1].strip()

        _logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result


class DefaultCredentialMapperLdift(LdiftBase):
    __class_name = 'DefaultCredentialMapperLdift'

    def __init__(self, ldift_file_name, model_context, aliases, credential_injector,
                 exception_type=ExceptionType.DISCOVER, download_temporary_dir=None):

        LdiftBase.__init__(self, model_context, exception_type, download_temporary_dir=download_temporary_dir)

        self._ldift_file_name = ldift_file_name
        self._aliases = aliases
        self._credential_injector = credential_injector
        self._credential_map_ldift_entries, self._resource_map_ldift_entries = self.read_ldift_file(ldift_file_name)

    # Override
    def read_ldift_file(self, ldift_file_name):
        _method_name = 'read_ldift_file'
        _logger.entering(ldift_file_name, class_name=self.__class_name, method_name=_method_name)

        credential_map_entries = list()
        resource_map_entries = list()
        string_entries = LdiftBase.read_ldift_file(self, ldift_file_name)
        for string_entry in string_entries:
            ldift_entry = DefaultCredentialMapperLdiftEntry(string_entry, self._exception_type)
            if ldift_entry.is_credential_map_entry():
                credential_map_entries.append(ldift_entry)
            elif ldift_entry.is_resource_map_entry():
                resource_map_entries.append(ldift_entry)
            else:
                # it is a header and not relevant to discover
                pass

        _logger.exiting(class_name=self.__class_name, method_name=_method_name,
                        result=[credential_map_entries, resource_map_entries])
        return credential_map_entries, resource_map_entries

    def get_cross_domain_dictionary(self):
        _method_name = 'get_cross_domain_dictionary'
        _logger.entering(class_name=self.__class_name, method_name=_method_name)

        count = 1
        result = OrderedDict()
        for credential_map_entry in self._credential_map_ldift_entries:
            if not credential_map_entry.is_credential_map_cross_domain():
                continue

            resource_map_entries = self._find_resource_map_entries_for_credential_map_entry(credential_map_entry)
            entry_name = 'Map-%s' % count
            entry_payload = self._get_cross_domain_model_entry(credential_map_entry, resource_map_entries, entry_name)
            result[entry_name] = entry_payload
            count += 1

        _logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result.keys())
        return result

    def get_remote_resource_dictionary(self):
        _method_name = 'get_remote_resource_dictionary'
        _logger.entering(class_name=self.__class_name, method_name=_method_name)

        count = 1
        result = OrderedDict()
        for credential_map_entry in self._credential_map_ldift_entries:
            if not credential_map_entry.is_credential_map_remote_resource():
                continue

            resource_map_entries = self._find_resource_map_entries_for_credential_map_entry(credential_map_entry)
            entry_name = 'Map-%s' % count
            entry_payload = self._get_remote_resource_model_entry(credential_map_entry, resource_map_entries, entry_name)
            result[entry_name] = entry_payload
            count += 1

        _logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result.keys())
        return result

    def _find_resource_map_entries_for_credential_map_entry(self, credential_map_ldift_entry):
        _method_name = '_find_resource_map_entries_for_credential_map_entry'
        _logger.entering(credential_map_ldift_entry, class_name=self.__class_name, method_name=_method_name)

        credential_map_ldift_entry_resource_name = credential_map_ldift_entry.get_credential_map_resource_name()
        resource_map_ldift_entries = list()
        for resource_map_ldift_entry in self._resource_map_ldift_entries:
            resource_map_ldift_entry_resource_name = resource_map_ldift_entry.get_resource_map_resource_name()
            if credential_map_ldift_entry_resource_name == resource_map_ldift_entry_resource_name:
                resource_map_ldift_entries.append(resource_map_ldift_entry)

        _logger.exiting(class_name=self.__class_name, method_name=_method_name, result=resource_map_ldift_entries)
        return resource_map_ldift_entries

    def _get_cross_domain_model_entry(self, credential_map_ldift_entry, resource_map_ldift_entries, entry_name):
        _method_name = '_get_cross_domain_model_entry'
        _logger.entering(credential_map_ldift_entry, resource_map_ldift_entries,
                         class_name=self.__class_name, method_name=_method_name)

        # This type of entry is very simple where we don't even need to look at the resource_map_ldift_entries
        #
        result = OrderedDict()
        resource_name = credential_map_ldift_entry.get_credential_map_resource_name()
        resource_name_map = credential_map_ldift_entry.get_credential_map_resource_name_map()

        remote_domain = \
            self._get_attribute_from_resource_name_map(resource_name_map, 'remoteHost',
                                                       'WLSDPLY-07119', resource_name)
        remote_user, remote_password = \
            self._get_principal_user_and_password_from_credential_map_ldift_entry(credential_map_ldift_entry,
                                                                                  CROSS_DOMAIN)
        result[REMOTE_DOMAIN] = remote_domain
        result[REMOTE_USER] = remote_user
        result[REMOTE_PASSWORD] = remote_password

        if self._credential_injector is not None:
            location = LocationContext().append_location(WLS_USER_PASSWORD_CREDENTIAL_MAPPINGS) \
                .append_location(CROSS_DOMAIN)
            name_token = self._aliases.get_name_token(location)
            location.add_name_token(name_token, entry_name)
            self._credential_injector.check_and_tokenize(result, REMOTE_USER, location)
            self._credential_injector.check_and_tokenize(result, REMOTE_PASSWORD, location)

        _logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return result

    def _get_remote_resource_model_entry(self, credential_map_ldift_entry, resource_map_ldift_entries, entry_name):
        _method_name = '_get_remote_resource_model_entry'
        _logger.entering(credential_map_ldift_entry, resource_map_ldift_entries,
                         class_name=self.__class_name, method_name=_method_name)

        resource_name = credential_map_ldift_entry.get_credential_map_resource_name()
        resource_name_map = credential_map_ldift_entry.get_credential_map_resource_name_map()

        protocol = self._get_attribute_from_resource_name_map(resource_name_map, 'protocol',
                                                              'WLSDPLY-07120', resource_name)
        remote_host = self._get_attribute_from_resource_name_map(resource_name_map, 'remoteHost',
                                                                 'WLSDPLY-07120', resource_name)
        remote_port = self._get_attribute_from_resource_name_map(resource_name_map, 'remotePort',
                                                                 'WLSDPLY-07120', resource_name)
        path = self._get_attribute_from_resource_name_map(resource_name_map, 'path',
                                                          'WLSDPLY-07120', resource_name)
        method = self._get_attribute_from_resource_name_map(resource_name_map, 'method',
                                                            'WLSDPLY-07120', resource_name)
        remote_user, remote_password = \
            self._get_principal_user_and_password_from_credential_map_ldift_entry(credential_map_ldift_entry,
                                                                                  REMOTE_RESOURCE)
        user = ','.join(self._get_principal_names_from_resource_maps(resource_map_ldift_entries))

        result = OrderedDict()
        result[PROTOCOL] = protocol
        result[REMOTE_HOST] = remote_host
        result[REMOTE_PORT] = remote_port
        result[PATH] = path
        result[METHOD] = method
        result[USER] = user
        result[REMOTE_USER] = remote_user
        result[REMOTE_PASSWORD] = remote_password

        if self._credential_injector is not None:
            location = LocationContext().append_location(WLS_USER_PASSWORD_CREDENTIAL_MAPPINGS) \
                .append_location(REMOTE_RESOURCE)
            name_token = self._aliases.get_name_token(location)
            location.add_name_token(name_token, entry_name)
            self._credential_injector.check_and_tokenize(result, REMOTE_USER, location)
            self._credential_injector.check_and_tokenize(result, REMOTE_PASSWORD, location)
            self._credential_injector.check_and_tokenize(result, USER, location)

        _logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result

    def _get_principal_user_and_password_from_credential_map_ldift_entry(self, ldift_entry, ldift_entry_type):
        _method_name = '_get_principal_user_and_password_from_credential_map_ldift_entry'
        _logger.entering(ldift_entry, ldift_entry_type, class_name=self.__class_name, method_name=_method_name)

        user_name = ldift_entry.get_credential_map_principal_name()
        try:
            password = \
                self.get_password_for_model(ldift_entry.get_credential_map_principal_password())
        except EncryptionException, ee:
            password = PASSWORD_TOKEN
            _logger.warning('WLSDPLY-07121', ldift_entry_type, password, ee.getLocalizedMessage(),
                            error=ee, class_name=self.__class_name, method_name=_method_name)

        _logger.exiting(class_name=self.__class_name, method_name=_method_name, result=user_name)
        return user_name, password

    def _get_principal_names_from_resource_maps(self, resource_map_ldift_entries):
        _method_name = '_get_principal_names_from_resource_maps'
        _logger.entering(resource_map_ldift_entries, class_name=self.__class_name, method_name=_method_name)

        result = list()
        for resource_map_ldift_entry in resource_map_ldift_entries:
            principal_name = resource_map_ldift_entry.get_resource_map_principal_name()
            result.append(principal_name)

        _logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result

    def _get_attribute_from_resource_name_map(self, resource_name_map, attribute_name, error_key, error_id, is_required=True):
        _method_name = '_get_attribute_from_resource_name_map'
        _logger.entering(resource_name_map, attribute_name, error_key, error_id,
                         class_name=self.__class_name, method_name=_method_name)

        result = None
        if attribute_name in resource_name_map:
            result = resource_name_map[attribute_name]
        elif is_required:
            _logger.warning(error_key, error_id, attribute_name,
                            class_name=self.__class_name, method_name=_method_name)

        _logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result
