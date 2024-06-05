"""
Copyright (c) 2023, 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""

from java.util.logging import Level
from oracle.weblogic.deploy.logging import WLSDeployLogEndHandler

from wlsdeploy.aliases.model_constants import CLUSTER
from wlsdeploy.aliases.model_constants import CROSS_DOMAIN
from wlsdeploy.aliases.model_constants import DOMAIN_INFO
from wlsdeploy.aliases.model_constants import DYNAMIC_SERVERS
from wlsdeploy.aliases.model_constants import REMOTE_DOMAIN
from wlsdeploy.aliases.model_constants import REMOTE_HOST
from wlsdeploy.aliases.model_constants import REMOTE_PASSWORD
from wlsdeploy.aliases.model_constants import REMOTE_RESOURCE
from wlsdeploy.aliases.model_constants import REMOTE_USER
from wlsdeploy.aliases.model_constants import SERVER_TEMPLATE
from wlsdeploy.aliases.model_constants import TOPOLOGY
from wlsdeploy.aliases.model_constants import WLS_USER_PASSWORD_CREDENTIAL_MAPPINGS
from wlsdeploy.exception import exception_helper
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.util import dictionary_utils


class ContentValidator(object):
    """
    Class for validating consistency and compatibility of model folders and attributes.
    These checks are done after alias folder and attribute checks.
    These checks should be performed against a detokenized, merged model.
    Tho model may be a sparse model. For example, it could referencce targets from another model.
    """
    _class_name = 'ContentValidator'
    _logger = PlatformLogger('wlsdeploy.validate')

    def __init__(self, model_context, aliases):
        self._model_context = model_context
        self._aliases = aliases

    def validate_model(self, model_dict):
        """
        Validate the contents of the specified model.
        :param model_dict: A Python dictionary of the model to be validated
        :raises ValidationException: if problems occur during validation
        """
        _method_name = 'validate_model'
        self._logger.entering(class_name=self._class_name, method_name=_method_name)

        self.validate_model_content(model_dict)

        summary_handler = WLSDeployLogEndHandler.getSummaryHandler()
        if summary_handler is not None:
            summary_level = summary_handler.getMaximumMessageLevel()

            if summary_level == Level.SEVERE:
                ce = exception_helper.create_validate_exception(
                    'WLSDPLY-05209', class_name=self._class_name, method_name=_method_name)
                self._logger.throwing(error=ce, class_name=self._class_name, method_name=_method_name)
                raise ce

        self._logger.exiting(class_name=self._class_name, method_name=_method_name)

    def validate_model_content(self, model_dict):
        #
        # This code is called by both Create Domain and Prepare Model.  Since passwords may still
        # be tokenized in Prepare Model, do not call validate_user_passwords() from here.
        #
        self.validate_dynamic_clusters(model_dict)
        self.validate_credential_mappings(model_dict)

    def validate_dynamic_clusters(self, model_dict):
        """
        Validate that dynamic clusters have a unique server template.
        :param model_dict: A Python dictionary of the model to be validated
        :raises ValidationException: if problems occur during validation
        """
        _method_name = 'validate_dynamic_clusters'

        server_templates = []
        topology_folder = dictionary_utils.get_dictionary_element(model_dict, TOPOLOGY)
        clusters_folder = dictionary_utils.get_dictionary_element(topology_folder, CLUSTER)
        for cluster_name, cluster_fields in clusters_folder.items():
            dynamic_folder = dictionary_utils.get_element(cluster_fields, DYNAMIC_SERVERS)
            if dynamic_folder is not None:
                server_template = dictionary_utils.get_element(dynamic_folder, SERVER_TEMPLATE)

                if not server_template:
                    self._logger.warning('WLSDPLY-05200', cluster_name, SERVER_TEMPLATE,
                                         class_name=self._class_name, method_name=_method_name)

                elif server_template in server_templates:
                    self._logger.warning('WLSDPLY-05201', cluster_name, SERVER_TEMPLATE, server_template,
                                         class_name=self._class_name, method_name=_method_name)

                else:
                    server_templates.append(server_template)

    def validate_credential_mappings(self, model_dict):
        """
        Validate the content of the WLSUserPasswordCredentialMappings section of the model.
        This does not include simple single-attribute validation such as value ranges,
        those are handled in domain_info_validator.__validate_wls_credential_mappings_section
        :param model_dict: the model to be validated
        """
        domain_info_folder = dictionary_utils.get_dictionary_element(model_dict, DOMAIN_INFO)
        mappings_folder = dictionary_utils.get_dictionary_element(domain_info_folder,
                                                                  WLS_USER_PASSWORD_CREDENTIAL_MAPPINGS)

        cross_domain_dict = dictionary_utils.get_dictionary_element(mappings_folder, CROSS_DOMAIN)
        for mapping_name, mapping_dict in cross_domain_dict.iteritems():
            self.__validate_required_field(mapping_dict, REMOTE_USER, CROSS_DOMAIN, mapping_name)
            self.__validate_required_field(mapping_dict, REMOTE_PASSWORD, CROSS_DOMAIN, mapping_name)
            self.__validate_required_field(mapping_dict, REMOTE_DOMAIN, CROSS_DOMAIN, mapping_name)

        remote_resources_dict = dictionary_utils.get_dictionary_element(mappings_folder, REMOTE_RESOURCE)
        for mapping_name, mapping_dict in remote_resources_dict.iteritems():
            self.__validate_required_field(mapping_dict, REMOTE_USER, REMOTE_RESOURCE, mapping_name)
            self.__validate_required_field(mapping_dict, REMOTE_PASSWORD, REMOTE_RESOURCE, mapping_name)
            self.__validate_required_field(mapping_dict, REMOTE_HOST, REMOTE_RESOURCE, mapping_name)

    def __validate_required_field(self, dictionary, field_name, parent_folder_name, folder_name):
        _method_name = '__validate_required_field'

        if field_name not in dictionary:
            self._logger.severe('WLSDPLY-05210', field_name, parent_folder_name, folder_name,
                                class_name=self._class_name, method_name=_method_name)

