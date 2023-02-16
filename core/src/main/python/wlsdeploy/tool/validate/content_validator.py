"""
Copyright (c) 2023, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
from wlsdeploy.aliases.model_constants import CLUSTER
from wlsdeploy.aliases.model_constants import DYNAMIC_SERVERS
from wlsdeploy.aliases.model_constants import SERVER_TEMPLATE
from wlsdeploy.aliases.model_constants import TOPOLOGY
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.util import dictionary_utils


class ContentValidator(object):
    """
    Class for validating consistency and compatibility of model folders and attributes.
    These checks are done after alias folder and attribute checks.
    The model may be a partial model from a multiple-model configuration.

    Dynamic clusters is currently the only validation.
    Other non-alias validations might fit here (RcuDbInfo?).
    """
    _class_name = 'ContentValidator'
    _logger = PlatformLogger('wlsdeploy.validate')

    def __init__(self, model_context):
        self._model_context = model_context

    def validate_model(self, model_dict):
        """
        Validate the contents of the specified model.
        :param model_dict: A Python dictionary of the model to be validated
        :raises ValidationException: if problems occur during validation
        """
        _method_name = 'validate_model'

        self.validate_dynamic_clusters(model_dict)

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
            if dynamic_folder:
                server_template = dictionary_utils.get_element(dynamic_folder, SERVER_TEMPLATE)

                if not server_template:
                    self._logger.warning('WLSDPLY-05200', cluster_name, SERVER_TEMPLATE,
                                         class_name=self._class_name, method_name=_method_name)

                elif server_template in server_templates:
                    self._logger.warning('WLSDPLY-05201', cluster_name, SERVER_TEMPLATE, server_template,
                                         class_name=self._class_name, method_name=_method_name)

                else:
                    server_templates.append(server_template)
