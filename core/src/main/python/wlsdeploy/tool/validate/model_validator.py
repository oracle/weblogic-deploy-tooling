"""
Copyright (c) 2017, 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""

from oracle.weblogic.deploy.util import WLSDeployArchive

import wlsdeploy.util.unicode_helper as str_helper
from wlsdeploy.aliases import model_constants
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import MASKED_PASSWORD
from wlsdeploy.aliases.validation_codes import ValidationCodes
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.validate import validation_utils
from wlsdeploy.util import dictionary_utils
from wlsdeploy.util import path_helper
from wlsdeploy.util import variables
from wlsdeploy.util.enum import Enum

_class_name = 'ModelValidator'
_logger = PlatformLogger('wlsdeploy.validate')

_ModelNodeTypes = Enum(['FOLDER_TYPE', 'NAME_TYPE', 'ATTRIBUTE', 'ARTIFICIAL_TYPE'])
_ValidationModes = Enum(['STANDALONE', 'TOOL'])


class ModelValidator(object):
    """
    Class for validating a model file and printing the metadata used in it.
    Subclasses can extend methods for more specific validations.
    """
    def __init__(self, variables_map, archive_helper, validation_mode, model_context, aliases,
                 wlst_mode):
        """
        Create a validator instance.
        :param variables_map: map of variables used in the model
        :param archive_helper: used to validate archive paths
        :param model_context: used to get command-line options
        :param aliases: used to validate folders, attributes. also determines exception type
        :param wlst_mode: online or offline mode
        """
        self._logger = _logger

        self._variable_properties = variables_map
        self._archive_helper = archive_helper
        self._validation_mode = validation_mode
        self._model_context = model_context
        self._validate_configuration = model_context.get_validate_configuration()

        self._wls_helper = model_context.get_weblogic_helper()
        self.path_helper = path_helper.get_path_helper()

        if wlst_mode is not None:
            # In TOOL validate mode, the WLST mode is specified by the calling tool and the
            # WebLogic version is always the current version used to run WLST.
            self._wlst_mode = wlst_mode
            self._wls_version = model_context.get_effective_wls_version()
        else:
            # In STANDALONE mode, the user can specify the target WLST mode and the target
            # WLS version using command-line args so get the value from the model_context.
            self._wlst_mode = model_context.get_target_wlst_mode()
            self._wls_version = model_context.get_effective_wls_version()

        self._aliases = aliases

        # need a token here for alias path resolution
        self._name_tokens_location = LocationContext()
        self._name_tokens_location.add_name_token('DOMAIN', 'base_domain')

        self._model_file_name = self._model_context.get_model_file()

    def validate_model_section(self, model_section_key, model_dict, valid_section_folders):
        """
        Validate a root-level section, such as topology, domainInfo
        :param model_section_key: the key for the section
        :param model_dict: the top-level model dictionary
        :param valid_section_folders: folders that are valid for this section
        """
        _method_name = 'validate_model_section'

        self._logger.info('WLSDPLY-05008', model_section_key, self._model_file_name,
                          class_name=_class_name, method_name=_method_name)

        if model_section_key not in model_dict.keys():
            # model_section-key is not in model_dict.keys(), so record this as a INFO log message,
            # then bail from validating this section of model_dict
            self._logger.info('WLSDPLY-05009', self._model_file_name, model_section_key,
                              class_name=_class_name, method_name=_method_name)
            return

        # only specific top-level sections have attributes
        attribute_location = self._aliases.get_model_section_attribute_location(model_section_key)

        valid_attr_infos = []
        path_tokens_attr_keys = []

        if attribute_location is not None:
            valid_attr_infos = self._aliases.get_model_attribute_names_and_types(attribute_location)
            self._logger.finer('WLSDPLY-05012', str_helper.to_string(attribute_location),
                               str_helper.to_string(valid_attr_infos),
                               class_name=_class_name, method_name=_method_name)
            path_tokens_attr_keys = self._aliases.get_model_uses_path_tokens_attribute_names(attribute_location)
            self._logger.finer('WLSDPLY-05013', str_helper.to_string(attribute_location),
                               str_helper.to_string(path_tokens_attr_keys),
                               class_name=_class_name, method_name=_method_name)

        model_folder_path = model_section_key + ":/"
        model_section_dict = model_dict[model_section_key]
        if not isinstance(model_section_dict, dict):
            self._logger.severe('WLSDPLY-05038', model_folder_path, class_name=_class_name, method_name=_method_name)
            return

        for section_dict_key, section_dict_value in model_section_dict.iteritems():
            # section_dict_key is either the name of a folder in the
            # section, or the name of an attribute in the section.
            validation_location = LocationContext()

            if variables.has_variables(section_dict_key):
                self._report_unsupported_variable_usage(section_dict_key, model_folder_path)

            # don't log section_dict_value here, it may be a password or dict with password
            self._logger.finer('WLSDPLY-05011', section_dict_key, MASKED_PASSWORD,
                               class_name=_class_name, method_name=_method_name)

            if section_dict_key in valid_attr_infos:
                # section_dict_key is the name of an attribute in the section
                self._validate_attribute(section_dict_key, section_dict_value, valid_attr_infos,
                                         path_tokens_attr_keys, model_folder_path, attribute_location)

            elif section_dict_key in valid_section_folders:
                # section_dict_key is a folder under the model section

                # Append section_dict_key to location context
                validation_location.append_location(section_dict_key)
                self._logger.finest('validation_location = {0}', str_helper.to_string(validation_location),
                                    class_name=_class_name, method_name=_method_name)

                # Call self.__validate_section_folder() passing in section_dict_value as the model_node to process
                self._validate_folder(section_dict_value, validation_location)

            else:
                # It's not one of the section's folders, and it's not an attribute of the section.
                # Record this as a validate ERROR in the validate results.
                if isinstance(section_dict_value, dict):
                    result, message = self._aliases.is_valid_model_folder_name(validation_location,
                                                                                    section_dict_key)
                    if result == ValidationCodes.CONTEXT_INVALID:
                        self._log_context_invalid(message, _method_name)
                    elif result == ValidationCodes.INVALID:
                        self._logger.severe('WLSDPLY-05026', section_dict_key, 'folder', model_folder_path,
                                            '%s' % ', '.join(valid_section_folders), class_name=_class_name,
                                            method_name=_method_name)

                elif attribute_location is not None:
                    result, message = self._aliases.is_valid_model_attribute_name(attribute_location,
                                                                                       section_dict_key)
                    if result == ValidationCodes.CONTEXT_INVALID:
                        self._log_context_invalid(message, _method_name)
                    elif result == ValidationCodes.INVALID:
                        self._logger.severe('WLSDPLY-05029', section_dict_key, model_folder_path,
                                            '%s' % ', '.join(valid_attr_infos), class_name=_class_name,
                                            method_name=_method_name)

                else:
                    self._logger.severe('WLSDPLY-05029', section_dict_key, model_folder_path,
                                        '%s' % ', '.join(valid_attr_infos), class_name=_class_name,
                                        method_name=_method_name)

    def _validate_folder(self, model_node, validation_location):
        """
        Validate a model folder that may contain named child folders (Server, Application),
        artificial folders (security providers), or attributes and sub-folders (JTA, WebAppContainer).
        :param model_node: the model node dictionary
        :param validation_location: the alias location for the folder
        """
        _method_name = '_validate_folder'

        result, message = self._aliases.is_version_valid_location(validation_location)
        if result == ValidationCodes.CONTEXT_INVALID:
            self._log_context_invalid(message, _method_name)
            return
        elif result == ValidationCodes.INVALID:
            self._logger.severe('WLSDPLY-05027', message, class_name=_class_name, method_name=_method_name)
            return

        # generate and add a flattened folder token, if required
        flattened_folder_info = self._aliases.get_wlst_flattened_folder_info(validation_location)
        if flattened_folder_info is not None:
            path_token = flattened_folder_info.get_path_token()
            validation_location.add_name_token(path_token, '%s-0' % path_token)

        model_folder_path = self._aliases.get_model_folder_path(validation_location)
        self._logger.finest('model_folder_path={0}', model_folder_path,
                            class_name=_class_name, method_name=_method_name)

        if not isinstance(model_node, dict):
            self._logger.severe('WLSDPLY-05038', model_folder_path, class_name=_class_name, method_name=_method_name)
            return

        if self._aliases.supports_multiple_mbean_instances(validation_location):
            self._logger.finer('model_node_type={0}',
                               _ModelNodeTypes.from_value(_ModelNodeTypes.NAME_TYPE),
                               class_name=_class_name, method_name=_method_name)

            for name in model_node:
                expanded_name = name
                if variables.has_variables(name):
                    expanded_name = self.__validate_variable_substitution(name, model_folder_path)

                self._logger.finest('expanded_name={0}', expanded_name,
                                    class_name=_class_name, method_name=_method_name)

                new_location = LocationContext(validation_location)

                name_token = self._aliases.get_name_token(new_location)
                self._logger.finest('WLSDPLY-05014', str_helper.to_string(validation_location), name_token,
                                    class_name=_class_name, method_name=_method_name)

                if name_token is not None:
                    new_location.add_name_token(name_token, expanded_name)

                self._logger.finest('new_location={0}', str_helper.to_string(new_location),
                                    class_name=_class_name, method_name=_method_name)

                value_dict = model_node[name]

                self._validate_folder_content(value_dict, new_location)

        elif self._aliases.requires_artificial_type_subfolder_handling(validation_location):
            self._logger.finer('model_node_type={0}',
                               _ModelNodeTypes.from_value(_ModelNodeTypes.ARTIFICIAL_TYPE),
                               class_name=_class_name, method_name=_method_name)

            for name in model_node:
                expanded_name = name
                if variables.has_variables(name):
                    self._report_unsupported_variable_usage(name, model_folder_path)

                self._logger.finest('expanded_name={0}', expanded_name,
                                    class_name=_class_name, method_name=_method_name)

                new_location = LocationContext(validation_location)

                name_token = self._aliases.get_name_token(new_location)
                self._logger.finest('name_token={0}', name_token,
                                    class_name=_class_name, method_name=_method_name)

                if name_token is not None:
                    new_location.add_name_token(name_token, expanded_name)

                self._logger.finest('new_location={0}', new_location,
                                    class_name=_class_name, method_name=_method_name)

                value_dict = model_node[name]

                self._validate_folder_content(value_dict, new_location)

        else:
            self._logger.finer('model_node_type={0}',
                               _ModelNodeTypes.from_value(_ModelNodeTypes.FOLDER_TYPE),
                               class_name=_class_name, method_name=_method_name)

            name_token = self._aliases.get_name_token(validation_location)
            self._logger.finest('name_token={0}', name_token,
                                class_name=_class_name, method_name=_method_name)

            if name_token is not None:
                name = self._name_tokens_location.get_name_for_token(name_token)

                if name is None:
                    name = '%s-0' % name_token

                self._logger.finest('name={0}', name,
                                    class_name=_class_name, method_name=_method_name)
                validation_location.add_name_token(name_token, name)
                self._logger.finest('validation_location={0}', validation_location,
                                    class_name=_class_name, method_name=_method_name)

            self._validate_folder_content(model_node, validation_location)

    def _validate_folder_content(self, model_node, validation_location):
        """
        Validate a model folder that contains attributes and sub-folders.
        This model folder is below the named or artificial folders.
        :param model_node: the model node dictionary
        :param validation_location: the alias location for the folder
        """
        _method_name = '_validate_folder_content'
        self._logger.entering(str_helper.to_string(validation_location),
                              class_name=_class_name, method_name=_method_name)

        model_folder_path = self._aliases.get_model_folder_path(validation_location)

        if not isinstance(model_node, dict):
            self._logger.severe('WLSDPLY-05038', model_folder_path, class_name=_class_name, method_name=_method_name)
            return

        valid_folder_keys = self._aliases.get_model_subfolder_names(validation_location)
        valid_attr_infos = self._aliases.get_model_attribute_names_and_types(validation_location)

        self._logger.finest('aliases.get_model_subfolder_names(validation_location) returned: {0}',
                            str_helper.to_string(valid_folder_keys),
                            class_name=_class_name, method_name=_method_name)
        self._logger.finest('aliases.get_model_attribute_names_and_types(validation_location) returned: {0}',
                            str_helper.to_string(valid_attr_infos),
                            class_name=_class_name, method_name=_method_name)
        self._logger.finest('model_folder_path={0}', model_folder_path, class_name=_class_name,
                            method_name=_method_name)

        for key, value in model_node.iteritems():
            if variables.has_variables(key):
                self._report_unsupported_variable_usage(key, model_folder_path)

            self._logger.finer('key={0}', key,
                               class_name=_class_name, method_name=_method_name)

            folder_validation_code, folder_validation_message = \
                self._aliases.is_valid_model_folder_name(validation_location, key)
            attribute_validation_code, attribute_validation_message = \
                self._aliases.is_valid_model_attribute_name(validation_location, key)

            if folder_validation_code == ValidationCodes.VALID:
                new_location = LocationContext(validation_location).append_location(key)
                self._logger.finer('new_location={0}', new_location,
                                   class_name=_class_name, method_name=_method_name)

                if self._aliases.is_artificial_type_folder(new_location):
                    # key is an ARTIFICIAL_TYPE folder
                    self._logger.finest('is_artificial_type_folder=True',
                                        class_name=_class_name, method_name=_method_name)
                    valid_attr_infos = self._aliases.get_model_attribute_names_and_types(new_location)

                    self._validate_attributes(value, valid_attr_infos, new_location)
                else:
                    self._validate_folder(value, new_location)
            elif attribute_validation_code == ValidationCodes.VALID:
                # aliases.get_model_attribute_names_and_types(location) filters out
                # attributes that ARE NOT valid in the wlst_version being used, so if
                # we're in this section of code we know key is a bonafide "valid" attribute
                valid_data_type = valid_attr_infos[key]
                if valid_data_type in ['properties']:
                    valid_prop_infos = {}
                    properties = validation_utils.get_properties(value)
                    self.__validate_properties(properties, valid_prop_infos, validation_location)

                else:
                    path_tokens_attr_keys = \
                        self._aliases.get_model_uses_path_tokens_attribute_names(validation_location)

                    self._validate_attribute(key, value, valid_attr_infos, path_tokens_attr_keys, model_folder_path,
                                             validation_location)
            elif folder_validation_code == ValidationCodes.CONTEXT_INVALID:
                self._log_context_invalid(folder_validation_message, _method_name)
            elif attribute_validation_code == ValidationCodes.CONTEXT_INVALID:
                self._log_context_invalid(attribute_validation_message, _method_name)
            elif self._aliases.is_custom_folder_allowed(validation_location):
                # custom folders are not validated, just log this and continue
                self._logger.info('WLSDPLY-05037', model_folder_path,
                                  class_name=_class_name, method_name=_method_name)
            else:
                # At this point we know that key IS NOT a valid attribute or folder, meaning
                # that given the location object, it is NOT:
                #
                #   1. A folder or attribute name in the current location, or
                #   2. A folder or attribute name belonging to the version we're working with.
                #
                if isinstance(value, dict):
                    # value is a dict, so key must be the name of a folder. key cannot be a folder
                    # instance name, because the _aliases.supports_multiple_mbean_instances()
                    # method pulls those out, in the self.__validate_section_folder().

                    # See if it's a version invalid folder
                    if folder_validation_code == ValidationCodes.INVALID:
                        # key is an INVALID folder
                        self._logger.severe('WLSDPLY-05026', key, 'folder', model_folder_path,
                                            '%s' % ', '.join(valid_folder_keys), class_name=_class_name,
                                            method_name=_method_name)
                else:
                    # value is not a dict, so key must be the name of an attribute. key cannot be a
                    # folder instance name, because the _aliases.supports_multiple_mbean_instances()
                    # method pulls those out, in the self.__validate_section_folder().

                    # See if it's a version invalid attribute
                    if attribute_validation_code == ValidationCodes.INVALID:
                        # key is an INVALID attribute
                        self._logger.severe('WLSDPLY-05029', key, model_folder_path,
                                            '%s' % ', '.join(valid_attr_infos), class_name=_class_name,
                                            method_name=_method_name)

    def _validate_attributes(self, attributes_dict, valid_attr_infos, validation_location):
        _method_name = '_validate_attributes'

        self._logger.finest('validation_location={0}', str_helper.to_string(validation_location),
                            class_name=_class_name, method_name=_method_name)

        model_folder_path = self._aliases.get_model_folder_path(validation_location)
        if not isinstance(attributes_dict, dict):
            self._logger.severe('WLSDPLY-05038', model_folder_path, class_name=_class_name, method_name=_method_name)
            return

        path_tokens_attr_keys = self._aliases.get_model_uses_path_tokens_attribute_names(validation_location)
        self._logger.finer('WLSDPLY-05013', str_helper.to_string(validation_location),
                           str_helper.to_string(path_tokens_attr_keys),
                           class_name=_class_name, method_name=_method_name)

        for attribute_name, attribute_value in attributes_dict.iteritems():
            self._validate_attribute(attribute_name, attribute_value, valid_attr_infos, path_tokens_attr_keys,
                                     model_folder_path, validation_location)

    def _validate_attribute(self, attribute_name, attribute_value, valid_attr_infos, path_tokens_attr_keys,
                            model_folder_path, validation_location):
        _method_name = '_validate_attribute'

        log_value = self.__get_attribute_log_value(attribute_name, attribute_value, valid_attr_infos)
        self._logger.entering(attribute_name, log_value, str_helper.to_string(valid_attr_infos),
                              str_helper.to_string(path_tokens_attr_keys), model_folder_path,
                              str_helper.to_string(validation_location),
                              class_name=_class_name, method_name=_method_name)

        if variables.has_variables(attribute_name):
            self._report_unsupported_variable_usage(attribute_name, model_folder_path)

        if variables.has_variables(str_helper.to_string(attribute_value)):
            attribute_value = self.__validate_variable_substitution(attribute_value, model_folder_path)

        if attribute_name in valid_attr_infos:
            expected_data_type = valid_attr_infos[attribute_name]
            actual_data_type = str_helper.to_string(type(attribute_value))
            self._logger.finer('WLSDPLY-05016', attribute_name, expected_data_type, actual_data_type,
                               class_name=_class_name, method_name=_method_name)
            if validation_utils.is_compatible_data_type(expected_data_type, actual_data_type) is False:
                if not self._aliases.model_attribute_has_set_method(validation_location, attribute_name):
                    self._logger.warning('WLSDPLY-05017', attribute_name, model_folder_path, expected_data_type,
                                         actual_data_type, class_name=_class_name, method_name=_method_name)

            if attribute_name in path_tokens_attr_keys:
                self.__validate_path_tokens_attribute(attribute_name, attribute_value, model_folder_path)
        else:
            result, message = self._aliases.is_valid_model_attribute_name(validation_location, attribute_name)
            if result == ValidationCodes.CONTEXT_INVALID:
                self._log_context_invalid(message, _method_name)
            elif result == ValidationCodes.INVALID:
                self._logger.severe('WLSDPLY-05029', attribute_name, model_folder_path,
                                    '%s' % ', '.join(valid_attr_infos), class_name=_class_name,
                                    method_name=_method_name)

        self._logger.exiting(class_name=_class_name, method_name=_method_name)

    def __validate_properties(self, properties_dict, valid_prop_infos, validation_location):
        _method_name = '__validate_properties'

        self._logger.entering(str_helper.to_string(validation_location),
                              class_name=_class_name, method_name=_method_name)

        for property_name, property_value in properties_dict.iteritems():
            valid_prop_infos[property_name] = validation_utils.get_python_data_type(property_value)
            self.__validate_property(property_name, property_value, valid_prop_infos, validation_location)

        self._logger.exiting(class_name=_class_name, method_name=_method_name)

    def __validate_property(self, property_name, property_value, valid_prop_infos, model_folder_path):

        _method_name = '__validate_property'

        self._logger.entering(property_name, str_helper.to_string(valid_prop_infos),
                              model_folder_path, class_name=_class_name, method_name=_method_name)

        if variables.has_variables(property_name):
            property_name = self.__validate_variable_substitution(property_name, model_folder_path)

        if variables.has_variables(str_helper.to_string(property_value)):
            property_value = self.__validate_variable_substitution(property_value, model_folder_path)

        if property_name in valid_prop_infos:
            expected_data_type = valid_prop_infos[property_name]
            actual_data_type = str_helper.to_string(type(property_value))
            self._logger.finer('WLSDPLY-05018', property_name, expected_data_type, actual_data_type,
                               class_name=_class_name, method_name=_method_name)
            if validation_utils.is_compatible_data_type(expected_data_type, actual_data_type) is False:
                self._logger.warning('WLSDPLY-05019', property_name, model_folder_path, expected_data_type,
                                     actual_data_type, class_name=_class_name, method_name=_method_name)
        else:
            self._logger.severe('WLSDPLY-05020', property_name, model_folder_path, class_name=_class_name,
                                method_name=_method_name)

    def __validate_variable_substitution(self, tokenized_value, model_folder_path):
        _method_name = '__validate_variable_substitution'

        self._logger.entering(model_folder_path, class_name=_class_name, method_name=_method_name)
        untokenized_value = tokenized_value

        if not isinstance(untokenized_value, dict):
            # Extract the variable substitution variables from tokenized_value
            matches = variables.get_variable_matches(tokenized_value)
            for token, property_name in matches:
                property_value = None
                if property_name in self._variable_properties:
                    property_value = self._variable_properties[property_name]
                if property_value is not None:
                    untokenized_value = untokenized_value.replace(token, property_value)
                else:
                    logger_method = self._logger.warning
                    if self._validate_configuration.allow_unresolved_variable_tokens():
                        logger_method = self._logger.info

                    variables_file_name = self._model_context.get_variable_file()

        self._logger.exiting(class_name=_class_name, method_name=_method_name, result=untokenized_value)
        return untokenized_value

    def __validate_path_tokens_attribute(self, attribute_name, attribute_value, model_folder_path):
        _method_name = '__validate_path_tokens_attribute'

        self._logger.entering(attribute_name, attribute_value, model_folder_path,
                              class_name=_class_name, method_name=_method_name)

        value_data_type = validation_utils.get_python_data_type(attribute_value)

        self._logger.finest('value_data_type={0}', value_data_type,
                            class_name=_class_name, method_name=_method_name)

        valid_value_data_types = ['list', 'string', 'unicode']
        if value_data_type not in valid_value_data_types:
            self._logger.severe('WLSDPLY-05023', attribute_name, model_folder_path, value_data_type,
                                class_name=_class_name, method_name=_method_name)
        else:
            attr_values = []

            if value_data_type == 'string' and model_constants.MODEL_LIST_DELIMITER in attribute_value:
                attr_values = attribute_value.split(model_constants.MODEL_LIST_DELIMITER)

            elif value_data_type in ['string', 'unicode']:
                attr_values.append(attribute_value)

            else:
                # must be a list
                attr_values.extend(attribute_value)

            for item_path in attr_values:
                self._validate_single_path_in_archive(item_path.strip(), attribute_name, model_folder_path)

        self._logger.exiting(class_name=_class_name, method_name=_method_name)

    def _validate_single_path_in_archive(self, path, attribute_name, model_folder_path):
        """
        Validate the path value specified by an attribute.
        :param path: the path to be validates
        :param attribute_name: the name of the attribute (for logging only)
        :param model_folder_path: the folder path (for logging)
        """
        _method_name = '_validate_single_path_in_archive'

        # There are 3 possible conditions:
        # 1.) The path is a relative path into the archive (so there will be no path tokens)
        # 2.) There are path tokens used at the front of the path to make it absolute
        # 3.) There is some other path for a file that is assumed to exist on the target system.
        #     This should be an absolute path.  If not, we should probably alter the user since
        #     there is no well-defined point from non-archive-referencing relative paths are
        #     anchored.  It will depend on the location from which the user invokes the tool
        #     on the target system.  If this is their intent, they should really use the @@PWD@@
        #     token to make that explicit in the model.
        #
        if WLSDeployArchive.isPathIntoArchive(path):
            # If the validate configuration allows unresolved archive references,
            # log INFO messages identifying missing entries, and allow validation to succeed.
            # Otherwise, log SEVERE messages that will cause validation to fail.
            log_method = self._logger.severe
            if self._validate_configuration.allow_unresolved_archive_references():
                log_method = self._logger.info

            if self._archive_helper is not None:
                archive_has_file = self._archive_helper.contains_file_or_path(path)
                if not archive_has_file:
                    archive_file_name = self._model_context.get_archive_file_name()
                    log_method('WLSDPLY-05024', attribute_name, model_folder_path, path,
                               archive_file_name, class_name=_class_name, method_name=_method_name)

                # If this is validating for remote use
                # check to see if it is a path into the archive
                # and the path is not applications/libraries then flag as error

                if self._model_context.is_remote() and self._archive_helper.is_path_forbidden_for_remote_update(path):
                    log_method('WLSDPLY-19313', attribute_name, model_folder_path, path,
                                   class_name=_class_name, method_name=_method_name)

            elif not self._model_context.is_remote() and not self._model_context.is_skip_archive():
                log_method('WLSDPLY-05025', attribute_name, model_folder_path, path,
                           class_name=_class_name, method_name=_method_name)
        else:
            tokens = validation_utils.extract_path_tokens(path)
            self._logger.finest('tokens={0}', str_helper.to_string(tokens),
                                class_name=_class_name, method_name=_method_name)
            # TODO(mwooten) - This would be a good place to validate any path token found...

            if not self._model_context.has_token_prefix(path):
                if self.path_helper.is_relative_local_path(path):
                    self._logger.info('WLSDPLY-05031', attribute_name, model_folder_path, path,
                                      class_name=_class_name, method_name=_method_name)

    def _report_unsupported_variable_usage(self, tokenized_value, model_folder_path):
        _method_name = '_report_unsupported_variable_usage'
        tokens = variables.get_variable_names(tokenized_value)
        for token in tokens:
            self._logger.severe('WLSDPLY-05030', model_folder_path, token,
                                class_name=_class_name, method_name=_method_name)

    def _log_context_invalid(self, message, method_name):
        """
        Log a message indicating that an attribute is not valid for the current WLS version and WLST mode.
        Log INFO or WARNING, depending on validation mode.
        """
        if self._validate_configuration.disregard_version_invalid_attributes():
            return

        log_method = self._logger.warning
        if self._validate_configuration.allow_version_invalid_attributes():
            log_method = self._logger.info
        log_method('WLSDPLY-05027', message, class_name=_class_name, method_name=method_name)

    ####################################################################################
    #
    # Private methods, private inner classes and static methods only, beyond here please
    #
    ####################################################################################

    def __get_attribute_log_value(self, attribute_name, attribute_value, attribute_infos):
        """
        Get the log output for an attribute value to protect sensitive data
        """
        result = attribute_value
        if attribute_name in attribute_infos:
            expected_data_type = dictionary_utils.get_element(attribute_infos, attribute_name)
            if expected_data_type == 'password':
                result = '<masked>'
        return result
