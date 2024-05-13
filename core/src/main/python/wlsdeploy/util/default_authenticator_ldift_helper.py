"""
Copyright (c) 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at https://oss.oracle.com/licenses/upl.

Module that contains the class for working with DefaultAuthenticator LDIFT files.
"""
from oracle.weblogic.deploy.encrypt import EncryptionException
from oracle.weblogic.deploy.util import PyOrderedDict as OrderedDict

from wlsdeploy.aliases.alias_constants import PASSWORD_TOKEN
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import DEFAULT_AUTHENTICATOR
from wlsdeploy.aliases.model_constants import DEFAULT_AUTHENTICATOR_USER_ATTRIBUTE_KEYS
from wlsdeploy.aliases.model_constants import DESCRIPTION
from wlsdeploy.aliases.model_constants import GROUP_MEMBER_OF
from wlsdeploy.aliases.model_constants import PASSWORD
from wlsdeploy.aliases.model_constants import SECURITY
from wlsdeploy.aliases.model_constants import USER
from wlsdeploy.aliases.model_constants import USER_ATTRIBUTES
from wlsdeploy.exception.exception_types import ExceptionType
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.util import string_utils
from wlsdeploy.util import unicode_helper as str_helper
from wlsdeploy.util.ldift_helper import LdiftBase
from wlsdeploy.util.ldift_helper import LdiftLine

_logger = PlatformLogger('wlsdeploy.ldift')


class DefaultAuthenticatorLdiftEntry(object):
    __class_name = 'DefaultAuthenticatorLdiftEntry'
    __log_mask = '<redacted>'

    def __init__(self, lines=None, exception_type=ExceptionType.DISCOVER):
        self._lines = list()
        self._exception_type = exception_type
        self._is_user_entry = False
        self._is_group_entry = False

        if lines is not None:
            for line in lines:
                ldift_line = LdiftLine(line)
                if ldift_line.get_key() == 'objectclass':
                    if ldift_line.get_value() == 'groupOfUniqueNames':
                        self._is_group_entry = True
                    elif ldift_line.get_value() == 'wlsUser':
                        self._is_user_entry = True
                self._lines.append(LdiftLine(line))

    def is_user_entry(self):
        return self._is_user_entry

    def is_group_entry(self):
        return self._is_group_entry

    def get_user_name(self):
        _method_name = 'get_user_name'
        _logger.entering(class_name=self.__class_name, method_name=_method_name)

        result = None
        if self._is_user_entry:
            result = self._get_attribute_value('cn')

        _logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result

    def get_user_password(self):
        _method_name = 'get_user_password'
        _logger.entering(class_name=self.__class_name, method_name=_method_name)

        result = None
        if self._is_user_entry:
            result = self._get_attribute_value('userpassword', True)
            if result is not None:
                result = str_helper.to_string(result)

        log_result = result
        if log_result is not None:
            log_result = self.__log_mask

        _logger.exiting(class_name=self.__class_name, method_name=_method_name, result=log_result)
        return result

    def get_user_description(self):
        _method_name = 'get_user_description'
        _logger.entering(class_name=self.__class_name, method_name=_method_name)

        result = None
        if self._is_user_entry:
            result = self._get_attribute_value('description')

        _logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result


    def get_user_group_memberships(self):
        _method_name = 'get_user_group_memberships'
        _logger.entering(class_name=self.__class_name, method_name=_method_name)

        result = OrderedDict()
        if self._is_user_entry:
            for line in self._lines:
                if line.get_key() == 'wlsMemberOf':
                    group_name = self._get_group_name_from_dn(line.get_value())
                    result[group_name] = line.get_value()

        _logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result

    def get_user_attributes(self):
        _method_name = 'get_user_attributes'
        _logger.entering(class_name=self.__class_name, method_name=_method_name)

        result = OrderedDict()
        if self._is_user_entry:
            for line in self._lines:
                if line.get_key() in DEFAULT_AUTHENTICATOR_USER_ATTRIBUTE_KEYS:
                    result[line.get_key()] = line.get_value()

        _logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result

    def get_group_name(self):
        _method_name = 'get_group_name'
        _logger.entering(class_name=self.__class_name, method_name=_method_name)

        result = None
        if self._is_group_entry:
            result = self._get_attribute_value('cn')

        _logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result

    def get_group_description(self):
        _method_name = 'get_group_description'
        _logger.entering(class_name=self.__class_name, method_name=_method_name)

        result = None
        if self._is_group_entry:
            result = self._get_attribute_value('description')

        _logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result

    def get_group_child_groups(self):
        _method_name = 'get_group_child_groups'
        _logger.entering(class_name=self.__class_name, method_name=_method_name)

        result = OrderedDict()
        if self._is_group_entry:
            for line in self._lines:
                if line.get_key() == 'uniquemember':
                    child_group_name = self._get_group_name_from_dn(line.get_value())
                    result[child_group_name] = line.get_value()

        _logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result

    def _get_attribute_value(self, attribute_key, mask_value_in_log=False):
        _method_name = '_get_attribute_value'
        _logger.entering(attribute_key, mask_value_in_log, lass_name=self.__class_name, method_name=_method_name)

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

    def _get_group_name_from_dn(self, dn):
        _method_name = '_get_group_name_from_dn'
        _logger.entering(dn, class_name=self.__class_name, method_name=_method_name)

        result = dn
        dn_elements = dn.strip().split(',')
        for dn_element in dn_elements:
            dn_element = dn_element.strip()
            if dn_element.startswith('cn='):
                result = dn_element[3:]
                break

        _logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result


class DefaultAuthenticatorLdift(LdiftBase):
    __class_name = 'DefaultAuthenticatorLdift'
    __DEFAULT_GROUPS_DICT = None
    __DEFAULT_USER_LIST = [ 'weblogic', 'OracleSystemUser', 'LCMUser' ]

    def __init__(self, ldift_file_name, model_context, aliases, credential_injector,
                 exception_type=ExceptionType.DISCOVER, download_temporary_dir=None):

        LdiftBase.__init__(self, model_context, exception_type, download_temporary_dir=download_temporary_dir)

        self._ldift_file_name = ldift_file_name
        self._aliases = aliases
        self._credential_injector = credential_injector
        self._ldift_entries = self.read_ldift_file(ldift_file_name)


    # Override
    def read_ldift_file(self, ldift_file_name):
        _method_name = 'read_ldift_file'
        _logger.entering(ldift_file_name, class_name=self.__class_name, method_name=_method_name)

        entries = list()
        string_entries = LdiftBase.read_ldift_file(self, ldift_file_name)
        for string_entry in string_entries:
            entries.append(DefaultAuthenticatorLdiftEntry(string_entry, self._exception_type))

        _logger.exiting(class_name=self.__class_name, method_name=_method_name, result=entries)
        return entries

    def get_users_dictionary(self, filter_defaults=False):
        _method_name = 'get_users_dictionary'
        _logger.entering(filter_defaults, class_name=self.__class_name, method_name=_method_name)

        result = OrderedDict()
        for ldift_entry in self._ldift_entries:
            if ldift_entry.is_user_entry():
                user_name = ldift_entry.get_user_name()
                if filter_defaults and user_name in self.__DEFAULT_USER_LIST:
                    continue

                user_password = self._get_encrypted_password(user_name, ldift_entry.get_user_password())
                user_description = ldift_entry.get_user_description()
                user_groups_names = ldift_entry.get_user_group_memberships().keys()
                user_attributes_dict = ldift_entry.get_user_attributes()

                user_entry = OrderedDict()
                user_entry[PASSWORD] = user_password

                if self._credential_injector is not None:
                    location = LocationContext().append_location(SECURITY).append_location(USER)
                    name_token = self._aliases.get_name_token(location)
                    location.add_name_token(name_token, user_name)
                    self._credential_injector.check_and_tokenize(user_entry, PASSWORD, location)

                if not string_utils.is_empty(user_description):
                    user_entry[DESCRIPTION] = user_description
                if len(user_groups_names) > 0:
                    user_entry[GROUP_MEMBER_OF] = user_groups_names
                if user_attributes_dict:
                    user_entry[USER_ATTRIBUTES] = user_attributes_dict

                result[user_name] = user_entry

        _logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result.keys())
        return result

    def get_groups_dictionary(self, filter_defaults=True):
        _method_name = 'get_groups_dictionary'
        _logger.entering(filter, class_name=self.__class_name, method_name=_method_name)

        result = OrderedDict()
        found_child_groups = False
        for ldift_entry in self._ldift_entries:
            if ldift_entry.is_group_entry():
                group_name = ldift_entry.get_group_name()
                group_description = ldift_entry.get_group_description()
                group_child_groups = ldift_entry.get_group_child_groups().keys()

                group_entry = OrderedDict()
                if not string_utils.is_empty(group_description):
                    group_entry[DESCRIPTION] = group_description
                if len(group_child_groups) > 0:
                    found_child_groups = True
                    group_entry['child_groups'] = group_child_groups
                result[group_name] = group_entry

        #
        # To convert the results into a model dictionary, we have to convert any child_groups
        # entry in the parent group to a GroupMemberOf entry in the child group.
        #
        if found_child_groups:
            # Can't use iteritems() since we are modifying the child dictionaries as we iterate.
            for group_name in result.keys():
                group_entry = result[group_name]

                if 'child_groups' in group_entry:
                    self._add_group_member_of_to_child_groups(result, group_entry['child_groups'], group_name)
                    del group_entry['child_groups']

        if filter_defaults:
            group_names_to_remove = list()
            for group_name, group_dict in result.iteritems():
                if self._is_default_group(group_name, group_dict):
                    group_names_to_remove.append(group_name)

            for group_name in group_names_to_remove:
                del result[group_name]

        _logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result

    def _add_group_member_of_to_child_groups(self, groups_dict, child_group_names, parent_group_name):
        _method_name = '_add_group_member_of_to_child_groups'
        _logger.entering(child_group_names, parent_group_name,
                         class_name=self.__class_name, method_name=_method_name)

        for child_group_name in child_group_names:
            child_group_dict = groups_dict[child_group_name]
            if GROUP_MEMBER_OF in child_group_dict:
                child_group_group_members_of_list = child_group_dict[GROUP_MEMBER_OF]
                if parent_group_name not in child_group_group_members_of_list:
                    child_group_group_members_of_list.append(parent_group_name)
            else:
                child_group_dict[GROUP_MEMBER_OF] = [ parent_group_name ]

        _logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def _get_default_groups(self):
        _method_name = '_get_default_groups'
        _logger.entering(class_name=self.__class_name, method_name=_method_name)

        if self.__DEFAULT_GROUPS_DICT is None:
            file_name = 'groups.json'
            self.__DEFAULT_GROUPS_DICT = self.load_provider_defaults_file(DEFAULT_AUTHENTICATOR, file_name)
            _logger.info('WLSDPLY-07109', file_name, class_name=self.__class_name, method_name=_method_name)

        _logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return self.__DEFAULT_GROUPS_DICT

    def _is_default_group(self, group_name, group_dict):
        _method_name = '_is_default_group'
        _logger.entering(group_name, group_dict, class_name=self.__class_name, method_name=_method_name)

        result = False
        defaults = self._get_default_groups()
        if group_name in defaults:
            default_group_dict = defaults[group_name]
            if len(group_dict) == len(default_group_dict):
                result = True
                for default_key, default_value in default_group_dict.iteritems():
                    if default_key in group_dict:
                        # default groups only have the description element set so no need to
                        # deal with the complexities of handling the GroupMemberOf attribute.
                        if default_value != group_dict[default_key]:
                            _logger.fine('WLSDPLY-07110', group_name, default_key, group_dict[default_key],
                                         default_value, class_name=self.__class_name, method_name=_method_name)
                    else:
                        _logger.fine('WLSDPLY-07111', group_name, default_key,
                                     class_name=self.__class_name, method_name=_method_name)
                        result = False
                        break
            else:
                _logger.fine('WLSDPLY-07112', group_name, len(group_dict), len(default_group_dict),
                             class_name=self.__class_name, method_name=_method_name)
        else:
            _logger.fine('WLSDPLY-07113', group_name, class_name=self.__class_name, method_name=_method_name)

        _logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result

    def _get_encrypted_password(self, user_name, password):
        _method_name = '_get_encrypted_password'
        _logger.entering(user_name, class_name=self.__class_name, method_name=_method_name)

        try:
            result = self.get_password_for_model(password)
        except EncryptionException, ee:
            result = PASSWORD_TOKEN
            _logger.warning('WLSDPLY-07115', user_name, result,ee.getLocalizedMessage(),
                            error=ee, class_name=self.__class_name, method_name=_method_name)

        _logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return result
