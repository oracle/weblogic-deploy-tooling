"""
Copyright (c) 2020, 2022, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""

from wlsdeploy.aliases.model_constants import KUBERNETES
from wlsdeploy.exception.expection_types import ExceptionType
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.extract import wko_schema_helper
from wlsdeploy.util import dictionary_utils


class KubernetesValidator(object):
    """
    Class for validating the kubernetes section of a model file
    """
    _class_name = 'KubernetesValidator'
    _logger = PlatformLogger('wlsdeploy.validate')

    def __init__(self, model_context):
        self._model_context = model_context

    def validate_model(self, model_dict):
        """
        Validate the kubernetes section of the specified model.
        :param model_dict: A Python dictionary of the model to be validated
        :raises ValidationException: if problems occur during validation
        """
        kubernetes_section = dictionary_utils.get_dictionary_element(model_dict, KUBERNETES)
        if not kubernetes_section:
            return

        schema = wko_schema_helper.get_domain_resource_schema(exception_type=ExceptionType.VALIDATE)

        model_path = KUBERNETES + ":"
        self.validate_folder(kubernetes_section, schema, None, model_path)

    def validate_folder(self, model_folder, schema_folder, schema_path, model_path):
        """
        Validate the specified model folder against the specified schema folder
        :param model_folder: the model folder to validate
        :param schema_folder: the schema folder to validate against
        :param schema_path: the path of schema elements (no array indices), used for supported check
        :param model_path: the path of model elements (including array indices), used for logging
        """
        _method_name = 'validate_folder'
        self._log_debug(str(model_path))

        if not isinstance(model_folder, dict):
            self._logger.severe("WLSDPLY-05038", model_path, class_name=self._class_name, method_name=_method_name)
            return

        schema_properties = wko_schema_helper.get_properties(schema_folder)

        for key in model_folder:
            properties = dictionary_utils.get_element(schema_properties, key)
            model_value = model_folder[key]

            if properties is not None:

                if wko_schema_helper.is_single_object(properties):
                    # single object instance
                    self._log_debug('  ' + key + ': single object')
                    next_schema_path = wko_schema_helper.append_path(schema_path, key)
                    next_model_path = model_path + "/" + key
                    if self._check_folder_path(next_schema_path, next_model_path):
                        self.validate_folder(model_value, properties, next_schema_path, next_model_path)

                elif wko_schema_helper.is_object_array(properties):
                    self._log_debug('  ' + key + ': object array')
                    next_schema_path = wko_schema_helper.append_path(schema_path, key)
                    next_model_path = model_path + "/" + key
                    if self._check_folder_path(next_schema_path, next_model_path):
                        item_info = wko_schema_helper.get_array_item_info(properties)
                        self._validate_object_array(model_value, item_info, next_schema_path, next_model_path)

                elif wko_schema_helper.is_simple_map(properties):
                    # map of key / value pairs
                    element_type = wko_schema_helper.get_map_element_type(properties)
                    self._log_debug('  ' + key + ': map of ' + element_type)
                    self._validate_simple_map(model_value, key, model_path)

                elif wko_schema_helper.is_simple_array(properties):
                    # array of simple type
                    element_type = wko_schema_helper.get_array_element_type(properties)
                    self._log_debug('  ' + key + ': array of ' + element_type)
                    self._validate_simple_array(model_value, key, model_path)

                else:
                    # simple type
                    property_type = wko_schema_helper.get_type(properties)
                    self._log_debug('  ' + key + ': ' + property_type)
                    self._validate_simple_type(model_value, property_type, key, model_path)

            else:
                self._logger.severe("WLSDPLY-05026", key, len(schema_properties), model_path,
                                    '%s' % ', '.join(schema_properties), class_name=self._class_name,
                                    method_name=_method_name)

    def _validate_object_array(self, model_value, property_map, schema_path, model_path):
        """
        Validate the contents of this object array.
        :param model_value: the model contents for a folder
        :param property_map: describes the contents of the sub-folder for each element
        :param schema_path: the path of schema elements (no array indices), used for supported check
        :param model_path: the path of model elements (including array indices), used for logging
        """
        _method_name = '_validate_object_array'

        # deprecated "named object list" format
        if isinstance(model_value, dict):
            self._logger.warning("WLSDPLY-05091", model_path, class_name=self._class_name, method_name=_method_name)
            for name in model_value:
                object_map = model_value[name]
                next_model_path = model_path + "/" + name
                self.validate_folder(object_map, property_map, schema_path, next_model_path)
            return
        # end deprecated

        if not isinstance(model_value, list):
            self._logger.severe("WLSDPLY-05040", model_path, class_name=self._class_name, method_name=_method_name)
            return

        index = 0
        for object_map in model_value:
            index_path = '%s[%s]' % (model_path, index)
            self.validate_folder(object_map, property_map, schema_path, index_path)
            index += 1

    def _validate_simple_map(self, model_value, property_name, model_path):
        _method_name = '_validate_simple_map'
        if not isinstance(model_value, dict):
            self._logger.severe("WLSDPLY-05032", property_name, model_path, str(type(model_value)),
                                class_name=self._class_name, method_name=_method_name)

    def _validate_simple_array(self, model_value, property_name, model_path):
        _method_name = '_validate_simple_array'
        if isinstance(model_value, dict):
            self._logger.severe("WLSDPLY-05017", property_name, model_path, "list", str(type(model_value)),
                                class_name=self._class_name, method_name=_method_name)

    def _validate_simple_type(self, model_value, property_type, property_name, model_path):
        _method_name = '_validate_simple_type'
        if isinstance(model_value, list) or isinstance(model_value, dict):
            self._logger.severe("WLSDPLY-05017", property_name, model_path, property_type, str(type(model_value)),
                                class_name=self._class_name, method_name=_method_name)

    def _check_folder_path(self, schema_path, model_path):
        """
        Log a warning if the specified path is unsupported in the schema.
        :param schema_path: the schema path to be checked
        :param model_path: the model path used for logging
        :return: True if the path is supported, False otherwise
        """
        _method_name = '_check_folder_path'
        if wko_schema_helper.is_unsupported_folder(schema_path):
            self._logger.warning("WLSDPLY-05090", model_path, class_name=self._class_name, method_name=_method_name)
            return False
        return True

    def _log_debug(self, message):
        self._logger.finest(message)
