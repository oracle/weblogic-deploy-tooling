"""
Copyright (c) 2021, 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import re

from java.io import File

from com.octetstring.vde.util import PasswordEncryptor
from com.bea.security.xacml.cache.resource import ResourcePolicyIdUtil
from oracle.weblogic.deploy.aliases import TypeUtils
from oracle.weblogic.deploy.create import CreateException

from wlsdeploy.aliases.model_constants import DESCRIPTION
from wlsdeploy.aliases.model_constants import GROUP
from wlsdeploy.aliases.model_constants import GROUP_MEMBER_OF
from wlsdeploy.aliases.model_constants import PASSWORD
from wlsdeploy.aliases.model_constants import USER
from wlsdeploy.aliases.model_constants import USER_ATTRIBUTES
from wlsdeploy.exception import exception_helper
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.util.targets import file_template_helper
from wlsdeploy.util import dictionary_utils
from wlsdeploy.util.weblogic_helper import WebLogicHelper

TEMPLATE_PATH = 'oracle/weblogic/deploy/security'
DEFAULT_AUTH_INIT_FILE = 'DefaultAuthenticatorInit.ldift'
SECURITY_SUBDIR = 'security'
GROUP_MAPPINGS = 'group'
USER_MAPPINGS = 'user'
EXISTING_ENTRIES = 'existingEntries'

# template hash constants
HASH_NAME = 'name'
HASH_DESCRIPTION = 'description'
HASH_GROUPS = 'groups'
HASH_GROUP = 'groupMemberOf'
HASH_USER_PASSWORD = 'password'
HASH_ATTRIBUTES = 'userattr'
HASH_ATTRIBUTE = 'attribute'
HASH_EXISTING_LINES = 'existingLines'
HASH_EXISTING_TEXT = 'existingText'
HASH_CHILD_GROUPS = 'childGroups'
HASH_CHILD_GROUP_NAME = 'childGroupName'

CN_REGEX = re.compile('^cn: (.+)$')


class DefaultAuthenticatorHelper(object):
    """
    This class is used to write the Security Group and User data into the ldift file. The reason is
    that there are several issues that are broken in offline, while they work in online. This works
    around these problems.
    """
    _class_name = 'DefaultAuthenticatorHelper'

    def __init__(self, model_context, aliases, exception_type):
        self._model_context = model_context
        self._aliases = aliases
        self._exception_type = exception_type
        self._logger = PlatformLogger('wlsdeploy.tool.util')
        self._weblogic_helper = WebLogicHelper(self._logger)
        self._resource_escaper = ResourcePolicyIdUtil.getEscaper()

    def create_default_init_file(self, security_mapping_nodes):
        """
        Use the security information to write user/groups to the DefaultAuthenticatorInit.ldift file.
        This file must exist before writing the data. Build a hash map from the model data and
        append to the file using the template file for structure.
        :param security_mapping_nodes: the Security elements from the model
        """
        _method_name = 'create_default_init_file'

        output_dir = File(self._model_context.get_domain_home(), SECURITY_SUBDIR)
        init_file = File(output_dir, DEFAULT_AUTH_INIT_FILE)

        template_hash = self._build_default_template_hash(security_mapping_nodes, init_file)
        template_path = TEMPLATE_PATH + '/' + DEFAULT_AUTH_INIT_FILE

        self._logger.info('WLSDPLY-01900', init_file,
                          class_name=self._class_name, method_name=_method_name)

        file_template_helper.create_file_from_resource(template_path, template_hash, init_file, self._exception_type)

    def _build_default_template_hash(self, mapping_section_nodes, init_file):
        """
        Create a dictionary of substitution values to apply to the default authenticator template.
        :param mapping_section_nodes: the security elements from the model
        :param init_file: java.io.File containing original LDIFT entries
        :return: the template hash dictionary
        """
        _method_name = '_build_default_template_hash'
        template_hash = dict()

        group_mappings = []
        user_mappings = []

        if GROUP in mapping_section_nodes.keys():
            group_mapping_nodes = mapping_section_nodes[GROUP]
            for name in group_mapping_nodes:
                mapping_hash = self._build_group_mapping_hash(group_mapping_nodes[name], name)
                group_mappings.append(mapping_hash)

        if USER in mapping_section_nodes.keys():
            user_mapping_nodes = mapping_section_nodes[USER]
            for name in user_mapping_nodes:
                try:
                    mapping_hash = self._build_user_mapping_hash(user_mapping_nodes[name], name)
                    user_mappings.append(mapping_hash)
                except CreateException, ce:
                    self._logger.warning('WLSDPLY-01902', name, ce.getLocalizedMessage(),
                                         error=ce, class_name=self._class_name, method_name=_method_name)

        # build a map of group names to group children
        group_child_map = {}
        for group_mapping in group_mappings:
            group_name = group_mapping[HASH_NAME]
            member_of_groups = group_mapping[HASH_GROUPS]
            for member_of_group in member_of_groups:
                member_of_name = member_of_group[HASH_GROUP]
                if not dictionary_utils.get_element(group_child_map, member_of_name):
                    group_child_map[member_of_name] = []
                group_child_map[member_of_name].append({HASH_CHILD_GROUP_NAME: group_name})

        # assign group child names to groups
        for group_mapping in group_mappings:
            group_name = group_mapping[HASH_NAME]
            child_groups = dictionary_utils.get_element(group_child_map, group_name)
            if child_groups:
                group_mapping[HASH_CHILD_GROUPS] = child_groups

        template_hash[GROUP_MAPPINGS] = group_mappings
        template_hash[USER_MAPPINGS] = user_mappings
        template_hash[EXISTING_ENTRIES] = self._build_existing_entries_list(init_file, group_child_map)
        return template_hash

    def _build_existing_entries_list(self, init_file, group_child_map):
        """
        Create a list of existing group entries from the original LDIFT file.
        Each entry is a list of string declarations, and a list of any child groups.
        :param init_file: java.io.File containing original LDIFT entries
        :param group_child_map: a map of group names to child group names
        :return: the existing entries list
        """
        init_reader = open(init_file.getPath(), 'r')
        init_lines = init_reader.readlines()
        init_reader.close()

        existing_entry = None
        existing_entries = []
        for init_line in init_lines:
            line_text = init_line.strip()
            if len(line_text) == 0:
                existing_entry = None
            else:
                if existing_entry is None:
                    existing_entry = {HASH_EXISTING_LINES: [], HASH_CHILD_GROUPS: []}
                    existing_entries.append(existing_entry)
                existing_entry[HASH_EXISTING_LINES].append({HASH_EXISTING_TEXT: line_text})

                match = re.match(CN_REGEX, line_text)
                if match:
                    child_groups = dictionary_utils.get_element(group_child_map, match.group(1))
                    if child_groups:
                        existing_entry[HASH_CHILD_GROUPS] = child_groups

        return existing_entries

    def _build_group_mapping_hash(self, group_mapping_section, name):
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
        groups = dictionary_utils.get_element(group_attributes, GROUP_MEMBER_OF)
        group_list = []
        group_mappings = list()
        if groups is not None:
            group_list = TypeUtils.convertToType('list', groups)
            for group in group_list:
                group_mappings.append({HASH_GROUP: group})
            hash_entry[HASH_GROUPS] = group_mappings
        else:
            hash_entry[HASH_GROUPS] = group_list

        return hash_entry

    def _user_attributes(self, user_mapping_section, user_attributes):
        """
        Build a template hash map from the user attributes found under the
        user attribute folder in the model.
        :param user_mapping_section: The security user section from the model
        :param name: user_attributes model section
        :return: template
        """
        hash_entry = list()
        if user_attributes is None or len(user_attributes) == 0:
           return

        for attribute in user_attributes:
            hash_entry.append({HASH_ATTRIBUTE: attribute + ': ' + user_attributes[attribute]})

        return hash_entry

    def _build_user_mapping_hash(self, user_mapping_section, name):
        """
        Build a template hash map from the security user data from the model.
        This includes encoding the required password.
        :param user_mapping_section: The security user section from the model
        :param name: name of the user for the user section
        :return: template hash map
        :raises: CreateException if the user's password cannot be encoded
        """
        hash_entry = dict()
        hash_entry[HASH_NAME] = name
        group_attributes = user_mapping_section
        description = dictionary_utils.get_element(group_attributes, DESCRIPTION)
        if description is not None:
            hash_entry[HASH_DESCRIPTION] = description
        else:
            hash_entry[HASH_DESCRIPTION] = ''
        groups = dictionary_utils.get_element(group_attributes, GROUP_MEMBER_OF)
        password = self._get_required_attribute(user_mapping_section, PASSWORD, USER, name)
        password = self._aliases.decrypt_password(password)
        password_encoded = self._encode_password(name, password)
        hash_entry[HASH_USER_PASSWORD] = password_encoded
        group_list = []
        group_mappings = list()
        if groups is not None:
            group_list = TypeUtils.convertToType('list', groups)
            for group in group_list:
                group_mappings.append({HASH_GROUP: group})
            hash_entry[HASH_GROUPS] = group_mappings
        else:
            hash_entry[HASH_GROUPS] = group_list
        attribute_folder = dictionary_utils.get_element(group_attributes, USER_ATTRIBUTES)
        dict_hash = self._user_attributes(user_mapping_section, attribute_folder)
        if dict_hash is not None and len(dict_hash) > 0:
            hash_entry[HASH_ATTRIBUTES] = dict_hash
        return hash_entry

    def _encode_password(self, user, password):
        _method_name = '_encode_password'
        try:
            encrypted_pass = PasswordEncryptor.doSSHA256(password)
            encrypted_pass = "{ssha256}" + encrypted_pass
        except Exception, e:
            ex = exception_helper.create_create_exception('WLSDPLY-01901',user, e.getLocalizedMessage(),
                                                          error=e)
            self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex
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