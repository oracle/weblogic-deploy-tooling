"""
Copyright (c) 2017, 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import copy
import os.path

from sets import Set

from java.io import File
from java.io import IOException
from java.security import NoSuchAlgorithmException
from oracle.weblogic.deploy.util import FileUtils
from oracle.weblogic.deploy.util import PyOrderedDict as OrderedDict

from wlsdeploy.aliases import alias_utils
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import ABSOLUTE_PLAN_PATH
from wlsdeploy.aliases.model_constants import ABSOLUTE_SOURCE_PATH
from wlsdeploy.aliases.model_constants import APPLICATION
from wlsdeploy.aliases.model_constants import DEPLOYMENT_ORDER
from wlsdeploy.aliases.model_constants import LIBRARY
from wlsdeploy.aliases.model_constants import MODULE_TYPE
from wlsdeploy.aliases.model_constants import PARTITION
from wlsdeploy.aliases.model_constants import PLAN_DIR
from wlsdeploy.aliases.model_constants import PLAN_PATH
from wlsdeploy.aliases.model_constants import PLAN_STAGING_MODE
from wlsdeploy.aliases.model_constants import RESOURCE_GROUP
from wlsdeploy.aliases.model_constants import RESOURCE_GROUP_TEMPLATE
from wlsdeploy.aliases.model_constants import SECURITY_DD_MODEL
from wlsdeploy.aliases.model_constants import SOURCE_PATH
from wlsdeploy.aliases.model_constants import STAGE_MODE
from wlsdeploy.aliases.model_constants import SUB_DEPLOYMENT
from wlsdeploy.aliases.model_constants import SUB_MODULE_TARGETS
from wlsdeploy.aliases.model_constants import TARGET
from wlsdeploy.aliases.model_constants import TARGETS
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception import exception_helper
from wlsdeploy.tool.deploy import deployer_utils
from wlsdeploy.tool.deploy.applications_deployer import ApplicationsDeployer
from wlsdeploy.util import dictionary_utils
from wlsdeploy.util import model_helper
from wlsdeploy.util import string_utils
from wlsdeploy.util import unicode_helper as str_helper


class OnlineApplicationsDeployer(ApplicationsDeployer):

    def __init__(self, model, model_context, aliases, base_location=LocationContext()):
        ApplicationsDeployer.__init__(self, model, model_context, aliases, WlstModes.ONLINE, base_location)
        self._class_name = 'OnlineApplicationsDeployer'

    def deploy(self, is_restart_required=False):
        """
        Deploy the libraries and applications from the model

        :param is_restart_required: is the server in a state where restart is required?
        :raises: DeployException: if an error occurs
        """
        _method_name = 'deploy'
        self.logger.entering(self._parent_name, self._parent_type, is_restart_required,
                             class_name=self._class_name, method_name=_method_name)

        # Make copies of the model dictionary since we are going
        # to modify it as we build the deployment strategy.
        #
        model_shared_libraries = copy.deepcopy(dictionary_utils.get_dictionary_element(self._parent_dict, LIBRARY))
        self._replace_deployments_path_tokens(LIBRARY, model_shared_libraries)
        model_applications = copy.deepcopy(dictionary_utils.get_dictionary_element(self._parent_dict, APPLICATION))
        self._replace_deployments_path_tokens(APPLICATION, model_applications)

        if len(model_shared_libraries) == 0 and len(model_applications) == 0:
            # Nothing to do...
            return

        existing_app_refs = self.__get_existing_apps()
        existing_lib_refs = self.__get_existing_library_references()

        # applications to be stopped and undeployed
        stop_and_undeploy_app_list = list()
        # libraries to be undeployed
        update_library_list = list()

        lib_location = LocationContext(self._base_location).append_location(LIBRARY)
        # Go through the model libraries and find existing libraries that are referenced
        # by applications and compute a processing strategy for each library.
        self.__build_library_deploy_strategy(lib_location, model_shared_libraries,
                                             existing_lib_refs, update_library_list)

        # Go through the model applications and compute the processing strategy for each application.
        app_location = LocationContext(self._base_location).append_location(APPLICATION)
        self.__build_app_deploy_strategy(app_location, model_applications, existing_app_refs,
                                         stop_and_undeploy_app_list)

        #  For in-place update of shared libraries (i.e. impl/spec versions are not updated in the MANIFEST.MF for
        #   update), trying to do so will result in error just like the console.
        #
        # we will not automatically detect the referencing app and try to figure out the dependency graph and orders
        # for undeploying apps.
        #
        #   1.  It needs to be fully undeploy shared library referenced apps
        #   2.  But if the user only provides a sparse model for library update, the sparse model will not have the
        #   original app, and it will not be deployed again
        #   3.  There maybe transitive references by shared library, and it will be difficult to handle processing order
        #    the full dependency graph
        #   4.  Console will result in error and ask user to undeploy the app first, so we are not trying to add new
        #   functionalities in wls.
        #

        # user provide new versioned app, it must be stopped and undeployed first
        for app in stop_and_undeploy_app_list:
            self.__stop_app(app)
            self.__undeploy_app(app)
            self.__delete_deployment_on_server(app, model_applications[app])

        # library is updated, it must be undeployed first
        for lib in update_library_list:
            self.__undeploy_app(lib, library_module='true')
            self.__delete_deployment_on_server(lib, model_shared_libraries[lib])

        self.__deploy_model_libraries(model_shared_libraries, lib_location)

        # deployed_app_list is list of apps that has been deployed and started again
        deployed_app_list = self.__deploy_model_applications(model_applications, app_location)

        self.__start_all_apps(deployed_app_list, self._base_location, is_restart_required)

        self.logger.exiting(class_name=self._class_name, method_name=_method_name)

    # Override
    def _extract_directory_from_archive(self, directory_path, deployment_name, deployment_type):
        """
        Extract the specified directory path from the archive.
        Extend for online to extract for SSH or remote.
        """
        _method_name = '_extract_directory_from_archive'

        # directory cannot be used for remote upload
        if self.model_context.is_remote():
            ex = exception_helper.create_deploy_exception(
                'WLSDPLY-09341',deployment_type, deployment_name, directory_path)
            self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex
        elif self.model_context.is_ssh():
            self.archive_helper.extract_directory(directory_path, location=self.upload_temporary_dir)
            self.upload_deployment_to_remote_server(directory_path, self.upload_temporary_dir)
        else:
            ApplicationsDeployer._extract_directory_from_archive(
                self, directory_path, deployment_name, deployment_type)

    # Override
    def _extract_file_from_archive(self, file_path, deployment_name, deployment_type):
        """
        Extract the specified file path from the archive.
        Extend for online to extract for SSH or remote.
        """
        if self.model_context.is_remote():
            self.archive_helper.extract_file(file_path, self.upload_temporary_dir, False)
        elif self.model_context.is_ssh():
            self.archive_helper.extract_file(file_path, self.upload_temporary_dir, False)
            self.upload_deployment_to_remote_server(file_path, self.upload_temporary_dir)
        else:
            ApplicationsDeployer._extract_file_from_archive(self, file_path, deployment_name, deployment_type)

    ###########################################################################
    #                      Get existing deployments                           #
    ###########################################################################

    def __get_existing_apps(self):
        """
        Getting the details of existing applications including hash values of the app and plan.
        :return: dictionary containing the details about the existing applications
        """
        _method_name = '__get_existing_apps'
        self.logger.entering(class_name=self._class_name, method_name=_method_name)

        ref_dictionary = OrderedDict()
        location = LocationContext(self._base_location).append_location(APPLICATION)
        wlst_list_path = self.aliases.get_wlst_list_path(location)
        token_name = self.aliases.get_name_token(location)

        self.wlst_helper.server_config()
        self.wlst_helper.cd(wlst_list_path)
        apps = self.wlst_helper.get_existing_object_list(wlst_list_path)

        self.wlst_helper.domain_runtime()
        #
        # Cannot use ApplicationRuntime since it includes datasources as ApplicationRuntimes
        #
        running_apps = self.wlst_helper.get('/AppRuntimeStateRuntime/AppRuntimeStateRuntime/ApplicationIds')
        self.wlst_helper.server_config()

        try:
            local_download_root = FileUtils.createTempDirectory("wdt-downloadtemp").getAbsolutePath()
        except IOException, e:
            ex = exception_helper.create_deploy_exception('WLSDPLY-06161', e.getLocalizedMessage(), error=e)
            self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

        for app in apps:
            if running_apps is not None and app in running_apps:
                if self.model_context.get_domain_typedef().is_filtered(location, app):
                    continue

                app_location = LocationContext(location).add_name_token(token_name, app)

                wlst_attributes_path = self.aliases.get_wlst_attributes_path(app_location)
                self.wlst_helper.cd(wlst_attributes_path)
                attributes_map = self.wlst_helper.lsa()
                absolute_source_path = self.__compute_absolute_source_path(attributes_map)
                absolute_plan_path = self.__compute_absolute_plan_path(attributes_map)
                deployment_order = dictionary_utils.get_element(attributes_map, DEPLOYMENT_ORDER)
                config_targets = self._get_config_targets()

                app_hash, plan_hash = \
                    self.__get_app_and_plan_hash(absolute_source_path, absolute_plan_path, local_download_root)
                _update_ref_dictionary(ref_dictionary, app, absolute_source_path, app_hash, config_targets,
                                       absolute_plan_path=absolute_plan_path, deploy_order=deployment_order,
                                       plan_hash=plan_hash)

        self.logger.exiting(class_name=self._class_name, method_name=_method_name, result=ref_dictionary.keys())
        return ref_dictionary

    def __get_existing_library_references(self):
        """
        Get shared library references.

        :return: dictionary of the referenced library details
        """
        _method_name = '__get_existing_library_references'
        self.logger.entering(class_name=self._class_name, method_name=_method_name)

        existing_libraries = OrderedDict()
        location = LocationContext(self._base_location).append_location(LIBRARY)
        token_name = self.aliases.get_name_token(location)

        # In 12.1.3 and older release this internal library is accidentally exposed in LibraryRuntimes mbean
        #
        internal_skip_list = ['bea_wls_async_response']

        self.wlst_helper.domain_runtime()
        server_runtime_path = '/ServerRuntimes/'
        server_runtimes = self.wlst_helper.get_existing_object_list(server_runtime_path)

        for server_runtime in server_runtimes:
            library_runtime_path = server_runtime_path + server_runtime + '/LibraryRuntimes/'

            self.wlst_helper.domain_runtime()
            libs = self.wlst_helper.get_existing_object_list(library_runtime_path)
            for lib in libs:
                if lib in internal_skip_list or self.model_context.get_domain_typedef().is_filtered(location, lib):
                    continue
                self.__get_library_reference_attributes(existing_libraries, lib, library_runtime_path, location,
                                                        token_name)

        self.logger.exiting(class_name=self._class_name, method_name=_method_name, result=existing_libraries.keys())
        return existing_libraries

    def __get_library_reference_attributes(self, existing_libraries, lib, library_runtime_path, location, token_name):
        _method_name = '__get_library_reference_attributes'
        self.logger.entering(existing_libraries.keys(), lib, library_runtime_path, str_helper.to_string(location),
                             token_name, class_name=self._class_name, method_name=_method_name)

        self.wlst_helper.domain_runtime()
        self.wlst_helper.cd(library_runtime_path + lib)
        runtime_attributes = self.wlst_helper.lsa()

        lib_location = LocationContext(location).add_name_token(token_name, lib)
        wlst_attributes_path = self.aliases.get_wlst_attributes_path(lib_location)

        self.wlst_helper.server_config()
        self.wlst_helper.cd(wlst_attributes_path)
        config_attributes = self.wlst_helper.lsa()
        config_targets = self._get_config_targets()

        # There are case in application where absolute source path is not set but sourepath is
        # if source path is not absolute then we need to add the domain path
        absolute_source_path = self.__compute_absolute_source_path(config_attributes)
        deployment_order = dictionary_utils.get_element(config_attributes, DEPLOYMENT_ORDER)

        if self.model_context.is_remote() or self.model_context.is_ssh():
            lib_hash = None
        else:
            lib_hash = self.__get_file_hash(absolute_source_path)

        if string_utils.to_boolean(runtime_attributes['Referenced']) is True:
            referenced_path = library_runtime_path + lib + '/ReferencingRuntimes/'

            self.wlst_helper.domain_runtime()
            referenced_by = self.wlst_helper.get_existing_object_list(referenced_path)
            self.wlst_helper.cd(referenced_path)

            for app_ref in referenced_by:
                # TODO(rpatrick) - what if it is partitioned?
                ref_attrs = self.wlst_helper.lsa(app_ref)
                app_type = ref_attrs['Type']
                app_id = None
                if app_type == 'ApplicationRuntime' and 'ApplicationName' in ref_attrs:
                    app_id = dictionary_utils.get_element(ref_attrs, 'ApplicationName')
                elif app_type == 'WebAppComponentRuntime' and 'ApplicationIdentifier' in ref_attrs:
                    app_id = ref_attrs['ApplicationIdentifier']

                _update_ref_dictionary(existing_libraries, lib, absolute_source_path, lib_hash, config_targets,
                                       deploy_order=deployment_order, app_name=app_id)
        else:
            _update_ref_dictionary(existing_libraries, lib, absolute_source_path, lib_hash, config_targets)

        self.logger.exiting(class_name=self._class_name, method_name=_method_name)

    def __compute_absolute_source_path(self, attributes_map):
        _method_name = '__compute_absolute_source_path'
        self.logger.entering(attributes_map, class_name=self._class_name, method_name=_method_name)

        absolute_source_path = dictionary_utils.get_element(attributes_map, ABSOLUTE_SOURCE_PATH)
        if string_utils.is_empty(absolute_source_path):
            absolute_source_path = dictionary_utils.get_element(attributes_map, SOURCE_PATH)

        if not string_utils.is_empty(absolute_source_path) and self.path_helper.is_relative_path(absolute_source_path):
            absolute_source_path = self.path_helper.join(self.model_context.get_domain_home(), absolute_source_path)

        self.logger.exiting(class_name=self._class_name, method_name=_method_name, result = absolute_source_path)
        return absolute_source_path

    def __compute_absolute_plan_path(self, attributes_map):
        _method_name = '__compute_absolute_plan_path'
        self.logger.entering(attributes_map, class_name=self._class_name, method_name=_method_name)

        absolute_plan_path = dictionary_utils.get_element(attributes_map, ABSOLUTE_PLAN_PATH)
        if string_utils.is_empty(absolute_plan_path):
            absolute_plan_path = dictionary_utils.get_element(attributes_map, PLAN_PATH)

            if not string_utils.is_empty(absolute_plan_path):
                plan_dir = dictionary_utils.get_element(attributes_map, PLAN_DIR)

                if not string_utils.is_empty(plan_dir) and self.path_helper.is_relative_path(absolute_plan_path):
                    absolute_plan_path = self.path_helper.join(plan_dir, absolute_plan_path)

        if not string_utils.is_empty(absolute_plan_path) and self.path_helper.is_relative_path(absolute_plan_path):
            absolute_plan_path = self.path_helper.join(self.model_context.get_domain_home(), absolute_plan_path)

        self.logger.exiting(class_name=self._class_name, method_name=_method_name, result = absolute_plan_path)
        return absolute_plan_path

    def __get_app_and_plan_hash(self, absolute_source_path, absolute_plan_path, local_download_root):
        _method_name = '__get_app_and_plan_hash'
        self.logger.entering(absolute_source_path, absolute_plan_path, local_download_root,
                             class_name=self._class_name, method_name=_method_name)

        app_hash = None
        plan_hash = None
        if self.model_context.is_ssh():
            local_download_app_path = \
                self.path_helper.download_file_from_remote_server(self.model_context, absolute_source_path,
                                                                  local_download_root, 'apps')
            local_download_plan_path = \
                self.path_helper.download_file_from_remote_server(self.model_context, absolute_plan_path,
                                                                  local_download_root, 'plans')
            if local_download_app_path:
                app_hash = self.__get_file_hash(local_download_app_path)
            if local_download_plan_path:
                plan_hash = self.__get_file_hash(local_download_plan_path)
        elif not self.model_context.is_remote():
            app_hash = self.__get_file_hash(absolute_source_path)
            if absolute_plan_path is not None:
                plan_hash = self.__get_file_hash(absolute_plan_path)
            else:
                plan_hash = None

        self.logger.exiting(class_name=self._class_name, method_name=_method_name, result=[app_hash, plan_hash])
        return app_hash, plan_hash

    def _get_config_targets(self):
        self.wlst_helper.cd(TARGETS)
        config_targets = self.wlst_helper.lsc()
        self.wlst_helper.cd('..')
        return config_targets

    def _get_mt_names_from_location(self, app_location):
        dummy_location = LocationContext()
        token_name = self.aliases.get_name_token(dummy_location)
        dummy_location.add_name_token(token_name, self.model_context.get_domain_name())

        dummy_location.append_location(RESOURCE_GROUP_TEMPLATE)
        token_name = self.aliases.get_name_token(dummy_location)
        resource_group_template_name = app_location.get_name_for_token(token_name)
        dummy_location.pop_location()

        dummy_location.append_location(RESOURCE_GROUP)
        token_name = self.aliases.get_name_token(dummy_location)
        resource_group_name = app_location.get_name_for_token(token_name)
        dummy_location.pop_location()

        dummy_location.append_location(PARTITION)
        token_name = self.aliases.get_name_token(dummy_location)
        partition_name = app_location.get_name_for_token(token_name)
        dummy_location.pop_location()
        return resource_group_template_name, resource_group_name, partition_name


    ###########################################################################
    #                      Build deploy strategies                            #
    ###########################################################################

    def __build_library_deploy_strategy(self, location, model_libs, existing_lib_refs, update_library_list):
        """
        Update maps and lists to control re-deployment processing.
        :param location: the location of the libraries
        :param model_libs: a copy of libraries from the model, attributes may be revised
        :param existing_lib_refs: map of information about each existing library
        :param update_library_list: a list to update with libraries to be stopped before deploying
        """
        _method_name = '__build_library_deploy_strategy'
        self.logger.entering(str_helper.to_string(location), class_name=self._class_name, method_name=_method_name)

        if model_libs is not None:
            existing_libs = existing_lib_refs.keys()

            # use items(), not iteritems(), to avoid ConcurrentModificationException if a lib is removed
            for lib, lib_dict in model_libs.items():
                if model_helper.is_delete_name(lib):
                    self.__update_delete_library_in_model(existing_libs, lib, model_libs, update_library_list)
                    continue

                # determine the versioned name of the library from the library's MANIFEST
                model_src_path = dictionary_utils.get_element(lib_dict, SOURCE_PATH)
                versioned_name = self.version_helper.get_library_versioned_name(model_src_path, lib)

                existing_lib_ref = dictionary_utils.get_dictionary_element(existing_lib_refs, versioned_name)

                # remove deleted targets from the model and the existing library targets
                self.__remove_delete_targets(lib_dict, existing_lib_ref)

                if versioned_name in existing_libs:
                    # skipping absolute path libraries if they are the same
                    model_targets = dictionary_utils.get_element(lib_dict, TARGET)
                    model_targets = alias_utils.create_list(model_targets, 'WLSDPLY-08000')
                    model_targets_set = Set(model_targets)

                    existing_lib_targets = dictionary_utils.get_element(existing_lib_ref, 'target')
                    if existing_lib_targets is None:
                        existing_lib_targets = list()
                    existing_lib_targets_set = Set(existing_lib_targets)

                    targets_not_changed = existing_lib_targets_set == model_targets_set
                    existing_src_path = dictionary_utils.get_element(existing_lib_ref, 'sourcePath')
                    # For update case, the sparse model may be just changing targets, therefore without SourcePath

                    if model_src_path is None and existing_src_path is not None:
                        model_src_path = existing_src_path

                    #
                    # If the library is a WebLogic-distributed shared library and
                    # the targets are the same then no need to deploy.
                    #
                    if self.__is_builtin_library_or_app(model_src_path) and existing_src_path == model_src_path:
                        self.__handle_builtin_libraries(targets_not_changed, model_libs, lib,
                                                        existing_lib_targets_set, model_targets_set)
                        continue

                    # always update if remote
                    if self.model_context.is_remote() or self.model_context.is_ssh():
                        update_library_list.append(versioned_name)
                        continue

                    # based on the hash value of the existing source path and the new one in the archive
                    # setup how the library should be deployed or redeployed.
                    self._update_library_build_strategy_based_on_hashes(existing_lib_targets_set, existing_src_path,
                                                                        lib, lib_dict, model_libs, model_src_path,
                                                                        model_targets_set, update_library_list,
                                                                        versioned_name)
        self.logger.exiting(class_name=self._class_name, method_name=_method_name)

    def __build_app_deploy_strategy(self, location, model_apps, existing_app_refs, stop_and_undeploy_app_list):
        """
        Update maps and lists to control re-deployment processing.
        :param location: the location of the applications
        :param model_apps: a copy of applications from the model, attributes may be revised
        :param existing_app_refs: map of information about each existing app
        :param stop_and_undeploy_app_list: a list to update with apps to be stopped and undeployed
        """
        _method_name = '__build_app_deploy_strategy'
        self.logger.entering(str_helper.to_string(location), stop_and_undeploy_app_list,
                             class_name=self._class_name, method_name=_method_name)

        if model_apps is not None:
            existing_apps = existing_app_refs.keys()

            # use items(), not iteritems(), to avoid ConcurrentModificationException if an app is removed
            for app, app_dict in model_apps.items():
                if model_helper.is_delete_name(app):
                    if self._does_deployment_to_delete_exist(app, existing_apps, 'app'):
                        # remove the !app from the model
                        self.__remove_app_from_deployment(model_apps, app)
                        # undeploy the app (without !)
                        stop_and_undeploy_app_list.append(model_helper.get_delete_item_name(app))
                    continue

                model_src_path = dictionary_utils.get_element(app_dict, SOURCE_PATH)
                # determine the versioned name of the library from the application's MANIFEST
                versioned_name = self.version_helper.get_application_versioned_name(model_src_path, app)
                existing_app_ref = dictionary_utils.get_dictionary_element(existing_app_refs, versioned_name)

                # remove deleted targets from the model and the existing app targets
                self.__remove_delete_targets(app_dict, existing_app_ref)

                if versioned_name in existing_apps:
                    # Compare the hashes of the domain's existing apps to the model's apps.
                    # If they match, remove them from the list to be deployed.
                    # If they are different, stop and un-deploy the app, and leave it in the list.

                    plan_path = dictionary_utils.get_element(existing_app_ref, 'planPath')
                    src_path = dictionary_utils.get_element(existing_app_ref, 'sourcePath')

                    # For update case, the sparse model may be just changing targets, therefore without SourcePath

                    if model_src_path is None and src_path is not None:
                        model_src_path = src_path

                    existing_app_targets = dictionary_utils.get_element(existing_app_ref, 'target')
                    existing_app_targets_set = Set(existing_app_targets)

                    # always update if remote
                    if self.model_context.is_remote() or self.model_context.is_ssh():
                        self.__append_to_stop_and_undeploy_apps(versioned_name, stop_and_undeploy_app_list
                                                                , existing_app_targets_set)
                        continue

                    # based on the hash value of existing app and the new one in the archive
                    # set up how the app should be deployed or redeployed
                    self.__update_app_build_strategy_based_on_hashes(app, app_dict, existing_app_targets_set,
                                                                     model_apps, model_src_path, plan_path, src_path,
                                                                     stop_and_undeploy_app_list, versioned_name)

        self.logger.exiting(class_name=self._class_name, method_name=_method_name)

    def __get_uses_path_tokens_attribute_names(self, app_location):
        location = LocationContext(app_location)
        token_name = self.aliases.get_name_token(location)
        if token_name is not None:
            location.add_name_token(token_name, 'dummy-app')

        return self.aliases.get_model_uses_path_tokens_attribute_names(location)

    def __update_delete_library_in_model(self, existing_libs, lib, model_libs, update_library_list):
        if self._does_deployment_to_delete_exist(lib, existing_libs, 'lib'):
            lib_name = model_helper.get_delete_item_name(lib)
            if lib_name in existing_libs:
                model_libs.pop(lib)
                update_library_list.append(lib_name)
            else:
                model_libs.pop(lib)

    def __is_builtin_library_or_app(self, path):
        oracle_home = self.model_context.get_oracle_home()
        return not deployer_utils.is_path_into_archive(path) and path.startswith(oracle_home)

    def __handle_builtin_libraries(self, targets_not_changed, model_libs, lib,
                                   existing_lib_targets_set, model_targets_set):
        if targets_not_changed or existing_lib_targets_set.issuperset(model_targets_set):
            self.__remove_lib_from_deployment(model_libs, lib)
        else:
            # adjust the targets to only the new ones
            # no need to check hash for WebLogic distributed libraries
            adjusted_set = model_targets_set.difference(existing_lib_targets_set)
            adjusted_targets = ','.join(adjusted_set)
            model_libs[lib][TARGET] = adjusted_targets

    def _update_library_build_strategy_based_on_hashes(self, existing_lib_targets_set, existing_src_path, lib, lib_dict,
                                                       model_libs, model_src_path, model_targets_set,
                                                       update_library_list, versioned_name):
        model_lib_hash = self.__get_hash(model_src_path)
        existing_lib_hash = self.__get_file_hash(existing_src_path)
        if model_lib_hash != existing_lib_hash:
            #
            # updated library and add referencing apps to the stop list
            #
            # The target needs to be set to the union to avoid changing
            # target in subsequent deploy affecting existing referencing apps.
            #
            union_targets_set = existing_lib_targets_set.union(model_targets_set)
            lib_dict[TARGET] = ','.join(union_targets_set)
            # For update case, the sparse model may be just changing targets, therefore without SourcePath
            if lib_dict[SOURCE_PATH] is None and existing_src_path is not None:
                lib_dict[SOURCE_PATH] = existing_src_path

            if versioned_name not in update_library_list:
                update_library_list.append(versioned_name)
        else:
            # If the hashes match, assume that the library did not change so there is no need
            # to redeploy them ot the referencing applications unless the targets are different.
            if existing_lib_targets_set.issuperset(model_targets_set):
                self.__remove_lib_from_deployment(model_libs, lib)
            else:
                # Adjust the targets to only the new targets so that existing apps on
                # already targeted servers are not impacted.
                adjusted_set = model_targets_set.difference(existing_lib_targets_set)
                adjusted_targets = ','.join(adjusted_set)
                lib_dict[TARGET] = adjusted_targets
                # For update case, the sparse model may be just changing targets, therefore without SourcePath
                if lib_dict[SOURCE_PATH] is None and existing_src_path is not None:
                    lib_dict[SOURCE_PATH] = existing_src_path

    def __remove_lib_from_deployment(self, model_dict, lib_name):
        _method_name = '__remove_lib_from_deployment'
        self.logger.info('WLSDPLY-09311', lib_name, class_name=self._class_name, method_name=_method_name)
        model_dict.pop(lib_name)

    def __get_hash(self, path):
        _method_name = '__get_hash'
        self.logger.entering(path, class_name=self._class_name, method_name=_method_name)

        if string_utils.is_empty(path):
            hash_value = None
        elif self.path_helper.is_absolute_local_path(path):
            hash_value = self.__get_file_hash(path)
        elif deployer_utils.is_path_into_archive(path):
            if self.archive_helper.contains_path(path):
                # if path is a directory in the archive, it is an exploded entry.
                # hash can't be calculated, return -1 to ensure this will not match existing hash.
                hash_value = -1
            else:
                hash_value = self.archive_helper.get_file_hash(path)
        else:
            path =  self.path_helper.local_join(self.model_context.get_domain_home(), path)
            if self.path_helper.is_absolute_local_path(path):
                hash_value = self.__get_file_hash(path)
            else:
                ex = exception_helper.create_deploy_exception('WLSDPLY-09310', path)
                self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                raise ex

        self.logger.exiting(class_name=self._class_name, method_name=_method_name, result=hash_value)
        return hash_value

    def __get_file_hash(self, filename):
        _method_name = '__get_file_hash'
        self.logger.entering(filename, class_name=self._class_name, method_name=_method_name)

        try:
            if filename is None:
                return None

            if os.path.isdir(filename):  # can't calculate for exploded apps, libraries, etc.
                return None

            hash_value = FileUtils.computeHash(filename)
        except (IOException, NoSuchAlgorithmException), e:
            ex = exception_helper.create_deploy_exception('WLSDPLY-09309', filename, e.getLocalizedMessage(), error=e)
            self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

        self.logger.exiting(class_name=self._class_name, method_name=_method_name, result=hash_value)
        return hash_value

    def __remove_app_from_deployment(self, model_dict, app_name, reason="delete"):
        _method_name = '__remove_app_from_deployment'
        self.logger.entering(app_name, reason, class_name=self._class_name, method_name=_method_name)

        if "superset" == reason:
            key = 'WLSDPLY-09338'
        elif "emptyset" == reason:
            key = 'WLSDPLY-09339'
        else:
            key = 'WLSDPLY-09337'

        self.logger.info(key, app_name, class_name=self._class_name, method_name=_method_name)
        model_dict.pop(app_name)
        self.logger.exiting(class_name=self._class_name, method_name=_method_name)

    def __remove_delete_targets(self, model_dict, existing_ref):
        """
        Remove deleted targets from the model and existing target dictionaries.
        :param model_dict: the model dictionary for the app or library, may be modified
        :param existing_ref: the existing dictionary for the app or library, may be modified
        """
        _method_name = '__remove_delete_targets'
        self.logger.entering(existing_ref, class_name=self._class_name, method_name=_method_name)

        model_targets = dictionary_utils.get_element(model_dict, TARGET)
        model_targets = alias_utils.create_list(model_targets, 'WLSDPLY-08000')

        existing_targets = dictionary_utils.get_element(existing_ref, 'target')
        if not existing_targets:
            existing_targets = list()

        model_targets_iterator = list(model_targets)
        for model_target in model_targets_iterator:
            if model_helper.is_delete_name(model_target):
                model_targets.remove(model_target)
                target_name = model_helper.get_delete_item_name(model_target)
                if target_name in existing_targets:
                    existing_targets.remove(target_name)

        model_dict[TARGET] = ",".join(model_targets)
        self.logger.exiting(class_name=self._class_name, method_name=_method_name)

    def __append_to_stop_and_undeploy_apps(self, versioned_name, stop_and_undeploy_app_list, existing_targets_set):
        _method_name = '__append_to_stop_and_undeploy_apps'
        self.logger.entering(versioned_name, stop_and_undeploy_app_list, existing_targets_set,
                             class_name=self._class_name, method_name=_method_name)

        if versioned_name not in stop_and_undeploy_app_list and len(existing_targets_set) > 0:
            stop_and_undeploy_app_list.append(versioned_name)

        self.logger.exiting(class_name=self._class_name, method_name=_method_name)

    def __should_check_for_target_change(self, src_path, model_src_path):
        # If the existing running app's source path (always absolute from runtime mbean) = the model's source path.
        # or if the model SourcePath + domain home is exactly equal to the running's app source path.
        # return True otherwise return False
        _method_name = '__should_check_for_target_change'
        self.logger.entering(src_path, model_src_path, class_name=self._class_name, method_name=_method_name)

        app_path = self.path_helper.get_canonical_path(src_path)
        model_path = self.path_helper.get_canonical_path(model_src_path, self.model_context.get_domain_home())

        result = app_path == model_path
        self.logger.exiting(class_name=self._class_name, method_name=_method_name, result=result)
        return result

    def __update_app_build_strategy_based_on_hashes(self, app, app_dict, existing_app_targets_set, model_apps,
                                                    model_src_path, plan_path, src_path, stop_and_undeploy_app_list,
                                                    versioned_name):
        _method_name = '__update_app_build_strategy_based_on_hashes'
        self.logger.entering(app, app_dict, existing_app_targets_set, model_src_path, plan_path, src_path,
                             stop_and_undeploy_app_list, versioned_name,
                             class_name=self._class_name, method_name=_method_name)

        model_plan_full_path = self._get_combined_model_plan_path(app_dict)

        model_src_hash = self.__get_hash(model_src_path)
        model_plan_hash = self.__get_hash(model_plan_full_path)
        existing_src_hash = self.__get_file_hash(src_path)
        existing_plan_hash = self.__get_file_hash(plan_path)
        if model_src_hash == existing_src_hash:
            if model_plan_hash == existing_plan_hash:
                if self.__should_check_for_target_change(src_path, model_src_path):
                    self._update_app_deploy_strategy_for_target_changes(app, app_dict,
                                                                        existing_app_targets_set, model_apps,
                                                                        src_path, stop_and_undeploy_app_list,
                                                                        versioned_name)
                else:
                    # same hash but different path, so redeploy it
                    self.__append_to_stop_and_undeploy_apps(versioned_name, stop_and_undeploy_app_list,
                                                            existing_app_targets_set)
            else:
                # updated deployment plan
                self.__append_to_stop_and_undeploy_apps(versioned_name, stop_and_undeploy_app_list,
                                                        existing_app_targets_set)
        else:
            # updated app
            self.__append_to_stop_and_undeploy_apps(versioned_name, stop_and_undeploy_app_list,
                                                    existing_app_targets_set)

        self.logger.exiting(class_name=self._class_name, method_name=_method_name)

    def _update_app_deploy_strategy_for_target_changes(self, app, app_dict, existing_app_targets_set,
                                                       model_apps, src_path, stop_and_undeploy_app_list, versioned_name):

        _method_name = '_update_app_deploy_strategy_for_target_changes'
        self.logger.entering(app, app_dict, existing_app_targets_set, src_path, stop_and_undeploy_app_list,
                             versioned_name, class_name=self._class_name, method_name=_method_name)

        # If model hashes match existing hashes, the application did not change.
        # Unless targets were added, there's no need to redeploy.
        # If it is an absolute path, there is nothing to compare so assume redeploy
        model_targets = dictionary_utils.get_element(app_dict, TARGET)
        model_targets_list = alias_utils.create_list(model_targets, 'WLSDPLY-08000')
        model_targets_set = Set(model_targets_list)
        if existing_app_targets_set == model_targets_set and len(existing_app_targets_set) > 0:
            # redeploy the app if everything is the same
            self.logger.info('WLSDPLY-09336', src_path, class_name=self._class_name, method_name=_method_name)
            self.__append_to_stop_and_undeploy_apps(versioned_name, stop_and_undeploy_app_list,
                                                    existing_app_targets_set)
        elif len(existing_app_targets_set) == 0 and len(model_targets_set) == 0:
            self.__remove_app_from_deployment(model_apps, app, "emptyset")
        elif existing_app_targets_set.issuperset(model_targets_set):
            self.__remove_app_from_deployment(model_apps, app, "superset")
        else:
            # Adjust the targets to only the new targets so that existing apps on
            # already targeted servers are not impacted.
            adjusted_set = model_targets_set.difference(existing_app_targets_set)
            adjusted_targets = ','.join(adjusted_set)
            app_dict[TARGET] = adjusted_targets

            # For update case, the sparse model may be just changing targets, therefore without SourcePath
            if app_dict[SOURCE_PATH] is None and src_path is not None:
                app_dict[SOURCE_PATH] = src_path

        self.logger.exiting(class_name=self._class_name, method_name=_method_name)

    ###########################################################################
    #                        Deploy and un-deploy                             #
    ###########################################################################

    def __deploy_model_applications(self, model_apps, app_location):
        return self.__deploy_model_deployments(model_apps, app_location, APPLICATION)

    def __deploy_model_libraries(self, model_libs, lib_location):
        return self.__deploy_model_deployments(model_libs, lib_location, LIBRARY)

    def __deploy_model_deployments(self, deployments, deployments_location, deployment_type):
        _method_name = '__deploy_model_deployments'
        self.logger.entering(str_helper.to_string(deployments_location), class_name=self._class_name,
                             method_name=_method_name)

        deployed_names = []
        if deployments is not None:
            deploy_ordered_keys = self.__get_deployment_ordering(deployments)
            location = LocationContext(deployments_location)
            token_name = self.aliases.get_name_token(location)
            for deployment_name in deploy_ordered_keys:
                if not model_helper.is_delete_name(deployment_name):
                    deployment_dict = deployments[deployment_name]
                    stage_mode = dictionary_utils.get_element(deployment_dict, STAGE_MODE)
                    targets = dictionary_utils.get_element(deployment_dict, TARGET)

                    options, sub_module_targets  = \
                        self.__get_deploy_options(deployments, deployment_name, deployment_type == LIBRARY)

                    self._extract_deployment_from_archive(deployment_name, deployment_type, deployment_dict)

                    if deployment_type == APPLICATION:
                        is_structured_app, _ = self._is_structured_app(deployment_name, deployment_dict)
                        if is_structured_app:
                            self._fixup_structured_app_plan_file_config_root(deployment_name, deployment_dict)

                    model_source_path = dictionary_utils.get_element(deployment_dict, SOURCE_PATH)
                    source_path = self.__get_online_deployment_path(deployment_name, deployment_type, SOURCE_PATH, model_source_path)
                    combined_plan_path = self._get_combined_model_plan_path(deployment_dict)
                    plan_path = self.__get_online_deployment_path(deployment_name, deployment_type, PLAN_PATH, combined_plan_path)

                    location.add_name_token(token_name, deployment_name)
                    resource_group_template_name, resource_group_name, partition_name = \
                        self._get_mt_names_from_location(location)

                    module_type = dictionary_utils.get_element(deployment_dict, MODULE_TYPE)

                    new_name = self.__deploy_app_or_library(deployment_name, model_source_path, source_path, targets,
                                                            plan=plan_path, stage_mode=stage_mode,
                                                            partition=partition_name,
                                                            resource_group=resource_group_name,
                                                            resource_group_template=resource_group_template_name,
                                                            module_type=module_type,
                                                            sub_module_targets=sub_module_targets,
                                                            options=options)

                    deployed_names.append(new_name)
                    self._substitute_appmodule_token(model_source_path, module_type)

                    location.remove_name_token(token_name)

        self.logger.exiting(class_name=self._class_name, method_name=_method_name)
        return deployed_names

    def __deploy_app_or_library(self, application_name, model_source_path, deploy_source_path, targets, stage_mode=None,
                                plan=None, partition=None, resource_group=None, resource_group_template=None,
                                sub_module_targets=None, module_type = None, options=None):
        """
        Deploy an application or shared library in online mode.
        :param application_name: the name of the app or library from the model
        :param model_source_path: the model source path of the app or library
        :param deploy_source_path: the full source path of the app or library
        :param targets: the intended targets
        :param plan: optional, the full path to the plan file
        :param partition: optional, the partition
        :param resource_group: optional, the resource group
        :param resource_group_template: optional, the resource group template
        :param options: optional, extra options for the WLST deploy() call
        """
        _method_name = '__deploy_app_or_library'
        self.logger.entering(application_name, model_source_path, deploy_source_path, targets, stage_mode, plan,
                             partition, resource_group, resource_group_template, sub_module_targets, module_type,
                             options, class_name=self._class_name, method_name=_method_name)

        is_library = False
        if options is not None:
            is_library = dictionary_utils.get_element(options, 'libraryModule') == 'true'

        type_name = APPLICATION
        if is_library:
            type_name = LIBRARY

        self.logger.info('WLSDPLY-09316', type_name, application_name, class_name=self._class_name,
                         method_name=_method_name)

        real_domain_home = self.model_context.get_domain_home()

        if string_utils.is_empty(model_source_path):
            ex = exception_helper.create_deploy_exception('WLSDPLY-09317', type_name, application_name, SOURCE_PATH)
            self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

        if not self.model_context.is_ssh() and self.path_helper.is_absolute_local_path(deploy_source_path) and \
                not os.path.exists(deploy_source_path):
            ex = exception_helper.create_deploy_exception('WLSDPLY-09318', type_name, application_name,
                                                          str_helper.to_string(deploy_source_path))
            self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

        if is_library:
            computed_name = self.version_helper.get_library_versioned_name(model_source_path, application_name)
        else:
            computed_name = self.version_helper.get_application_versioned_name(model_source_path, application_name,
                                                                               module_type=module_type)

        application_name = computed_name

        # build the dictionary of named arguments to pass to the deploy_application method
        args = list()
        kwargs = {'path': str_helper.to_string(deploy_source_path), 'targets': str_helper.to_string(targets)}
        if options is not None:
            is_remote = dictionary_utils.get_element(options, 'remote') == 'true'
        else:
            is_remote = False

        if plan is not None:
            if self.path_helper.is_relative_local_path(plan):
                plan = self.path_helper.local_join(real_domain_home, plan)

            if not is_remote and not os.path.exists(plan):
                ex = exception_helper.create_deploy_exception('WLSDPLY-09319', type_name, application_name, plan)
                self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                raise ex
            kwargs['planPath'] = str_helper.to_string(plan)
        if resource_group is not None:
            kwargs['resourceGroup'] = str_helper.to_string(resource_group)
        if resource_group_template is not None:
            kwargs['resourceGroupTemplate'] = str_helper.to_string(resource_group_template)
        if partition is not None:
            kwargs['partition'] = str_helper.to_string(partition)
        if stage_mode is not None:
            kwargs['stageMode'] = str_helper.to_string(stage_mode)
        if options is not None:
            for key, value in options.iteritems():
                kwargs[key] = value
        kwargs['timeout'] = self.model_context.get_model_config().get_deploy_timeout()

        if self.version_helper.is_module_type_app_module(module_type) and sub_module_targets is not None:
            kwargs[SUB_MODULE_TARGETS] = sub_module_targets

        self.logger.fine('WLSDPLY-09320', type_name, application_name, kwargs,
                         class_name=self._class_name, method_name=_method_name)
        self.wlst_helper.deploy_application(application_name, *args, **kwargs)

        self.logger.exiting(class_name=self._class_name, method_name=_method_name, result=application_name)
        return application_name

    def __get_deployment_ordering(self, apps):
        _method_name = '__get_deployment_ordering'
        self.logger.entering(apps, class_name=self._class_name, method_name=_method_name)

        name_sorted_keys = apps.keys()
        name_sorted_keys.sort()

        has_deploy_order_apps = []
        pop_keys = []
        for key in name_sorted_keys:
            if apps[key].has_key(DEPLOYMENT_ORDER):
                has_deploy_order_apps.append(key)
                pop_keys.append(key)

        for key in pop_keys:
            name_sorted_keys.remove(key)

        # now sort the has_deploy_order_apps
        deploy_order_list = []
        for app in has_deploy_order_apps:
            deploy_order = apps[app][DEPLOYMENT_ORDER]
            if deploy_order not in deploy_order_list:
                deploy_order_list.append(deploy_order)
        deploy_order_list.sort()

        ordered_list = []
        for order in deploy_order_list:
            this_list = _get_deployment_order(apps, has_deploy_order_apps, order)
            ordered_list.extend(this_list)

        result_deploy_order = []
        result_deploy_order.extend(ordered_list)
        if name_sorted_keys is not None:
            result_deploy_order.extend(name_sorted_keys)

        self.logger.fine('WLSDPLY-09326', str_helper.to_string(result_deploy_order),
                         class_name=self._class_name, method_name=_method_name)

        self.logger.exiting(class_name=self._class_name, method_name=_method_name,
                            result=str_helper.to_string(result_deploy_order))
        return result_deploy_order

    def __get_deploy_options(self, model_apps, app_name, is_library_module):
        """
        Get the deploy command options.
        :param model_apps: the apps dictionary
        :param app_name: the app name
        :param is_library_module: whether it is a library (boolean)
        :return: dictionary of the deploy options
        """
        _method_name = '__get_deploy_options'
        self.logger.entering(app_name, is_library_module, class_name=self._class_name, method_name=_method_name)

        deploy_options = OrderedDict()
        # not sure about altDD, altWlsDD
        app = dictionary_utils.get_dictionary_element(model_apps, app_name)
        for option in [DEPLOYMENT_ORDER, SECURITY_DD_MODEL, PLAN_STAGING_MODE, STAGE_MODE]:
            value = dictionary_utils.get_element(app, option)

            option_name = ''
            if option == DEPLOYMENT_ORDER:
                option_name = 'deploymentOrder'
            elif option == SECURITY_DD_MODEL:
                option_name = 'securityModel'
            elif option == PLAN_STAGING_MODE:
                option_name = 'planStageMode'
            elif option == STAGE_MODE:
                option_name = 'stageMode'

            if value is not None:
                deploy_options[option_name] = str_helper.to_string(value)

        if is_library_module:
            deploy_options['libraryModule'] = 'true'

        if self.model_context.is_remote():
            # In the -remote use case, if the SourcePath and combined PlanDir/PlanPath are absolute paths in
            # the model, we do not try to upload them and instead assume that they are available on the remote
            # machine already.
            #
            deploy_should_upload = self.__remote_deploy_should_upload_app(app, app_name, is_library_module)
            if deploy_should_upload:
                deploy_options['upload'] = 'true'
            else:
                deploy_options['remote'] = 'true'
        elif self.model_context.is_ssh():
            deploy_options['remote'] = 'true'

        if len(deploy_options) == 0:
            deploy_options = None

        module_type = dictionary_utils.get_element(app, MODULE_TYPE)
        sub_module_targets = ''
        sub_module_targets = self.__set_sub_deployments_for_app_module(app, module_type, sub_module_targets)

        self.logger.exiting(class_name=self._class_name, method_name=_method_name,
                            result=[deploy_options, sub_module_targets])
        return deploy_options, sub_module_targets

    def __remote_deploy_should_upload_app(self, deployment_dict, deployment_name, is_library_module):
        """
        In the -remote use case, should the deployment be uploaded>
        :param deployment_dict: the model dictionary
        :param deployment_name: the model name
        :param is_library_module: whether the deployment is a shared library
        :return: True, if the deploy options should set upload to true; False otherwise
        :raises: DeployException: if the model deployment paths are inconsistent
        """
        _method_name = '__remote_deploy_should_upload_app'
        self.logger.entering(deployment_dict, deployment_name, is_library_module,
                             class_name=self._class_name, method_name=_method_name)

        deploy_should_upload = True

        model_source_path = dictionary_utils.get_element(deployment_dict, SOURCE_PATH)
        if not string_utils.is_empty(model_source_path):
            if self.path_helper.is_absolute_path(model_source_path):
                deploy_should_upload = False

        model_combined_plan_path = self._get_combined_model_plan_path(deployment_dict)
        if not string_utils.is_empty(model_combined_plan_path):
            if self.path_helper.is_absolute_path(model_combined_plan_path):
                if string_utils.is_empty(model_source_path):
                    deploy_should_upload = False
                elif deploy_should_upload:
                    # SourcePath was not empty and not an absolute path but the plan is an absolute path so
                    # the model is inconsistent and the deploy operation cannot process it.
                    #
                    model_type = APPLICATION
                    if is_library_module:
                        model_type = LIBRARY
                    ex = exception_helper.create_deploy_exception('WLSDPLY-09350', model_type, deployment_name,
                                                                  model_source_path, model_combined_plan_path)
                    self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                    raise ex
                # else deploy_should_upload already set to false so there is nothing to do

        self.logger.exiting(class_name=self._class_name, method_name=_method_name, result=deploy_should_upload)
        return deploy_should_upload

    def __set_sub_deployments_for_app_module(self, app, module_type, sub_module_targets):
        _method_name = '__set_sub_deployments_for_app_module'
        self.logger.entering(app, module_type, sub_module_targets, class_name=self._class_name, method_name=_method_name)

        if self.version_helper.is_module_type_app_module(module_type):
            sub_deployments = dictionary_utils.get_element(app, SUB_DEPLOYMENT)
            if sub_deployments is not None:
                for sub_deployment in sub_deployments:
                    if sub_module_targets != '':
                        sub_module_targets += ','
                    name = sub_deployment
                    target = sub_deployments[name][TARGET]
                    sub_module_targets += '%s@%s' % (name, target)

        self.logger.exiting(class_name=self._class_name, method_name=_method_name, result=sub_module_targets)
        return sub_module_targets

    def __undeploy_app(self, application_name, library_module='false', partition_name=None,
                       resource_group_template=None, targets=None):
        _method_name = '__undeploy_app'
        self.logger.entering(application_name, library_module, partition_name, resource_group_template, targets,
                             class_name=self._class_name, method_name=_method_name)

        type_name = APPLICATION
        if library_module == 'true':
            type_name = LIBRARY

        if targets is not None:
            self.logger.info('WLSDPLY-09335', type_name, application_name, targets, class_name=self._class_name,
                             method_name=_method_name)
        else:
            self.logger.info('WLSDPLY-09314', type_name, application_name, class_name=self._class_name,
                             method_name=_method_name)

        self.wlst_helper.undeploy_application(application_name, libraryModule=library_module, partition=partition_name,
                                              resourceGroupTemplate=resource_group_template,
                                              timeout=self.model_context.get_model_config().get_undeploy_timeout(),
                                              targets=targets)

        self.logger.exiting(class_name=self._class_name, method_name=_method_name)

    def __delete_deployment_on_server(self, deployment_name, deployment_dict):
        """
        Remove deployed files on server after undeploy.
        :param deployment_dict: model dictionary for application or library
        """
        # remove if ssh or local
        # For remote then the undeploy should already been removed the source
        #
        # Check for None and source path, a simple partial model may not have all the information
        # e.g. appDeployments:
        #        "!myear":
        #
        _method_name = '__delete_deployment_on_server'
        self.logger.entering(deployment_name, deployment_dict, class_name=self._class_name, method_name=_method_name)

        if deployment_dict is not None and SOURCE_PATH in deployment_dict:
            source_path = deployment_dict[SOURCE_PATH]
            plan_path = self._get_combined_model_plan_path(deployment_dict)

            delete_path = source_path
            if source_path.startswith(self.STRUCTURED_APPLICATION_PATH_INTO_ARCHIVE):
                delete_path = self._get_structured_app_archive_path(deployment_name, source_path, plan_path)

            if self.path_helper.is_relative_path(delete_path):
                if self.model_context.is_ssh():
                    self.model_context.get_ssh_context().remove_file_or_directory(self.path_helper.remote_join(
                        self.model_context.get_domain_home(), delete_path))
                else:
                    if not self.model_context.is_remote():
                        FileUtils.deleteDirectory(File(self.path_helper.local_join(
                            self.model_context.get_domain_home(), delete_path)))

        self.logger.exiting(class_name=self._class_name, method_name=_method_name)

    def _replace_deployments_path_tokens(self, deployment_type, deployments_dict):
        _method_name = '_replace_deployments_path_tokens'
        self.logger.entering(deployment_type, class_name=self._class_name, method_name=_method_name)

        if deployments_dict is not None:
            for deployment_name, deployment_dict in deployments_dict.iteritems():
                self._replace_path_tokens_for_deployment(deployment_type, deployment_name, deployment_dict)

        self.logger.exiting(class_name=self._class_name, method_name=_method_name)

    def __get_online_deployment_path(self, model_name, model_type, attribute_name, attribute_value):
        _method_name = '__get_online_deployment_path'
        self.logger.entering(model_name, model_type, attribute_name, attribute_value,
                             class_name=self._class_name, method_name=_method_name)

        result = attribute_value
        if not string_utils.is_empty(attribute_value):
            if self.archive_helper and self.archive_helper.is_path_into_archive(attribute_value):
                if self.model_context.is_remote():
                    result = self.path_helper.local_join(self.upload_temporary_dir, attribute_value)
                elif self.model_context.is_ssh():
                    result = self.path_helper.remote_join(self.model_context.get_domain_home(), attribute_value)
                else:
                    result = self.path_helper.local_join(self.model_context.get_domain_home(), attribute_value)
            elif self.path_helper.is_relative_path(attribute_value):
                ex = exception_helper.create_deploy_exception('WLSDPLY-09351', model_type, model_name,
                                                              attribute_name, attribute_value)
                self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                raise ex

        self.logger.exiting(class_name=self._class_name, method_name=_method_name, result=result)
        return result

    ###########################################################################
    #                       Start and stop applications                       #
    ###########################################################################

    def __stop_app(self, application_name, partition_name=None):
        _method_name = '__stop_app'
        self.logger.entering(application_name, partition_name, class_name=self._class_name, method_name=_method_name)

        self.logger.info('WLSDPLY-09312', application_name, class_name=self._class_name, method_name=_method_name)
        progress = self.wlst_helper.stop_application(application_name, partition=partition_name,
            timeout=self.model_context.get_model_config().get_stop_app_timeout())
        while progress.isRunning():
            continue
        if progress.isFailed():
            ex = exception_helper.create_deploy_exception('WLSDPLY-09327', application_name, progress.getMessage())
            self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

        self.logger.exiting(class_name=self._class_name, method_name=_method_name)

    def __start_app(self, application_name, partition_name=None):
        _method_name = '__start_app'
        self.logger.entering(application_name, partition_name, class_name=self._class_name, method_name=_method_name)

        self.logger.info('WLSDPLY-09313', application_name, class_name=self._class_name, method_name=_method_name)
        self.wlst_helper.start_application(application_name, partition=partition_name,
                                           timeout=self.model_context.get_model_config().get_start_app_timeout())

        self.logger.exiting(class_name=self._class_name, method_name=_method_name)

    def __start_all_apps(self, deployed_app_list, base_location, is_restart_required=False):
        _method_name = '__start_all_apps'
        self.logger.entering(deployed_app_list, str_helper.to_string(base_location), is_restart_required,
                             class_name=self._class_name, method_name=_method_name)

        if is_restart_required:
            for app in deployed_app_list:
                self.logger.notification('WLSDPLY-09800', app, class_name=self._class_name, method_name=_method_name)
            self.logger.exiting(class_name=self._class_name, method_name=_method_name)
            return

        temp_app_dict = OrderedDict()
        location = LocationContext(base_location).append_location(APPLICATION)
        token_name = self.aliases.get_name_token(location)

        self.wlst_helper.server_config()
        for app in deployed_app_list:
            location.add_name_token(token_name, app)
            wlst_attribute_path = self.aliases.get_wlst_attributes_path(location)
            self.wlst_helper.cd(wlst_attribute_path)
            deployment_order = self.wlst_helper.get(DEPLOYMENT_ORDER)

            if temp_app_dict.has_key(app) is False:
                temp_app_dict[app] = OrderedDict()
            temp_app_dict[app][DEPLOYMENT_ORDER] = deployment_order

        start_order = self.__get_deployment_ordering(temp_app_dict)
        for app in start_order:
            self.__start_app(app)

        self.logger.exiting(class_name=self._class_name, method_name=_method_name)


def _get_deployment_order(apps_dict, ordered_list, order):
    """
    Get the deployment order for the applications
    :param apps_dict: the apps dict
    :param ordered_list: the ordered list
    :param order: the order
    :return: list of ordered app name in deployment order
    """
    result = []
    for app_name in ordered_list:
        if order == apps_dict[app_name][DEPLOYMENT_ORDER]:
            result.append(app_name)
    return result

def _update_ref_dictionary(ref_dictionary, lib_name, absolute_source_path, lib_hash, configured_targets,
                           absolute_plan_path=None, plan_hash=None, app_name=None, deploy_order=None):
    """
    Update the reference dictionary for the apps/libraries
    :param ref_dictionary: the reference dictionary to update
    :param lib_name: the library name
    :param absolute_source_path: the absolute source path value
    :param lib_hash: the hash of the library file
    :param configured_targets: the configured targets
    :param absolute_plan_path: the absolute plan path
    :param plan_hash: the plan hash
    :param app_name: the app name
    :param deploy_order: the deploy order
    """
    if ref_dictionary.has_key(lib_name) is False:
        ref_dictionary[lib_name] = OrderedDict()
        ref_dictionary[lib_name]['sourcePath'] = absolute_source_path
        ref_dictionary[lib_name]['hash'] = lib_hash
        ref_dictionary[lib_name]['planPath'] = absolute_plan_path
        ref_dictionary[lib_name]['planHash'] = plan_hash
        ref_dictionary[lib_name]['target'] = configured_targets

    if app_name is not None:
        lib = ref_dictionary[lib_name]
        if lib.has_key('referencingApp') is False:
            lib['referencingApp'] = OrderedDict()
        referencing_app = lib['referencingApp']
        if referencing_app.has_key(app_name) is False:
            referencing_app[app_name] = OrderedDict()
        referencing_app[app_name][DEPLOYMENT_ORDER] = deploy_order
