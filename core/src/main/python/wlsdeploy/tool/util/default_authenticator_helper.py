"""
Copyright (c) 2021, 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
from java.io import File

from com.octetstring.vde.util import PasswordEncryptor
from com.bea.security.xacml.cache.resource import ResourcePolicyIdUtil
from oracle.weblogic.deploy.aliases import TypeUtils
from oracle.weblogic.deploy.create import CreateException
from oracle.weblogic.deploy.validate.PasswordValidator import OLD_PASSWORD_ENCODING_MARKER
from oracle.weblogic.deploy.validate.PasswordValidator import PASSWORD_ENCODING_MARKER

from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import DESCRIPTION
from wlsdeploy.aliases.model_constants import DOMAIN_INFO
from wlsdeploy.aliases.model_constants import GROUP
from wlsdeploy.aliases.model_constants import GROUP_MEMBER_OF
from wlsdeploy.aliases.model_constants import PASSWORD
from wlsdeploy.aliases.model_constants import SECURITY
from wlsdeploy.aliases.model_constants import USER
from wlsdeploy.aliases.model_constants import USER_ATTRIBUTES
from wlsdeploy.exception import exception_helper
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.util import ldif_entry
from wlsdeploy.tool.util.ldif_entry import LDIFEntry
from wlsdeploy.tool.util.targets import file_template_helper
from wlsdeploy.util import dictionary_utils

TEMPLATE_PATH = 'oracle/weblogic/deploy/security'
DEFAULT_AUTH_INIT_FILE = 'DefaultAuthenticatorInit.ldift'
SECURITY_SUBDIR = 'security'

# template hash constants
HASH_CHILD_GROUP_NAME = 'childGroupName'
HASH_CHILD_GROUPS = 'childGroups'
HASH_DESCRIPTION = 'description'
HASH_EXISTING_ENTRIES = 'existingEntries'
HASH_EXISTING_LINES = 'existingLines'
HASH_EXISTING_TEXT = 'existingText'
HASH_GROUPS = 'group'
HASH_KEY = 'key'
HASH_NAME = 'name'
HASH_USER_ATTRIBUTES = 'userAttributes'
HASH_USER_GROUP_NAME = 'userGroupName'
HASH_USER_GROUPS = 'userGroups'
HASH_USERS = 'user'
HASH_USER_PASSWORD = 'password'
HASH_VALUE = 'value'

# LDIFT fields
LDIFT_PASSWORD = 'userpassword'
LDIFT_DESCRIPTION = 'description'
LDIFT_UNIQUE_MEMBER = 'uniquemember'
LDIFT_WLS_MEMBER_OF = 'wlsMemberOf'


class DefaultAuthenticatorHelper(object):
    """
    This class is used to write the Security Group and User data into the ldift file. The reason is
    that there are several issues that are broken in offline, while they work in online. This works
    around these problems.
    """
    _class_name = 'DefaultAuthenticatorHelper'

    def __init__(self, model_context, aliases, exception_type, using_password_digest=False):
        self._model_context = model_context
        self._aliases = aliases
        self._exception_type = exception_type
        self._logger = PlatformLogger('wlsdeploy.tool.util')
        self._weblogic_helper = model_context.get_weblogic_helper()
        self._resource_escaper = ResourcePolicyIdUtil.getEscaper()
        self._using_password_digest = using_password_digest

    def create_default_init_file(self, security_mapping_nodes, admin_credentials):
        """
        Use the security information to write user/groups to the DefaultAuthenticatorInit.ldift file.
        This file must exist before writing the data. Build a hash map from the model data and
        append to the file using the template file for structure.
        :param security_mapping_nodes: the Security elements from the model
        :param admin_credentials: admin credentials from the DomainInfo section of the model
        """
        _method_name = 'create_default_init_file'

        output_dir = File(self._model_context.get_domain_home(), SECURITY_SUBDIR)
        init_file = File(output_dir, DEFAULT_AUTH_INIT_FILE)

        template_hash = self._build_default_template_hash(security_mapping_nodes, admin_credentials, init_file)
        template_path = TEMPLATE_PATH + '/' + DEFAULT_AUTH_INIT_FILE + file_template_helper.MUSTACHE_SUFFIX

        self._logger.info('WLSDPLY-01900', init_file,
                          class_name=self._class_name, method_name=_method_name)

        file_template_helper.create_file_from_resource(template_path, template_hash, init_file, self._exception_type)

    def _build_default_template_hash(self, model_security_dict, admin_credentials, init_file):
        """
        Create a dictionary of substitution values to apply to the default authenticator template.
        :param model_security_dict: the security elements from the model
        :param init_file: java.io.File containing original LDIFT entries
        :param admin_credentials: admin credentials from the DomainInfo section of the model
        :return: the template hash dictionary
        """
        _method_name = '_build_default_template_hash'
        template_hash = dict()

        existing_entries = ldif_entry.read_entries(init_file)

        # in the WDT model, group parents are assigned to groups using GroupMemberOf.
        # in the LDIFT file, group children are assigned to groups, using uniquemember assignments.
        # we need a map of groups to child groups to build the LDIFT assignments.
        group_child_map = self._build_group_child_map(model_security_dict)

        groups_hash = []
        if GROUP in model_security_dict.keys():
            group_mapping_nodes = model_security_dict[GROUP]
            for name in group_mapping_nodes:
                if not self._update_existing_group(name, group_mapping_nodes[name], existing_entries):
                    group_hash = self._build_group_template_hash(group_mapping_nodes[name], name, group_child_map)
                    groups_hash.append(group_hash)

        users_hash = []
        if USER in model_security_dict.keys():
            user_mapping_nodes = model_security_dict[USER]
            for name in user_mapping_nodes:
                try:
                    if not self._update_existing_user(name, user_mapping_nodes[name], admin_credentials,
                                                      existing_entries):
                        user_hash = self._build_user_template_hash(user_mapping_nodes[name], name, admin_credentials)
                        users_hash.append(user_hash)
                except CreateException, ce:
                    self._logger.warning('WLSDPLY-01902', name, ce.getLocalizedMessage(),
                                         error=ce, class_name=self._class_name, method_name=_method_name)

        # assign child groups to existing groups - parent groups may not have been in the model
        for group_name, child_list in group_child_map.iteritems():
            existing_group = ldif_entry.find_entry(group_name, existing_entries)
            if existing_group:
                child_groups = dictionary_utils.get_element(group_child_map, group_name)
                existing_group.add_qualified_assignments(LDIFT_UNIQUE_MEMBER, child_groups)

        existing_entries_hash = []
        for existing_entry in existing_entries:  # type: LDIFEntry
            lines_hash = []
            for line in existing_entry.get_assignment_lines():
                lines_hash.append({HASH_EXISTING_TEXT: line})
            existing_entries_hash.append({HASH_EXISTING_LINES: lines_hash})

        template_hash[HASH_GROUPS] = groups_hash
        template_hash[HASH_USERS] = users_hash
        template_hash[HASH_EXISTING_ENTRIES] = existing_entries_hash
        return template_hash

    def _build_group_template_hash(self, group_mapping_section, name, group_child_map):
        """
        Build a template hash for the specified mapping element from the model.
        :param group_mapping_section: the security group entry from the model
        :param name: The name of the group
        :return: the template hash
        """
        hash_entry = dict()
        hash_entry[HASH_NAME] = name
        group_attributes = group_mapping_section
        description = dictionary_utils.get_element(group_attributes, DESCRIPTION)
        if description is not None:
            hash_entry[HASH_DESCRIPTION] = description
        else:
            hash_entry[HASH_DESCRIPTION] = ''

        # assign child group names using group_child_map, not model GroupMemberOf
        child_groups_hash = []
        child_groups = dictionary_utils.get_element(group_child_map, name)
        if child_groups:
            child_groups = TypeUtils.convertToType('list', child_groups)
            for child_group in child_groups:
                child_groups_hash.append({HASH_CHILD_GROUP_NAME: child_group})
        hash_entry[HASH_CHILD_GROUPS] = child_groups_hash

        return hash_entry

    def _build_user_template_hash(self, user_mapping_section, name, admin_credentials):
        """
        Build a template hash map from the security user data from the model.
        This includes encoding the required password.
        :param user_mapping_section: The security user section from the model
        :param name: name of the user for the user section
        :param admin_credentials: admin credentials from the DomainInfo section of the model
        :return: template hash map
        :raises: CreateException if the user's password cannot be encoded
        """
        _method_name = '_build_user_template_hash'

        hash_entry = dict()
        hash_entry[HASH_NAME] = name
        group_attributes = user_mapping_section
        description = dictionary_utils.get_element(group_attributes, DESCRIPTION)
        if description is not None:
            hash_entry[HASH_DESCRIPTION] = description
        else:
            hash_entry[HASH_DESCRIPTION] = ''

        password = self._get_required_attribute(user_mapping_section, PASSWORD, USER, name)
        password_encoded = self._get_encoded_user_password(password, name, admin_credentials)
        hash_entry[HASH_USER_PASSWORD] = password_encoded

        groups = dictionary_utils.get_element(group_attributes, GROUP_MEMBER_OF)
        group_mappings = list()
        if groups is not None:
            group_list = TypeUtils.convertToType('list', groups)
            for group in group_list:
                group_mappings.append({HASH_USER_GROUP_NAME: group})
        hash_entry[HASH_USER_GROUPS] = group_mappings

        attribute_folder = dictionary_utils.get_dictionary_element(group_attributes, USER_ATTRIBUTES)
        attribute_hashes = list()
        for key, value in attribute_folder.iteritems():
            attribute_hashes.append({HASH_KEY: key, HASH_VALUE: value})
        hash_entry[HASH_USER_ATTRIBUTES] = attribute_hashes

        return hash_entry

    def _build_group_child_map(self, model_security_dict):
        """
        Build a map of group names to child groups for LDIFT assignments.
        :param model_security_dict: user security model section
        :return: template
        """
        group_child_map = {}
        groups_dict = dictionary_utils.get_dictionary_element(model_security_dict, GROUP)
        for group_name, group_dict in groups_dict.iteritems():
            group_parents = dictionary_utils.get_element(group_dict, GROUP_MEMBER_OF)
            if group_parents is not None:
                group_parents = TypeUtils.convertToType('list', group_parents)
                for group_parent in group_parents:
                    if not dictionary_utils.get_element(group_child_map, group_parent):
                        group_child_map[group_parent] = []
                    group_child_map[group_parent].append(group_name)
        return group_child_map

    #################################################################
    # Update existing users and groups from the original LDIFT file
    #################################################################

    def _update_existing_user(self, name, model_user_dictionary, admin_credentials, existing_entries):
        """
        Update the specified user if it existed in the original LDIFT file.
        :param name: the name of the user
        :param model_user_dictionary: the model dictionary for the user
        :param admin_credentials: admin credentials from the DomainInfo section of the model
        :param existing_entries: existing entries from the LDIFT file
        :return: True if an existing user was updated, False otherwise
        """
        _method_name = '_update_existing_user'

        existing_user = ldif_entry.find_entry(name, existing_entries)
        if existing_user:
            self._logger.info('WLSDPLY-01903', name,
                              class_name=self._class_name, method_name=_method_name)

            model_password = dictionary_utils.get_element(model_user_dictionary, PASSWORD)
            password_encoded = self._get_encoded_user_password(model_password, name, admin_credentials)
            existing_user.update_single_field(LDIFT_PASSWORD, password_encoded)

            model_description = dictionary_utils.get_element(model_user_dictionary, DESCRIPTION)
            if model_description:
                existing_user.update_single_field(LDIFT_DESCRIPTION, model_description)

            # add any groups that are in the model, but not currently assigned
            model_group_names = dictionary_utils.get_element(model_user_dictionary, GROUP_MEMBER_OF)
            if model_group_names:
                model_group_names = TypeUtils.convertToType('list', model_group_names)
                existing_user.add_qualified_assignments(LDIFT_WLS_MEMBER_OF, model_group_names)

            # add any user attributes that are in the model, but not currently assigned
            model_attributes_dict = dictionary_utils.get_dictionary_element(model_user_dictionary, USER_ATTRIBUTES)
            for key, value in model_attributes_dict.iteritems():
                existing_user.update_single_field(key, value)

            return True

        return False

    def _update_existing_group(self, name, model_group_dictionary, existing_entries):
        """
        Update the specified group if it existed in the original LDIFT file.
        :param name: the name of the group
        :param model_group_dictionary: the model dictionary for the group
        :param existing_entries: existing entries from the LDIFT file
        :return: True if an existing group was updated, False otherwise
        """
        _method_name = '_update_existing_group'

        existing_group = ldif_entry.find_entry(name, existing_entries)
        if existing_group:
            self._logger.info('WLSDPLY-01904', name,
                              class_name=self._class_name, method_name=_method_name)

            model_description = dictionary_utils.get_element(model_group_dictionary, DESCRIPTION)
            if model_description:
                existing_group.update_single_field(LDIFT_DESCRIPTION, model_description)

            # child groups are handled separately in _build_default_template_hash()
            return True
        return False

    def _get_encoded_user_password(self, model_password, user_name, admin_credentials):
        """
        Encode the model password for use in the template hash.
        If the username matches the admin user from the DomainInfo section, override the password value.
        :param model_password: the password from the model
        :param user_name: the username from the model
        :param admin_credentials: the admin credentials from DomainInfo
        :return: the encoded password value
        """
        _method_name = '_get_encoded_user_password'

        admin_user = dictionary_utils.get_element(admin_credentials, 'user')
        if user_name == admin_user:
            admin_password = dictionary_utils.get_element(admin_credentials, 'password')
            if admin_password:
                model_password = admin_password
                security_location = LocationContext().append_location(SECURITY)
                security_location.add_name_token(self._aliases.get_name_token(security_location), 'X')
                security_location.append_location(USER)
                security_path = self._aliases.get_model_folder_path(security_location)
                self._logger.notification('WLSDPLY-01905', user_name, DOMAIN_INFO, security_path,
                                          class_name=self._class_name, method_name=_method_name)

        model_password = self._aliases.decrypt_password(model_password)
        return self._encode_password(user_name, model_password)

    def _encode_password(self, user, password):
        """
        Encode the specified password using the correct algorithm for the authenticator.
        :param user: the username, for error logging
        :param password: the password to encode
        :return: the encoded password
        """
        _method_name = '_encode_password'
        self._logger.entering(user,  class_name=self._class_name, method_name=_method_name)

        encrypted_pass = password
        if not password.startswith(PASSWORD_ENCODING_MARKER) and not password.startswith(OLD_PASSWORD_ENCODING_MARKER):
            try:
                if self._using_password_digest:
                    encrypted_pass = self._weblogic_helper.encrypt(password, self._model_context.get_domain_home())
                else:
                    encrypted_pass = self._hash_password_for_ldift(password)
            except Exception, e:
                ex = exception_helper.create_create_exception('WLSDPLY-01901',user, e.getLocalizedMessage(),
                                                              error=e)
                self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                raise ex

        self._logger.exiting(class_name=self._class_name, method_name=_method_name)
        return encrypted_pass

    def _hash_password_for_ldift(self, password):
        """
        This method abstracts out the differences between older and newer WebLogic releases.
        :param password: the clear-text password to hash
        :return: the hashed password string ready to put into the LDIFT file
        """
        _method_name = '_hash_password_for_ldift'

        if self._weblogic_helper.is_weblogic_version_or_above('12.2.1'):
            encrypted_pass = PasswordEncryptor.doSSHA256(password)
            encrypted_pass = '%s%s' % (PASSWORD_ENCODING_MARKER, encrypted_pass)
        else:
            encrypted_pass = PasswordEncryptor.doSSHA(password)
            encrypted_pass = '%s%s' % (OLD_PASSWORD_ENCODING_MARKER, encrypted_pass)
        return encrypted_pass

    def _get_required_attribute(self, dictionary, name, mapping_type, mapping_name):
        """
        Return the value of the specified attribute from the specified dictionary.
        Log and throw an exception if the attribute is not found.
        :param dictionary: the dictionary to be checked
        :param name: the name of the attribute to find
        :param mapping_type: the type of the mapping, such as 'CrossDomain'
        :param mapping_name: the mapping name from the model, such as 'map1'
        :return: the value of the attribute
        :raises: Tool type exception: if an the attribute is not found
        """
        _method_name = '_get_required_attribute'

        result = dictionary_utils.get_element(dictionary, name)

        if result is None:
            pwe = exception_helper.create_exception(self._exception_type, 'WLSDPLY-01791', name, mapping_type,
                                                    mapping_name)
            self._logger.throwing(class_name=self._class_name, method_name=_method_name, error=pwe)
            raise pwe
        return result
