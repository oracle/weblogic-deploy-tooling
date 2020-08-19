"""
Copyright (c) 2020, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
from java.io import File

from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.util.targets import file_template_helper
from wlsdeploy.util import dictionary_utils

DEFAULT_MAPPER_INIT_FILE = 'DefaultCredentialMapperInit.ldift'
SECURITY_SUBDIR = 'security'
TEMPLATE_PATH = 'oracle/weblogic/deploy/security'

CROSS_DOMAIN_CREDENTIALS = 'crossDomainCredentials'
CROSS_DOMAIN_MAPS = 'crossDomainMaps'
REMOTE_RESOURCE_CREDENTIALS = 'remoteResourceCredentials'
REMOTE_RESOURCE_MAPS = 'remoteResourceMaps'

_class_name = 'CredentialMapHelper'


class CredentialMapHelper(object):

    def __init__(self, model_context, exception_type):
        self._model_context = model_context
        self._exception_type = exception_type
        self._logger = PlatformLogger('wlsdeploy.tool.util')

    def create_default_init_file(self, default_mapping_nodes):
        """
        Create a model context object from the specified argument map, with the domain typedef set up correctly.
        If the domain_typedef is not specified, construct it from the argument map.
        :param default_mapping_nodes: the program name, used for logging
        """
        _method_name = 'create_default_init_file'

        template_hash = self._build_default_template_hash(default_mapping_nodes)
        template_path = TEMPLATE_PATH + '/' + DEFAULT_MAPPER_INIT_FILE

        output_dir = File(self._model_context.get_domain_home(), SECURITY_SUBDIR)
        output_file = File(output_dir, DEFAULT_MAPPER_INIT_FILE)

        self._logger.info('WLSDPLY-01790', output_file, class_name=_class_name, method_name=_method_name)

        file_template_helper.create_file(template_path, template_hash, output_file, self._exception_type)

    def _build_default_template_hash(self, default_mapping_nodes):
        """
        Create a dictionary of substitution values to apply to the default credential mappers template.
        :param default_mapping_nodes: the default credential mappings model section
        :return: the hash dictionary
        """
        template_hash = dict()

        # domain name and prefix

        cross_domain_credentials = ["1", "2", "3"]

        # domain_name = dictionary_utils.get_element(model.get_model_topology(), NAME)
        # if domain_name is None:
        #     domain_name = DEFAULT_WLS_DOMAIN_NAME

        template_hash[CROSS_DOMAIN_CREDENTIALS] = cross_domain_credentials

        # should change spaces to hyphens?

        template_hash[CROSS_DOMAIN_MAPS] = cross_domain_credentials

        # domain UID

        template_hash[REMOTE_RESOURCE_CREDENTIALS] = cross_domain_credentials

        # admin credential

        template_hash[REMOTE_RESOURCE_MAPS] = cross_domain_credentials

        return template_hash
