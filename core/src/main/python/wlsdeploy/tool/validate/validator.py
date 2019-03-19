"""
Copyright (c) 2017, 2019, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""
import os
import copy

from oracle.weblogic.deploy.util import WLSDeployArchive
from oracle.weblogic.deploy.util import VariableException

from wlsdeploy.aliases import model_constants
from wlsdeploy.aliases.aliases import Aliases
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.validation_codes import ValidationCodes
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception.expection_types import ExceptionType
from wlsdeploy.exception import exception_helper
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.util.alias_helper import AliasHelper
from wlsdeploy.tool.util.archive_helper import ArchiveHelper
from wlsdeploy.tool.validate import validation_utils
from wlsdeploy.tool.validate.validation_results import ValidationResults, ValidationResult
from wlsdeploy.tool.validate.usage_printer import UsagePrinter
from wlsdeploy.util import dictionary_utils
from wlsdeploy.util import model
from wlsdeploy.util import variables
from wlsdeploy.util.enum import Enum
from wlsdeploy.util.weblogic_helper import WebLogicHelper

from wlsdeploy.aliases.model_constants import DOMAIN_LIBRARIES
from wlsdeploy.aliases.model_constants import MODEL_LIST_DELIMITER
from wlsdeploy.aliases.model_constants import NAME
from wlsdeploy.aliases.model_constants import SERVER_GROUP_TARGETING_LIMITS
from wlsdeploy.aliases.model_constants import TOPOLOGY

_class_name = 'Validator'
_logger = PlatformLogger('wlsdeploy.validate')
_ModelNodeTypes = Enum(['FOLDER_TYPE', 'NAME_TYPE', 'ATTRIBUTE', 'ARTIFICIAL_TYPE'])
_ValidationModes = Enum(['STANDALONE', 'TOOL'])
_ROOT_LEVEL_VALIDATION_AREA = validation_utils.format_message('WLSDPLY-05000')
_DOMAIN_INFO_VALIDATION_AREA = validation_utils.format_message('WLSDPLY-05001', model_constants.DOMAIN_INFO)
_TOPOLOGY_VALIDATION_AREA = validation_utils.format_message('WLSDPLY-05001', model_constants.TOPOLOGY)
_RESOURCES_VALIDATION_AREA = validation_utils.format_message('WLSDPLY-05001', model_constants.RESOURCES)
_APP_DEPLOYMENTS_VALIDATION_AREA = validation_utils.format_message('WLSDPLY-05001', model_constants.APP_DEPLOYMENTS)


class Validator(object):
    """
    Class for validating a model file and printing the metadata used in it
    """
    ValidationStatus = Enum(['VALID', 'INFOS_VALID', 'WARNINGS_INVALID', 'INVALID'])
    ReturnCode = Enum(['PROCEED', 'STOP'])

    def __init__(self, model_context, aliases=None, logger=None, wlst_mode=None, domain_name='base_domain'):
        self._model_context = model_context

        if logger is None:
            # No logger specified, so use the one declared at the module level
            self._logger = _logger
        else:
            self._logger = logger

        self._validation_mode = None
        self._validation_results = ValidationResults()
        self._variable_properties = {}
        self._wls_helper = WebLogicHelper(self._logger)

        if wlst_mode is not None:
            # In TOOL validate mode, the WLST mode is specified by the calling tool and the
            # WebLogic version is always the current version used to run WLST.
            self._wlst_mode = wlst_mode
            self._wls_version = self._wls_helper.get_actual_weblogic_version()
        else:
            # In STANDALONE mode, the user can specify the target WLST mode and the target
            # WLS version using command-line args so get the value from the model_context.
            self._wlst_mode = model_context.get_target_wlst_mode()
            self._wls_version = model_context.get_target_wls_version()

        if aliases is None:
            self._aliases = Aliases(model_context=model_context)
        else:
            self._aliases = aliases
        self._alias_helper = AliasHelper(self._aliases, self._logger, ExceptionType.VALIDATE)

        self._name_tokens_location = LocationContext()
        self._name_tokens_location.add_name_token('DOMAIN', domain_name)

        self._archive_helper = None
        self._archive_file_name = None
        self._archive_entries = None
        self._model_file_name = self._model_context.get_model_file()
        return

    def validate_in_standalone_mode(self, model_dict, variables_file_name=None, archive_file_name=None):
        """
        Performs model file validate and returns a ValidationResults object.

        Prints a text representation of the returned object to STDOUT, using an 80 characters per
        line format (when possible). Info-related items are printed first, followed by warning-related
        ones, followed by error-related ones.

        :param model_dict: A Python dictionary of the model to be validated
        :param variables_file_name: Path to file containing variable substitution data used with model file.
        Defaults to None.
        :param archive_file_name: Path to file containing binaries associated with the model file.
        Defaults to None.
        :return: A ValidationResults object
        :raises ValidationException: if an AliasException is raised during an invocation of an aliases API call.
        """
        _method_name = 'validate_in_standalone_mode'

        # We need to make a deep copy of model_dict here, to ensure it's
        # treated as a "read-only'" reference variable, during the variable
        # file validation process. The variable file validation process could
        # actually require changes to be made to the cloned model dictionary
        cloned_model_dict = copy.deepcopy(model_dict)

        self._logger.entering(variables_file_name, archive_file_name, class_name=_class_name, method_name=_method_name)
        self._validation_mode = _ValidationModes.STANDALONE
        self.__validate_model_file(cloned_model_dict, variables_file_name, archive_file_name)

        self._logger.exiting(class_name=_class_name, method_name=_method_name)
        return self._validation_results

    def validate_in_tool_mode(self, model_dict, variables_file_name=None, archive_file_name=None):
        """
        Performs model file validate and returns a code that allows a tool (e.g. discover,
        deploy, create, etc.) to determine if it should proceed, or not. Validation results are
        written to a log file, instead of STDOUT.

        Possible return codes are:

            PROCEED     No error messages, put possibly warning or info messages.
            STOP        One or more error messages.

        :param model_dict: A Python dictionary of the model to be validated
        :param variables_file_name: Path to file containing variable substitution data used with model file.
        Defaults to None.
        :param archive_file_name: Path to file containing binaries associated with the model file.
        Defaults to None.
        :return: A Validator.ReturnCode value
        :raises ValidationException: if an unhandleable AliasException is raised during an invocation of an
        aliases API call.
        """
        _method_name = 'validate_in_tool_mode'

        # We need to make a deep copy of model_dict here, to ensure it's
        # treated as a "read-only'" reference variable, during the variable
        # file validation process. The variable file validation process could
        # actually require changes to be made to the cloned model dictionary
        cloned_model_dict = copy.deepcopy(model_dict)

        self._logger.entering(variables_file_name, archive_file_name, class_name=_class_name, method_name=_method_name)
        return_code = Validator.ReturnCode.STOP
        self._validation_mode = _ValidationModes.TOOL
        self.__validate_model_file(cloned_model_dict, variables_file_name, archive_file_name)

        status = Validator.ValidationStatus.VALID

        if self._validation_results.get_errors_count() > 0:
            status = Validator.ValidationStatus.INVALID
        elif self._validation_results.get_warnings_count() > 0:
            status = Validator.ValidationStatus.WARNINGS_INVALID
        elif self._validation_results.get_infos_count() > 0:
            status = Validator.ValidationStatus.INFOS_VALID

        self._validation_results.log_results(self._logger)

        if status == Validator.ValidationStatus.VALID or status == Validator.ValidationStatus.INFOS_VALID \
                or status == Validator.ValidationStatus.WARNINGS_INVALID:
            return_code = Validator.ReturnCode.PROCEED

        self._logger.exiting(class_name=_class_name, method_name=_method_name, result=return_code)
        return return_code

    def print_usage(self, model_path, control_option=None):
        """
        Prints out the usage information for a given model_path, using control_option to filter what is output

        :param model_path: A forward-slash delimited string contain the model path to print usage for
        :param control_option: A command-line switch that controls what is output to STDOUT
        :return:
        """
        _method_name = 'print_usage'

        self._logger.entering(model_path, class_name=_class_name, method_name=_method_name)

        if control_option is None:
            # Try to determine control option using the model_context
            if self._model_context.get_recursive_control_option():
                control_option = UsagePrinter.ControlOptions.RECURSIVE
            elif self._model_context.get_attributes_only_control_option():
                control_option = UsagePrinter.ControlOptions.ATTRIBUTES_ONLY

        if control_option is None:
            # Checking the model_context didn't produce a definitive control
            # option, so default to FOLDERS_ONLY
            control_option = UsagePrinter.ControlOptions.FOLDERS_ONLY

        usage_printer = UsagePrinter(self._alias_helper, self._logger)
        usage_printer.print_model_path_usage(model_path, control_option)

        self._logger.exiting(class_name=_class_name, method_name=_method_name)

        return

    ####################################################################################
    #
    # Private methods, private inner classes and static methods only, beyond here please
    #
    ####################################################################################

    def __validate_model_file(self, model_dict, variables_file_name, archive_file_name):
        _method_name = '__validate_model_file'

        self.__pre_validation_setup(model_dict, archive_file_name)

        self._logger.entering(variables_file_name, archive_file_name, class_name=_class_name, method_name=_method_name)
        self._logger.info('WLSDPLY-05002', _ValidationModes.from_value(self._validation_mode), self._wls_version,
                          WlstModes.from_value(self._wlst_mode), class_name=_class_name, method_name=_method_name)

        if self._model_file_name is not None:
            self._logger.info('WLSDPLY-05003', self._model_file_name, class_name=_class_name, method_name=_method_name)

        try:
            if variables_file_name is not None:
                self._logger.info('WLSDPLY-05004', variables_file_name, class_name=_class_name, method_name=_method_name)
                self._variable_properties = variables.load_variables(variables_file_name)

            variables.substitute(model_dict, self._variable_properties, self._model_context)
        except VariableException, ve:
            ex = exception_helper.create_validate_exception('WLSDPLY-20004', 'validateModel',
                                                            ve.getLocalizedMessage(), error=ve)
            self._logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex

        if archive_file_name is not None:
            self._logger.info('WLSDPLY-05005', archive_file_name, class_name=_class_name, method_name=_method_name)
            self._archive_entries = self._archive_helper.get_archive_entries()
            # TODO(mwooten) - this would be a good place to validate the structure of the archive.  If we are
            # not going to validate the structure and only validate things referenced by the model, then no
            # need to load the archive_entries variable because it is not being used.

        validation_result = ValidationResult(_ROOT_LEVEL_VALIDATION_AREA)
        validation_result = self.__validate_root_level(model_dict,
                                                       model.get_model_top_level_keys(),
                                                       validation_result)
        self._validation_results.set_validation_result(validation_result)

        validation_result = ValidationResult(_DOMAIN_INFO_VALIDATION_AREA)
        validation_result = self.__validate_domain_info_section(model.get_model_domain_info_key(),
                                                                model_dict,
                                                                validation_result)
        self._validation_results.set_validation_result(validation_result)

        validation_result = ValidationResult(_TOPOLOGY_VALIDATION_AREA)
        validation_result = self.__validate_model_section(model.get_model_topology_key(),
                                                          model_dict,
                                                          self._aliases.get_model_topology_top_level_folder_names(),
                                                          validation_result)
        self._validation_results.set_validation_result(validation_result)

        validation_result = ValidationResult(_RESOURCES_VALIDATION_AREA)
        validation_result = \
            self.__validate_model_section(model.get_model_resources_key(),
                                          model_dict,
                                          self._aliases.get_model_resources_top_level_folder_names(),
                                          validation_result)
        self._validation_results.set_validation_result(validation_result)

        validation_result = ValidationResult(_APP_DEPLOYMENTS_VALIDATION_AREA)
        validation_result = \
            self.__validate_model_section(model.get_model_deployments_key(),
                                          model_dict,
                                          self._aliases.get_model_app_deployments_top_level_folder_names(),
                                          validation_result)
        self._validation_results.set_validation_result(validation_result)

        self._logger.exiting(class_name=_class_name, method_name=_method_name)
        return

    def __pre_validation_setup(self, model_dict, archive_file_name):
        """
        Performs pre-validation setup activities. These include things like:

            1.  Obtaining the domain name using either the WebLogicHelper object,
                parameter passed ti the constructor or the model context object.
            2.  Creating an ArchiveHelper object, which servers as a facade for
                an Archive object.

        :param model_dict: A Python dictionary of the model to be validated
        :param archive_file_name: Path to file containing binaries associated with the model file.
        :return: Nothing.
        """
        topology_dict = dictionary_utils.get_dictionary_element(model_dict, TOPOLOGY)
        domain_name = dictionary_utils.get_element(topology_dict, NAME)

        if domain_name is None:
            domain_name = WebLogicHelper(self._logger).get_default_wls_domain_name()

        if domain_name is not None:
            self._name_tokens_location.add_name_token('DOMAIN', domain_name)

        if archive_file_name is not None:
            self._archive_file_name = archive_file_name
            self._archive_helper = ArchiveHelper(self._archive_file_name, domain_name,
                                                 self._logger, ExceptionType.VALIDATE)
        return

    def __validate_root_level(self, model_dict, valid_root_level_keys, validation_result):
        _method_name = '__validate_root_level'

        # Get list of root level keys from model_dict
        model_root_level_keys = model_dict.keys()
        self._logger.entering(model_root_level_keys, valid_root_level_keys,
                              class_name=_class_name, method_name=_method_name)

        if not model_root_level_keys:
            if self._validation_mode == _ValidationModes.STANDALONE:
                # The model_dict didn't have any top level keys, so record it
                # as a INFO message in the validate results and bail.
                validation_result.add_info('WLSDPLY-05006', self._model_file_name)
            else:
                # The model_dict didn't have any top level keys, so record it
                # as a ERROR message in the validate results and bail.
                validation_result.add_error('WLSDPLY-05006', self._model_file_name)

            return validation_result

        # Loop through model_root_level_keys
        for key in model_root_level_keys:
            if key not in valid_root_level_keys:
                # Found a model_root_level_keys key that isn't in
                # valid_root_level_keys, so log it at a INFO level
                self._logger.info('WLSDPLY-05007', self._model_file_name, key,
                                  '%s' % ', '.join(valid_root_level_keys),
                                  class_name=_class_name, method_name=_method_name)

        self._logger.exiting(class_name=_class_name, method_name=_method_name)
        return validation_result

    def __validate_domain_info_section(self, model_section_key, model_dict, validation_result):
        """
        Performs validation on just the domainInfo section of the model.

        :param model_section_key: Name of the model section, which is model_constants.DOMAIN_INFO
        :param model_dict: Python dictionary of the model file
        :param validation_result: A validation result object used only for capturing validation
        messages, associated with the domainInfo model section
        :return:
        """
        _method_name = '__validate_domain_info_section'
        self._logger.info('WLSDPLY-05008', model_section_key, self._model_file_name,
                          class_name=_class_name, method_name=_method_name)

        if model_section_key not in model_dict.keys():
            # model_section_key is not in model_dict.keys(), so record this as a
            # INFO log message, then bail from validating this section of
            # model_dict
            self._logger.info('WLSDPLY-05009', self._model_file_name, model_section_key,
                              class_name=_class_name, method_name=_method_name)
            return validation_result

        # Start with an empty location
        validation_location = LocationContext()

        # alias_helper.get_model_folder_path(location) does not currently know how to
        # associate attributes in the model_constants.DOMAIN_INFO section with 'domainInfo:'.
        # This being the case, we need to use model_section_key to generate the correct model
        # folder path for the model_constants.DOMAIN_INFO section
        model_folder_path = '%s:/' % model_section_key

        # Call aliases to get dictionary of the valid attributes for the
        # model_constants.DOMAIN_INFO section.
        valid_attr_infos = self._alias_helper.get_model_domain_info_attribute_names_and_types()
        self._logger.finer('WLSDPLY-05010', str(valid_attr_infos),
                           class_name=_class_name, method_name=_method_name)

        path_tokens_attr_keys = []
        model_section_dict = model_dict[model_section_key]

        for section_dict_key, section_dict_value in model_section_dict.iteritems():
            # section_dict_key is either the name of a folder in the
            # section, or the name of an attribute in the section.
            # section_dict_value is either the dict of a folder in the
            # section, or the value of an attribute in the section
            if '${' in section_dict_key:
                validation_result.add_error('WLSDPLY-05035', model_folder_path, section_dict_key)

            self._logger.finer('WLSDPLY-05011', section_dict_key, section_dict_value,
                               class_name=_class_name, method_name=_method_name)

            if section_dict_key in valid_attr_infos:
                # section_dict_key is an attribute under the model section, and
                # also in valid_attr_infos.
                if section_dict_key == DOMAIN_LIBRARIES:
                    validation_result = self.__validate_path_tokens_attribute(section_dict_key,
                                                                              section_dict_value,
                                                                              model_folder_path,
                                                                              validation_result)
                elif section_dict_key == SERVER_GROUP_TARGETING_LIMITS:
                    validation_result = self.__validate_server_group_targeting_limits(section_dict_key,
                                                                                      section_dict_value,
                                                                                      valid_attr_infos,
                                                                                      model_folder_path,
                                                                                      validation_location,
                                                                                      validation_result)
                else:
                    validation_result = self.__validate_attribute(section_dict_key,
                                                                  section_dict_value,
                                                                  valid_attr_infos,
                                                                  path_tokens_attr_keys,
                                                                  model_folder_path,
                                                                  validation_location,
                                                                  validation_result)
            else:
                # section_dict_key is not an attribute allowed under the model
                # section, so record this as a validate ERROR in the validate
                # results.
                validation_result.add_error('WLSDPLY-05029', section_dict_key, model_folder_path,
                                            valid_attr_infos.keys())

        return validation_result

    def __validate_model_section(self, model_section_key, model_dict, valid_section_folders, validation_result):
        _method_name = '__validate_model_section'

        self._logger.info('WLSDPLY-05008', model_section_key, self._model_file_name,
                          class_name=_class_name, method_name=_method_name)

        if model_section_key not in model_dict.keys():
            # model_section-key is not in model_dict.keys(), so record this as a
            # INFO log message, then bail from validating this section of
            # model_dict
            self._logger.info('WLSDPLY-05009', self._model_file_name, model_section_key,
                              class_name=_class_name, method_name=_method_name)
            return validation_result

        model_section_dict = model_dict[model_section_key]
        for section_dict_key, section_dict_value in model_section_dict.iteritems():
            # section_dict_key is either the name of a folder in the
            # section, or the name of an attribute in the section.
            validation_location = LocationContext()

            model_folder_path = self._alias_helper.get_model_folder_path(validation_location)

            if '${' in section_dict_key:
                validation_result = _report_unsupported_variable_usage(section_dict_key,
                                                                       model_folder_path,
                                                                       validation_result)

            self._logger.finer('WLSDPLY-05011', section_dict_key, section_dict_value,
                               class_name=_class_name, method_name=_method_name)

            valid_attr_infos = self._alias_helper.get_model_attribute_names_and_types(validation_location)
            self._logger.finer('WLSDPLY-05012', str(validation_location), str(valid_attr_infos),
                               class_name=_class_name, method_name=_method_name)

            path_tokens_attr_keys = self._alias_helper.get_model_uses_path_tokens_attribute_names(validation_location)
            self._logger.finer('WLSDPLY-05013', str(validation_location), str(path_tokens_attr_keys),
                               class_name=_class_name, method_name=_method_name)

            if section_dict_key in valid_attr_infos:
                # section_dict_key is the name of an attribute in the section
                validation_result = self.__validate_attribute(section_dict_key,
                                                              section_dict_value,
                                                              valid_attr_infos,
                                                              path_tokens_attr_keys,
                                                              model_folder_path,
                                                              validation_location,
                                                              validation_result)
            elif section_dict_key in valid_section_folders:
                # section_dict_key is a folder under the model section

                # Append section_dict_key to location context
                validation_location.append_location(section_dict_key)
                self._logger.finest('validation_location = {0}', str(validation_location),
                                    class_name=_class_name, method_name=_method_name)

                # Call self.__validate_section_folder() passing in section_dict_value
                # as the model_node to process
                validation_result = self.__validate_section_folder(section_dict_value,
                                                                   validation_location,
                                                                   validation_result)
            else:
                # It's not one of the section's folders and it's not an attribute of a
                # the section. Record this as a validate ERROR in the validate
                # results.
                if isinstance(section_dict_value, dict):
                    result, message = self._alias_helper.is_valid_model_folder_name(validation_location,
                                                                                    section_dict_key)
                    if result == ValidationCodes.VERSION_INVALID:
                        # key is a VERSION_INVALID folder
                        validation_result.add_warning('WLSDPLY-05027', message)
                    elif result == ValidationCodes.INVALID:
                        validation_result.add_error('WLSDPLY-05026', section_dict_key, 'folder',
                                                    model_folder_path, '%s' % ', '.join(valid_section_folders))
                else:
                    result, message = self._alias_helper.is_valid_model_attribute_name(validation_location,
                                                                                       section_dict_key)
                    if result == ValidationCodes.VERSION_INVALID:
                        validation_result.add_warning('WLSDPLY-05027', message)
                    elif result == ValidationCodes.INVALID:
                        validation_result.add_error('WLSDPLY-05029', section_dict_key,
                                                    model_folder_path, '%s' % ', '.join(valid_attr_infos))

        return validation_result

    def __validate_section_folder(self, model_node, validation_location, validation_result):
        _method_name = '__validate_section_folder'

        result, message = self._alias_helper.is_version_valid_location(validation_location)
        if result == ValidationCodes.VERSION_INVALID:
            validation_result.add_warning('WLSDPLY-05027', message)
            return validation_result
        elif result == ValidationCodes.INVALID:
            validation_result.add_error('WLSDPLY-05027', message)
            return validation_result

        model_folder_path = self._alias_helper.get_model_folder_path(validation_location)
        self._logger.finest('1 model_folder_path={0}', model_folder_path,
                            class_name=_class_name, method_name=_method_name)

        if self._alias_helper.supports_multiple_mbean_instances(validation_location):
            self._logger.finer('2 model_node_type={0}',
                               _ModelNodeTypes.from_value(_ModelNodeTypes.NAME_TYPE),
                               class_name=_class_name, method_name=_method_name)

            for name in model_node:
                expanded_name = name
                if '${' in name:
                    expanded_name, validation_result = \
                        self.__validate_variable_substitution(name, model_folder_path, validation_result)

                self._logger.finest('2 expanded_name={0}', expanded_name,
                                    class_name=_class_name, method_name=_method_name)

                new_location = LocationContext(validation_location)

                name_token = self._alias_helper.get_name_token(new_location)
                self._logger.finest('WLSDPLY-05014', str(validation_location), name_token,
                                    class_name=_class_name, method_name=_method_name)

                if name_token is not None:
                    new_location.add_name_token(name_token, expanded_name)

                self._logger.finest('2 new_location={0}', new_location,
                                    class_name=_class_name, method_name=_method_name)

                value_dict = model_node[name]

                self.__process_model_node(value_dict, new_location, validation_result)

        elif self._alias_helper.requires_artificial_type_subfolder_handling(validation_location):
            self._logger.finer('3 model_node_type={0}',
                               _ModelNodeTypes.from_value(_ModelNodeTypes.ARTIFICIAL_TYPE),
                               class_name=_class_name, method_name=_method_name)

            for name in model_node:
                expanded_name = name
                if '${' in name:
                    _report_unsupported_variable_usage(name, model_folder_path, validation_result)

                self._logger.finest('3 expanded_name={0}', expanded_name,
                                    class_name=_class_name, method_name=_method_name)

                new_location = LocationContext(validation_location)

                name_token = self._alias_helper.get_name_token(new_location)
                self._logger.finest('3 name_token={0}', name_token,
                                    class_name=_class_name, method_name=_method_name)

                if name_token is not None:
                    new_location.add_name_token(name_token, expanded_name)

                self._logger.finest('3 new_location={0}', new_location,
                                    class_name=_class_name, method_name=_method_name)

                value_dict = model_node[name]

                self.__process_model_node(value_dict, new_location, validation_result)

        else:
            self._logger.finer('4 model_node_type={0}',
                               _ModelNodeTypes.from_value(_ModelNodeTypes.FOLDER_TYPE),
                               class_name=_class_name, method_name=_method_name)

            name_token = self._alias_helper.get_name_token(validation_location)
            self._logger.finest('4 name_token={0}', name_token,
                                class_name=_class_name, method_name=_method_name)

            if name_token is not None:
                name = self._name_tokens_location.get_name_for_token(name_token)

                if name is None:
                    name = '%s-0' % name_token

                self._logger.finest('4 name={0}', name,
                                    class_name=_class_name, method_name=_method_name)
                validation_location.add_name_token(name_token, name)
                self._logger.finest('4 validation_location={0}', validation_location,
                                    class_name=_class_name, method_name=_method_name)

            self.__process_model_node(model_node, validation_location, validation_result)

        return validation_result

    def __process_model_node(self, model_node, validation_location, validation_result):

        _method_name = '__process_model_node'

        valid_folder_keys = self._alias_helper.get_model_subfolder_names(validation_location)
        valid_attr_infos = self._alias_helper.get_model_attribute_names_and_types(validation_location)
        model_folder_path = self._alias_helper.get_model_folder_path(validation_location)

        self._logger.finest('5 model_node={0}', str(model_node), class_name=_class_name, method_name=_method_name)
        self._logger.finest('5 aliases.get_model_subfolder_names(validation_location) returned: {0}',
                            str(valid_folder_keys),
                            class_name=_class_name, method_name=_method_name)
        self._logger.finest('5 aliases.get_model_attribute_names_and_types(validation_location) returned: {0}',
                            str(valid_attr_infos),
                            class_name=_class_name, method_name=_method_name)
        self._logger.finest('5 model_folder_path={0}', model_folder_path, class_name=_class_name,
                            method_name=_method_name)

        for key, value in model_node.iteritems():
            if '${' in key:
                _report_unsupported_variable_usage(key, model_folder_path, validation_result)

            self._logger.finer('5 key={0}', key,
                               class_name=_class_name, method_name=_method_name)
            self._logger.finer('5 value={0}', value,
                               class_name=_class_name, method_name=_method_name)

            if key in valid_folder_keys:
                new_location = LocationContext(validation_location).append_location(key)
                self._logger.finer('6 new_location={0}', new_location,
                                   class_name=_class_name, method_name=_method_name)

                if self._alias_helper.is_artificial_type_folder(new_location):
                    # key is an ARTIFICIAL_TYPE folder
                    self._logger.finest('6 is_artificial_type_folder=True',
                                        class_name=_class_name, method_name=_method_name)
                    valid_attr_infos = self._alias_helper.get_model_attribute_names_and_types(new_location)

                    validation_result = self.__validate_attributes(value, valid_attr_infos,
                                                                   new_location, validation_result)
                else:
                    self.__validate_section_folder(value, new_location, validation_result)

            elif key in valid_attr_infos:
                # aliases.get_model_attribute_names_and_types(location) filters out
                # attributes that ARE NOT valid in the wlst_version being used, so if
                # we're in this section of code we know key is a bonafide "valid" attribute
                valid_data_type = valid_attr_infos[key]
                if valid_data_type in ['properties']:
                    valid_prop_infos = {}
                    properties = validation_utils.get_properties(value)
                    validation_result = self.__validate_properties(properties, valid_prop_infos, validation_location,
                                                                   validation_result)

                else:
                    path_tokens_attr_keys = \
                        self._alias_helper.get_model_uses_path_tokens_attribute_names(validation_location)

                    validation_result = self.__validate_attribute(key,
                                                                  value,
                                                                  valid_attr_infos,
                                                                  path_tokens_attr_keys,
                                                                  model_folder_path,
                                                                  validation_location,
                                                                  validation_result)
            elif self._alias_helper.is_custom_folder_allowed(validation_location):
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
                    # instance name, because the _alias_helper.supports_multiple_mbean_instances()
                    # method pulls those out, in the self.__validate_section_folder().

                    # See if it's a version invalid folder
                    result, message = self._alias_helper.is_valid_model_folder_name(validation_location, key)
                    if result == ValidationCodes.VERSION_INVALID:
                        # key is a VERSION_INVALID folder
                        validation_result.add_warning('WLSDPLY-05027', message)
                    elif result == ValidationCodes.INVALID:
                        # key is an INVALID folder
                        validation_result.add_error('WLSDPLY-05026', key, 'folder',
                                                    model_folder_path, '%s' % ', '.join(valid_folder_keys))
                else:
                    # value is not a dict, so key must be the name of an attribute. key cannot be a
                    # folder instance name, because the _alias_helper.supports_multiple_mbean_instances()
                    # method pulls those out, in the self.__validate_section_folder().

                    # See if it's a version invalid attribute
                    result, message = self._alias_helper.is_valid_model_attribute_name(validation_location, key)
                    if result == ValidationCodes.VERSION_INVALID:
                        # key is a VERSION_INVALID attribute
                        validation_result.add_warning('WLSDPLY-05027', message)
                    elif result == ValidationCodes.INVALID:
                        # key is an INVALID attribute
                        validation_result.add_error('WLSDPLY-05029', key,
                                                    model_folder_path, '%s' % ', '.join(valid_attr_infos))

        return validation_result

    def __validate_attributes(self, attributes_dict, valid_attr_infos,
                              validation_location, validation_result):
        _method_name = '__validate_attributes'

        self._logger.finest('attributes_dict={0}', str(attributes_dict),
                            class_name=_class_name, method_name=_method_name)

        path_tokens_attr_keys = self._alias_helper.get_model_uses_path_tokens_attribute_names(validation_location)
        self._logger.finer('WLSDPLY-05013', str(validation_location), str(path_tokens_attr_keys),
                           class_name=_class_name, method_name=_method_name)

        model_folder_path = self._alias_helper.get_model_folder_path(validation_location)

        for attribute_name, attribute_value in attributes_dict.iteritems():
            validation_result = self.__validate_attribute(attribute_name,
                                                          attribute_value,
                                                          valid_attr_infos,
                                                          path_tokens_attr_keys,
                                                          model_folder_path,
                                                          validation_location,
                                                          validation_result)

        return validation_result

    def __validate_attribute(self, attribute_name, attribute_value, valid_attr_infos, path_tokens_attr_keys,
                             model_folder_path, validation_location, validation_result):
        _method_name = '__validate_attribute'

        log_value = attribute_value
        expected_data_type = dictionary_utils.get_element(valid_attr_infos, attribute_name)
        if expected_data_type == 'password':
            log_value = '<masked>'

        self._logger.entering(attribute_name, log_value, str(valid_attr_infos), str(path_tokens_attr_keys),
                              model_folder_path, str(validation_location),
                              class_name=_class_name, method_name=_method_name)

        if '${' in attribute_name:
            validation_result = _report_unsupported_variable_usage(attribute_name, model_folder_path, validation_result)

        if '${' in str(attribute_value):
            attribute_value, validation_result = self.__validate_variable_substitution(attribute_value,
                                                                                       model_folder_path,
                                                                                       validation_result)

        if attribute_name in valid_attr_infos:
            expected_data_type = valid_attr_infos[attribute_name]
            actual_data_type = str(type(attribute_value))
            self._logger.finer('WLSDPLY-05016', attribute_name, expected_data_type, actual_data_type,
                               class_name=_class_name, method_name=_method_name)
            if validation_utils.is_compatible_data_type(expected_data_type, actual_data_type) is False:
                validation_result.add_warning('WLSDPLY-05017', attribute_name, model_folder_path,
                                              expected_data_type, actual_data_type)

            if attribute_name in path_tokens_attr_keys:
                validation_result = self.__validate_path_tokens_attribute(attribute_name,
                                                                          attribute_value,
                                                                          model_folder_path,
                                                                          validation_result)
        else:
            result, message = self._alias_helper.is_valid_model_attribute_name(validation_location, attribute_name)
            if result == ValidationCodes.VERSION_INVALID:
                validation_result.add_warning('WLSDPLY-05027', message)
            elif result == ValidationCodes.INVALID:
                validation_result.add_error('WLSDPLY-05029', attribute_name,
                                            model_folder_path, '%s' % ', '.join(valid_attr_infos))

        self._logger.exiting(class_name=_class_name, method_name=_method_name)

        return validation_result

    def __validate_properties(self, properties_dict, valid_prop_infos,
                              validation_location, validation_result):
        _method_name = '__validate_properties'

        self._logger.entering(str(properties_dict), str(validation_location),
                              class_name=_class_name, method_name=_method_name)

        for property_name, property_value in properties_dict.iteritems():
            valid_prop_infos[property_name] = validation_utils.get_python_data_type(property_value)
            validation_result = self.__validate_property(property_name,
                                                         property_value,
                                                         valid_prop_infos,
                                                         validation_location,
                                                         validation_result)

        self._logger.exiting(class_name=_class_name, method_name=_method_name)

        return validation_result

    def __validate_property(self, property_name, property_value, valid_prop_infos,
                            model_folder_path, validation_result):

        _method_name = '__validate_property'

        self._logger.entering(property_name, property_value, str(valid_prop_infos), model_folder_path,
                              class_name=_class_name, method_name=_method_name)

        if '${' in property_name:
            property_name, validation_result = self.__validate_variable_substitution(property_name,
                                                                                     model_folder_path,
                                                                                     validation_result)
        if '${' in str(property_value):
            property_value, validation_result = self.__validate_variable_substitution(property_value,
                                                                                      model_folder_path,
                                                                                      validation_result)

        if property_name in valid_prop_infos:
            expected_data_type = valid_prop_infos[property_name]
            actual_data_type = str(type(property_value))
            self._logger.finer('WLSDPLY-05018', property_name, expected_data_type, actual_data_type,
                               class_name=_class_name, method_name=_method_name)
            if validation_utils.is_compatible_data_type(expected_data_type, actual_data_type) is False:
                validation_result.add_warning('WLSDPLY-05019', property_name, model_folder_path,
                                              expected_data_type, actual_data_type)
        else:
            validation_result.add_error('WLSDPLY-05020', property_name, model_folder_path)

        return validation_result

    def __validate_variable_substitution(self, tokenized_value, model_folder_path, validation_result):
        _method_name = '__validate_variable_substitution'

        self._logger.entering(tokenized_value, model_folder_path, class_name=_class_name, method_name=_method_name)

        # FIXME(mwooten) - What happens in tool mode when the variable_file_name passed is None but
        # model_context.get_variable_file() returns the variable file passed on the command-line?  I
        # don't think we should be executing this code if the variable_file_name passed was None.
        untokenized_value = tokenized_value

        if not isinstance(untokenized_value, dict):
            # Extract the variable substitution variables from tokenized_value
            tokens = validation_utils.extract_substitution_tokens(tokenized_value)
            for token in tokens:
                property_name = token[2:len(token)-1]
                property_value = None
                if property_name in self._variable_properties:
                    property_value = self._variable_properties[property_name]
                if property_value is not None:
                    untokenized_value = untokenized_value.replace(token, property_value)
                else:
                    # FIXME(mwooten) - the cla_utils should be fixing all windows paths to use forward slashes already...
                    # assuming that the value is not None
                    variables_file_name = self._model_context.get_variable_file()
                    if variables_file_name is None:
                        self._logger.warning('WLSDPLY-05021', model_folder_path, property_name,
                                             class_name=_class_name, method_name=_method_name)
                    else:
                        self._logger.warning('WLSDPLY-05022', model_folder_path, property_name, variables_file_name,
                                             class_name=_class_name, method_name=_method_name)

        self._logger.exiting(class_name=_class_name, method_name=_method_name, result=untokenized_value)
        return untokenized_value, validation_result

    def __validate_path_tokens_attribute(self, attribute_name, attribute_value, model_folder_path, validation_result):
        _method_name = '__validate_path_tokens_attribute'

        self._logger.entering(attribute_name, attribute_value, model_folder_path,
                              class_name=_class_name, method_name=_method_name)

        value_data_type = validation_utils.get_python_data_type(attribute_value)

        self._logger.finest('value_data_type={0}', value_data_type,
                            class_name=_class_name, method_name=_method_name)

        valid_valus_data_types = ['list', 'string']
        if value_data_type not in valid_valus_data_types:
            validation_result.add_error('WLSDPLY-05023', attribute_name, model_folder_path, value_data_type)
        else:
            attr_values = []

            if value_data_type == 'string' and model_constants.MODEL_LIST_DELIMITER in attribute_value:
                attr_values = attribute_value.split(model_constants.MODEL_LIST_DELIMITER)

            elif value_data_type == 'string':
                attr_values.append(attribute_value)

            else:
                # must be a list
                attr_values.extend(attribute_value)

            for item_path in attr_values:
                validation_result = self.__validate_single_path_in_archive(item_path.strip(), attribute_name,
                                                                           model_folder_path, validation_result)

        return validation_result

    def __validate_single_path_in_archive(self, path, attribute_name, model_folder_path, validation_result):
        _method_name = '__validate_single_path_in_archive'

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
            if self._archive_helper is not None:
                archive_has_file = self._archive_helper.contains_file_or_path(path)
                if not archive_has_file:
                    validation_result.add_error('WLSDPLY-05024', attribute_name, model_folder_path,
                                                path, self._archive_file_name)
            else:
                # If running in standalone mode, and the archive was not supplied, simply
                # alert the user to the references but don;t fail validation because of
                # the dangling references.  In TOOL mode, this is an error.
                if self._validation_mode == _ValidationModes.STANDALONE:
                    validation_result.add_info('WLSDPLY-05025', attribute_name, model_folder_path, path)
                elif self._validation_mode == _ValidationModes.TOOL:
                    validation_result.add_error('WLSDPLY-05025', attribute_name, model_folder_path, path)
        else:
            tokens = validation_utils.extract_path_tokens(path)
            self._logger.finest('tokens={0}', str(tokens), class_name=_class_name, method_name=_method_name)
            # TODO(mwooten) - This would be a good place to validate any path token found...

            if not self._model_context.has_token_prefix(path):
                if not os.path.isabs(path):
                    validation_result.add_info('WLSDPLY-05031', attribute_name, model_folder_path, path)

        return validation_result

    def __validate_server_group_targeting_limits(self, attribute_name, attribute_value, valid_attr_infos,
                                                 model_folder_path, validation_location, validation_result):
        __method_name = '__validate_server_group_targeting_limits'

        self._logger.entering(attribute_name, attribute_value, valid_attr_infos, model_folder_path,
                              str(validation_location), class_name=_class_name, method_name=__method_name)

        if attribute_value is not None:
            if not isinstance(attribute_value, dict):
                validation_result.add_error('WLSDPLY-05032',
                                            attribute_name, model_folder_path,
                                            str(type(attribute_value)))
            else:
                model_folder_path += '/' + attribute_name
                for key, value in attribute_value.iteritems():
                    if type(key) is not str:
                        # Force the key to a string for any value validation issues reported below
                        key = str(key)
                        validation_result.add_error('WLSDPLY-05033', key, model_folder_path, str(type(key)))
                    else:
                        if '${' in key:
                            key, validation_result = \
                                _report_unsupported_variable_usage(key, model_folder_path, validation_result)

                    if type(value) is str and MODEL_LIST_DELIMITER in value:
                        value = value.split(MODEL_LIST_DELIMITER)

                    if type(value) is list:
                        for element in value:
                            validation_result = \
                                _validate_single_server_group_target_limits_value(key, element.strip(),
                                                                                  model_folder_path,
                                                                                  validation_result)
                    elif type(value) is str:
                        validation_result = \
                            _validate_single_server_group_target_limits_value(key, value, model_folder_path,
                                                                              validation_result)
                    else:
                        validation_result.add_error('WLSDPLY-05034', key, model_folder_path, str(type(value)))

        self._logger.exiting(class_name=_class_name, method_name=__method_name)
        return validation_result


def _validate_single_server_group_target_limits_value(key, value, model_folder_path, validation_result):
    if type(value) is str:
        if '${' in str(value):
            value, validation_result = \
                _report_unsupported_variable_usage(str(value), model_folder_path, validation_result)
    else:
        validation_result.add_error('WLSDPLY-05035', key, str(value), model_folder_path, str(type(value)))

    return validation_result


def _report_unsupported_variable_usage(tokenized_value, model_folder_path, validation_result):
    tokens = validation_utils.extract_substitution_tokens(tokenized_value)
    for token in tokens:
        validation_result.add_error('WLSDPLY-05030', model_folder_path, token)

    return validation_result
