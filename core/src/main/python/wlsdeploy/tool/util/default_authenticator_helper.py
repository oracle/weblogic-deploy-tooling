"""
Copyright (c) 2021, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import com.octetstring.vde.util.PasswordEncryptor as PasswordEncryptor
import com.bea.security.xacml.cache.resource.ResourcePolicyIdUtil as ResourcePolicyIdUtil
from java.io import File
from java.lang import String
import java.util.regex.Pattern as Pattern

import oracle.weblogic.deploy.aliases.TypeUtils as TypeUtils

from wlsdeploy.aliases.model_constants import DESCRIPTION
from wlsdeploy.aliases.model_constants import GROUP
from wlsdeploy.aliases.model_constants import GROUP_MEMBER_OF
from wlsdeploy.aliases.model_constants import PASSWORD
from wlsdeploy.aliases.model_constants import USER
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

# template hash constants
HASH_NAME = 'name'
HASH_DESCRIPTION = 'description'
HASH_GROUPS = 'groups'
HASH_GROUP = 'groupMemberOf'
HASH_USER_PASSWORD = 'password'


class DefaultAuthenticatorHelper(object):
    """
    This class is used to write the Security Group and User data into the ldift file. The reason is
    that there are several issues that are broken in offline, while they work in online. This works
    around these problems.
    """
    _class_name = 'DefaultAuthenticatorHelper'

    def __init__(self, model_context, exception_type):
        self._model_context = model_context
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

        template_hash = self._build_default_template_hash(security_mapping_nodes)
        template_path = TEMPLATE_PATH + '/' + DEFAULT_AUTH_INIT_FILE

        output_dir = File(self._model_context.get_domain_home(), SECURITY_SUBDIR)
        output_file = File(output_dir, DEFAULT_AUTH_INIT_FILE)

        self._logger.info('WLSDPLY-01900', output_file, class_name=self._class_name, method_name=_method_name)

        file_template_helper.append_file_from_resource(template_path, template_hash, output_file, self._exception_type)

    def _build_default_template_hash(self, mapping_section_nodes):
        """
        Create a dictionary of substitution values to apply to the default authenticator template.
        :param mapping_section_nodes: the security elements from the model
        :return: the template hash dictionary
        """
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
                mapping_hash = self._build_user_mapping_hash(user_mapping_nodes[name], name)
                user_mappings.append(mapping_hash)

        template_hash[GROUP_MAPPINGS] = group_mappings
        template_hash[USER_MAPPINGS] = user_mappings
        return template_hash

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
        hash_entry[HASH_DESCRIPTION] = description
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

    def _build_user_mapping_hash(self, user_mapping_section, name):
        """
        Build a template hash map from the security user data from the model.
        This includes encoding the required password.
        :param user_mapping_section: The security user section from the model
        :param name: name of the user for the user section
        :return: template hash map
        """
        hash_entry = dict()
        hash_entry[HASH_NAME] = name
        group_attributes = user_mapping_section
        description = dictionary_utils.get_element(group_attributes, DESCRIPTION)
        hash_entry[HASH_DESCRIPTION] = description
        groups = dictionary_utils.get_element(group_attributes, GROUP_MEMBER_OF)
        password = self._get_required_attribute(user_mapping_section, PASSWORD, USER, name)
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

        return hash_entry

    def _encode_password(self, user, password):
        pwdPattern = '[\\!a-zA-Z]{1,}'
        matches = Pattern.matches(pwdPattern, password)
        if len(password) < 8 or matches:
            self._logger.warning('WLSDPLY-01902', user)
            return None
        try:
            encryptedPass = PasswordEncryptor.doSSHA256(password)
            encryptedPass = "{ssha256}" + encryptedPass
        except Exception, e:
            self._logger.warning('WLSDPLY-01901', user, e)
            return None
        return encryptedPass

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
            pwe = exception_helper.create_exception(self._exception_type, '-01791', name, mapping_type,
                                                    mapping_name)
            self._logger.throwing(class_name=self._class_name, method_name=_method_name, error=pwe)
            raise pwe
        return result