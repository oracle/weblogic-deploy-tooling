"""
Copyright (c) 2017, 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import copy
from java.util.logging import Level
from oracle.weblogic.deploy.logging import WLSDeployLogEndHandler
from oracle.weblogic.deploy.util import VariableException

from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import KNOWN_TOPLEVEL_MODEL_SECTIONS
from wlsdeploy.aliases.model_constants import NAME
from wlsdeploy.aliases.model_constants import TOPOLOGY
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception import exception_helper
from wlsdeploy.exception.exception_types import ExceptionType
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.util.archive_helper import ArchiveList
from wlsdeploy.tool.validate.crd_sections_validator import CrdSectionsValidator
from wlsdeploy.tool.validate.deployments_validator import DeploymentsValidator
from wlsdeploy.tool.validate.domain_info_validator import DomainInfoValidator
from wlsdeploy.tool.validate.model_validator import ModelValidator
from wlsdeploy.util import dictionary_utils
from wlsdeploy.util import model
from wlsdeploy.util import path_helper
from wlsdeploy.util import variables
from wlsdeploy.util.enum import Enum

_class_name = 'Validator'
_logger = PlatformLogger('wlsdeploy.validate')

_ValidationModes = Enum(['STANDALONE', 'TOOL'])


class Validator(object):
    """
    Class for validating a model file and printing the metadata used in it
    """
    ValidationStatus = Enum(['VALID', 'INFOS_VALID', 'WARNINGS_INVALID', 'INVALID'])
    ReturnCode = Enum(['PROCEED', 'STOP'])

    def __init__(self, model_context, aliases, wlst_mode=None, validate_crd_sections=True):
        """
        Create a validator instance.
        :param model_context: used to get command-line options
        :param aliases: used to validate folders, attributes. also determines exception type
        :param wlst_mode: online or offline mode
        :param validate_crd_sections: True if CRD sections (such as kubernetes) should be validated
        """
        self._model_context = model_context

        self._logger = _logger
        self._validation_mode = None
        self._variable_properties = {}
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

        self._archive_helper = None
        self._archive_file_name = None
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
        self._logger.entering(archive_file_name, class_name=_class_name, method_name=_method_name)

        # If standalone, log file will not be passed, so get a new logger with correct mode type
        self._validation_mode = _ValidationModes.STANDALONE

        return_code = self.__run_validation(model_dict, variable_map, archive_file_name)

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
        self._logger.entering(variables_file_name, archive_file_name, class_name=_class_name,
                              method_name=_method_name)

        self._validation_mode = _ValidationModes.TOOL
        variable_map = self.load_variables(variables_file_name)

        return_code = self.__run_validation(model_dict, variable_map, archive_file_name)

        self._logger.exiting(class_name=_class_name, method_name=_method_name, result=return_code)
        return return_code

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

    ####################################################################################
    #
    # Private methods, private inner classes and static methods only, beyond here please
    #
    ####################################################################################

    def __run_validation(self, model_dict, variable_map, archive_file_name):
        """
        Run validation and determine the return code based on the summary handler logging
        :param model_dict: model dictionary to be validated
        :param variable_map: variable map to use
        :param archive_file_name: name of the archive file, or None
        :return: the return code PROCEED or STOP
        """
        # We need to make a deep copy of model_dict here, to ensure it's
        # treated as a "read-only'" reference variable, during the variable
        # file validation process. The variable file validation process could
        # actually require changes to be made to the cloned model dictionary
        cloned_model_dict = copy.deepcopy(model_dict)

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

        return_code = Validator.ReturnCode.STOP
        if status == Validator.ValidationStatus.VALID or status == Validator.ValidationStatus.INFOS_VALID \
                or status == Validator.ValidationStatus.WARNINGS_INVALID:
            return_code = Validator.ReturnCode.PROCEED

        return return_code

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
            # self._archive_entries = self._archive_helper.get_archive_entries()
            # TODO(mwooten) - this would be a good place to validate the structure of the archive.  If we are
            # not going to validate the structure and only validate things referenced by the model, then no
            # need to load the archive_entries variable because it is not being used.

        self.__validate_root_level(model_dict)

        domain_info_validator = DomainInfoValidator(variables_map, self._archive_helper, self._validation_mode,
                                                    self._model_context, self._aliases, self._wlst_mode)

        domain_info_validator.validate(model_dict)

        base_validator = ModelValidator(variables_map, self._archive_helper, self._validation_mode,
                                        self._model_context, self._aliases, self._wlst_mode)

        base_validator.validate_model_section(model.get_model_topology_key(), model_dict,
                                              self._aliases.get_model_topology_top_level_folder_names())

        base_validator.validate_model_section(model.get_model_resources_key(), model_dict,
                                              self._aliases.get_model_resources_top_level_folder_names())

        deployments_validator = DeploymentsValidator(variables_map, self._archive_helper, self._validation_mode,
                                                     self._model_context, self._aliases, self._wlst_mode)

        deployments_validator.validate(model_dict)

        if self._validate_crd_sections:
            k8s_validator = CrdSectionsValidator(self._model_context)
            k8s_validator.validate_model(model_dict)

        self._logger.exiting(class_name=_class_name, method_name=_method_name)

    def __validate_root_level(self, model_dict):
        _method_name = '__validate_root_level'

        # Get list of root level keys from model_dict
        valid_root_level_keys = KNOWN_TOPLEVEL_MODEL_SECTIONS
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

    def __pre_validation_setup(self, model_dict, archive_file_name):
        """
        Performs pre-validation setup activities. These include things like:

            1.  Obtaining the domain name using either the WebLogicHelper object,
                parameter passed to the constructor or the model context object.
            2.  Creating an ArchiveList object, which serves as a facade for
                multiple Archive objects.

        :param model_dict: A Python dictionary of the model to be validated
        :param archive_file_name: Path to file containing binaries associated with the model file.
        :return: Nothing.
        """
        topology_dict = dictionary_utils.get_dictionary_element(model_dict, TOPOLOGY)
        domain_name = dictionary_utils.get_element(topology_dict, NAME)

        if domain_name is None:
            domain_name = self._wls_helper.get_default_wls_domain_name()

        if domain_name is not None:
            self._name_tokens_location.add_name_token('DOMAIN', domain_name)

        if archive_file_name is not None:
            self._archive_file_name = archive_file_name
            self._archive_helper = ArchiveList(self._archive_file_name, self._model_context, ExceptionType.VALIDATE)
