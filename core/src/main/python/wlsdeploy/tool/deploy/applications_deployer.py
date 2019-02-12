"""
Copyright (c) 2017, 2018, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""
import copy
import javaos as os
from java.io import ByteArrayOutputStream
from java.io import File
from java.io import FileNotFoundException
from java.io import IOException
from java.lang import IllegalStateException
from java.security import NoSuchAlgorithmException
from java.util.jar import JarFile
from java.util.zip import ZipException
from sets import Set
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import ABSOLUTE_SOURCE_PATH
from wlsdeploy.aliases.model_constants import APPLICATION
from wlsdeploy.aliases.model_constants import APP_DEPLOYMENTS
from wlsdeploy.aliases.model_constants import DEPLOYMENT_ORDER
from wlsdeploy.aliases.model_constants import LIBRARY
from wlsdeploy.aliases.model_constants import PARTITION
from wlsdeploy.aliases.model_constants import PLAN_PATH
from wlsdeploy.aliases.model_constants import PLAN_STAGE_MODE
from wlsdeploy.aliases.model_constants import RESOURCES
from wlsdeploy.aliases.model_constants import RESOURCE_GROUP
from wlsdeploy.aliases.model_constants import RESOURCE_GROUP_TEMPLATE
from wlsdeploy.aliases.model_constants import SECURITY_DD_MODEL
from wlsdeploy.aliases.model_constants import SOURCE_PATH
from wlsdeploy.aliases.model_constants import TARGET
from wlsdeploy.aliases.model_constants import TARGETS
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception import exception_helper
from wlsdeploy.tool.deploy import deployer_utils
from wlsdeploy.tool.deploy.deployer import Deployer
from wlsdeploy.util import dictionary_utils
from wlsdeploy.util import string_utils

import oracle.weblogic.deploy.util.FileUtils as FileUtils
import oracle.weblogic.deploy.util.PyOrderedDict as OrderedDict


class ApplicationsDeployer(Deployer):
    """
    class docstring
    """
    _EXTENSION_INDEX = 0
    _SPEC_INDEX = 1
    _IMPL_INDEX = 2

    def __init__(self, model, model_context, aliases, wlst_mode=WlstModes.OFFLINE, base_location=LocationContext()):
        Deployer.__init__(self, model, model_context, aliases, wlst_mode)
        self._class_name = 'ApplicationDeployer'
        self._base_location = base_location
        self._parent_dict, self._parent_name, self._parent_type = self.__get_parent_by_location(self._base_location)

    def deploy(self):
        """
        Deploy the libraries and applications from the model
        :raises: DeployException: if an error occurs
        """
        if self.wlst_mode == WlstModes.OFFLINE:
            self.__add_shared_libraries()
            self.__add_applications()
        else:
            deployer_utils.ensure_no_uncommitted_changes_or_edit_sessions()
            self.__online_deploy_apps_and_libs(self._base_location)
        return

    def __add_shared_libraries(self):
        """
        Add shared libraries in WLST offline mode.
        :raises: DeployException: if an error occurs
        """
        _method_name = '__add_shared_libraries'

        self.logger.entering(self._parent_name, self._parent_type,
                             class_name=self._class_name, method_name=_method_name)
        shared_libraries = dictionary_utils.get_dictionary_element(self._parent_dict, LIBRARY)
        if len(shared_libraries) == 0:
            self.logger.finer('WLSDPLY-09300', self._parent_type, self._parent_name,
                              class_name=self._class_name, method_name=_method_name)
            return

        root_path = self.alias_helper.get_wlst_subfolders_path(self._base_location)
        shared_library_location = LocationContext(self._base_location).append_location(LIBRARY)
        shared_library_token = self.alias_helper.get_name_token(shared_library_location)
        existing_shared_libraries = deployer_utils.get_existing_object_list(shared_library_location, self.alias_helper)

        for shared_library_name in shared_libraries:
            self.logger.info('WLSDPLY-09608', LIBRARY, shared_library_name, self._parent_type, self._parent_name,
                             class_name=self._class_name, method_name=_method_name)
            #
            # In WLST offline mode, the shared library name must match the fully qualified name, including
            # the spec and implementation versions from the deployment descriptor.  Since we want to allow
            # users to not tie the model to a specific release when deploy shared libraries shipped with
            # WebLogic, we have to go compute the required name and change the name in the model prior to
            # making changes to the domain.
            #
            shared_library = \
                copy.deepcopy(dictionary_utils.get_dictionary_element(shared_libraries, shared_library_name))
            shlib_source_path = dictionary_utils.get_element(shared_library, SOURCE_PATH)
            if string_utils.is_empty(shlib_source_path):
                ex = exception_helper.create_deploy_exception('WLSDPLY-09302', shared_library_name, SOURCE_PATH)
                self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                raise ex

            if deployer_utils.is_path_into_archive(shlib_source_path):
                if self.archive_helper is not None:
                    self.archive_helper.extract_file(shlib_source_path)
                else:
                    ex = exception_helper.create_deploy_exception('WLSDPLY-09303', shared_library_name)
                    self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                    raise ex
                full_source_path = File(File(self.model_context.get_domain_home()), shlib_source_path).getAbsolutePath()
            else:
                full_source_path = File(self.model_context.replace_token_string(shlib_source_path)).getAbsolutePath()

            library_name = \
                self.__get_deployable_library_versioned_name(full_source_path, shared_library_name)
            quoted_library_name = self.wlst_helper.get_quoted_name_for_wlst(library_name)
            shared_library_location.add_name_token(shared_library_token, quoted_library_name)

            self.wlst_helper.cd(root_path)
            deployer_utils.create_and_cd(shared_library_location, existing_shared_libraries, self.alias_helper)
            self.set_attributes(shared_library_location, shared_library)
            shared_library_location.remove_name_token(shared_library_token)
        self.logger.exiting(class_name=self._class_name, method_name=_method_name)
        return

    def __add_applications(self):
        """
        Add applications in WLST offline mode.
        :raises: DeployException: if an error occurs
        """
        _method_name = '__add_applications'
        self.logger.entering(self._parent_name, self._parent_type,
                             class_name=self._class_name, method_name=_method_name)

        applications = dictionary_utils.get_dictionary_element(self._parent_dict, APPLICATION)
        if len(applications) == 0:
            self.logger.finer('WLSDPLY-09304', self._parent_type, self._parent_name,
                              class_name=self._class_name, method_name=_method_name)
            return

        root_path = self.alias_helper.get_wlst_subfolders_path(self._base_location)
        application_location = LocationContext(self._base_location).append_location(APPLICATION)
        application_token = self.alias_helper.get_name_token(application_location)
        existing_applications = deployer_utils.get_existing_object_list(application_location, self.alias_helper)

        for application_name in applications:
            self.logger.info('WLSDPLY-09301', APPLICATION, application_name, self._parent_type, self._parent_name,
                             class_name=self._class_name, method_name=_method_name)

            application = \
                copy.deepcopy(dictionary_utils.get_dictionary_element(applications, application_name))

            app_source_path = dictionary_utils.get_element(application, SOURCE_PATH)
            if string_utils.is_empty(app_source_path):
                ex = exception_helper.create_deploy_exception('WLSDPLY-09302', application_name, SOURCE_PATH)
                self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                raise ex

            if deployer_utils.is_path_into_archive(app_source_path):
                if self.archive_helper is not None:
                    self.archive_helper.extract_file(app_source_path)
                else:
                    ex = exception_helper.create_deploy_exception('WLSDPLY-09303', application_name)
                    self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                    raise ex
                full_source_path = File(File(self.model_context.get_domain_home()), app_source_path).getAbsolutePath()
            else:
                full_source_path = File(self.model_context.replace_token_string(app_source_path)).getAbsolutePath()

            application_name = \
                self.__get_deployable_library_versioned_name(full_source_path, application_name)

            quoted_application_name = self.wlst_helper.get_quoted_name_for_wlst(application_name)
            application_location.add_name_token(application_token, quoted_application_name)

            self.wlst_helper.cd(root_path)
            deployer_utils.create_and_cd(application_location, existing_applications, self.alias_helper)
            self.set_attributes(application_location, application)
            application_location.remove_name_token(application_token)
        self.logger.exiting(class_name=self._class_name, method_name=_method_name)
        return

    def __online_deploy_apps_and_libs(self, base_location):
        """
        Deploy shared libraries and applications in online mode.

        This method tries to validate that the binaries have actually changed prior to deploy them.
        It also handles shared libraries that have changed by undeploying all of their referencing
        applications first, deploy the new shared library, and then redeploying the newest version
        of the referencing applications.
        :raises: DeployException: if an error occurs
        """
        _method_name = '__online_deploy_apps_and_libs'

        # Don't log the parent dictionary since it will be large
        self.logger.entering(self._parent_name, self._parent_type,
                             class_name=self._class_name, method_name=_method_name)

        # Make copies of the model dictionary since we are going
        # to modify it as we build the deployment strategy.
        model_shared_libraries = copy.deepcopy(dictionary_utils.get_dictionary_element(self._parent_dict, LIBRARY))
        model_applications = copy.deepcopy(dictionary_utils.get_dictionary_element(self._parent_dict, APPLICATION))

        if len(model_shared_libraries) == 0 and len(model_applications) == 0:
            # Nothing to do...
            return

        existing_app_refs = self.__get_existing_apps(self._base_location)
        existing_lib_refs = self.__get_library_references(self._base_location)
        existing_libs = existing_lib_refs.keys()
        existing_apps = existing_app_refs.keys()

        stop_app_list = list()
        stop_and_undeploy_app_list = list()
        update_library_list = list()

        lib_location = LocationContext(base_location).append_location(LIBRARY)
        # Go through the model libraries and find existing libraries that are referenced
        # by applications and compute a processing strategy for each library.
        self.__build_library_deploy_strategy(lib_location, model_shared_libraries, existing_libs, existing_lib_refs,
                                             stop_app_list, update_library_list)

        # Go through the model applications and compute the processing strategy for each application.
        app_location = LocationContext(base_location).append_location(APPLICATION)
        self.__build_app_deploy_strategy(app_location, model_applications, existing_apps,
                                         existing_app_refs, stop_and_undeploy_app_list)

        # deployed_app_list is list of apps that has been deployed and stareted again
        # redeploy_app_list is list of apps that needs to be redeplyed
        deployed_app_list = []
        redeploy_app_list = []

        # shared library updated, app referenced must be stopped, redeployed, and started so stop the app first
        for app in stop_app_list:
            self.__stop_app(app)
            # add the referenced app to the redeploy list
            redeploy_app_list.append(app)
            # add the referenced app to the start list
            deployed_app_list.append(app)

        # app is updated, it must be stopped and undeployed first
        for app in stop_and_undeploy_app_list:
            self.__stop_app(app)
            self.__undeploy_app(app)

        # library is updated, it must be undeployed first
        for lib in update_library_list:
            self.__undeploy_app(lib, library_module='true')

        self.__deploy_model_libraries(model_shared_libraries, lib_location)
        self.__deploy_model_applications(model_applications, app_location, deployed_app_list)

        for app in redeploy_app_list:
            self.__redeploy_app(app)

        self.__start_all_apps(deployed_app_list, base_location)
        self.logger.exiting(class_name=self._class_name, method_name=_method_name)
        return


    ###########################################################################
    #                      Private utility methods                            #
    ###########################################################################

    def __get_parent_by_location(self, location):
        _method_name = '_get_parent_by_location'

        self.logger.entering(str(location), class_name=self._class_name, method_name=_method_name)
        location_folders = location.get_model_folders()
        if len(location_folders) == 0:
            parent_dict = self.model.get_model_app_deployments()
            self.logger.exiting(class_name=self._class_name, method_name=_method_name,
                                result=[self.model_context.get_domain_name(), 'Domain'])
            return parent_dict, self.model_context.get_domain_name(), 'Domain'

        top_folder = location_folders[0]
        resources = self.model.get_model_resources()
        if top_folder == RESOURCE_GROUP:
            result_dict, result_name = \
                self.__get_parent_dict_and_name_for_resource_group(location, resources, RESOURCES)
            result_type = RESOURCE_GROUP

        elif top_folder == RESOURCE_GROUP_TEMPLATE:
            if RESOURCE_GROUP_TEMPLATE not in resources:
                ex = exception_helper.create_deploy_exception('WLSDPLY-09305', RESOURCE_GROUP_TEMPLATE, RESOURCES)
                self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                raise ex

            rgt_token = self.alias_helper.get_name_token(location)
            rgt_name = location.get_name_for_token(rgt_token)
            if rgt_name is None:
                ex = exception_helper.create_deploy_exception('WLSDPLY-09306', rgt_token, RESOURCE_GROUP_TEMPLATE)
                self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                raise ex
            elif rgt_name not in resources[RESOURCE_GROUP_TEMPLATE]:
                ex = exception_helper.create_deploy_exception('WLSDPLY-09307', rgt_name,
                                                              RESOURCE_GROUP_TEMPLATE, RESOURCES)
                self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                raise ex

            result_dict = resources[RESOURCE_GROUP_TEMPLATE][rgt_name]
            result_name = rgt_name
            result_type = RESOURCE_GROUP_TEMPLATE

        elif top_folder == PARTITION:
            if PARTITION not in resources:
                ex = exception_helper.create_deploy_exception('WLSDPLY-09305', PARTITION, RESOURCES)
                self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                raise ex

            part_location = LocationContext().append_location(PARTITION)
            part_token = self.alias_helper.get_name_token(part_location)
            part_name = location.get_name_for_token(part_token)
            if part_name is None:
                ex = exception_helper.create_deploy_exception('WLSDPLY-09306', part_token, PARTITION)
                self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                raise ex
            elif part_name not in resources[PARTITION]:
                ex = exception_helper.create_deploy_exception('WLSDPLY-09307', part_name, PARTITION, RESOURCES)
                self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                raise ex

            part_dict = resources[PARTITION][part_name]
            path = RESOURCES + '/' + PARTITION + '/' + part_name
            result_dict, result_name = self.__get_parent_dict_and_name_for_resource_group(location, part_dict, path)
            result_type = RESOURCE_GROUP

        else:
            ex = exception_helper.create_deploy_exception('WLSDPLY-09308', top_folder)
            self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

        self.logger.exiting(class_name=self._class_name, method_name=_method_name,
                            result=[result_name, result_type])
        return result_dict, result_name, result_type

    def __get_parent_dict_and_name_for_resource_group(self, location, parent_dict, parent_path):
        _method_name = '__get_parent_dict_and_name_for_resource_group'

        self.logger.entering(str(location), parent_path, class_name=self._class_name, method_name=_method_name)
        if RESOURCE_GROUP not in parent_dict:
            ex = exception_helper.create_deploy_exception('WLSDPLY-09305', RESOURCE_GROUP, parent_path)
            self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

        rg_token = self.alias_helper.get_name_token(location)
        rg_name = location.get_name_for_token(rg_token)
        if rg_name is None:
            ex = exception_helper.create_deploy_exception('WLSDPLY-09306', rg_token, RESOURCE_GROUP)
            self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex
        elif rg_name not in parent_dict[RESOURCE_GROUP]:
            ex = exception_helper.create_deploy_exception('WLSDPLY-09307', rg_name, RESOURCE_GROUP, parent_path)
            self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex
        return parent_dict[RESOURCE_GROUP][rg_name], rg_name

    def __get_existing_apps(self, base_location):
        _method_name = '__get_existing_apps'

        self.logger.entering(str(base_location), class_name=self._class_name, method_name=_method_name)
        ref_dictionary = OrderedDict()

        location = LocationContext(base_location).append_location(APPLICATION)
        wlst_list_path = self.alias_helper.get_wlst_list_path(location)
        token_name = self.alias_helper.get_name_token(location)

        self.wlst_helper.server_config()
        self.wlst_helper.cd(wlst_list_path)
        apps = self.wlst_helper.get_existing_object_list(APP_DEPLOYMENTS)
        self.wlst_helper.domain_runtime()
        #
        # Cannot use ApplicationRuntime since it includes datasources as ApplicationRuntimes
        #
        running_apps = self.wlst_helper.get('/AppRuntimeStateRuntime/AppRuntimeStateRuntime/ApplicationIds')
        self.wlst_helper.server_config()

        for app in apps:
            if running_apps is not None and app in running_apps:
                app_location = LocationContext(location).add_name_token(token_name, app)
                wlst_attributes_path = self.alias_helper.get_wlst_attributes_path(app_location)
                self.wlst_helper.cd(wlst_attributes_path)
                attributes_map = self.wlst_helper.lsa()
                absolute_sourcepath = attributes_map['AbsoluteSourcePath']
                absolute_planpath = attributes_map['AbsolutePlanPath']
                deployment_order = attributes_map['DeploymentOrder']
                app_hash = self.__get_file_hash(absolute_sourcepath)
                if absolute_planpath is not None:
                    plan_hash = self.__get_file_hash(absolute_planpath)
                else:
                    plan_hash = None

                _update_ref_dictionary(ref_dictionary, app, absolute_sourcepath, app_hash, None,
                                       absolute_plan_path=absolute_planpath, deploy_order=deployment_order,
                                       plan_hash=plan_hash)
        return ref_dictionary

    def __get_library_references(self, base_location):
        _method_name = '__get_library_references'

        self.logger.entering(str(base_location), class_name=self._class_name, method_name=_method_name)
        # In 12.1.3 and older release this internal library is accidentally exposed in libraryruntimes mbean

        internal_skip_list = ['bea_wls_async_response']

        location = LocationContext(base_location).append_location(LIBRARY)
        token_name = self.alias_helper.get_name_token(location)

        existing_libraries = OrderedDict()
        self.wlst_helper.domain_runtime()
        server_runtime_path = '/ServerRuntimes/'
        server_runtimes = self.wlst_helper.get_existing_object_list(server_runtime_path)

        for server_runtime in server_runtimes:
            library_runtime_path = server_runtime_path + server_runtime + '/LibraryRuntimes/'

            self.wlst_helper.domain_runtime()
            libs = self.wlst_helper.get_existing_object_list(library_runtime_path)

            for lib in libs:
                if lib in internal_skip_list:
                    continue
                self.wlst_helper.domain_runtime()
                self.wlst_helper.cd(library_runtime_path + lib)
                runtime_attributes = self.wlst_helper.lsa()

                lib_location = LocationContext(location).add_name_token(token_name, lib)
                wlst_attributes_path = self.alias_helper.get_wlst_attributes_path(lib_location)
                self.wlst_helper.server_config()
                self.wlst_helper.cd(wlst_attributes_path)
                config_attributes = self.wlst_helper.lsa()
                config_targets = self.__get_config_targets()

                # TODO(jshum) - Why does the deployment plan not get considered?
                absolute_source_path = config_attributes[ABSOLUTE_SOURCE_PATH]
                deployment_order = config_attributes[DEPLOYMENT_ORDER]
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
                        if app_type == 'ApplicationRuntime':
                            app_id = ref_attrs['ApplicationName']
                        if app_type == 'WebAppComponentRuntime':
                            app_id = ref_attrs['ApplicationIdentifier']

                        _update_ref_dictionary(existing_libraries, lib, absolute_source_path, lib_hash, config_targets,
                                               deploy_order=deployment_order, app_name=app_id)
                else:
                    _update_ref_dictionary(existing_libraries, lib, absolute_source_path, lib_hash, config_targets)
        return existing_libraries

    def __build_library_deploy_strategy(self, location, model_libs, existing_libs, existing_lib_refs,
                                        stop_app_list, update_library_list):
        if model_libs is not None:
            uses_path_tokens_model_attribute_names = self.__get_uses_path_tokens_attribute_names(location)
            for lib, lib_dict in model_libs.iteritems():
                for param in uses_path_tokens_model_attribute_names:
                    if param in lib_dict:
                        self.model_context.replace_tokens(LIBRARY, lib, param, lib_dict)

                if lib in existing_libs:
                    existing_lib_ref = dictionary_utils.get_dictionary_element(existing_lib_refs, lib)

                    # skipping absolute path libraries if they are the same
                    model_src_path = dictionary_utils.get_element(lib_dict, SOURCE_PATH)
                    model_targets = dictionary_utils.get_element(lib_dict, TARGET)
                    # Model Target could be a comma-delimited string or a list...
                    if type(model_targets) is str:
                        model_targets = model_targets.split(',')

                    existing_lib_targets = dictionary_utils.get_element(existing_lib_ref, 'target')
                    model_targets_set = Set(model_targets)
                    existing_lib_targets_set = Set(existing_lib_targets)

                    targets_not_changed = existing_lib_targets_set == model_targets_set
                    existing_src_path = dictionary_utils.get_element(existing_lib_ref, 'sourcePath')
                    #
                    # If the library is a WebLogic-distributed shared library and
                    # the targets are the same then no need to deploy.
                    #
                    if self.__is_builtin_library_or_app(model_src_path) and existing_src_path == model_src_path:
                        self.__handle_builtin_libraries(targets_not_changed, model_libs, lib,
                                                        existing_lib_targets_set, model_targets_set)
                        continue

                    # user libraries
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
                        lib_dict['Target'] = ','.join(union_targets_set)

                        _add_ref_apps_to_stoplist(stop_app_list, existing_lib_refs, lib)
                        update_library_list.append(lib)
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
                            lib_dict['Target'] = adjusted_targets
        return

    def __build_app_deploy_strategy(self, location, model_apps, existing_apps, existing_app_refs,
                                    stop_and_undeploy_app_list):
        if model_apps is not None:
            uses_path_tokens_model_attribute_names = self.__get_uses_path_tokens_attribute_names(location)

            for app, app_dict in model_apps.iteritems():
                for param in uses_path_tokens_model_attribute_names:
                    if param in app_dict:
                        self.model_context.replace_tokens(APPLICATION, app, param, app_dict)

                if app in existing_apps:
                    existing_app_ref = dictionary_utils.get_dictionary_element(existing_app_refs, app)
                    plan_path = dictionary_utils.get_element(existing_app_ref, 'planPath')
                    src_path = dictionary_utils.get_element(existing_app_ref, 'sourcePath')

                    model_src_hash = \
                        self.__get_hash(dictionary_utils.get_element(app_dict, SOURCE_PATH))
                    model_plan_hash = \
                        self.__get_hash(dictionary_utils.get_element(app_dict, PLAN_PATH))

                    existing_src_hash = self.__get_file_hash(src_path)
                    existing_plan_hash = self.__get_file_hash(plan_path)
                    if model_src_hash == existing_src_hash:
                        if model_plan_hash == existing_plan_hash:
                            self.__remove_app_from_deployment(model_apps, app)
                        else:
                            # updated deployment plan
                            stop_and_undeploy_app_list.append(app)
                    else:
                        # updated app
                        stop_and_undeploy_app_list.append(app)
        return

    def __get_uses_path_tokens_attribute_names(self, app_location):
        location = LocationContext(app_location)
        token_name = self.alias_helper.get_name_token(location)
        if token_name is not None:
            location.add_name_token(token_name, 'dummy-app')

        return self.alias_helper.get_model_uses_path_tokens_attribute_names(location)

    def __get_file_hash(self, filename):
        _method_name = '__get_file_hash'

        try:
            hash_value = FileUtils.computeHash(filename)
        except (IOException, NoSuchAlgorithmException), e:
            ex = exception_helper.create_deploy_exception('WLSDPLY-09309', filename, e.getLocalizedMessage(), error=e)
            self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex
        return hash_value

    def __get_hash(self, path):
        _method_name = '__get_hash'

        if string_utils.is_empty(path):
            hash_value = None
        elif os.path.isabs(path):
            hash_value = self.__get_file_hash(path)
        elif deployer_utils.is_path_into_archive(path):
            hash_value = self.archive_helper.get_file_hash(path)
        else:
            ex = exception_helper.create_deploy_exception('WLSDPLY-09310', path)
            self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex
        return hash_value

    def __get_config_targets(self):
        self.wlst_helper.cd(TARGETS)
        config_targets = self.wlst_helper.lsc()
        self.wlst_helper.cd('..')
        return config_targets

    def __is_builtin_library_or_app(self, path):
        oracle_home = self.model_context.get_oracle_home()
        return not deployer_utils.is_path_into_archive(path) and path.startswith(oracle_home)

    def __handle_builtin_libraries(self, targets_not_changed, model_libs, lib,
                                   existing_lib_targets_set, model_targets_set):
        if targets_not_changed or existing_lib_targets_set.issuperset(model_targets_set):
            self.__remove_lib_from_deployment(model_libs, lib)
        else:
            # adjust the targets to only the new ones
            # no need to check hash for weblogic distributed libraries
            adjusted_set = model_targets_set.difference(existing_lib_targets_set)
            adjusted_targets = ','.join(adjusted_set)
            model_libs[lib][TARGET] = adjusted_targets
        return

    def __remove_app_from_deployment(self, model_dict, app_name):
        self.logger.info('WLSDPLY-09311', app_name,
                         class_name=self._class_name, method_name='remove_app_from_deployment')
        model_dict.pop(app_name)
        return

    def __remove_lib_from_deployment(self, model_dict, lib_name):
        _method_name = '__remove_lib_from_deployment'
        self.logger.info('WLSDPLY-09311', lib_name, class_name=self._class_name, method_name=_method_name)
        model_dict.pop(lib_name)
        return

    def __stop_app(self, application_name, partition_name=None, timeout=None):
        _method_name = '__stop_app'

        self.logger.info('WLSDPLY-09312', application_name, class_name=self._class_name, method_name=_method_name)
        progress = self.wlst_helper.stop_application(application_name, partition=partition_name, timeout=timeout)
        while progress.isRunning():
            continue
        return

    def __start_app(self, application_name, partition_name=None):
        _method_name = '__start_app'

        self.logger.info('WLSDPLY-09313', application_name, class_name=self._class_name, method_name=_method_name)
        self.wlst_helper.start_application(application_name, partition=partition_name)
        return

    def __undeploy_app(self, application_name, library_module='false', partition_name=None,
                       resource_group_template=None, timeout=None):
        _method_name = '__undeploy_app'

        self.logger.info('WLSDPLY-09314', application_name, class_name=self._class_name, method_name=_method_name)
        self.wlst_helper.undeploy_application(application_name, libraryModule=library_module, partition=partition_name,
                                              resourceGroupTemplate=resource_group_template, timeout=timeout)
        return

    def __redeploy_app(self, application_name):
        _method_name = '__redeploy_app'

        self.logger.info('WLSDPLY-09315', application_name, class_name=self._class_name, method_name=_method_name)
        self.wlst_helper.redeploy_application(application_name)
        return

    def __deploy_model_libraries(self, model_libs, lib_location):
        if model_libs is not None and len(model_libs) > 0:
            uses_path_tokens_attribute_names = self.__get_uses_path_tokens_attribute_names(lib_location)
            deploy_ordered_keys = self.__get_deployment_ordering(model_libs)
            location = LocationContext(lib_location)
            token_name = self.alias_helper.get_name_token(location)
            for lib_name in deploy_ordered_keys:
                lib_dict = model_libs[lib_name]
                src_path = dictionary_utils.get_element(lib_dict, SOURCE_PATH)
                plan_file = dictionary_utils.get_element(lib_dict, PLAN_PATH)
                targets = dictionary_utils.get_element(lib_dict, TARGET)
                options = _get_deploy_options(model_libs, lib_name, library_module='true')
                for uses_path_tokens_attribute_name in uses_path_tokens_attribute_names:
                    if uses_path_tokens_attribute_name in lib_dict:
                        self.__extract_file_from_archive(lib_dict[uses_path_tokens_attribute_name])

                location.add_name_token(token_name, lib_name)
                resource_group_template_name, resource_group_name, partition_name = \
                    self.__get_mt_names_from_location(location)
                self.__deploy_app_online(lib_name, src_path, targets, plan=plan_file,
                                         partition=partition_name, resource_group=resource_group_name,
                                         resource_group_template=resource_group_template_name, options=options)
                location.remove_name_token(token_name)
        return

    def __deploy_model_applications(self, model_apps, app_location, deployed_applist):
        if model_apps is not None:
            uses_path_tokens_attribute_names = self.__get_uses_path_tokens_attribute_names(app_location)
            deploy_ordered_keys = self.__get_deployment_ordering(model_apps)
            location = LocationContext(app_location)
            token_name = self.alias_helper.get_name_token(location)
            for app_name in deploy_ordered_keys:
                app_dict = model_apps[app_name]
                src_path = dictionary_utils.get_element(app_dict, SOURCE_PATH)
                plan_file = dictionary_utils.get_element(app_dict, PLAN_PATH)
                targets = dictionary_utils.get_element(app_dict, TARGET)
                options = _get_deploy_options(model_apps, app_name, library_module='false')
                for uses_path_tokens_attribute_name in uses_path_tokens_attribute_names:
                    if uses_path_tokens_attribute_name in app_dict:
                        self.__extract_file_from_archive(app_dict[uses_path_tokens_attribute_name])

                location.add_name_token(token_name, app_name)
                resource_group_template_name, resource_group_name, partition_name = \
                    self.__get_mt_names_from_location(location)

                new_app_name = self.__deploy_app_online(app_name, src_path, targets, plan=plan_file,
                                         partition=partition_name, resource_group=resource_group_name,
                                         resource_group_template=resource_group_template_name, options=options)
                location.remove_name_token(token_name)
                deployed_applist.append(new_app_name)
        return

    def __get_mt_names_from_location(self, app_location):
        dummy_location = LocationContext()
        token_name = self.alias_helper.get_name_token(dummy_location)
        dummy_location.add_name_token(token_name, self.model_context.get_domain_name())

        dummy_location.append_location(RESOURCE_GROUP_TEMPLATE)
        token_name = self.alias_helper.get_name_token(dummy_location)
        resource_group_template_name = app_location.get_name_for_token(token_name)
        dummy_location.pop_location()

        dummy_location.append_location(RESOURCE_GROUP)
        token_name = self.alias_helper.get_name_token(dummy_location)
        resource_group_name = app_location.get_name_for_token(token_name)
        dummy_location.pop_location()

        dummy_location.append_location(PARTITION)
        token_name = self.alias_helper.get_name_token(dummy_location)
        partition_name = app_location.get_name_for_token(token_name)
        dummy_location.pop_location()
        return resource_group_template_name, resource_group_name, partition_name

    def __deploy_app_online(self, application_name, source_path, targets, plan=None, partition=None,
                            resource_group=None, resource_group_template=None, options=None):
        _method_name = '__deploy_app_online'

        self.logger.info('WLSDPLY-09316', application_name, class_name=self._class_name, method_name=_method_name)

        if string_utils.is_empty(source_path):
            ex = exception_helper.create_deploy_exception('WLSDPLY-09317', application_name, SOURCE_PATH)
            self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

        if not os.path.isabs(source_path):
            source_path = self.model_context.get_domain_home() + '/' + source_path

        if not os.path.exists(source_path):
            ex = exception_helper.create_deploy_exception('WLSDPLY-09318', application_name, str(source_path))
            self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

        # if options is not None and 'libraryModule' in options and string_utils.to_boolean(options['libraryModule']):
        computed_name = self.__get_deployable_library_versioned_name(source_path, application_name)
        application_name = computed_name

        # build the dictionary of named arguments to pass to the deploy_application method
        args = list()
        kwargs = {'path': str(source_path), 'targets': str(targets)}
        if plan is not None:
            if not os.path.isabs(plan):
                plan = self.model_context.get_domain_home() + '/' + plan

            if not os.path.exists(plan):
                ex = exception_helper.create_deploy_exception('WLSDPLY-09319', application_name, plan)
                self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                raise ex
            kwargs['planPath'] = str(plan)
        if resource_group is not None:
            kwargs['resourceGroup'] = str(resource_group)
        if resource_group_template is not None:
            kwargs['resourceGroupTemplate'] = str(resource_group_template)
        if partition is not None:
            kwargs['partition'] = str(partition)
        if options is not None:
            for key, value in options.iteritems():
                kwargs[key] = value

        self.logger.fine('WLSDPLY-09320', application_name, kwargs,
                         class_name=self._class_name, method_name=_method_name)
        self.wlst_helper.deploy_application(application_name, *args, **kwargs)
        return application_name

    def __extract_file_from_archive(self, path):
        if path is not None and deployer_utils.is_path_into_archive(path):
            self.archive_helper.extract_file(path)
        return

    def __get_deployable_library_versioned_name(self, source_path, model_name):
        """
        Get the proper name of the deployable library that WLST requires in the target domain.  This method is
        primarily needed for shared libraries in the Oracle Home where the implementation version may have
        changed.  Rather than requiring the modeller to have to know/adjust the shared library name, we extract
        the information from the target domain's archive file (e.g., war file) and compute the correct name.
        :param source_path: the SourcePath value of the shared library
        :param model_name: the model name of the library
        :return: the updated shared library name for the target environment
        :raises: DeployException: if an error occurs
        """
        _method_name = '__get_deployable_library_versioned_name'

        self.logger.entering(source_path, model_name, class_name=self._class_name, method_name=_method_name)

        old_name_tuple = deployer_utils.get_library_name_components(model_name, self.wlst_mode)
        try:
            source_path = self.model_context.replace_token_string(source_path)
            archive = JarFile(source_path)
            manifest_object = archive.getManifest()
            tokens = []
            if manifest_object is not None:
                bao = ByteArrayOutputStream()
                manifest_object.write(bao)
                manifest = bao.toString('UTF-8')
                tokens = manifest.split()

            # this is specific to application not shared library, so just returns it

            if 'Weblogic-Application-Version:' in tokens:
                weblogic_appname_index = tokens.index('Weblogic-Application-Version:')
                versioned_name = old_name_tuple[self._EXTENSION_INDEX] + '#' + tokens[weblogic_appname_index+1]
                return versioned_name

            if 'Extension-Name:' in tokens:
                extension_index = tokens.index('Extension-Name:')
                if len(tokens) > extension_index:
                    versioned_name = tokens[extension_index + 1]
                else:
                    ex = exception_helper.create_deploy_exception('WLSDPLY-09321', model_name, source_path, tokens)
                    self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                    raise ex
            else:
                versioned_name = old_name_tuple[self._EXTENSION_INDEX]

            if 'Specification-Version:' in tokens:
                spec_index = tokens.index('Specification-Version:')
                if len(tokens) > spec_index:
                    versioned_name += '#' + tokens[spec_index + 1]

                    # Cannot specify an impl version without a spec version
                    if 'Implementation-Version:' in tokens:
                        impl_index = tokens.index('Implementation-Version:')
                        if len(tokens) > impl_index:
                            versioned_name += '@' + tokens[impl_index + 1]
                        else:
                            ex = exception_helper.create_deploy_exception('WLSDPLY-09322', model_name,
                                                                          source_path, tokens)
                            self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                            raise ex
                else:
                    ex = exception_helper.create_deploy_exception('WLSDPLY-09323', model_name, source_path, tokens)
                    self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                    raise ex



            self.logger.info('WLSDPLY-09324', model_name, versioned_name,
                             class_name=self._class_name, method_name=_method_name)
        except (IOException, FileNotFoundException, ZipException, IllegalStateException), e:
            ex = exception_helper.create_deploy_exception('WLSDPLY-09325', model_name, source_path, str(e), error=e)
            self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

        self.logger.exiting(class_name=self._class_name, method_name=_method_name, result=versioned_name)
        return versioned_name

    def __get_deployment_ordering(self, apps):
        _method_name = '__get_deployment_ordering'
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
            this_list = _find_deployorder_list(apps, has_deploy_order_apps, order)
            ordered_list.extend(this_list)

        result_deploy_order = []
        if ordered_list is not None:
            result_deploy_order.extend(ordered_list)
        if name_sorted_keys is not None:
            result_deploy_order.extend(name_sorted_keys)

        self.logger.fine('WLSDPLY-09326', str(result_deploy_order),
                         class_name=self._class_name, method_name=_method_name)
        return result_deploy_order

    def __start_all_apps(self, deployed_app_list, base_location):

        temp_app_dict = OrderedDict()
        location = LocationContext(base_location).append_location(APPLICATION)
        token_name = self.alias_helper.get_name_token(location)

        self.wlst_helper.server_config()
        for app in deployed_app_list:
            location.add_name_token(token_name, app)
            wlst_attribute_path = self.alias_helper.get_wlst_attributes_path(location)
            self.wlst_helper.cd(wlst_attribute_path)
            deployment_order = self.wlst_helper.get(DEPLOYMENT_ORDER)

            if temp_app_dict.has_key(app) is False:
                temp_app_dict[app] = OrderedDict()
            temp_app_dict[app][DEPLOYMENT_ORDER] = deployment_order

        start_order = self.__get_deployment_ordering(temp_app_dict)
        for app in start_order:
            self.__start_app(app)
        return

def _get_deploy_options(model_apps, app_name, library_module):
    """
    Get the deploy command options.
    :param model_apps: the apps dictionary
    :param app_name: the app name
    :param library_module: whether or not it is a library (as a string)
    :return: dictionary of the deploy options
    """
    deploy_options = OrderedDict()
    # not sure about altDD, altWlsDD
    for option in [DEPLOYMENT_ORDER, SECURITY_DD_MODEL, PLAN_STAGE_MODE]:
        app = dictionary_utils.get_dictionary_element(model_apps, app_name)
        value = dictionary_utils.get_element(app, option)

        option_name = ''
        if option == DEPLOYMENT_ORDER:
            option_name = 'deploymentOrder'
        elif option == SECURITY_DD_MODEL:
            option_name = 'securityModel'
        elif option == PLAN_STAGE_MODE:
            option_name = 'planStageMode'

        if value is not None:
            deploy_options[option_name] = str(value)

    if library_module == 'true':
        deploy_options['libraryModule'] = 'true'

    if len(deploy_options) == 0:
        deploy_options = None
    return deploy_options

def _find_deployorder_list(apps_dict, ordered_list, order):
    """
    Get the deployment order for the apps
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

def _add_ref_apps_to_stoplist(stop_applist, lib_refs, lib_name):
    """
    Add the referencing apps for the specified shared library to the stop list.
    :param stop_applist: the stop list
    :param lib_refs: the library references
    :param lib_name: the library name
    """
    if lib_refs[lib_name].has_key('referencingApp'):
        apps = lib_refs[lib_name]['referencingApp'].keys()
        for app in apps:
            stop_applist.append(app)
    return

def _update_ref_dictionary(ref_dictionary, lib_name, absolute_sourcepath, lib_hash, configured_targets,
                           absolute_plan_path=None, plan_hash=None, app_name=None, deploy_order=None):
    """
    Update the reference dictionary for the apps/libraries
    :param ref_dictionary: the reference dictionary to update
    :param lib_name: the library name
    :param absolute_sourcepath: the absolute source path value
    :param lib_hash: the hash of the library file
    :param configured_targets: the configured targets
    :param absolute_plan_path: the absolute plan path
    :param plan_hash: the plan hash
    :param app_name: the app name
    :param deploy_order: the deploy order
    """
    if ref_dictionary.has_key(lib_name) is False:
        ref_dictionary[lib_name] = OrderedDict()
        ref_dictionary[lib_name]['sourcePath'] = absolute_sourcepath
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
    return
