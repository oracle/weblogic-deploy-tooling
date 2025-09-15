"""
Copyright (c) 2017, 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import copy

from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import APPLICATION
from wlsdeploy.aliases.model_constants import DB_CLIENT_DATA_DIRECTORY
from wlsdeploy.aliases.model_constants import LIBRARY
from wlsdeploy.aliases.model_constants import MODULE_TYPE
from wlsdeploy.aliases.model_constants import PLUGIN_DEPLOYMENT
from wlsdeploy.aliases.model_constants import SOURCE_PATH
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception import exception_helper
from wlsdeploy.tool.deploy import deployer_utils
from wlsdeploy.tool.deploy.applications_deployer import ApplicationsDeployer
from wlsdeploy.util import dictionary_utils
from wlsdeploy.util import model_helper
from wlsdeploy.util import string_utils


class OfflineApplicationsDeployer(ApplicationsDeployer):

    def __init__(self, model, model_context, aliases, base_location=LocationContext()):
        ApplicationsDeployer.__init__(self, model, model_context, aliases, WlstModes.OFFLINE, base_location)
        self._class_name = 'OfflineApplicationsDeployer'

    def deploy(self, _is_restart_required):
        _method_name = 'deploy'
        self.logger.entering(self._parent_name, self._parent_type, _is_restart_required,
                             class_name=self._class_name, method_name=_method_name)

        self.__deploy_shared_libraries()
        self.__deploy_applications()
        self.__deploy_db_client_data()

        self.logger.exiting(class_name=self._class_name, method_name=_method_name)

    def deploy_plugins(self):
        """
        Deploy PluginDeployment elements from the model. These need to be deployed before SecurityConfiguration,
        so they are not included in OfflineApplicationsDeployer.deploy()
        """
        self.__update_deployments(PLUGIN_DEPLOYMENT)

    def __deploy_shared_libraries(self):
        self.__update_deployments(LIBRARY)

    def __deploy_applications(self):
        self.__update_deployments(APPLICATION)

    def __deploy_db_client_data(self):
        self.__update_deployments(DB_CLIENT_DATA_DIRECTORY)

    def __update_deployments(self, deployment_type):
        _method_name = '__update_deployments'
        self.logger.entering(deployment_type, class_name=self._class_name, method_name=_method_name)

        deployments = dictionary_utils.get_dictionary_element(self._parent_dict, deployment_type)
        if len(deployments) > 0:
            deployments_location = LocationContext(self._base_location).append_location(deployment_type)
            if not self.aliases.is_model_location_valid(deployments_location):
                return

            root_path = self.aliases.get_wlst_subfolders_path(self._base_location)
            deployments_token = self.aliases.get_name_token(deployments_location)

            for deployment_name in deployments:
                self.wlst_helper.cd(root_path)  # avoid cd to pwd that may contain slashed names
                existing_deployments = deployer_utils.get_existing_object_list(deployments_location, self.aliases)

                if model_helper.is_delete_name(deployment_name):
                    self.__delete_existing_deployment(existing_deployments, deployment_name, deployment_type)
                    continue

                self.logger.info('WLSDPLY-09301', deployment_type, deployment_name, self._parent_type,
                                 self._parent_name, class_name=self._class_name, method_name=_method_name)

                #
                # In WLST offline mode, the deployment name must match the fully qualified name, including
                # the spec and implementation versions from the deployment descriptor. Since we want to allow
                # users to not tie the model to a specific release when deploying items shipped with
                # WebLogic, we have to go compute the required name and change the name in the model prior to
                # making changes to the domain.
                #
                deployment = copy.deepcopy(dictionary_utils.get_dictionary_element(deployments, deployment_name))

                self._replace_path_tokens_for_deployment(deployment_type, deployment_name, deployment)

                self.__validate_deployment_source_path(deployment_name, deployment_type, deployment,
                                                       existing_deployments)

                if deployment_type != DB_CLIENT_DATA_DIRECTORY:  # wallets were already extracted
                    self._extract_deployment_from_archive(deployment_name, deployment_type, deployment)

                # If SourcePath is empty and hasn't caused an error, deployment_name will be unchanged.
                source_path = dictionary_utils.get_element(deployment, SOURCE_PATH)
                module_type = dictionary_utils.get_element(deployment, MODULE_TYPE)
                deployment_name = self._get_versioned_name(source_path, deployment_name, deployment_type, module_type)

                # names are quoted/escaped later, when paths are resolved
                deployments_location.add_name_token(deployments_token, deployment_name)

                self.wlst_helper.cd(root_path)
                deployer_utils.create_and_cd(deployments_location, existing_deployments, self.aliases)
                self._set_attributes_and_add_subfolders(deployments_location, deployment)

                if deployment_type == APPLICATION:
                    self._substitute_appmodule_token(source_path, module_type)
                    is_structured_app, __ = self._is_structured_app(deployment_name, deployment)
                    if is_structured_app:
                        self._fixup_structured_app_plan_file_config_root(deployment_name, deployment)

                deployments_location.remove_name_token(deployments_token)
        else:
            self.logger.finer('WLSDPLY-09357', deployment_type, self._parent_type, self._parent_name,
                              class_name=self._class_name, method_name=_method_name)

        self.logger.exiting(class_name=self._class_name, method_name=_method_name)

    def __delete_existing_deployment(self, existing_deployment_names_list, deployment_name, deployment_type):
        _method_name = '__delete_existing_deployment'
        self.logger.entering(existing_deployment_names_list, deployment_name, deployment_type,
                             class_name=self._class_name, method_name=_method_name)

        if self._does_deployment_to_delete_exist(deployment_name, existing_deployment_names_list, deployment_type):
            location = LocationContext(self._base_location)
            location.append_location(deployment_type)

            deployer_utils.delete_named_element(location, deployment_name, existing_deployment_names_list, self.aliases)

        self.logger.exiting(class_name=self._class_name, method_name=_method_name)

    def __validate_deployment_source_path(self, deployment_name, deployment_type, deployment_dict,
                                          existing_deployment_names):
        _method_name = '__validate_deployment_source_path'
        self.logger.entering(deployment_name, deployment_type, deployment_dict, existing_deployment_names,
                             class_name=self._class_name, method_name=_method_name)

        #
        # Any model-defined deployment the SourcePath requires that the deployment is already deployed.
        # Since we need the deployment descriptor to determine the actual name of the deployment,
        # we have a Catch-22 situation...for now, we simply reject an empty SourcePath if the deployment name
        # does not have an exact match in the existing deployments that are already deployed.
        #
        deployment_source_path = dictionary_utils.get_element(deployment_dict, SOURCE_PATH)
        if string_utils.is_empty(deployment_source_path):
            found_exact_match = False
            possible_matches = list()
            deployment_pattern = '%s#' % deployment_name
            for existing_deployment_name in existing_deployment_names:
                if existing_deployment_name == deployment_name:
                    found_exact_match = True
                    break
                elif existing_deployment_name.startswith(deployment_pattern):
                    possible_matches.append(existing_deployment_name)
            if not found_exact_match:
                if len(possible_matches) > 0:
                    ex = exception_helper.create_deploy_exception(
                        "WLSDPLY-09358", deployment_type, deployment_name, SOURCE_PATH, ', '.join(possible_matches))
                else:
                    ex = exception_helper.create_deploy_exception('WLSDPLY-09302', deployment_type,
                                                                  deployment_name, SOURCE_PATH)
                self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                raise ex

        self.logger.exiting(class_name=self._class_name, method_name=_method_name)
