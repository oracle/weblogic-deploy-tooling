"""
Copyright (c) 2017, 2022, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import os
import copy

from java.util.logging import Level

from oracle.weblogic.deploy.logging import WLSDeployLogEndHandler
from oracle.weblogic.deploy.util import WLSDeployArchive
from oracle.weblogic.deploy.util import VariableException

from wlsdeploy.aliases import model_constants
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.validation_codes import ValidationCodes
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception.expection_types import ExceptionType
from wlsdeploy.exception import exception_helper
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.create import wlsroles_helper
from wlsdeploy.tool.util.archive_helper import ArchiveHelper
from wlsdeploy.tool.validate import validation_utils
from wlsdeploy.tool.validate.kubernetes_validator import KubernetesValidator
from wlsdeploy.tool.validate.validator_logger import ValidatorLogger
from wlsdeploy.util import dictionary_utils
from wlsdeploy.util import model
import wlsdeploy.util.unicode_helper as str_helper
from wlsdeploy.util import variables
from wlsdeploy.util.enum import Enum
from wlsdeploy.util.weblogic_helper import WebLogicHelper

from wlsdeploy.aliases.model_constants import DOMAIN_INFO
from wlsdeploy.aliases.model_constants import DYNAMIC_CLUSTER_SERVER_GROUP_TARGETING_LIMITS
from wlsdeploy.aliases.model_constants import MASKED_PASSWORD
from wlsdeploy.aliases.model_constants import MODEL_LIST_DELIMITER
from wlsdeploy.aliases.model_constants import NAME
from wlsdeploy.aliases.model_constants import SERVER_GROUP_TARGETING_LIMITS
from wlsdeploy.aliases.model_constants import TOPOLOGY
from wlsdeploy.aliases.model_constants import WLS_ROLES

_class_name = 'Validator'
_logger = ValidatorLogger('wlsdeploy.validate')
_info_logger = PlatformLogger('wlsdeploy.validate')
_ModelNodeTypes = Enum(['FOLDER_TYPE', 'NAME_TYPE', 'ATTRIBUTE', 'ARTIFICIAL_TYPE'])
_ValidationModes = Enum(['STANDALONE', 'TOOL'])
_ROOT_LEVEL_VALIDATION_AREA = validation_utils.format_message('WLSDPLY-05000')
_DOMAIN_INFO_VALIDATION_AREA = validation_utils.format_message('WLSDPLY-05001', model_constants.DOMAIN_INFO)
_TOPOLOGY_VALIDATION_AREA = validation_utils.format_message('WLSDPLY-05001', model_constants.TOPOLOGY)
_RESOURCES_VALIDATION_AREA = validation_utils.format_message('WLSDPLY-05001', model_constants.RESOURCES)
_APP_DEPLOYMENTS_VALIDATION_AREA = validation_utils.format_message('WLSDPLY-05001', model_constants.APP_DEPLOYMENTS)
_GLOBAL_LEVEL_VARAIBLE_SUBSTITUTE = validation_utils.format_message('WLSDPLY-05001',
                                                                    model_constants.GLOBAL_VARIABLE_SUBSTITUTION)


class Validator(object):
    """
    Class for validating a model file and printing the metadata used in it
    """
    ValidationStatus = Enum(['VALID', 'INFOS_VALID', 'WARNINGS_INVALID', 'INVALID'])
    ReturnCode = Enum(['PROCEED', 'STOP'])

    def __init__(self, model_context, aliases, logger=None, wlst_mode=None, validate_crd_sections=True):
        """
        Create a validator instance.
        :param model_context: used to get command-line options
        :param aliases: used to validate folders, attributes. also determines exception type
        :param logger: alternate logger to use
        :param wlst_mode: online or offline mode
        :param validate_crd_sections: True if CRD sections (such as kubernetes) should be validated
        """
        self._model_context = model_context
        self._validate_configuration = model_context.get_validate_configuration()

        if logger is None:
            # No logger specified, so use the one declared at the module level
            self._logger = _logger
        else:
            self._logger = logger

        self._validation_mode = None
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

        self._aliases = aliases

        # need a token here for alias path resolution
        self._name_tokens_location = LocationContext()
        self._name_tokens_location.add_name_token('DOMAIN', 'base_domain')

        self._archive_helper = None
        self._archive_file_name = None
        self._archive_entries = None
        self._model_file_name = self._model_context.get_model_file()
        self._validate_crd_sections = validate_crd_sections

    def validate_in_standalone_mode(self, model_dict, variable_map, archive_file_name=None):
        """
        Performs model file validate and returns a ValidationResults object.

        Prints a text representation of the returned object to STDOUT, using an 80 characters per
        line format (when possible). Info-related items are printed first, followed by warning-related
        ones, followed by error-related ones.

        :param model_dict: A Python dictionary of the model to be validated
        :param variable_map: Map used for variable substitution
        :param archive_file_name: Path to file containing binaries associated with the model file.
        Defaults to None.
        :raises ValidationException: if an AliasException is raised during an invocation of an aliases API call.
        """
        _method_name = 'validate_in_standalone_mode'

        # If standalone, log file will not be passed, so get a new logger with correct mode type
        self._validation_mode = _ValidationModes.STANDALONE
        return_code = Validator.ReturnCode.STOP
        self._logger = ValidatorLogger(self._logger.get_name(), _ValidationModes.from_value(self._validation_mode))
        self._logger.entering(archive_file_name, class_name=_class_name, method_name=_method_name)

        # We need to make a deep copy of model_dict here, to ensure it's
        # treated as a "read-only'" reference variable, during the variable
        # file validation process. The variable file validation process could
        # actually require changes to be made to the cloned model dictionary
        cloned_model_dict = copy.deepcopy(model_dict)

        self._logger.entering(archive_file_name, class_name=_class_name, method_name=_method_name)
        self.__validate_model_file(cloned_model_dict, variable_map, archive_file_name)

        status = Validator.ValidationStatus.VALID
        summary_handler = WLSDeployLogEndHandler.getSummaryHandler()
        if summary_handler is not None:
            summary_level = summary_handler.getMaximumMessageLevel()
            if summary_level == Level.SEVERE:
                status = Validator.ValidationStatus.INVALID
            elif summary_level == Level.WARNING:
                status = Validator.ValidationStatus.WARNINGS_INVALID
        else:
            # TODO - Should really report/throw an error here if the summary logger was not found!
            pass

        if status == Validator.ValidationStatus.VALID or status == Validator.ValidationStatus.INFOS_VALID \
                or status == Validator.ValidationStatus.WARNINGS_INVALID:
            return_code = Validator.ReturnCode.PROCEED
        self._logger.exiting(class_name=_class_name, method_name=_method_name, result=return_code)
        return return_code

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
        variable_map = self.load_variables(variables_file_name)
        self.__validate_model_file(cloned_model_dict, variable_map, archive_file_name)

        status = Validator.ValidationStatus.VALID

        summary_handler = WLSDeployLogEndHandler.getSummaryHandler()
        if summary_handler is not None:
            summary_level = summary_handler.getMaximumMessageLevel()
            if summary_level == Level.SEVERE:
                status = Validator.ValidationStatus.INVALID
            elif summary_level == Level.WARNING:
                status = Validator.ValidationStatus.WARNINGS_INVALID
        else:
            # TODO - Should really report/throw an error here if the summary logger was not found!
            pass

        if status == Validator.ValidationStatus.VALID or status == Validator.ValidationStatus.INFOS_VALID \
                or status == Validator.ValidationStatus.WARNINGS_INVALID:
            return_code = Validator.ReturnCode.PROCEED

        self._logger.exiting(class_name=_class_name, method_name=_method_name, result=return_code)
        return return_code

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

    def __validate_model_file(self, model_dict, variables_map, archive_file_name):
        _method_name = '__validate_model_file'

        self.__pre_validation_setup(model_dict, archive_file_name)

        self._logger.entering(archive_file_name, class_name=_class_name, method_name=_method_name)
        self._logger.info('WLSDPLY-05002', _ValidationModes.from_value(self._validation_mode), self._wls_version,
                          WlstModes.from_value(self._wlst_mode), class_name=_class_name, method_name=_method_name)

        if self._model_file_name is not None:
            self._logger.info('WLSDPLY-05003', self._model_file_name, class_name=_class_name, method_name=_method_name)

        self._variable_properties = variables_map
        # don't substitute model here, it should be validated with variables intact

        if archive_file_name is not None:
            self._logger.info('WLSDPLY-05005', archive_file_name, class_name=_class_name, method_name=_method_name)
            self._archive_entries = self._archive_helper.get_archive_entries()
            # TODO(mwooten) - this would be a good place to validate the structure of the archive.  If we are
            # not going to validate the structure and only validate things referenced by the model, then no
            # need to load the archive_entries variable because it is not being used.

        self.__validate_root_level(model_dict, model.get_model_top_level_keys())

        self.__validate_model_section(model.get_model_domain_info_key(), model_dict,
                                      self._aliases.get_model_section_top_level_folder_names(DOMAIN_INFO))

        self.__validate_model_section(model.get_model_topology_key(), model_dict,
                                      self._aliases.get_model_topology_top_level_folder_names())

        self.__validate_model_section(model.get_model_resources_key(), model_dict,
                                      self._aliases.get_model_resources_top_level_folder_names())

        self.__validate_model_section(model.get_model_deployments_key(), model_dict,
                                      self._aliases.get_model_app_deployments_top_level_folder_names())

        if self._validate_crd_sections:
            k8s_validator = KubernetesValidator(self._model_context)
            k8s_validator.validate_model(model_dict)

        self._logger.exiting(class_name=_class_name, method_name=_method_name)

    def load_variables(self, variables_file_name):
        """
        Load the variables properties from the specified file.
        :param variables_file_name: the name of the variables file, or None if not specified
        :return: the variables properties
        """
        _method_name = 'load_variables'

        try:
            if variables_file_name is not None:
                self._logger.info('WLSDPLY-05004', variables_file_name, class_name=_class_name,
                                  method_name=_method_name)
                return variables.load_variables(variables_file_name, allow_multiple_files=True)
            return {}
        except VariableException, ve:
            ex = exception_helper.create_validate_exception('WLSDPLY-20004', 'validateModel',
                                                            ve.getLocalizedMessage(), error=ve)
            self._logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex

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

    def __validate_root_level(self, model_dict, valid_root_level_keys):
        _method_name = '__validate_root_level'

        # Get list of root level keys from model_dict
        model_root_level_keys = model_dict.keys()
        self._logger.entering(model_root_level_keys, valid_root_level_keys,
                              class_name=_class_name, method_name=_method_name)

        if not model_root_level_keys:
            if self._validation_mode == _ValidationModes.STANDALONE:
                # The model_dict didn't have any top level keys, so record it
                # as a INFO message in the validate results and bail.
                self._logger.info('WLSDPLY-05006', self._model_file_name, class_name=_class_name,
                                  method_name=_method_name)
            else:
                # The model_dict didn't have any top level keys, so record it
                # as a ERROR message in the validate results and bail.
                self._logger.severe('WLSDPLY-05006', self._model_file_name, class_name=_class_name,
                                    method_name=_method_name)
            return

        # Loop through model_root_level_keys
        for key in model_root_level_keys:
            if key not in valid_root_level_keys:
                # Found a model_root_level_keys key that isn't in
                # valid_root_level_keys, so log it at the ERROR level
                self._logger.severe('WLSDPLY-05007', self._model_file_name, key,
                                    '%s' % ', '.join(valid_root_level_keys), class_name=_class_name,
                                    method_name=_method_name)

        self._logger.exiting(class_name=_class_name, method_name=_method_name)

    def __validate_model_section(self, model_section_key, model_dict, valid_section_folders):
        """
        Validate a root-level section, such as topology, domainInfo
        :param model_section_key: the key for the section
        :param model_dict: the top-level model dictionary
        :param valid_section_folders: folders that are valid for this section
        """
        _method_name = '__validate_model_section'

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
                self.__validate_attribute(section_dict_key, section_dict_value, valid_attr_infos,
                                          path_tokens_attr_keys, model_folder_path, attribute_location)

                # Some top-level attributes have additional validation
                self.__validate_top_field_extended(section_dict_key, section_dict_value, model_folder_path)

            elif section_dict_key in valid_section_folders:
                # section_dict_key is a folder under the model section

                # Append section_dict_key to location context
                validation_location.append_location(section_dict_key)
                self._logger.finest('validation_location = {0}', str_helper.to_string(validation_location),
                                    class_name=_class_name, method_name=_method_name)

                # Call self.__validate_section_folder() passing in section_dict_value as the model_node to process
                self.__validate_section_folder(section_dict_value, validation_location)

                # Some top-level folders have additional validation
                self.__validate_top_field_extended(section_dict_key, section_dict_value, model_folder_path)

            else:
                # It's not one of the section's folders and it's not an attribute of the section.
                # Record this as a validate ERROR in the validate results.
                if isinstance(section_dict_value, dict):
                    result, message = self._aliases.is_valid_model_folder_name(validation_location,
                                                                                    section_dict_key)
                    if result == ValidationCodes.VERSION_INVALID:
                        self._log_version_invalid(message, _method_name)
                    elif result == ValidationCodes.INVALID:
                        self._logger.severe('WLSDPLY-05026', section_dict_key, 'folder', model_folder_path,
                                            '%s' % ', '.join(valid_section_folders), class_name=_class_name,
                                            method_name=_method_name)

                elif attribute_location is not None:
                    result, message = self._aliases.is_valid_model_attribute_name(attribute_location,
                                                                                       section_dict_key)
                    if result == ValidationCodes.VERSION_INVALID:
                        self._log_version_invalid(message, _method_name)
                    elif result == ValidationCodes.INVALID:
                        self._logger.severe('WLSDPLY-05029', section_dict_key, model_folder_path,
                                            '%s' % ', '.join(valid_attr_infos), class_name=_class_name,
                                            method_name=_method_name)

                else:
                    self._logger.severe('WLSDPLY-05029', section_dict_key, model_folder_path,
                                        '%s' % ', '.join(valid_attr_infos), class_name=_class_name,
                                        method_name=_method_name)

    def __validate_section_folder(self, model_node, validation_location):
        _method_name = '__validate_section_folder'

        result, message = self._aliases.is_version_valid_location(validation_location)
        if result == ValidationCodes.VERSION_INVALID:
            self._log_version_invalid(message, _method_name)
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
        self._logger.finest('1 model_folder_path={0}', model_folder_path,
                            class_name=_class_name, method_name=_method_name)

        if not isinstance(model_node, dict):
            self._logger.severe('WLSDPLY-05038', model_folder_path, class_name=_class_name, method_name=_method_name)
            return

        if self._aliases.supports_multiple_mbean_instances(validation_location):
            self._logger.finer('2 model_node_type={0}',
                               _ModelNodeTypes.from_value(_ModelNodeTypes.NAME_TYPE),
                               class_name=_class_name, method_name=_method_name)

            for name in model_node:
                expanded_name = name
                if variables.has_variables(name):
                    expanded_name = self.__validate_variable_substitution(name, model_folder_path)

                self._logger.finest('2 expanded_name={0}', expanded_name,
                                    class_name=_class_name, method_name=_method_name)

                new_location = LocationContext(validation_location)

                name_token = self._aliases.get_name_token(new_location)
                self._logger.finest('WLSDPLY-05014', str_helper.to_string(validation_location), name_token,
                                    class_name=_class_name, method_name=_method_name)

                if name_token is not None:
                    new_location.add_name_token(name_token, expanded_name)

                self._logger.finest('2 new_location={0}', str_helper.to_string(new_location),
                                    class_name=_class_name, method_name=_method_name)

                value_dict = model_node[name]

                self.__process_model_node(value_dict, new_location)

        elif self._aliases.requires_artificial_type_subfolder_handling(validation_location):
            self._logger.finer('3 model_node_type={0}',
                               _ModelNodeTypes.from_value(_ModelNodeTypes.ARTIFICIAL_TYPE),
                               class_name=_class_name, method_name=_method_name)

            for name in model_node:
                expanded_name = name
                if variables.has_variables(name):
                    self._report_unsupported_variable_usage(name, model_folder_path)

                self._logger.finest('3 expanded_name={0}', expanded_name,
                                    class_name=_class_name, method_name=_method_name)

                new_location = LocationContext(validation_location)

                name_token = self._aliases.get_name_token(new_location)
                self._logger.finest('3 name_token={0}', name_token,
                                    class_name=_class_name, method_name=_method_name)

                if name_token is not None:
                    new_location.add_name_token(name_token, expanded_name)

                self._logger.finest('3 new_location={0}', new_location,
                                    class_name=_class_name, method_name=_method_name)

                value_dict = model_node[name]

                self.__process_model_node(value_dict, new_location)

        else:
            self._logger.finer('4 model_node_type={0}',
                               _ModelNodeTypes.from_value(_ModelNodeTypes.FOLDER_TYPE),
                               class_name=_class_name, method_name=_method_name)

            name_token = self._aliases.get_name_token(validation_location)
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

            self.__process_model_node(model_node, validation_location)

    def __process_model_node(self, model_node, validation_location):
        _method_name = '__process_model_node'

        model_folder_path = self._aliases.get_model_folder_path(validation_location)

        if not isinstance(model_node, dict):
            self._logger.severe('WLSDPLY-05038', model_folder_path, class_name=_class_name, method_name=_method_name)
            return

        valid_folder_keys = self._aliases.get_model_subfolder_names(validation_location)
        valid_attr_infos = self._aliases.get_model_attribute_names_and_types(validation_location)

        self._logger.finest('5 model_node={0}', str_helper.to_string(model_node),
                            class_name=_class_name, method_name=_method_name)
        self._logger.finest('5 aliases.get_model_subfolder_names(validation_location) returned: {0}',
                            str_helper.to_string(valid_folder_keys),
                            class_name=_class_name, method_name=_method_name)
        self._logger.finest('5 aliases.get_model_attribute_names_and_types(validation_location) returned: {0}',
                            str_helper.to_string(valid_attr_infos),
                            class_name=_class_name, method_name=_method_name)
        self._logger.finest('5 model_folder_path={0}', model_folder_path, class_name=_class_name,
                            method_name=_method_name)

        for key, value in model_node.iteritems():
            if variables.has_variables(key):
                self._report_unsupported_variable_usage(key, model_folder_path)

            self._logger.finer('5 key={0}', key,
                               class_name=_class_name, method_name=_method_name)
            self._logger.finer('5 value={0}', value,
                               class_name=_class_name, method_name=_method_name)

            if key in valid_folder_keys:
                new_location = LocationContext(validation_location).append_location(key)
                self._logger.finer('6 new_location={0}', new_location,
                                   class_name=_class_name, method_name=_method_name)

                if self._aliases.is_artificial_type_folder(new_location):
                    # key is an ARTIFICIAL_TYPE folder
                    self._logger.finest('6 is_artificial_type_folder=True',
                                        class_name=_class_name, method_name=_method_name)
                    valid_attr_infos = self._aliases.get_model_attribute_names_and_types(new_location)

                    self.__validate_attributes(value, valid_attr_infos, new_location)
                else:
                    self.__validate_section_folder(value, new_location)

            elif key in valid_attr_infos:
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

                    self.__validate_attribute(key, value, valid_attr_infos, path_tokens_attr_keys, model_folder_path,
                                              validation_location)

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
                    result, message = self._aliases.is_valid_model_folder_name(validation_location, key)
                    if result == ValidationCodes.VERSION_INVALID:
                        self._log_version_invalid(message, _method_name)
                    elif result == ValidationCodes.INVALID:
                        # key is an INVALID folder
                        self._logger.severe('WLSDPLY-05026', key, 'folder', model_folder_path,
                                            '%s' % ', '.join(valid_folder_keys), class_name=_class_name,
                                            method_name=_method_name)
                else:
                    # value is not a dict, so key must be the name of an attribute. key cannot be a
                    # folder instance name, because the _aliases.supports_multiple_mbean_instances()
                    # method pulls those out, in the self.__validate_section_folder().

                    # See if it's a version invalid attribute
                    result, message = self._aliases.is_valid_model_attribute_name(validation_location, key)
                    if result == ValidationCodes.VERSION_INVALID:
                        self._log_version_invalid(message, _method_name)
                    elif result == ValidationCodes.INVALID:
                        # key is an INVALID attribute
                        self._logger.severe('WLSDPLY-05029', key, model_folder_path,
                                            '%s' % ', '.join(valid_attr_infos), class_name=_class_name,
                                            method_name=_method_name)

    def __validate_attributes(self, attributes_dict, valid_attr_infos, validation_location):
        _method_name = '__validate_attributes'

        self._logger.finest('validation_location={0}, attributes_dict={0}', str_helper.to_string(validation_location),
                            str_helper.to_string(attributes_dict),
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
            self.__validate_attribute(attribute_name, attribute_value, valid_attr_infos, path_tokens_attr_keys,
                                      model_folder_path, validation_location)

    def __validate_attribute(self, attribute_name, attribute_value, valid_attr_infos, path_tokens_attr_keys,
                             model_folder_path, validation_location):
        _method_name = '__validate_attribute'

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
                if not self._aliases.model_mbean_has_set_mbean_type_attribute_name(validation_location, attribute_name):
                    self._logger.warning('WLSDPLY-05017', attribute_name, model_folder_path, expected_data_type,
                                         actual_data_type, class_name=_class_name, method_name=_method_name)

            if attribute_name in path_tokens_attr_keys:
                self.__validate_path_tokens_attribute(attribute_name, attribute_value, model_folder_path)
        else:
            result, message = self._aliases.is_valid_model_attribute_name(validation_location, attribute_name)
            if result == ValidationCodes.VERSION_INVALID:
                self._log_version_invalid(message, _method_name)
            elif result == ValidationCodes.INVALID:
                self._logger.severe('WLSDPLY-05029', attribute_name, model_folder_path,
                                    '%s' % ', '.join(valid_attr_infos), class_name=_class_name,
                                    method_name=_method_name)

        self._logger.exiting(class_name=_class_name, method_name=_method_name)

    def __validate_properties(self, properties_dict, valid_prop_infos, validation_location):
        _method_name = '__validate_properties'

        self._logger.entering(str_helper.to_string(properties_dict), str_helper.to_string(validation_location),
                              class_name=_class_name, method_name=_method_name)

        for property_name, property_value in properties_dict.iteritems():
            valid_prop_infos[property_name] = validation_utils.get_python_data_type(property_value)
            self.__validate_property(property_name, property_value, valid_prop_infos, validation_location)

        self._logger.exiting(class_name=_class_name, method_name=_method_name)

    def __validate_property(self, property_name, property_value, valid_prop_infos, model_folder_path):

        _method_name = '__validate_property'

        self._logger.entering(property_name, property_value, str_helper.to_string(valid_prop_infos),
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

        self._logger.entering(tokenized_value, model_folder_path, class_name=_class_name, method_name=_method_name)
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
                        logger_method = _info_logger.info

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

        valid_valus_data_types = ['list', 'string', 'unicode']
        if value_data_type not in valid_valus_data_types:
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
                self.__validate_single_path_in_archive(item_path.strip(), attribute_name, model_folder_path)

    def __validate_single_path_in_archive(self, path, attribute_name, model_folder_path):
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
            # If the validate configuration allows unresolved archive references,
            # log INFO messages identifying missing entries, and allow validation to succeed.
            # Otherwise, log SEVERE messages that will cause validation to fail.
            log_method = self._logger.severe
            if self._validate_configuration.allow_unresolved_archive_references():
                log_method = _info_logger.info

            if self._archive_helper is not None:
                archive_has_file = self._archive_helper.contains_file_or_path(path)
                if not archive_has_file:
                    log_method('WLSDPLY-05024', attribute_name, model_folder_path, path,
                               self._archive_file_name, class_name=_class_name, method_name=_method_name)
            elif not self._model_context.is_remote() and not self._model_context.skip_archive():
                log_method('WLSDPLY-05025', attribute_name, model_folder_path, path,
                           class_name=_class_name, method_name=_method_name)
        else:
            tokens = validation_utils.extract_path_tokens(path)
            self._logger.finest('tokens={0}', str_helper.to_string(tokens),
                                class_name=_class_name, method_name=_method_name)
            # TODO(mwooten) - This would be a good place to validate any path token found...

            if not self._model_context.has_token_prefix(path):
                if not os.path.isabs(path):
                    self._logger.info('WLSDPLY-05031', attribute_name, model_folder_path, path,
                                      class_name=_class_name, method_name=_method_name)

    def __validate_top_field_extended(self, field_key, field_value, model_folder_path):
        """
        Perform additional validation on some top-level fields.
        :param field_key: the name of the field
        :param field_value: the value of the field
        :param model_folder_path: the model folder path, for logging
        :return:
        """
        if field_key == SERVER_GROUP_TARGETING_LIMITS or field_key == DYNAMIC_CLUSTER_SERVER_GROUP_TARGETING_LIMITS:
            self.__validate_server_group_targeting_limits(field_key, field_value, model_folder_path)

        elif field_key == WLS_ROLES:
            self.__validate_wlsroles_section(field_value)

    def __validate_server_group_targeting_limits(self, attribute_key, attribute_value, model_folder_path):
        """
        Verify that entries in the ServerGroupTargetingLimits and DynamicClusterServerGroupTargetingLimits are
        the correct types, and do not use tokens.
        :param attribute_key: the name of the attribute
        :param attribute_value: the value of the attribute
        :param model_folder_path: the model folder path, for logging
        """
        __method_name = '__validate_server_group_targeting_limits'
        self._logger.entering(attribute_key, attribute_value, model_folder_path, class_name=_class_name,
                              method_name=__method_name)

        if attribute_value is not None:
            if not isinstance(attribute_value, dict):
                self._logger.severe('WLSDPLY-05032', attribute_key, model_folder_path,
                                    str_helper.to_string(type(attribute_value)),
                                    class_name=_class_name, method_name=__method_name)
            else:
                model_folder_path += '/' + attribute_key
                for key, value in attribute_value.iteritems():
                    if type(key) is not str:
                        # Force the key to a string for any value validation issues reported below
                        key = str_helper.to_string(key)
                        self._logger.severe('WLSDPLY-05033', str_helper.to_string, model_folder_path,
                                            str_helper.to_string(type(key)),
                                            class_name=_class_name, method_name=__method_name)
                    else:
                        if variables.has_variables(key):
                            self._report_unsupported_variable_usage(key, model_folder_path)

                    if isinstance(value, basestring) and MODEL_LIST_DELIMITER in value:
                        value = value.split(MODEL_LIST_DELIMITER)

                    if type(value) is list:
                        for element in value:
                            self._validate_single_server_group_target_limits_value(key, element,
                                                                                   model_folder_path)
                    elif type(value) is str:
                        self._validate_single_server_group_target_limits_value(key, value, model_folder_path)
                    else:
                        self._logger.severe('WLSDPLY-05034', key, model_folder_path,
                                            str_helper.to_string(type(value)),
                                            class_name=_class_name, method_name=__method_name)

        self._logger.exiting(class_name=_class_name, method_name=__method_name)

    def _validate_single_server_group_target_limits_value(self, key, value, model_folder_path):
        _method_name = '_validate_single_server_group_target_limits_value'

        if type(value) in [unicode, str]:
            if variables.has_variables(str_helper.to_string(value)):
                self._report_unsupported_variable_usage(str_helper.to_string(value), model_folder_path)
        else:
            self._logger.severe('WLSDPLY-05035', key, str_helper.to_string(value), model_folder_path,
                                str_helper.to_string(type(value)),
                                class_name=_class_name, method_name=_method_name)

    def __validate_wlsroles_section(self, attribute_value):
        __method_name = '__validate_wlsroles_section'
        self._logger.entering(class_name=_class_name, method_name=__method_name)

        # Validate WebLogic role content using WLSRoles helper
        wlsroles_validator = wlsroles_helper.validator(attribute_value, self._logger)
        wlsroles_validator.validate_roles()

        self._logger.exiting(class_name=_class_name, method_name=__method_name)

    def _report_unsupported_variable_usage(self, tokenized_value, model_folder_path):
        _method_name = '_report_unsupported_variable_usage'
        tokens = variables.get_variable_names(tokenized_value)
        for token in tokens:
            self._logger.severe('WLSDPLY-05030', model_folder_path, token,
                                class_name=_class_name, method_name=_method_name)

    def _log_version_invalid(self, message, method_name):
        """
        Log a message indicating that an attribute is not valid for the current WLS version and WLST mode.
        Log INFO or WARNING, depending on validation mode.
        """
        log_method = self._logger.warning
        if self._validate_configuration.allow_version_invalid_attributes():
            log_method = _info_logger.info
        log_method('WLSDPLY-05027', message, class_name=_class_name, method_name=method_name)
