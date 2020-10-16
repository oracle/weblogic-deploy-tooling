"""
Copyright (c) 2020, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import com.bea.common.security.utils.encoders.BASE64Encoder as BASE64Encoder
import com.bea.security.xacml.cache.resource.ResourcePolicyIdUtil as ResourcePolicyIdUtil
from java.io import File
from java.lang import String
from oracle.weblogic.deploy.aliases import TypeUtils

from wlsdeploy.aliases.model_constants import CROSS_DOMAIN
from wlsdeploy.aliases.model_constants import METHOD
from wlsdeploy.aliases.model_constants import PATH
from wlsdeploy.aliases.model_constants import PROTOCOL
from wlsdeploy.aliases.model_constants import REMOTE_DOMAIN
from wlsdeploy.aliases.model_constants import REMOTE_HOST
from wlsdeploy.aliases.model_constants import REMOTE_PASSWORD
from wlsdeploy.aliases.model_constants import REMOTE_PORT
from wlsdeploy.aliases.model_constants import REMOTE_USER
from wlsdeploy.aliases.model_constants import USER
from wlsdeploy.exception import exception_helper
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.util.targets import file_template_helper
from wlsdeploy.util import dictionary_utils
from wlsdeploy.util.weblogic_helper import WebLogicHelper

DEFAULT_MAPPER_INIT_FILE = 'DefaultCredentialMapperInit.ldift'
SECURITY_SUBDIR = 'security'
TEMPLATE_PATH = 'oracle/weblogic/deploy/security'

CREDENTIAL_MAPPINGS = 'credentialMappings'
RESOURCE_MAPPINGS = 'resourceMappings'

CROSS_DOMAIN_PROTOCOL = 'cross-domain-protocol'
CROSS_DOMAIN_USER = 'cross-domain'
NULL = 'null'

# template hash constants
HASH_CREDENTIAL_CN = 'credentialCn'
HASH_LOCAL_USER = 'localUser'
HASH_PASSWORD_ENCODED = 'passwordEncoded'
HASH_REMOTE_USER = 'remoteUser'
HASH_RESOURCE_CN = 'resourceCn'
HASH_RESOURCE_NAME = 'resourceName'

# keys in resource name
ID_METHOD = 'method'
ID_PATH = 'path'
ID_PROTOCOL = 'protocol'
ID_REMOTE_HOST = 'remoteHost'
ID_REMOTE_PORT = 'remotePort'

# ordered to match resource name output
RESOURCE_FIELDS = [
    ID_PROTOCOL,
    ID_REMOTE_HOST,
    ID_REMOTE_PORT,
    ID_PATH,
    ID_METHOD
]


class CredentialMapHelper(object):
    """
    Creates .ldift initialization file for user/password credential mappings
    """
    _class_name = 'CredentialMapHelper'

    def __init__(self, model_context, exception_type):
        """
        Initialize an instance of CredentialMapHelper.
        :param model_context: used to find domain home
        :param exception_type: the type of exception to be thrown
        """
        self._model_context = model_context
        self._exception_type = exception_type
        self._logger = PlatformLogger('wlsdeploy.tool.util')
        self._weblogic_helper = WebLogicHelper(self._logger)
        self._resource_escaper = ResourcePolicyIdUtil.getEscaper()
        self._b64_encoder = BASE64Encoder()

    def create_default_init_file(self, default_mapping_nodes):
        """
        Create a .ldift file to initialize default credential mappers.
        Build a hash map for use with a template file resource.
        Write the file to a known location in the domain.
        :param default_mapping_nodes: the credential mapping elements from the model
        """
        _method_name = 'create_default_init_file'

        template_hash = self._build_default_template_hash(default_mapping_nodes)
        template_path = TEMPLATE_PATH + '/' + DEFAULT_MAPPER_INIT_FILE

        output_dir = File(self._model_context.get_domain_home(), SECURITY_SUBDIR)
        output_file = File(output_dir, DEFAULT_MAPPER_INIT_FILE)

        self._logger.info('WLSDPLY-01790', output_file, class_name=self._class_name, method_name=_method_name)

        file_template_helper.create_file_from_resource(template_path, template_hash, output_file, self._exception_type)

    def _build_default_template_hash(self, mapping_section_nodes):
        """
        Create a dictionary of substitution values to apply to the default credential mappers template.
        :param mapping_section_nodes: the credential mapping elements from the model
        :return: the template hash dictionary
        """
        template_hash = dict()

        credential_mappings = []
        resource_mappings = []

        for mapping_type in mapping_section_nodes.keys():
            mapping_name_nodes = mapping_section_nodes[mapping_type]
            for mapping_name in mapping_name_nodes.keys():
                mapping = mapping_name_nodes[mapping_name]
                mapping_hash = self._build_mapping_hash(mapping_type, mapping_name, mapping)

                # add a hash with remote target details to create a single passwordCredentialMap element
                credential_mappings.append(mapping_hash)

                # add a modified hash for each local user to create resourceMap elements
                resource_name = mapping_hash[HASH_RESOURCE_NAME]
                local_users = self._get_local_users(mapping_type, mapping_name, mapping)
                for local_user in local_users:
                    resource_hash = dict(mapping_hash)
                    resource_hash[HASH_LOCAL_USER] = local_user
                    resource_hash[HASH_RESOURCE_CN] = self._create_cn(resource_name, local_user)
                    resource_mappings.append(resource_hash)

        template_hash[CREDENTIAL_MAPPINGS] = credential_mappings
        template_hash[RESOURCE_MAPPINGS] = resource_mappings
        return template_hash

    def _build_mapping_hash(self, mapping_type, mapping_name, mapping):
        """
        Build a template hash for the specified mapping element from the model.
        :param mapping_type: the type of the mapping, such as 'CrossDomain'
        :param mapping_name: the mapping name from the model, such as 'map1'
        :param mapping: the mapping element from the model
        :return: the template hash
        """
        resource_name = self._build_resource_name(mapping_type, mapping_name, mapping)

        remote_user = self._get_required_attribute(mapping, REMOTE_USER, mapping_type, mapping_name)
        credential_cn = self._create_cn(resource_name, remote_user)

        # the password needs to be encrypted, then base64 encoded
        password = self._get_required_attribute(mapping, REMOTE_PASSWORD, mapping_type, mapping_name)
        encrypted = self._weblogic_helper.encrypt(password, self._model_context.get_domain_home())
        password_encoded = self._b64_encoder.encodeBuffer(String(encrypted).getBytes("UTF-8"))

        # the local user and resource CN will be updated later for each user
        return {
            HASH_CREDENTIAL_CN: credential_cn,
            HASH_LOCAL_USER: NULL,
            HASH_PASSWORD_ENCODED: password_encoded,
            HASH_REMOTE_USER: remote_user,
            HASH_RESOURCE_CN: NULL,
            HASH_RESOURCE_NAME: resource_name
        }

    def _build_resource_name(self, mapping_type, mapping_name, mapping):
        """
        Build the resource name based on elements in the mapping element from the model.
        Example: type=<remote>, protocol=http, remoteHost=my.host, remotePort=7020, path=/myapp, method=POST
        :param mapping_type: the type of the mapping, such as 'CrossDomain'
        :param mapping_name: the mapping name from the model, such as 'map1'
        :param mapping: the mapping element from the model
        :return: the resource name
        """

        # for cross-domain mapping, use domain for remote host, and set cross-domain protocol
        if mapping_type == CROSS_DOMAIN:
            remote_host = self._get_required_attribute(mapping, REMOTE_DOMAIN, mapping_type, mapping_name)
            protocol = CROSS_DOMAIN_PROTOCOL
        else:
            remote_host = self._get_required_attribute(mapping, REMOTE_HOST, mapping_type, mapping_name)
            protocol = dictionary_utils.get_element(mapping, PROTOCOL)

        # build a map of available values, some may be None
        resource_name_values = {
            ID_METHOD: dictionary_utils.get_element(mapping, METHOD),
            ID_PATH: dictionary_utils.get_element(mapping, PATH),
            ID_PROTOCOL: protocol,
            ID_REMOTE_HOST: remote_host,
            ID_REMOTE_PORT: dictionary_utils.get_element(mapping, REMOTE_PORT)
        }

        # build the resource name string
        resource_name = 'type=<remote>'
        for field in RESOURCE_FIELDS:
            value = dictionary_utils.get_element(resource_name_values, field)
            if value is not None:
                resource_name += ', %s=%s' % (field, value)

        return resource_name

    def _get_local_users(self, mapping_type, mapping_name, mapping):
        """
        Get the local users list, based on the mapping element from the model.
        :param mapping_type: the type of the mapping, such as 'CrossDomain'
        :param mapping_name: the mapping name from the model, such as 'map1'
        :param mapping: the mapping element from the model
        :return: a list of local users
        """
        if mapping_type == CROSS_DOMAIN:
            return [CROSS_DOMAIN_USER]

        local_user_value = self._get_required_attribute(mapping, USER, mapping_type, mapping_name)
        return TypeUtils.convertToType(list, local_user_value)

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

    def _create_cn(self, resource_name, user):
        """
        Create a CN string from the specified resource name and user name.
        The result should be escaped for use as a CN.
        :param resource_name: the name of the resource
        :param user: the user name
        :return: the CN string
        """
        name = resource_name + "." + user
        return self._resource_escaper.escapeString(name)
