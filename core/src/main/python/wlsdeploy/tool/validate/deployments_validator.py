"""
Copyright (c) 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""

from oracle.weblogic.deploy.util import WLSDeployArchive

from wlsdeploy.aliases.model_constants import APPLICATION
from wlsdeploy.aliases.model_constants import APP_DEPLOYMENTS
from wlsdeploy.aliases.model_constants import LIBRARY
from wlsdeploy.aliases.model_constants import PLAN_DIR
from wlsdeploy.aliases.model_constants import PLAN_PATH
from wlsdeploy.aliases.model_constants import SOURCE_PATH
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.validate.model_validator import ModelValidator
from wlsdeploy.util import dictionary_utils
from wlsdeploy.util import variables

_class_name = 'DeploymentsValidator'
_logger = PlatformLogger('wlsdeploy.validate')

ARCHIVE_APPS_PREFIX = WLSDeployArchive.ARCHIVE_APPS_TARGET_DIR + WLSDeployArchive.ZIP_SEP
ARCHIVE_SHLIBS_PREFIX = WLSDeployArchive.ARCHIVE_SHLIBS_TARGET_DIR + WLSDeployArchive.ZIP_SEP
ARCHIVE_STRUCT_APPS_PREFIX = WLSDeployArchive.ARCHIVE_STRUCT_APPS_TARGET_DIR + WLSDeployArchive.ZIP_SEP


class DeploymentsValidator(ModelValidator):
    """
    Class for validating the appDeployments section of a model file
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
        ModelValidator.__init__(self, variables_map, archive_helper, validation_mode, model_context, aliases,
                                wlst_mode)

    def validate(self, model_dict):
        """
        Validate the app deployments section of the model.
        :param model_dict: the top-level model dictionary
        """
        self.validate_model_section(APP_DEPLOYMENTS, model_dict,
                                    self._aliases.get_model_app_deployments_top_level_folder_names())

    # Override
    def _validate_folder_content(self, model_node, validation_location):
        """
        Override this method to validate combined PlanDir and PlanPath, if both are present.
        """
        ModelValidator._validate_folder_content(self, model_node, validation_location)

        plan_path = dictionary_utils.get_element(model_node, PLAN_PATH)
        if plan_path:
            plan_path = variables.substitute_key(plan_path, self._variable_properties)
            model_folder_path = self._aliases.get_model_folder_path(validation_location)

            plan_dir = dictionary_utils.get_element(model_node, PLAN_DIR)
            if plan_dir:
                plan_dir = variables.substitute_key(plan_dir, self._variable_properties)
                combined_path = '%s/%s' % (plan_dir, plan_path)
                combined_name = '%s+%s' % (PLAN_DIR, PLAN_PATH)  # attribute name for logging
                self._validate_single_path_in_archive(combined_path, combined_name, model_folder_path)
                self.__validate_deployment_path(combined_path, combined_name, validation_location)
            else:
                # call the superclass method, method in this class intentionally skips this attribute
                ModelValidator._validate_single_path_in_archive(self, plan_path, PLAN_PATH, model_folder_path)
                self.__validate_deployment_path(plan_path, PLAN_PATH, validation_location)

    # Override
    def _validate_attribute(self, attribute_name, attribute_value, valid_attr_infos, path_tokens_attr_keys,
                            model_folder_path, validation_location):
        """
        Extend this method to verify that archive source paths have prescribed directory names.
        """
        ModelValidator._validate_attribute(self, attribute_name, attribute_value, valid_attr_infos,
                                           path_tokens_attr_keys, model_folder_path, validation_location)

        if attribute_name == SOURCE_PATH:
            source_path = variables.substitute_key(attribute_value, self._variable_properties)
            self.__validate_deployment_path(source_path, SOURCE_PATH, validation_location)

    # Override
    def _validate_single_path_in_archive(self, path, attribute_name, model_folder_path):
        """
        Override superclass method exclude PlanPath from validation.
        This is handled in tandem with optional PlanDir in _process_model_node.
        :param path: the path to be checked
        :param attribute_name: the name of the attribute to be checked
        :param model_folder_path: the model folder path, used for logging
        """
        if attribute_name != PLAN_PATH:
            ModelValidator._validate_single_path_in_archive(self, path, attribute_name, model_folder_path)

    def __validate_deployment_path(self, deployment_path, attribute_name, location):
        """
        Verify that an archive source or plan path has a prescribed directory name.
        :param deployment_path: the path to be validated
        :param attribute_name: the attribute name, for logging only
        :param location: the model location, for logging
        """
        if WLSDeployArchive.isPathIntoArchive(deployment_path):
            deployment_type = location.get_current_model_folder()
            model_folder_path = self._aliases.get_model_folder_path(location)

            if deployment_type == APPLICATION:
                if not deployment_path.startswith(ARCHIVE_APPS_PREFIX) and \
                        not deployment_path.startswith(ARCHIVE_STRUCT_APPS_PREFIX):
                    self._logger.severe('WLSDPLY-05241', attribute_name, deployment_path, model_folder_path,
                                        ARCHIVE_APPS_PREFIX, ARCHIVE_STRUCT_APPS_PREFIX)

            if deployment_type == LIBRARY:
                if not deployment_path.startswith(ARCHIVE_SHLIBS_PREFIX):
                    self._logger.severe('WLSDPLY-05240', attribute_name, deployment_path, model_folder_path,
                                        ARCHIVE_SHLIBS_PREFIX)
