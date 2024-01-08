"""
Copyright (c) 2020, 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""

from wlsdeploy.exception.exception_types import ExceptionType
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.util.targets import model_crd_helper
from wlsdeploy.tool.util.targets import schema_helper
from wlsdeploy.util import dictionary_utils
import wlsdeploy.util.unicode_helper as str_helper


class CrdSectionsValidator(object):
    """
    Class for validating a CRD-based section of a model file.
    This includes kubernetes and verrazzano sections.
    """
    _class_name = 'CrdSectionsValidator'
    _logger = PlatformLogger('wlsdeploy.validate')

    def __init__(self, model_context):
        self._model_context = model_context
        self._crd_helper = model_crd_helper.get_helper(model_context, ExceptionType.VALIDATE)
        self._section_name = self._crd_helper.get_model_section()
        self._try_validate = False  # suspend severe logging for "try" validations
        self._invalid_count = 0  # the count of invalid log messages since last reset

    def validate_model(self, model_dict):
        """
        Validate the CRD-based section of the specified model.
        :param model_dict: A Python dictionary of the model to be validated
        :raises ValidationException: if problems occur during validation
        """
        _method_name = 'validate_model'

        crd_section = dictionary_utils.get_dictionary_element(model_dict, self._section_name)
        if not crd_section:
            return

        model_path = self._section_name + ":"

        keyless_crd_folder = self._crd_helper.get_keyless_crd_folder()
        if keyless_crd_folder:
            # this WKO version does not require CRD sub-folders for this section, continue with the keyless schema
            schema = keyless_crd_folder.get_schema()
            self.validate_folder(crd_section, schema, None, model_path)
        else:
            # this WKO version requires CRD sub-folders for this section, validate and process each folder
            for key in crd_section:
                crd_folder = self._crd_helper.get_crd_folder(key)
                if not crd_folder:
                    valid_keys = self._crd_helper.get_crd_folder_keys()
                    self._log_invalid("WLSDPLY-05026", key, len(valid_keys), model_path,
                                      '%s' % ', '.join(valid_keys),
                                      class_name=self._class_name, method_name=_method_name)
                    continue

                model_content = crd_section[key]
                model_path += '/' + key
                schema = crd_folder.get_schema()
                if crd_folder.is_array():
                    self._validate_object_array(model_content, schema, None, model_path)
                else:
                    self.validate_folder(model_content, schema, None, model_path)

    def validate_folder(self, model_folder, schema_folder, schema_path, model_path):
        """
        Validate the specified model folder against the specified schema folder
        :param model_folder: the model folder to validate
        :param schema_folder: the schema folder to validate against
        :param schema_path: the path of schema elements (no array indices), used for supported check
        :param model_path: the path of model elements (including array indices), used for logging
        """
        _method_name = 'validate_folder'
        self._log_debug(str_helper.to_string(model_path))

        if not isinstance(model_folder, dict):
            self._log_invalid("WLSDPLY-05038", model_path, class_name=self._class_name, method_name=_method_name)
            return

        folder_options = schema_helper.get_one_of_options(schema_folder)
        if folder_options:
            # if schema folder has multiple content options, find one matching the model folder content
            folder_option = self.find_folder_option(model_folder, folder_options, schema_path, model_path)
            if not folder_option:
                self._log_invalid("WLSDPLY-05043", model_path, len(folder_options),
                                  class_name=self._class_name, method_name=_method_name)
        else:
            # if folder has one set of properties, validate against those
            schema_properties = schema_helper.get_properties(schema_folder)
            self.validate_folder_properties(model_folder, schema_properties, schema_path, model_path)

    def validate_folder_properties(self, model_folder, schema_properties, schema_path, model_path):
        """
        Validate the specified model folder against the specified schema properties.
        These properties may be directly from the schema folder, or an option in a "one of" list.
        :param model_folder: the model folder to validate
        :param schema_properties: the schema properties to validate against
        :param schema_path: the path of schema elements (no array indices), used for supported check
        :param model_path: the path of model elements (including array indices), used for logging
        """
        _method_name = 'validate_folder_properties'

        for key in model_folder:
            properties = dictionary_utils.get_element(schema_properties, key)
            model_value = model_folder[key]

            if properties is not None:

                if schema_helper.is_single_object(properties):
                    # single object instance
                    self._log_debug('  ' + key + ': single object')
                    next_schema_path = schema_helper.append_path(schema_path, key)
                    next_model_path = model_path + "/" + key
                    if self._check_folder_path(next_schema_path, next_model_path):
                        self.validate_folder(model_value, properties, next_schema_path, next_model_path)

                elif schema_helper.is_object_array(properties):
                    self._log_debug('  ' + key + ': object array')
                    next_schema_path = schema_helper.append_path(schema_path, key)
                    next_model_path = model_path + "/" + key
                    if self._check_folder_path(next_schema_path, next_model_path):
                        item_info = schema_helper.get_array_item_info(properties)
                        self._validate_object_array(model_value, item_info, next_schema_path, next_model_path)

                elif schema_helper.is_simple_map(properties):
                    # map of key / value pairs
                    element_type = schema_helper.get_map_element_type(properties)
                    self._log_debug('  ' + key + ': map of ' + element_type)
                    self._validate_simple_map(model_value, key, model_path)

                elif schema_helper.is_simple_array(properties):
                    # array of simple type
                    element_type = schema_helper.get_array_element_type(properties)
                    self._log_debug('  ' + key + ': array of ' + element_type)
                    self._validate_simple_array(model_value, key, model_path)

                else:
                    # simple type
                    property_type = schema_helper.get_type(properties)
                    self._log_debug('  ' + key + ': ' + property_type)
                    self._validate_simple_type(model_value, property_type, key, model_path)

            else:
                self._log_invalid("WLSDPLY-05026", key, len(schema_properties), model_path,
                                  '%s' % ', '.join(schema_properties), class_name=self._class_name,
                                  method_name=_method_name)

    def find_folder_option(self, model_folder, folder_options, schema_path, model_path):
        """
        Find a schema folder option that corresponds to the specified model folder contents.
        Try validating with each folder option until successful.
        :param model_folder: the model folder to match
        :param folder_options: a list of folder options from the schema
        :param schema_path: the path of schema elements (no array indices), used for supported check
        :param model_path: the path of model elements (including array indices), used for logging
        :return: the matching folder option, or None
        """
        _method_name = 'find_folder_option'

        # try validating against each option until successful
        result = None
        self._try_validate = True
        for index, folder_option in enumerate(folder_options):
            self._logger.fine("WLSDPLY-05041", index, model_path,
                              class_name=self._class_name, method_name=_method_name)
            self._invalid_count = 0
            schema_properties = schema_helper.get_properties(folder_option)
            self.validate_folder_properties(model_folder, schema_properties, schema_path, model_path)
            if not self._invalid_count:
                self._logger.fine("WLSDPLY-05042", index, model_path,
                                  class_name=self._class_name, method_name=_method_name)
                result = folder_option
                break

        self._try_validate = False
        return result

    def _validate_object_array(self, model_value, property_map, schema_path, model_path):
        """
        Validate the contents of this object array.
        :param model_value: the model contents for a folder
        :param property_map: describes the contents of the sub-folder for each element
        :param schema_path: the path of schema elements (no array indices), used for supported check
        :param model_path: the path of model elements (including array indices), used for logging
        """
        _method_name = '_validate_object_array'

        if not isinstance(model_value, list):
            self._log_invalid("WLSDPLY-05040", model_path, class_name=self._class_name, method_name=_method_name)
            return

        index = 0
        for object_map in model_value:
            index_path = '%s[%s]' % (model_path, index)
            self.validate_folder(object_map, property_map, schema_path, index_path)
            index += 1

    def _validate_simple_map(self, model_value, property_name, model_path):
        _method_name = '_validate_simple_map'
        if not isinstance(model_value, dict):
            self._log_invalid("WLSDPLY-05032", property_name, model_path, str_helper.to_string(type(model_value)),
                              class_name=self._class_name, method_name=_method_name)

    def _validate_simple_array(self, model_value, property_name, model_path):
        _method_name = '_validate_simple_array'
        if isinstance(model_value, dict):
            self._log_invalid("WLSDPLY-05017", property_name, model_path, "list",
                              str_helper.to_string(type(model_value)),
                              class_name=self._class_name, method_name=_method_name)

    def _validate_simple_type(self, model_value, property_type, property_name, model_path):
        _method_name = '_validate_simple_type'
        if isinstance(model_value, list) or isinstance(model_value, dict):
            self._log_invalid("WLSDPLY-05017", property_name, model_path, property_type,
                              str_helper.to_string(type(model_value)),
                              class_name=self._class_name, method_name=_method_name)

    def _check_folder_path(self, schema_path, model_path):
        """
        Log a warning if the specified path is unsupported in the schema.
        :param schema_path: the schema path to be checked
        :param model_path: the model path used for logging
        :return: True if the path is supported, False otherwise
        """
        _method_name = '_check_folder_path'
        if schema_helper.is_unsupported_folder(schema_path):
            self._logger.warning("WLSDPLY-05090", model_path, class_name=self._class_name, method_name=_method_name)
            return False
        return True

    def _log_debug(self, message):
        self._logger.finest(message)

    def _log_invalid(self, message, *args, **kwargs):
        log_method = self._logger.severe
        if self._try_validate:
            log_method = self._logger.fine
        log_method(message, *args, **kwargs)
        self._invalid_count += 1
