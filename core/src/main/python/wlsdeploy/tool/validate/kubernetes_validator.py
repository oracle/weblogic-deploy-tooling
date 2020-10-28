"""
Copyright (c) 2017, 2020, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""

from wlsdeploy.aliases import model_constants
from wlsdeploy.aliases.model_constants import KUBERNETES
from wlsdeploy.exception.expection_types import ExceptionType
from wlsdeploy.tool.extract import wko_schema_helper
from wlsdeploy.tool.validate import validation_utils
from wlsdeploy.tool.validate.validator_logger import ValidatorLogger
from wlsdeploy.util import dictionary_utils
from wlsdeploy.util.enum import Enum


_ModelNodeTypes = Enum(['FOLDER_TYPE', 'NAME_TYPE', 'ATTRIBUTE', 'ARTIFICIAL_TYPE'])
_ValidationModes = Enum(['STANDALONE', 'TOOL'])
_ROOT_LEVEL_VALIDATION_AREA = validation_utils.format_message('WLSDPLY-05000')
_DOMAIN_INFO_VALIDATION_AREA = validation_utils.format_message('WLSDPLY-05001', model_constants.DOMAIN_INFO)
_TOPOLOGY_VALIDATION_AREA = validation_utils.format_message('WLSDPLY-05001', model_constants.TOPOLOGY)
_RESOURCES_VALIDATION_AREA = validation_utils.format_message('WLSDPLY-05001', model_constants.RESOURCES)
_APP_DEPLOYMENTS_VALIDATION_AREA = validation_utils.format_message('WLSDPLY-05001', model_constants.APP_DEPLOYMENTS)
_GLOBAL_LEVEL_VARAIBLE_SUBSTITUTE = validation_utils.format_message('WLSDPLY-05001',
                                                                    model_constants.GLOBAL_VARIABLE_SUBSTITUTION)


class KubernetesValidator(object):
    """
    Class for validating the kubernetes section of a model file
    """
    _class_name = 'KubernetesValidator'
    _logger = ValidatorLogger('wlsdeploy.validate')

    def __init__(self, model_context):
        self._model_context = model_context
        return

    def validate_model(self, model_dict):
        """
        Validate the kubernetes section of the specified model.
        :param model_dict: A Python dictionary of the model to be validated
        :raises ValidationException: if problems occur during validation
        """
        _method_name = 'validate_model'

        kubernetes_section = dictionary_utils.get_dictionary_element(model_dict, KUBERNETES)
        if not kubernetes_section:
            return

        schema = wko_schema_helper.get_domain_resource_schema(exception_type=ExceptionType.VALIDATE)

        # validate top-level attributes

        self.validate_folder(kubernetes_section, schema, None)

    def validate_folder(self, model_folder, schema_folder, path, extra_attributes=None):
        """
        Validate the specified model folder against the specified schema folder
        """
        # if extra_attributes is None:
        #     extra_attributes = {}

        self._log_debug(str(path))

        properties = dictionary_utils.get_dictionary_element(schema_folder, "properties")

        for key in model_folder:
            property_map = dictionary_utils.get_element(properties, key)
            model_value = model_folder[key]

            if property_map is not None:
                property_type = dictionary_utils.get_element(property_map, "type")

                if property_type == "object":
                    additional = dictionary_utils.get_dictionary_element(property_map, "additionalProperties")
                    additional_type = dictionary_utils.get_element(additional, "type")
                    if additional_type:
                        # map of key / value pairs
                        self._log_debug('  ' + key + ': map of ' + additional_type)
                        self._validate_simple_map(model_value, property_map)
                    else:
                        # single object instance
                        self._log_debug('  ' + key + ': folder')
                        next_path = _get_next_path(path, key)
                        self.validate_folder(model_value, property_map, next_path)

                elif property_type == "array":
                    array_items = dictionary_utils.get_dictionary_element(property_map, "items")
                    array_type = dictionary_utils.get_dictionary_element(array_items, "type")
                    if array_type == "object":
                        # multiple object instances
                        self._log_debug('  ' + key + ': multiple folder')
                        next_path = _get_next_path(path, key)
                        self._validate_multiple_folder(model_value, array_items, next_path)
                    else:
                        # array of simple type
                        self._log_debug('  ' + key + ': array of ' + array_type)
                        self._validate_simple_array(model_value, property_map)

                else:
                    self._log_debug('  ' + key + ': ' + property_type)
                    self._validate_simple_type(model_value, property_type)

            else:
                self._log_debug('  *** ' + key + " not in " + str(properties))

    def _validate_simple_map(self, model_value, property_map):
        pass

    def _validate_multiple_folder(self, model_value, property_map, path):
        if not isinstance(model_value, dict):
            self._logger.severe("expecting dict at " + path)

        for name in model_value:
            name_map = model_value[name]
            next_path = _get_next_path(path, name)
            self.validate_folder(name_map, property_map, next_path)

    def _validate_simple_array(self, model_value, property_map):
        pass

    def _validate_simple_type(self, model_value, property_type):
        pass

    def _log_debug(self, message):
        self._logger.finest(message)


def _get_next_path(path, key):
    if path is None:
        return key
    return path + '/' + key
