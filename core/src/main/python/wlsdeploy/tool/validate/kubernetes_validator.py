"""
Copyright (c) 2020, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""

from wlsdeploy.aliases.model_constants import KUBERNETES
from wlsdeploy.exception.expection_types import ExceptionType
from wlsdeploy.tool.extract import wko_schema_helper
from wlsdeploy.tool.validate.validator_logger import ValidatorLogger
from wlsdeploy.util import dictionary_utils


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

    def validate_folder(self, model_folder, schema_folder, path):
        """
        Validate the specified model folder against the specified schema folder
        :param model_folder: the model folder to validate
        :param schema_folder: the schema folder to validate against
        :param path: the path of model elements, used for logging
        """
        _method_name = 'validate_folder'
        self._log_debug(str(path))

        log_path = _get_log_path(path)

        if not isinstance(model_folder, dict):
            self._logger.severe("WLSDPLY-05038", log_path, class_name=self._class_name, method_name=_method_name)
            return

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
                        self._validate_simple_map(model_value, key, log_path)
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
                        self._validate_simple_array(model_value, key, log_path)

                else:
                    self._log_debug('  ' + key + ': ' + property_type)
                    self._validate_simple_type(model_value, property_type, key, log_path)

            else:
                self._logger.severe("WLSDPLY-05026", key, len(properties), log_path, class_name=self._class_name,
                                    method_name=_method_name)

    def _validate_simple_map(self, model_value, property_name, log_path):
        _method_name = '_validate_simple_map'
        if not isinstance(model_value, dict):
            self._logger.severe("WLSDPLY-05032", property_name, log_path, str(type(model_value)),
                                class_name=self._class_name, method_name=_method_name)

    def _validate_multiple_folder(self, model_value, property_map, path):
        _method_name = '_validate_multiple_folder'
        if not isinstance(model_value, dict):
            self._logger.severe("WLSDPLY-05039", _get_log_path(path), class_name=self._class_name,
                                method_name=_method_name)
            return

        for name in model_value:
            name_map = model_value[name]
            next_path = _get_next_path(path, name)
            self.validate_folder(name_map, property_map, next_path)

    def _validate_simple_array(self, model_value, property_name, log_path):
        _method_name = '_validate_simple_array'
        if isinstance(model_value, dict):
            self._logger.severe("WLSDPLY-05017", property_name, log_path, "list", str(type(model_value)),
                                class_name=self._class_name, method_name=_method_name)

    def _validate_simple_type(self, model_value, property_type, property_name, log_path):
        _method_name = '_validate_simple_type'
        if isinstance(model_value, list) or isinstance(model_value, dict):
            self._logger.severe("WLSDPLY-05017", property_name, log_path, property_type, str(type(model_value)),
                                class_name=self._class_name, method_name=_method_name)

    def _log_debug(self, message):
        self._logger.finest(message)


def _get_next_path(path, key):
    if path is None:
        return key
    return path + '/' + key


def _get_log_path(path):
    log_path = KUBERNETES + ':/'
    if path:
        log_path = log_path + path
    return log_path
