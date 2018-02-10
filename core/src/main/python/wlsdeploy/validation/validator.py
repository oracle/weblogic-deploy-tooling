"""
Copyright (c) 2017, 2018, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""

from java.io import IOException
from java.lang import IllegalArgumentException
from java.util import Properties
from java.io import BufferedReader
from java.io import FileReader

import os
import re

from wlsdeploy.aliases import model_constants
from wlsdeploy.aliases.aliases import Aliases
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.validation_codes import ValidationCodes
from wlsdeploy.exception import exception_helper
from wlsdeploy.validation import validation_utils
from wlsdeploy.validation.usage_printer import UsagePrinter
from wlsdeploy.util.enum import Enum
from wlsdeploy.util import model

import oracle.weblogic.deploy.aliases.AliasException as AliasException
import oracle.weblogic.deploy.validation.ValidateException as ValidateException

_class_name = 'Validator'
_logger = PlatformLogger('wlsdeploy.validate')
_ModelNodeTypes = Enum(['FOLDER', 'FOLDER_INSTANCE', 'ATTRIBUTE'])
_ROOT_LEVEL_VALIDATION_AREA = validation_utils.format_message('WLSDPLY-03225')
_DOMAIN_INFO_VALIDATION_AREA = validation_utils.format_message('WLSDPLY-03226', model_constants.DOMAIN_INFO)
_TOPOLOGY_VALIDATION_AREA = validation_utils.format_message('WLSDPLY-03226', model_constants.TOPOLOGY)
_RESOURCES_VALIDATION_AREA = validation_utils.format_message('WLSDPLY-03226', model_constants.RESOURCES)
_APP_DEPLOYMENTS_VALIDATION_AREA = validation_utils.format_message('WLSDPLY-03226', model_constants.APP_DEPLOYMENTS)
_ARCHIVE_ENTRIES_VALIDATION_AREA = validation_utils.format_message('WLSDPLY-03227')


class Validator(object):
    """

    """
    ValidationStatus = Enum(['VALID', 'INFOS_VALID', 'WARNINGS_INVALID', 'INVALID'])

    def __init__(self, model_context, logger=None, wlst_mode=None):
        self._model_context = model_context

        if logger is None:
            self._logger = _logger
        else:
            self._logger = logger

        self._validation_results = Validator.ValidationResults()

        # The wlst_mode argument is only used by the tools calling validation.
        # In the standalone validation tool use case, the user can specify the target
        # mode on the command-line so we can get the value from the model context...
        if wlst_mode is not None:
            self._wlst_mode = wlst_mode
        else:
            self._wlst_mode = model_context.get_target_wlst_mode()

        self._wls_version = model_context.get_target_wls_version()

        self._aliases = Aliases(model_context=model_context)

    def validate_in_standalone_mode(self, model_dict, variables_file_name=None, archive_file_name=None):
        """
        Performs model file validation and returns a Validator.ValidationResults object.

        Prints a text representation of the returned object to STDOUT, using an 80 characters per
        line format (when possible). Info-related items are printed first, followed by warning-related
        ones, followed by error-related ones.

        :param model_dict: A Python dictionary of the model to be validated
        :param variables_file_name: Path to file containing variable substitution data used with model file.
        Defaults to None.
        :param archive_file_name: Path to file containing binaries associated with the model file.
        Defaults to None.
        :return: A Validator.ValidationResults object
        :raises ValidationException: if an AliasException is raised during an invocation of an aliases API call.
        """

        _method_name = 'validate_in_standalone_mode'

        self._logger.finer('WLSDPLY-03211', class_name=_class_name, method_name=_method_name)

        try:
            model_file_name = str(self._model_context.get_model_file()).replace('\\', '/')
            self._logger.info('WLSDPLY-03207', model_file_name, class_name=_class_name, method_name=_method_name)

            if variables_file_name is not None:
                variables_file_name = str(variables_file_name).replace('\\', '/')
                validation_result = self.__validate_variable_substitutions(model_file_name, variables_file_name)
                self._validation_results.set_validation_result(validation_result)

            validation_result = Validator.ValidationResult(_ROOT_LEVEL_VALIDATION_AREA)
            validation_result = self.__validate_root_level(model_dict,
                                                           model.get_model_top_level_keys(),
                                                           validation_result)
            self._validation_results.set_validation_result(validation_result)

            validation_result = Validator.ValidationResult(_DOMAIN_INFO_VALIDATION_AREA)
            validation_result = self.__validate_domain_info_section(model.get_model_domain_info_key(),
                                                                    model_dict,
                                                                    validation_result)
            self._validation_results.set_validation_result(validation_result)

            validation_result = Validator.ValidationResult(_TOPOLOGY_VALIDATION_AREA)
            validation_result = self.__validate_model_section(model.get_model_topology_key(),
                                                              model_dict,
                                                              self._aliases.get_model_topology_top_level_folder_names(),
                                                              validation_result)
            self._validation_results.set_validation_result(validation_result)

            validation_result = Validator.ValidationResult(_RESOURCES_VALIDATION_AREA)
            validation_result = \
                self.__validate_model_section(model.get_model_resources_key(),
                                              model_dict,
                                              self._aliases.get_model_resources_top_level_folder_names(),
                                              validation_result)
            self._validation_results.set_validation_result(validation_result)

            validation_result = Validator.ValidationResult(_APP_DEPLOYMENTS_VALIDATION_AREA)
            validation_result = \
                self.__validate_model_section(model.get_model_deployments_key(),
                                              model_dict,
                                              self._aliases.get_model_app_deployments_top_level_folder_names(),
                                              validation_result)
            self._validation_results.set_validation_result(validation_result)

            self._logger.finer('archive_file_name={0}', archive_file_name,
                               class_name=_class_name, method_name=_method_name)

            if archive_file_name is not None:
                archive_file_name = str(archive_file_name).replace('\\', '/')
                validation_result = self.__validate_archive_entries(model_dict, archive_file_name)
                self._validation_results.set_validation_result(validation_result)

        except AliasException, ae:
            ex = exception_helper.create_validate_exception(error=ae)
            self._logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex

        return self._validation_results

    def validate_in_tool_mode(self, model_dict, variables_file_name=None, archive_file_name=None):
        """
        Performs model file validation and returns a status that allows a tool (e.g. discover,
        deploy, create, etc.) to determine if it should proceed, or not. Validation results are
        written to a log file, instead of STDOUT.

        Possible status codes are:

            VALID                   No error, warning or info messages.
            INFOS_VALID             No error or warning messages, but one or more info messages.
            WARNINGS_INVALID        No error messages, but one or more warnings.
            INVALID                 One or more error messages.

        :param model_dict: A Python dictionary of the model to be validated
        :param variables_file_name: Path to file containing variable substitution data used with model file.
        Defaults to None.
        :param archive_file_name: Path to file containing binaries associated with the model file.
        Defaults to None.
        :return: A Validator.ValidationStatus value
        :raises ValidationException: if an AliasException is raised during an invocation of an aliases API call.
        """

        _method_name = 'validate_in_tool_mode'

        self._logger.entering(class_name=_class_name, method_name=_method_name)

        self.validate_in_standalone_mode(model_dict, variables_file_name, archive_file_name)

        rtnval = Validator.ValidationStatus.VALID

        if self._validation_results.get_errors_count() > 0:
            rtnval = Validator.ValidationStatus.INVALID
        elif self._validation_results.get_warnings_count() > 0:
            rtnval = Validator.ValidationStatus.WARNINGS_INVALID
        elif self._validation_results.get_infos_count() > 0:
            rtnval = Validator.ValidationStatus.INFOS_VALID

        self._validation_results.log_results(self._logger)

        self._logger.exiting(class_name=_class_name, method_name=_method_name)

        return rtnval

    def print_usage(self, model_path, control_option=None):
        """

        :param model_path:
        :param control_option:
        :return:
        """
        _method_name = 'print_usage'

        self._logger.entering(model_path, class_name=_class_name, method_name=_method_name)

        if control_option is None:
            # Check the model_context
            if self._model_context.get_recursive_control_option():
                control_option = UsagePrinter.ControlOptions.RECURSIVE
            elif self._model_context.get_attributes_only_control_option():
                control_option = UsagePrinter.ControlOptions.ATTRIBUTES_ONLY

        if control_option is None:
            # Default to FOLDERS_ONLY
            control_option = UsagePrinter.ControlOptions.FOLDERS_ONLY

        try:
            usage_printer = UsagePrinter(self._aliases, self._logger)
            usage_printer.print_model_path_usage(model_path, control_option)

            self._logger.exiting(class_name=_class_name, method_name=_method_name)
        except AliasException, ae:
            ex = exception_helper.create_validate_exception(error=ae)
            self._logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex
        except ValidateException, ve:
            raise ve

        return

    ####################################################################################
    #
    # Private methods, private inner classes and static methods only, beyond here please
    #
    ####################################################################################

    def __validate_root_level(self, model_dict, valid_root_level_keys, validation_result):
        _method_name = '__validate_root_level'

        # Get list of root level keys from model_dict
        model_root_level_keys = model_dict.keys()

        if not model_root_level_keys:
            # The model_dict didn't have any top level keys, so record it
            # as a INFO message in the validation results and bail.
            info_item_message = validation_utils.format_message('WLSDPLY-03206')
            validation_result.add_info(info_item_message)

            return validation_result

        self._logger.entering(model_root_level_keys, valid_root_level_keys,
                              class_name=_class_name, method_name=_method_name)

        # Loop through model_root_level_keys
        for key in model_root_level_keys:
            if key not in valid_root_level_keys:
                # Found a model_root_level_keys key that isn't in valid_root_level_keys,
                # so record it as a INFO message in the validation results
                info_item_message = validation_utils.format_message('WLSDPLY-03209', key,
                                                                    '%s' % ', '.join(valid_root_level_keys))
                validation_result.add_info(info_item_message)

        self._logger.exiting(class_name=_class_name, method_name=_method_name)

        return validation_result

    def __validate_domain_info_section(self, model_section_key, model_dict, validation_result):
        _method_name = '__validate_domain_info_section'

        self._logger.info('WLSDPLY-03150',
                          model_section_key, self._model_context.get_model_file(),
                          class_name=_class_name, method_name=_method_name)

        validation_location = LocationContext()

        # Neither model.py nor aliases.py currently provide a method that returns the
        # valid attributes for the model_constants.DOMAIN_INFO section. This being the
        # case, we'll use a local function defined in validation_utils.py
        valid_attr_infos = validation_utils.get_domain_info_data_types()
        self._logger.finer('validation_helper.get_domain_info_data_types() returned: {0}',
                           str(valid_attr_infos),
                           class_name=_class_name, method_name=_method_name)

        model_section_dict = model_dict[model_section_key]

        if model_section_dict is not None:
            for section_dict_key, section_dict_value in model_section_dict.iteritems():
                # section_dict_key is either the name of a folder in the
                # section, or the name of an attribute in the section.
                # section_dict_value is either the dict of a folder in the
                # section, or the value of an attribute in the section
                self._logger.finer('section_dict_key={0}', section_dict_key,
                                   class_name=_class_name, method_name=_method_name)
                self._logger.finer('section_dict_value={0}', section_dict_value,
                                   class_name=_class_name, method_name=_method_name)

                if section_dict_key in valid_attr_infos:
                    # section_dict_key is an attribute under the model section, and
                    # also in valid_attr_infos.
                    validation_result = self.__validate_attribute(section_dict_key,
                                                                  section_dict_value,
                                                                  valid_attr_infos,
                                                                  validation_location,
                                                                  validation_result)
                else:
                    model_path = self._aliases.get_model_folder_path(validation_location)
                    # section_dict_key is not an attribute allowed under the model
                    # section, so record this as a validation ERROR in the validation
                    # results.
                    error_message, valid_items = self.__create_invalid_attribute_message(section_dict_key,
                                                                                         valid_attr_infos.keys(),
                                                                                         model_path)
                    validation_result.add_error(error_message, valid_items)

        return validation_result

    def __validate_model_section(self, model_section_key, model_dict, valid_section_folders, validation_result):
        _method_name = '__validate_model_section'

        self._logger.info('WLSDPLY-03150',
                          model_section_key, self._model_context.get_model_file(),
                          class_name=_class_name, method_name=_method_name)

        if model_section_key not in model_dict.keys():
            # model_section is not in model_dict.keys(), so record this as a
            # INFO message in the validation results, then bail from validating
            # this section of model_dict
            info_item_message = validation_utils.format_message('WLSDPLY-03205', model_section_key)
            validation_result.add_info(info_item_message)
            return validation_result

        model_section_dict = model_dict[model_section_key]

        for section_dict_key, section_dict_value in model_section_dict.iteritems():
            # section_dict_key is either the name of a folder in the
            # section, or the name of an attribute in the section.
            self._logger.finer('section_dict_key={0}', section_dict_key,
                               class_name=_class_name, method_name=_method_name)
            self._logger.finer('section_dict_value={0}', section_dict_value,
                               class_name=_class_name, method_name=_method_name)

            validation_location = LocationContext()

            valid_attr_infos = self._aliases.get_model_attribute_names_and_types(validation_location)
            self._logger.finer('aliases.get_model_attribute_names_and_types(validation_location) returned: {0}',
                               str(valid_attr_infos),
                               class_name=_class_name, method_name=_method_name)

            if section_dict_key in valid_attr_infos:
                # section_dict_key is the name of an attribute in the section
                validation_result = self.__validate_attribute(section_dict_key,
                                                              section_dict_value,
                                                              valid_attr_infos,
                                                              validation_location,
                                                              validation_result)
            elif section_dict_key in valid_section_folders:
                # section_dict_key is a folder under the model section

                # Append section_dict_key to location context
                validation_location.append_location(section_dict_key)
                self._logger.finer('validation_location={0}', validation_location,
                                   class_name=_class_name, method_name=_method_name)

                # Call self.__validate_section_folder() passing in section_dict_value
                # as the model_node to process
                validation_result = self.__validate_section_folder(section_dict_value,
                                                                   validation_location,
                                                                   validation_result)
            else:
                # It's not one of the section's folders and it's not an attribute of a
                # the section. Record this as a validation ERROR in the validation
                # results.
                model_path = self._aliases.get_model_folder_path(validation_location)
                error_message, valid_items_message = \
                    self.__create_invalid_folder_message(section_dict_key,
                                                         valid_section_folders,
                                                         model_path)

                validation_result.add_error(error_message, valid_items_message)

        return validation_result

    def __validate_section_folder(self, model_node, validation_location, validation_result):

        _method_name = '__validate_section_folder'

        model_path = self._aliases.get_model_folder_path(validation_location)
        self._logger.finer('WLSDPLY-03208', model_path,
                           class_name=_class_name, method_name=_method_name)

        name_token = None
        try:
            name_token = self._aliases.get_name_token(validation_location)
        except AliasException, ae:
            # This is an unexpected exception. They are generally related to intentional or
            # unintentional misspellings of folder or attribute names, aliases file typos or
            # incompletely populated location objects. Use the exception message to record an
            # ERROR validation result item, but continue with the validation process.
            validation_result.add_error(ae.getLocalizedMessage())

        self._logger.finer('name_token={0}', name_token,
                           class_name=_class_name, method_name=_method_name)

        if self._aliases.supports_multiple_mbean_instances(validation_location):
            self._logger.finer('1 model_item_category={0}',
                               _ModelNodeTypes.from_value(_ModelNodeTypes.FOLDER_INSTANCE),
                               class_name=_class_name, method_name=_method_name)
            for name in model_node:
                self._logger.finer('1 name={0}', name,
                                   class_name=_class_name, method_name=_method_name)
                new_location = LocationContext(validation_location)
                self._logger.finer('1 new_location={0}', new_location,
                                   class_name=_class_name, method_name=_method_name)
                if name_token is not None:
                    new_location.add_name_token(name_token, name)
                    self._logger.finer('1 new_location={0}', new_location,
                                       class_name=_class_name, method_name=_method_name)

                value_dict = model_node[name]
                self.__process_model_node(value_dict, new_location, validation_result)
        else:
            if name_token is not None:
                self._logger.finer('2 validation_location={0}', validation_location,
                                   class_name=_class_name, method_name=_method_name)
                name = '%s-0' % name_token
                self._logger.finer('2 name={0}', name,
                                   class_name=_class_name, method_name=_method_name)
                validation_location.add_name_token(name_token, name)
                self._logger.finer('2 validation_location={0}', validation_location,
                                   class_name=_class_name, method_name=_method_name)

            self.__process_model_node(model_node, validation_location, validation_result)

        return validation_result

    def __process_model_node(self, model_node, validation_location, validation_result):

        _method_name = '__process_model_node'

        self._logger.finer('2 model_node={0}', str(model_node),
                           class_name=_class_name, method_name=_method_name)

        valid_folder_keys = self._aliases.get_model_subfolder_names(validation_location)
        self._logger.finer('2 aliases.get_model_subfolder_names(validation_location) returned: {0}',
                           str(valid_folder_keys),
                           class_name=_class_name, method_name=_method_name)

        valid_attr_infos = self._aliases.get_model_attribute_names_and_types(validation_location)
        self._logger.finer('2 aliases.get_model_attribute_names_and_types(validation_location) returned: {0}',
                           str(valid_attr_infos),
                           class_name=_class_name, method_name=_method_name)

        for key, value in model_node.iteritems():
            self._logger.finer('2 key={0}', key,
                               class_name=_class_name, method_name=_method_name)
            self._logger.finer('2 value={0}', value,
                               class_name=_class_name, method_name=_method_name)

            if key in valid_folder_keys:
                self._logger.finer('2 model_item_category={0}',
                                   _ModelNodeTypes.from_value(_ModelNodeTypes.FOLDER),
                                   class_name=_class_name, method_name=_method_name)
                self._logger.finer('2 validation_location={0}', validation_location,
                                   class_name=_class_name, method_name=_method_name)
                new_location = LocationContext(validation_location)
                new_location.append_location(key)
                self._logger.finer('2 new_location={0}', new_location,
                                   class_name=_class_name, method_name=_method_name)
                validation_result = self.__validate_section_folder(value,
                                                                   new_location,
                                                                   validation_result)
            elif key in valid_attr_infos:
                self._logger.finer('2 model_item_category={0}',
                                   _ModelNodeTypes.from_value(_ModelNodeTypes.ATTRIBUTE),
                                   class_name=_class_name, method_name=_method_name)
                valid_data_type = valid_attr_infos[key]
                if valid_data_type == 'properties':
                    valid_prop_infos = {}
                    properties = validation_utils.get_properties(value)
                    for property_name, property_value in properties.iteritems():
                        valid_prop_infos[property_name] = validation_utils.get_property_data_type(property_value)
                        validation_result = self.__validate_property(property_name,
                                                                     property_value,
                                                                     valid_prop_infos,
                                                                     validation_location,
                                                                     validation_result)

                else:
                    validation_result = self.__validate_attribute(key,
                                                                  value,
                                                                  valid_attr_infos,
                                                                  validation_location,
                                                                  validation_result)
            else:
                self._logger.finer('2 validation_location={0}', validation_location,
                                   class_name=_class_name, method_name=_method_name)
                valid_attr_infos = self._aliases.get_model_attribute_names_and_types(validation_location)
                self._logger.finer('2 aliases.get_model_attribute_names_and_types(validation_location) returned: {0}',
                                   str(valid_attr_infos),
                                   class_name=_class_name, method_name=_method_name)
                # Aliases says that given the contents of validation_location, key is not
                # a valid folder or attribute.
                model_path = self._aliases.get_model_folder_path(validation_location)
                error_item = validation_utils.format_message('WLSDPLY-03198',
                                                             key,
                                                             'folder, folder instance or attribute',
                                                             model_path)
                valid_items = validation_utils.format_message('WLSDPLY-03152', 'folders',
                                                              '%s' % ', '.join(valid_folder_keys), str(valid_attr_infos))
                validation_result.add_error(error_item, valid_items)

        self._logger.exiting(class_name=_class_name, method_name=_method_name)

        return validation_result

    def __validate_attribute(self, attribute_name, attribute_value, valid_attr_infos,
                             validation_location, validation_result):
        _method_name = '__validate_attribute'

        self._logger.finer('WLSDPLY-03212', class_name=_class_name, method_name=_method_name)
        self._logger.finer('attribute_name={0}', attribute_name,
                           class_name=_class_name, method_name=_method_name)
        self._logger.finer('attribute_value={0}', attribute_value,
                           class_name=_class_name, method_name=_method_name)
        self._logger.finer('valid_attr_infos={0}', str(valid_attr_infos),
                           class_name=_class_name, method_name=_method_name)
        self._logger.finer('validation_location={0}', validation_location,
                           class_name=_class_name, method_name=_method_name)

        model_path = self._aliases.get_model_folder_path(validation_location)

        if attribute_name in valid_attr_infos:
            expected_data_type = valid_attr_infos[attribute_name]
            actual_data_type = str(type(attribute_value))
            self._logger.finer('expected_data_type={0}', expected_data_type,
                               class_name=_class_name, method_name=_method_name)
            self._logger.finer('actual_data_type={0}', actual_data_type,
                               class_name=_class_name, method_name=_method_name)
            if validation_utils.is_compatible_data_type(expected_data_type, actual_data_type) is False:
                warning_item_message = validation_utils.format_message('WLSDPLY-03210',
                                                                       attribute_name,
                                                                       model_path,
                                                                       expected_data_type, actual_data_type)
                validation_result.add_warning(warning_item_message)

                result, message = self._aliases.is_valid_model_attribute_name(validation_location, attribute_name)
                if result == ValidationCodes.VERSION_INVALID:
                    validation_result.add_warning(message)
                elif result == ValidationCodes.INVALID:
                    validation_result.add_error(message)
        else:
            warning_item_message = validation_utils.format_message('WLSDPLY-03149',
                                                                   attribute_name,
                                                                   model_path)
            validation_result.add_warning(warning_item_message)

        return validation_result

    def __validate_property(self, property_name, property_value, valid_prop_infos,
                            validation_location, validation_result):

        _method_name = '__validate_property'

        self._logger.finer('WLSDPLY-03213', class_name=_class_name, method_name=_method_name)

        self._logger.finer('property_name={0}', property_name,
                           class_name=_class_name, method_name=_method_name)
        self._logger.finer('property_value={0}', property_value,
                           class_name=_class_name, method_name=_method_name)
        self._logger.finer('valid_prop_infos={0}', str(valid_prop_infos),
                           class_name=_class_name, method_name=_method_name)
        self._logger.finer('validation_location={0}', validation_location,
                           class_name=_class_name, method_name=_method_name)

        model_path = self._aliases.get_model_folder_path(validation_location)

        if property_name in valid_prop_infos:
            expected_data_type = valid_prop_infos[property_name]
            actual_data_type = str(type(property_value))
            self._logger.finer('expected_data_type={0}', expected_data_type,
                               class_name=_class_name, method_name=_method_name)
            self._logger.finer('actual_data_type={0}', actual_data_type,
                               class_name=_class_name, method_name=_method_name)
            if validation_utils.is_compatible_data_type(expected_data_type, actual_data_type) is False:
                warning_item_message = validation_utils.format_message('WLSDPLY-03210',
                                                                       property_name,
                                                                       model_path,
                                                                       expected_data_type, actual_data_type)
                validation_result.add_warning(warning_item_message)
        else:
            warning_item_message = validation_utils.format_message('WLSDPLY-03149',
                                                                   property_name,
                                                                   model_path)
            validation_result.add_warning(warning_item_message)

        return validation_result

    def __validate_variable_substitutions(self, model_file, variables_file):
        _method_name = '__validate_variable_substitutions'

        self._logger.info('WLSDPLY-03155', variables_file,
                          class_name=_class_name, method_name=_method_name)

        self._logger.finer('model_file={0}', model_file,
                           class_name=_class_name, method_name=_method_name)
        self._logger.finer('variables_file={0}', variables_file,
                           class_name=_class_name, method_name=_method_name)

        validation_result = Validator.ValidationResult('Variable Substitutions')

        valid_items = None

        try:
            variable_properties = Properties()

            if variables_file is not None:
                variable_properties = validation_utils.load_model_variables_file_properties(variables_file,
                                                                                            self._logger)
            b = BufferedReader(FileReader(model_file))
            line_num = 0
            while True:
                read_line = b.readLine()
                line_num += 1
                if read_line:
                    tokens = re.findall(r'\$\{[\w.-]+\}', str(read_line))
                    for token in tokens:
                        if variable_properties.get(token[2:len(token)-1]) is None:
                            error_message = validation_utils.format_message('WLSDPLY-03176',
                                                                            str(line_num), model_file,
                                                                            variables_file, token)
                            validation_result.add_error(error_message, valid_items)
                else:
                    break

        except (IOException, IllegalArgumentException), e:
            error_message = validation_utils.format_message('WLSDPLY-03123', variables_file,
                                                            e.getLocalizedMessage())
            validation_result.add_error(error_message, valid_items)
        except re.error, e:
            error_message = validation_utils.format_message('WLSDPLY-03179', variables_file,
                                                            e.getLocalizedMessage())
            validation_result.add_error(error_message, valid_items)

        return validation_result

    def __validate_archive_entries(self, model_dict, archive_file_name):

        _method_name = '__validate_archive_entries'

        self._logger.info('WLSDPLY-03217', archive_file_name,
                          class_name=_class_name, method_name=_method_name)

        self._logger.finer('archive_file_name={0}', archive_file_name,
                           class_name=_class_name, method_name=_method_name)

        validation_result = Validator.ValidationResult(_ARCHIVE_ENTRIES_VALIDATION_AREA)

        model_section_key = model.get_model_deployments_key()

        if model_section_key in model_dict:
            archive = validation_utils.load_model_archive_file_entries(archive_file_name, self._logger)
            valid_archive_entries_keys = validation_utils.get_valid_archive_entries_keys()
            validation_result = self.__validate_archive_entries_keys(archive.namelist(),
                                                                     valid_archive_entries_keys,
                                                                     archive_file_name,
                                                                     validation_result)

            model_deployables_dict = model_dict[model_section_key]

            validation_result = self.__validate_model_references(model_deployables_dict,
                                                                 archive.namelist(),
                                                                 archive_file_name,
                                                                 validation_result)
        else:
            info_item_message = validation_utils.format_message('WLSDPLY-03205',
                                                                model_section_key)
            validation_result.add_info(info_item_message)

        return validation_result

    def __validate_archive_entries_keys(self, archive_entries, valid_archive_entries_keys, archive_file_name,
                                        validation_result):
        _method_name = '__validate_archive_entries_keys'

        for entry in archive_entries:
            self._logger.finer('entry={0}', entry,
                               class_name=_class_name, method_name=_method_name)
            valid = False
            for valid_entry_path in valid_archive_entries_keys:
                if entry.startswith('%s/' % valid_entry_path):
                    valid = True
                    break

            if not valid:
                valid_items_message = validation_utils.format_message('WLSDPLY-03160',
                                                                      '%s' % ', '.join(valid_archive_entries_keys))
                warning_message = validation_utils.format_message('WLSDPLY-03159', archive_file_name,
                                                                  entry)
                validation_result.add_warning(warning_message, valid_items_message)

        return validation_result

    def __validate_model_references(self, model_deployables_dict, archive_entries, archive_file_name,
                                    validation_result):

        _method_name = '__validate_model_references'

        if not archive_entries:
            return validation_result

        validation_location = LocationContext()

        valid_section_folders = [model_constants.APPLICATION, model_constants.LIBRARY]

        for resource in valid_section_folders:
            # Here, resource will be the name of a folder under the
            # 'appDeployments' section of the model.
            self._logger.finer('4 resource={0}', resource,
                               class_name=_class_name, method_name=_method_name)
            validation_location.append_location(resource)
            validation_result = self.__validate_source_and_plan_path(model_deployables_dict,
                                                                     resource,
                                                                     archive_entries,
                                                                     archive_file_name,
                                                                     model_constants.APPLICATION,
                                                                     model_constants.LIBRARY,
                                                                     validation_location,
                                                                     validation_result)
            validation_location.pop_location()

        return validation_result

    def __validate_source_and_plan_path(self, model_deployables_dict, resource,
                                        archive_entries, archive_file_name, constant_application, constant_library,
                                        validation_location, validation_result):
        _method_name = '__validate_source_and_plan_path'

        self._logger.finer('4 validation_location={0}', validation_location,
                           class_name=_class_name, method_name=_method_name)

        if resource not in model_deployables_dict:
            # appDeployments:/<resource> is not in the model, so log to for
            # debugging purposes and bail.
            self._logger.finer('WLSDPLY-03218', str(model_deployables_dict), resource,
                               class_name=_class_name, method_name=_method_name)
            return validation_result

        deployable_resources = model_deployables_dict[resource]

        # Loop through the deployables for the resource (e.g. 'Application',
        # 'Library') we're working with
        for deployable_resource in deployable_resources:
            # deployable_resource should be the resource instance's name.
            self._logger.finer('4 deployable_resource={0}', deployable_resource,
                               class_name=_class_name, method_name=_method_name)
            try:
                name_token = self._aliases.get_name_token(validation_location)
            except AliasException, ae:
                validation_result.add_error(ae.getLocalizedMessage())

            self._logger.finer('4 name_token={0}', name_token,
                               class_name=_class_name, method_name=_method_name)
            if name_token is not None:
                validation_location.add_name_token(name_token, deployable_resource)

            for item_path in validation_utils.get_deployable_item_paths():
                path = validation_utils.get_param_value(
                    deployable_resources[deployable_resource],
                    item_path
                )
                self._logger.finer('path={0}', path, class_name=_class_name, method_name=_method_name)

                if path and not os.path.isabs(path) and not path.startswith('@@'):
                    if path not in archive_entries:
                        self._logger.finer('4 validation_location={0}', validation_location,
                                           class_name=_class_name, method_name=_method_name)
                        model_folder_path = self._aliases.get_model_folder_path(validation_location)
                        error_item, valid_items = self.__create_archive_sourcepath_message(resource,
                                                                                           model_folder_path,
                                                                                           item_path, path,
                                                                                           archive_file_name)
                        validation_result.add_error(error_item, valid_items)
                    else:
                        # path is in the archive, check whether it is legal
                        if (resource == constant_application and not path.startswith(
                                validation_utils.get_valid_app_sourcepath_entries()[0])) or \
                                (resource == constant_library and not path.startswith(
                                    validation_utils.get_valid_lib_sourcepath_entries()[0])):
                            error_item, valid_items = self.__create_archive_sourcepath_invalid_message(
                                resource, item_path, deployable_resource)
                            validation_result.add_error(error_item, valid_items)

        return validation_result

    def __create_invalid_folder_message(self, folder_key, valid_folder_keys, model_path):
        return validation_utils.format_message('WLSDPLY-03198', folder_key, 'folder', model_path), \
               validation_utils.format_message('WLSDPLY-03152', '%s' % ', '.join(valid_folder_keys))

    def __create_invalid_folder_instance_message(self, folder_instance_key, model_path):
        return validation_utils.format_message('WLSDPLY-03151', folder_instance_key, model_path)

    def __create_invalid_attribute_message(self, attribute_name, valid_attr_keys, model_path):
        return validation_utils.format_message('WLSDPLY-03197', attribute_name, model_path), \
               validation_utils.format_message('WLSDPLY-03152', '%s' % ', '.join(valid_attr_keys))

    def __create_archive_sourcepath_message(self, resource, model_folder_path, item_path, path, archive_location):
        constant_application = model_constants.APPLICATION
        error_item_message = validation_utils.format_message('WLSDPLY-03175',
                                                             model_folder_path, item_path, path, archive_location)

        if resource == constant_application:
            valid_items_message = \
                validation_utils.format_message('WLSDPLY-03178', archive_location, path,
                                                model_folder_path, item_path,
                                                str(validation_utils.get_valid_app_sourcepath_entries()))
        else:
            valid_items_message = \
                validation_utils.format_message('WLSDPLY-03178', archive_location, path,
                                                model_folder_path, item_path,
                                                str(validation_utils.get_valid_lib_sourcepath_entries()))

        return error_item_message, valid_items_message

    def __create_archive_sourcepath_invalid_message(self, resource, item_path, deployable_resource):
        constant_application = model_constants.APPLICATION
        error_item_message = None

        if resource == constant_application:
            valid_items_message = \
                validation_utils.format_message('WLSDPLY-03178', item_path, resource, deployable_resource,
                                                str(validation_utils.get_valid_app_sourcepath_entries()))
        else:
            valid_items_message = \
                validation_utils.format_message('WLSDPLY-03178', item_path, resource, deployable_resource,
                                                str(validation_utils.get_valid_lib_sourcepath_entries()))

        return error_item_message, valid_items_message

    class ValidationResults(object):
        def __init__(self):
            self._validation_result_dict = {
                '%s Section' % model.get_model_domain_info_key(): None,
                '%s Section' % model.get_model_topology_key(): None,
                '%s Section' % model.get_model_deployments_key(): None,
                '%s Section' % model.get_model_resources_key(): None
            }

        def __str__(self):
            print self.__to_string()

        def set_validation_result(self, validation_result):
            self._validation_result_dict[validation_result.get_validation_area()] = validation_result

        def get_errors_count(self):
            """

            :return:
            """
            results_summary = self.__get_summary()
            return results_summary['errors_count']

        def get_warnings_count(self):
            """

            :return:
            """
            results_summary = self.__get_summary()
            return results_summary['warnings_count']

        def get_infos_count(self):
            """

            :return:
            """
            results_summary = self.__get_summary()
            return results_summary['infos_count']

        def print_details(self):
            """

            :return:
            """

            for key, validation_result in self._validation_result_dict.iteritems():
                if validation_result.get_errors_count() > 0 \
                        or validation_result.get_warnings_count() > 0 \
                        or validation_result.get_infos_count():

                    indent_level = 0
                    validation_area = validation_utils.format_message('WLSDPLY-03219',
                                                                      validation_result.get_validation_area())
                    validation_utils.print_blank_lines()
                    validation_utils.print_indent(validation_utils.divider_string, indent_level)
                    validation_utils.print_indent(validation_area, indent_level)
                    validation_utils.print_indent(validation_utils.divider_string, indent_level)

                    if validation_result.get_infos_count() > 0:
                        self.__print_results_category_details(validation_utils.format_message('WLSDPLY-03220'),
                                                              validation_result.get_infos_count(),
                                                              validation_result.get_infos_messages(), indent_level)

                    if validation_result.get_warnings_count() > 0:
                        self.__print_results_category_details(validation_utils.format_message('WLSDPLY-03221'),
                                                              validation_result.get_warnings_count(),
                                                              validation_result.get_warnings_messages(), indent_level)

                    if validation_result.get_errors_count() > 0:
                        self.__print_results_category_details(validation_utils.format_message('WLSDPLY-03222'),
                                                              validation_result.get_errors_count(),
                                                              validation_result.get_errors_messages(), indent_level)

        def __print_results_category_details(self, result_category, category_count, category_messages, indent_level):
            validation_utils.print_blank_lines()
            validation_utils.print_indent('%s: %d' % (result_category, category_count), indent_level + 1)

            for i in range(len(category_messages)):
                messages = category_messages[i]
                if 'message' in messages:
                    validation_utils.print_indent(
                        validation_utils.format_message('WLSDPLY-03223', messages['message']), indent_level + 2
                    )
                elif 'valid_items' in messages:
                    validation_utils.print_indent(
                        validation_utils.format_message('WLSDPLY-03224', messages['valid_items']), indent_level + 2
                    )
                if i == len(messages):
                    validation_utils.print_blank_lines()

        def log_results(self, logger):
            """

            :return:
            """
            _method_name = 'log_results'

            if logger is not None:
                logger.info(self.__to_string(), class_name=_class_name, method_name=_method_name)

        def __get_summary(self):
            """

            :return:
            """

            results_summary = {
                'errors_count': 0,
                'warnings_count': 0,
                'infos_count': 0
            }

            for key, validation_result in self._validation_result_dict.iteritems():
                if validation_result is not None:
                    results_summary['errors_count'] += validation_result.get_errors_count()
                    results_summary['warnings_count'] += validation_result.get_warnings_count()
                    results_summary['infos_count'] += validation_result.get_infos_count()

            return results_summary

        def __to_string(self):
            """

            :return:
            """

            tmp = ''

            for key, validation_result in self._validation_result_dict.iteritems():
                if validation_result.get_errors_count() > 0 \
                        or validation_result.get_warnings_count() > 0 \
                        or validation_result.get_infos_count():
                    tmp += str(validation_result)
                    tmp += ','

            if tmp[-1:] == ',':
                # Strip off trailing ','
                tmp = tmp[:-1]

            return '[%s]' % tmp

    class ValidationResult(object):
        """

        """
        def __init__(self, validation_area):
            self._result = {
                "validation_area": validation_area,
                "errors": {
                    "count": 0,
                    "messages": []
                },
                "warnings": {
                    "count": 0,
                    "messages": []
                },
                "infos": {
                    "count": 0,
                    "messages": []
                }
            }

        def __str__(self):
            tmp = '"validation_area": "%s",' % self._result['validation_area']
            if self.get_errors_count() > 0:
                tmp += self.__to_string('errors')
            if self.get_warnings_count() > 0:
                tmp += self.__to_string('warnings')
            if self.get_infos_count() > 0:
                tmp += self.__to_string('infos')

            if tmp[-1:] == ',':
                # Strip off trailing ','
                tmp = tmp[:-1]

            return "{%s}" % tmp

        def add_error(self, error_item_message, valid_items_message=None):
            """

            :param error_item_message:
            :param valid_items_message:
            :return:
            """
            self._result['errors']['count'] += 1
            message = {'message': error_item_message}
            if valid_items_message is not None:
                message['valid_items'] = valid_items_message
            self._result['errors']['messages'].append(message)

        def add_warning(self, warning_item_message, valid_items_message=None):
            """

            :param warning_item_message:
            :param valid_items_message:
            :return:
            """
            self._result['warnings']['count'] += 1
            message = {'message': warning_item_message}
            if valid_items_message is not None:
                message['valid_items'] = valid_items_message
            self._result['warnings']['messages'].append(message)

        def add_info(self, info_item_message):
            """

            :param info_item_message:
            :return:
            """
            self._result['infos']['count'] += 1
            message = {'message': info_item_message}
            self._result['infos']['messages'].append(message)

        def get_validation_area(self):
            """

            :return:
            """
            return self._result['validation_area']

        def get_errors_count(self):
            """

            :return:
            """
            return self._result['errors']['count']

        def get_errors_messages(self):
            """

            :return:
            """
            return self._result['errors']['messages']

        def get_warnings_count(self):
            """

            :return:
            """
            return self._result['warnings']['count']

        def get_warnings_messages(self):
            """

            :return:
            """
            return self._result['warnings']['messages']

        def get_infos_count(self):
            """

            :return:
            """
            return self._result['infos']['count']

        def get_infos_messages(self):
            """

            :return:
            """
            return self._result['infos']['messages']

        def print_details(self):
            pass

        def __to_string(self, category_name):
            tmp = ' "%s": {' % category_name
            tmp += '"count": %d, ' % self._result[category_name]['count']
            tmp += '"messages": ['
            for message in self._result[category_name]['messages']:
                tmp += "{"
                message_list = message.keys()
                message_list.sort()
                for name in message_list:
                    value = message[name]
                    tmp += '"%s": "%s",' % (name, value)
                if tmp[-1:] == ',':
                    # Strip off trailing ','
                    tmp = tmp[:-1]
                tmp += "},"
            if tmp[-1:] == ',':
                # Strip off trailing ','
                tmp = tmp[:-1]
            # Concatenate closing ']}'
            tmp += "]},"

            return tmp
