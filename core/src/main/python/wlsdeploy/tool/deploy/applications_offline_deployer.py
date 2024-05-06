"""
Copyright (c) 2017, 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import copy

from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import APPLICATION
from wlsdeploy.aliases.model_constants import LIBRARY
from wlsdeploy.aliases.model_constants import MODULE_TYPE
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

        self.logger.exiting(class_name=self._class_name, method_name=_method_name)

    def __deploy_shared_libraries(self):
        _method_name = '__deploy_shared_libraries'
        self.logger.entering(class_name=self._class_name, method_name=_method_name)

        shared_libraries = dictionary_utils.get_dictionary_element(self._parent_dict, LIBRARY)
        if len(shared_libraries) > 0:
            root_path = self.aliases.get_wlst_subfolders_path(self._base_location)
            shared_library_location = LocationContext(self._base_location).append_location(LIBRARY)
            shared_library_token = self.aliases.get_name_token(shared_library_location)

            for shared_library_name in shared_libraries:
                self.wlst_helper.cd(root_path)  # avoid cd to pwd that may contain slashed names
                existing_shared_libs = deployer_utils.get_existing_object_list(shared_library_location, self.aliases)

                if model_helper.is_delete_name(shared_library_name):
                    self.__delete_existing_deployment(existing_shared_libs, shared_library_name, 'lib')
                    continue

                self.logger.info('WLSDPLY-09301', LIBRARY, shared_library_name, self._parent_type, self._parent_name,
                                 class_name=self._class_name, method_name=_method_name)

                #
                # In WLST offline mode, the shared library name must match the fully qualified name, including
                # the spec and implementation versions from the deployment descriptor.  Since we want to allow
                # users to not tie the model to a specific release when deploying shared libraries shipped with
                # WebLogic, we have to go compute the required name and change the name in the model prior to
                # making changes to the domain.
                #
                shared_library = \
                    copy.deepcopy(dictionary_utils.get_dictionary_element(shared_libraries, shared_library_name))
                self._replace_path_tokens_for_deployment(LIBRARY, shared_library_name, shared_library)

                self.__validate_deployment_source_path(shared_library_name, LIBRARY, shared_library,
                                                       existing_shared_libs)
                self._extract_deployment_from_archive(shared_library_name, LIBRARY, shared_library)

                # If SourcePath is empty and hasn't caused an error, library_name will be shared_library_name.
                shlib_source_path = dictionary_utils.get_element(shared_library, SOURCE_PATH)
                library_name = \
                    self.version_helper.get_library_versioned_name(shlib_source_path, shared_library_name)
                # names are quoted/escaped later, when paths are resolved
                shared_library_location.add_name_token(shared_library_token, library_name)

                self.wlst_helper.cd(root_path)
                deployer_utils.create_and_cd(shared_library_location, existing_shared_libs, self.aliases)
                self.set_attributes(shared_library_location, shared_library)
                shared_library_location.remove_name_token(shared_library_token)
        else:
            self.logger.finer('WLSDPLY-09300', self._parent_type, self._parent_name,
                              class_name=self._class_name, method_name=_method_name)

        self.logger.exiting(class_name=self._class_name, method_name=_method_name)

    def __deploy_applications(self):
        _method_name = '__deploy_applications'
        self.logger.entering(class_name=self._class_name, method_name=_method_name)

        applications = dictionary_utils.get_dictionary_element(self._parent_dict, APPLICATION)
        if len(applications) > 0:
            root_path = self.aliases.get_wlst_subfolders_path(self._base_location)
            application_location = LocationContext(self._base_location).append_location(APPLICATION)
            application_token = self.aliases.get_name_token(application_location)

            for application_name in applications:
                self.wlst_helper.cd(root_path)  # avoid cd to pwd that may contain slashed names
                existing_apps = deployer_utils.get_existing_object_list(application_location, self.aliases)

                if model_helper.is_delete_name(application_name):
                    self.__delete_existing_deployment(existing_apps, application_name, 'app')
                    continue

                self.logger.info('WLSDPLY-09301', APPLICATION, application_name, self._parent_type, self._parent_name,
                                 class_name=self._class_name, method_name=_method_name)

                application = \
                    copy.deepcopy(dictionary_utils.get_dictionary_element(applications, application_name))
                self._replace_path_tokens_for_deployment(APPLICATION, application_name, application)

                self.__validate_deployment_source_path(application_name, APPLICATION, application, existing_apps)
                self._extract_deployment_from_archive(application_name, APPLICATION, application)

                # If SourcePath is empty and hasn't caused an error, library_name will be shared_library_name.
                app_source_path = dictionary_utils.get_element(application, SOURCE_PATH)
                module_type = dictionary_utils.get_element(application, MODULE_TYPE)
                application_name = self.version_helper.get_application_versioned_name(app_source_path, application_name,
                                                                                      module_type=module_type)
                # names are quoted/escaped later, when paths are resolved
                application_location.add_name_token(application_token, application_name)

                self.wlst_helper.cd(root_path)
                deployer_utils.create_and_cd(application_location, existing_apps, self.aliases)
                self._set_attributes_and_add_subfolders(application_location, application)

                self._substitute_appmodule_token(app_source_path, module_type)
                is_structured_app, __ = self._is_structured_app(application_name, application)
                if is_structured_app:
                    self._fixup_structured_app_plan_file_config_root(application_name, application)

                application_location.remove_name_token(application_token)
        else:
            self.logger.finer('WLSDPLY-09304', self._parent_type, self._parent_name,
                              class_name=self._class_name, method_name=_method_name)

        self.logger.exiting(class_name=self._class_name, method_name=_method_name)

    def __delete_existing_deployment(self, existing_deployment_names_list, deployment_name, deployment_type):
        _method_name = '__delete_existing_deployment'
        self.logger.entering(existing_deployment_names_list, deployment_name, deployment_type,
                             class_name=self._class_name, method_name=_method_name)

        if self._does_deployment_to_delete_exist(deployment_name, existing_deployment_names_list, deployment_type):
            location = LocationContext(self._base_location)
            if deployment_type == 'lib':
                location.append_location(LIBRARY)
            else:
                location.append_location(APPLICATION)

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
                    if deployment_type == LIBRARY:
                        key = 'WLSDPLY-09347'
                    else:
                        key = 'WLSDPLY-09348'
                    ex = exception_helper.create_deploy_exception(key, deployment_name, possible_matches)
                else:
                    ex = exception_helper.create_deploy_exception('WLSDPLY-09302', deployment_type,
                                                                  deployment_name, SOURCE_PATH)
                self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                raise ex

        self.logger.exiting(class_name=self._class_name, method_name=_method_name)
