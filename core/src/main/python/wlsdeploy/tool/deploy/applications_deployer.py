"""
Copyright (c) 2017, 2022, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import copy
import re
from sets import Set

import os
from java.io import File
from java.io import IOException
from java.io import FileOutputStream
from java.security import NoSuchAlgorithmException
from javax.xml.parsers import DocumentBuilderFactory
from javax.xml.transform import OutputKeys
from javax.xml.transform import TransformerFactory
from javax.xml.transform.dom import DOMSource
from javax.xml.transform.stream import StreamResult

import oracle.weblogic.deploy.util.FileUtils as FileUtils
import oracle.weblogic.deploy.util.PyOrderedDict as OrderedDict
from oracle.weblogic.deploy.util import WLSDeployArchive

from wlsdeploy.aliases import alias_utils
from wlsdeploy.aliases import model_constants
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import ABSOLUTE_SOURCE_PATH
from wlsdeploy.aliases.model_constants import APPLICATION
from wlsdeploy.aliases.model_constants import DEPLOYMENT_ORDER
from wlsdeploy.aliases.model_constants import LIBRARY
from wlsdeploy.aliases.model_constants import MODULE_TYPE
from wlsdeploy.aliases.model_constants import PARTITION
from wlsdeploy.aliases.model_constants import PLAN_DIR
from wlsdeploy.aliases.model_constants import PLAN_PATH
from wlsdeploy.aliases.model_constants import PLAN_STAGING_MODE
from wlsdeploy.aliases.model_constants import RESOURCES
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
from wlsdeploy.tool.deploy.applications_version_helper import ApplicationsVersionHelper
from wlsdeploy.tool.deploy.deployer import Deployer
from wlsdeploy.util import dictionary_utils
from wlsdeploy.util import model_helper
from wlsdeploy.util import string_utils
import wlsdeploy.util.unicode_helper as str_helper
from wlsdeploy.tool.util import appmodule_helper

import wlsdeploy.util.variables as variables


class ApplicationsDeployer(Deployer):
    """
    class docstring
    """

    def __init__(self, model, model_context, aliases, wlst_mode=WlstModes.OFFLINE, base_location=LocationContext()):
        Deployer.__init__(self, model, model_context, aliases, wlst_mode)
        self._class_name = 'ApplicationDeployer'
        self._base_location = base_location
        self._parent_dict, self._parent_name, self._parent_type = self.__get_parent_by_location(self._base_location)
        self.version_helper = ApplicationsVersionHelper(model_context, self.archive_helper)

    def deploy(self):
        """
        Deploy the libraries and applications from the model
        :raises: DeployException: if an error occurs
        """
        if self.wlst_mode == WlstModes.OFFLINE:
            self.__add_shared_libraries()
            self.__add_applications()
        else:
            self.__online_deploy_apps_and_libs(self._base_location)

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

        root_path = self.aliases.get_wlst_subfolders_path(self._base_location)
        shared_library_location = LocationContext(self._base_location).append_location(LIBRARY)
        shared_library_token = self.aliases.get_name_token(shared_library_location)

        for shared_library_name in shared_libraries:
            existing_shared_libraries = deployer_utils.get_existing_object_list(shared_library_location, self.aliases)

            if model_helper.is_delete_name(shared_library_name):
                if self.__verify_delete_versioned_app(shared_library_name, existing_shared_libraries, type='lib'):
                    location = LocationContext()
                    location.append_location(model_constants.LIBRARY)
                    existing_names = deployer_utils.get_existing_object_list(location, self.aliases)
                    deployer_utils.delete_named_element(location, shared_library_name, existing_names, self.aliases)
                continue
            else:
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
                ex = exception_helper.create_deploy_exception('WLSDPLY-09302', LIBRARY, shared_library_name,
                                                              SOURCE_PATH)
                self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                raise ex

            if deployer_utils.is_path_into_archive(shlib_source_path):
                if self.archive_helper is not None:
                    self.__extract_source_path_from_archive(shlib_source_path, LIBRARY, shared_library_name)
                else:
                    ex = exception_helper.create_deploy_exception('WLSDPLY-09303', LIBRARY, shared_library_name)
                    self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                    raise ex

            library_name = \
                self.version_helper.get_library_versioned_name(shlib_source_path, shared_library_name)
            quoted_library_name = self.wlst_helper.get_quoted_name_for_wlst(library_name)
            shared_library_location.add_name_token(shared_library_token, quoted_library_name)

            self.wlst_helper.cd(root_path)
            deployer_utils.create_and_cd(shared_library_location, existing_shared_libraries, self.aliases)
            self.set_attributes(shared_library_location, shared_library)
            shared_library_location.remove_name_token(shared_library_token)
        self.logger.exiting(class_name=self._class_name, method_name=_method_name)

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

        root_path = self.aliases.get_wlst_subfolders_path(self._base_location)
        application_location = LocationContext(self._base_location).append_location(APPLICATION)
        application_token = self.aliases.get_name_token(application_location)

        for application_name in applications:
            existing_applications = deployer_utils.get_existing_object_list(application_location, self.aliases)

            if model_helper.is_delete_name(application_name):
                if self.__verify_delete_versioned_app(application_name, existing_applications, type='app'):
                    location = LocationContext()
                    location.append_location(model_constants.APPLICATION)
                    existing_names = deployer_utils.get_existing_object_list(location, self.aliases)
                    deployer_utils.delete_named_element(location, application_name, existing_names, self.aliases)
                continue
            else:
                self.logger.info('WLSDPLY-09301', APPLICATION, application_name, self._parent_type, self._parent_name,
                                 class_name=self._class_name, method_name=_method_name)

            application = \
                copy.deepcopy(dictionary_utils.get_dictionary_element(applications, application_name))

            app_source_path = dictionary_utils.get_element(application, SOURCE_PATH)
            if string_utils.is_empty(app_source_path):
                ex = exception_helper.create_deploy_exception('WLSDPLY-09302', APPLICATION, application_name,
                                                              SOURCE_PATH)
                self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                raise ex

            if deployer_utils.is_path_into_archive(app_source_path):
                if self.archive_helper is not None:
                    self.__extract_source_path_from_archive(app_source_path, APPLICATION, application_name)
                else:
                    ex = exception_helper.create_deploy_exception('WLSDPLY-09303', APPLICATION, application_name)
                    self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                    raise ex

            module_type = dictionary_utils.get_element(application, MODULE_TYPE)

            application_name = \
                self.version_helper.get_application_versioned_name(app_source_path, application_name,
                                                                   module_type=module_type)

            quoted_application_name = self.wlst_helper.get_quoted_name_for_wlst(application_name)

            application_location.add_name_token(application_token, quoted_application_name)

            self.wlst_helper.cd(root_path)
            deployer_utils.create_and_cd(application_location, existing_applications, self.aliases)

            self._set_attributes_and_add_subfolders(application_location, application)

            application_location.remove_name_token(application_token)
            self.__substitute_appmodule_token(app_source_path, module_type)

            if app_source_path.startswith(WLSDeployArchive.ARCHIVE_STRUCT_APPS_TARGET_DIR):
                plan_dir = dictionary_utils.get_element(application, PLAN_DIR)
                plan_path = dictionary_utils.get_element(application, PLAN_PATH)
                self._fix_plan_file(plan_dir, plan_path)

        self.logger.exiting(class_name=self._class_name, method_name=_method_name)

    def __substitute_appmodule_token(self, path, module_type):
        # we need to substitute any token in the app module xml file
        if  self.version_helper.is_module_type_app_module(module_type):
            if os.path.isabs(path):
                abspath = path
            else:
                abspath = self.model_context.get_domain_home() + os.sep + path

            original_variables = {}
            variable_file = self.model_context.get_variable_file()
            if variable_file is not None and os.path.exists(variable_file):
                original_variables = variables.load_variables(variable_file)

            fh = open(abspath, 'r')
            text = fh.read()
            fh.close()
            newtext = variables.substitute_value(text, original_variables, self.model_context)
            # only jdbc and jms for now
            if module_type == 'jdbc':
                newtext = appmodule_helper.process_jdbc_appmodule_xml(newtext, self.model_context)
            elif module_type == 'jms':
                newtext = appmodule_helper.process_jms_appmodule_xml(newtext, self.model_context)

            newfh = open(abspath, 'w')
            newfh.write(newtext)
            newfh.close()


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

        # stop the app if the referenced shared library is newer or if the source path changes
        stop_app_list = list()

        # applications to be stopped and undeployed
        stop_and_undeploy_app_list = list()

        # libraries to be undeployed
        update_library_list = list()

        lib_location = LocationContext(base_location).append_location(LIBRARY)
        # Go through the model libraries and find existing libraries that are referenced
        # by applications and compute a processing strategy for each library.
        self.__build_library_deploy_strategy(lib_location, model_shared_libraries, existing_lib_refs,
                                             stop_app_list, update_library_list)


        # Go through the model applications and compute the processing strategy for each application.
        app_location = LocationContext(base_location).append_location(APPLICATION)
        self.__build_app_deploy_strategy(app_location, model_applications, existing_app_refs,
                                         stop_and_undeploy_app_list)

        # deployed_app_list is list of apps that has been deployed and started again
        deployed_app_list = []

        #  For in-place update of shared libraries (i.e. impl/spec versions are not updated in the MANIFEST.MF for
        #   update), trying to do so will result in error just like the console.
        #
        # we will not automatically detect the referencing app and try to figure out the dependency graph and orders
        # for undeploying apps.
        #
        #   1.  It needs to be fully undeploy shared library referenced apps
        #   2.  But if the user only provides a sparse model for library update,  the sparse model will not have the
        #   original app and it will not be deployed again
        #   3.  There maybe transitive references by shared library and it will be difficult to handle processing order
        #    the full dependency graph
        #   4.  Console will result in error and ask user to undeploy the app first, so we are not trying to add new
        #   functionalities in wls.
        #

        # user provide new versioned app, it must be stopped and undeployed first
        for app in stop_and_undeploy_app_list:
            self.__stop_app(app)
            self.__undeploy_app(app)

        # library is updated, it must be undeployed first
        for lib in update_library_list:
            self.__undeploy_app(lib, library_module='true')

        self.__deploy_model_libraries(model_shared_libraries, lib_location)
        self.__deploy_model_applications(model_applications, app_location, deployed_app_list)

        self.__start_all_apps(deployed_app_list, base_location)
        self.logger.exiting(class_name=self._class_name, method_name=_method_name)

    ###########################################################################
    #                      Private utility methods                            #
    ###########################################################################

    def __get_parent_by_location(self, location):
        _method_name = '_get_parent_by_location'

        self.logger.entering(str_helper.to_string(location), class_name=self._class_name, method_name=_method_name)
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

            rgt_token = self.aliases.get_name_token(location)
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
            part_token = self.aliases.get_name_token(part_location)
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
        self.logger.entering(str_helper.to_string(location), parent_path,
                             class_name=self._class_name, method_name=_method_name)

        if RESOURCE_GROUP not in parent_dict:
            ex = exception_helper.create_deploy_exception('WLSDPLY-09305', RESOURCE_GROUP, parent_path)
            self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

        rg_token = self.aliases.get_name_token(location)
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
        self.logger.entering(str_helper.to_string(base_location),
                             class_name=self._class_name, method_name=_method_name)

        ref_dictionary = OrderedDict()

        location = LocationContext(base_location).append_location(APPLICATION)
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

        for app in apps:
            if running_apps is not None and app in running_apps:
                app_location = LocationContext(location).add_name_token(token_name, app)
                wlst_attributes_path = self.aliases.get_wlst_attributes_path(app_location)
                self.wlst_helper.cd(wlst_attributes_path)
                attributes_map = self.wlst_helper.lsa()
                absolute_sourcepath = attributes_map['AbsoluteSourcePath']
                absolute_planpath = attributes_map['AbsolutePlanPath']
                config_targets = self.__get_config_targets()

                if absolute_planpath is None:
                    absolute_planpath = attributes_map['PlanPath']

                if absolute_planpath is not None and not os.path.isabs(absolute_planpath):
                    absolute_planpath = self.model_context.get_domain_home() + '/' + absolute_planpath

                if absolute_sourcepath is None:
                    absolute_sourcepath = attributes_map['SourcePath']

                if absolute_sourcepath is not None and not os.path.isabs(absolute_sourcepath):
                    absolute_sourcepath = self.model_context.get_domain_home() + '/' + absolute_sourcepath

                deployment_order = attributes_map['DeploymentOrder']

                app_hash = self.__get_file_hash(absolute_sourcepath)
                if absolute_planpath is not None:
                    plan_hash = self.__get_file_hash(absolute_planpath)
                else:
                    plan_hash = None

                _update_ref_dictionary(ref_dictionary, app, absolute_sourcepath, app_hash, config_targets,
                                       absolute_plan_path=absolute_planpath, deploy_order=deployment_order,
                                       plan_hash=plan_hash)
        return ref_dictionary

    def __get_library_references(self, base_location):
        _method_name = '__get_library_references'
        self.logger.entering(str_helper.to_string(base_location),
                             class_name=self._class_name, method_name=_method_name)

        # In 12.1.3 and older release this internal library is accidentally exposed in libraryruntimes mbean

        internal_skip_list = ['bea_wls_async_response']

        location = LocationContext(base_location).append_location(LIBRARY)
        token_name = self.aliases.get_name_token(location)

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
                wlst_attributes_path = self.aliases.get_wlst_attributes_path(lib_location)
                self.wlst_helper.server_config()
                self.wlst_helper.cd(wlst_attributes_path)
                config_attributes = self.wlst_helper.lsa()
                config_targets = self.__get_config_targets()

                # There are case in application where absolute source path is not set but sourepath is
                # if source path is not absolute then we need to add the domain path

                absolute_source_path = config_attributes[ABSOLUTE_SOURCE_PATH]
                if absolute_source_path is None:
                    absolute_source_path = config_attributes['SourcePath']

                if absolute_source_path is not None and not os.path.isabs(absolute_source_path):
                    absolute_source_path = self.model_context.get_domain_home() + '/' + absolute_source_path

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
                        if app_type == 'ApplicationRuntime' and 'ApplicationName' in ref_attrs:
                            app_id = ref_attrs['ApplicationName']
                        if app_type == 'WebAppComponentRuntime' and 'ApplicationIdentifier' in ref_attrs:
                            app_id = ref_attrs['ApplicationIdentifier']

                        _update_ref_dictionary(existing_libraries, lib, absolute_source_path, lib_hash, config_targets,
                                               deploy_order=deployment_order, app_name=app_id)
                else:
                    _update_ref_dictionary(existing_libraries, lib, absolute_source_path, lib_hash, config_targets)
        return existing_libraries

    def __build_library_deploy_strategy(self, location, model_libs, existing_lib_refs, stop_app_list,
                                        update_library_list):
        """
        Update maps and lists to control re-deployment processing.
        :param location: the location of the libraries
        :param model_libs: a copy of libraries from the model, attributes may be revised
        :param existing_lib_refs: map of information about each existing library
        :param stop_app_list: a list to update with dependent apps to be stopped and undeployed
        :param update_library_list: a list to update with libraries to be stopped before deploying
        """
        if model_libs is not None:
            existing_libs = existing_lib_refs.keys()
            uses_path_tokens_model_attribute_names = self.__get_uses_path_tokens_attribute_names(location)

            # use items(), not iteritems(), to avoid ConcurrentModificationException if a lib is removed
            for lib, lib_dict in model_libs.items():
                for param in uses_path_tokens_model_attribute_names:
                    if param in lib_dict:
                        self.model_context.replace_tokens(LIBRARY, lib, param, lib_dict)

                if model_helper.is_delete_name(lib):
                    if self.__verify_delete_versioned_app(lib, existing_libs, 'lib'):
                        lib_name = model_helper.get_delete_item_name(lib)
                        if lib_name in existing_libs:
                            model_libs.pop(lib)
                            update_library_list.append(lib_name)
                        else:
                            model_libs.pop(lib)
                    continue

                # determine the versioned name of the library from the library's MANIFEST
                model_src_path = dictionary_utils.get_element(lib_dict, SOURCE_PATH)
                versioned_name = self.version_helper.get_library_versioned_name(model_src_path, lib,
                                                                                from_archive=True)

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
                    # For update case, the sparse model may be just changing targets, therefore without sourcepath

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
                        # For update case, the sparse model may be just changing targets, therefore without sourcepath
                        if lib_dict['SourcePath'] is None and existing_src_path is not None:
                            lib_dict['SourcePath'] = existing_src_path

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
                            lib_dict['Target'] = adjusted_targets
                            # For update case, the sparse model may be just changing targets, therefore without sourcepath
                            if lib_dict['SourcePath'] is None and existing_src_path is not None:
                                lib_dict['SourcePath'] = existing_src_path

    def __shouldCheckForTargetChange(self, src_path, model_src_path):
        # If the existing running app's source path (always absolute from runtime mbean) = the model's source path.
        # or if the model sourcepath + domain home is exactly equal to the running's app source path.
        # return True otherwise return False
        if not os.path.isabs(model_src_path):
            return FileUtils.getCanonicalPath(self.model_context.get_domain_home() + '/' + model_src_path) == src_path
        else:
            return FileUtils.getCanonicalPath(src_path) == FileUtils.getCanonicalPath(model_src_path)

    def __append_to_stop_and_undeploy_apps(self, versioned_name, stop_and_undeploy_app_list, existing_targets_set):
        if versioned_name not in stop_and_undeploy_app_list and len(existing_targets_set) > 0:
            stop_and_undeploy_app_list.append(versioned_name)


    def __build_app_deploy_strategy(self, location, model_apps, existing_app_refs, stop_and_undeploy_app_list):
        """
        Update maps and lists to control re-deployment processing.
        :param location: the location of the applications
        :param model_apps: a copy of applications from the model, attributes may be revised
        :param existing_app_refs: map of information about each existing app
        :param stop_and_undeploy_app_list: a list to update with apps to be stopped and undeployed
        """
        _method_name = '__build_app_deploy_strategy'

        if model_apps is not None:
            existing_apps = existing_app_refs.keys()
            uses_path_tokens_model_attribute_names = self.__get_uses_path_tokens_attribute_names(location)

            # use items(), not iteritems(), to avoid ConcurrentModificationException if an app is removed
            for app, app_dict in model_apps.items():
                for param in uses_path_tokens_model_attribute_names:
                    if param in app_dict:
                        self.model_context.replace_tokens(APPLICATION, app, param, app_dict)

                    if param == SOURCE_PATH and param.startswith(WLSDeployArchive.ARCHIVE_STRUCT_APPS_TARGET_DIR):
                        plan_dir = dictionary_utils.get_element(app, PLAN_DIR)
                        plan_path = dictionary_utils.get_element(app, PLAN_PATH)
                        self._fix_plan_file(plan_dir, plan_path)

                if model_helper.is_delete_name(app):
                    if self.__verify_delete_versioned_app(app, existing_apps, 'app'):
                        # remove the !app from the model
                        self.__remove_app_from_deployment(model_apps, app)
                        # undeploy the app (without !)
                        stop_and_undeploy_app_list.append(model_helper.get_delete_item_name(app))
                    continue

                # determine the versioned name of the library from the application's MANIFEST
                model_src_path = dictionary_utils.get_element(app_dict, SOURCE_PATH)
                versioned_name = self.version_helper.get_application_versioned_name(model_src_path, app,
                                                                                    from_archive=True)

                existing_app_ref = dictionary_utils.get_dictionary_element(existing_app_refs, versioned_name)

                # remove deleted targets from the model and the existing app targets
                self.__remove_delete_targets(app_dict, existing_app_ref)

                if versioned_name in existing_apps:
                    # Compare the hashes of the domain's existing apps to the model's apps.
                    # If they match, remove them from the list to be deployed.
                    # If they are different, stop and un-deploy the app, and leave it in the list.

                    plan_path = dictionary_utils.get_element(existing_app_ref, 'planPath')
                    src_path = dictionary_utils.get_element(existing_app_ref, 'sourcePath')

                    # For update case, the sparse model may be just changing targets, therefore without sourcepath

                    if model_src_path is None and src_path is not None:
                        model_src_path = src_path

                    model_src_hash = self.__get_hash(model_src_path)
                    model_plan_hash = self.__get_hash(dictionary_utils.get_element(app_dict, PLAN_PATH))

                    existing_src_hash = self.__get_file_hash(src_path)
                    existing_plan_hash = self.__get_file_hash(plan_path)
                    existing_app_targets = dictionary_utils.get_element(existing_app_ref, 'target')
                    existing_app_targets_set = Set(existing_app_targets)
                    if model_src_hash == existing_src_hash:
                        if model_plan_hash == existing_plan_hash:
                            if self.__shouldCheckForTargetChange(src_path, model_src_path):
                                # If model hashes match existing hashes, the application did not change.
                                # Unless targets were added, there's no need to redeploy.
                                # If it is an absolute path, there is nothing to compare so assume redeploy
                                model_targets = dictionary_utils.get_element(app_dict, TARGET)
                                model_targets_list = alias_utils.create_list(model_targets, 'WLSDPLY-08000')
                                model_targets_set = Set(model_targets_list)

                                if existing_app_targets_set == model_targets_set and len(existing_app_targets_set) > 0:
                                    # redeploy the app if everything is the same
                                    self.logger.info('WLSDPLY-09336', src_path,
                                                     class_name=self._class_name, method_name=_method_name)
                                    self.__append_to_stop_and_undeploy_apps(versioned_name, stop_and_undeploy_app_list
                                                                            , existing_app_targets_set)
                                elif len(existing_app_targets_set) == 0 and len(model_targets_set) == 0:
                                    self.__remove_app_from_deployment(model_apps, app, "emptyset")
                                elif existing_app_targets_set.issuperset(model_targets_set):
                                    self.__remove_app_from_deployment(model_apps, app, "superset")
                                else:
                                    # Adjust the targets to only the new targets so that existing apps on
                                    # already targeted servers are not impacted.
                                    adjusted_set = model_targets_set.difference(existing_app_targets_set)
                                    adjusted_targets = ','.join(adjusted_set)
                                    app_dict['Target'] = adjusted_targets

                                    # For update case, the sparse model may be just changing targets, therefore without sourcepath

                                    if app_dict['SourcePath'] is None and src_path is not None:
                                        app_dict['SourcePath'] = src_path
                            else:
                                # same hash but different path, so redeploy it
                                self.__append_to_stop_and_undeploy_apps(versioned_name, stop_and_undeploy_app_list
                                                                        , existing_app_targets_set)
                        else:
                            # updated deployment plan
                            self.__append_to_stop_and_undeploy_apps(versioned_name, stop_and_undeploy_app_list
                                                                    , existing_app_targets_set)
                    else:
                        # updated app
                        self.__append_to_stop_and_undeploy_apps(versioned_name, stop_and_undeploy_app_list
                                                                , existing_app_targets_set)

    def __remove_delete_targets(self, model_dict, existing_ref):
        """
        Remove deleted targets from the model and existing target dictionaries.
        :param model_dict: the model dictionary for the app or library, may be modified
        :param existing_ref: the existing dictionary for the app or library, may be modified
        """
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

    def __verify_delete_versioned_app(self, app, existing_apps, type='app'):
        """
        Verify that the specified app or library is in the existing list.  Since this app/library
        has been sepcified in the model as one to be deleted, this method will only consider
        it a match if the names match exactly.  That is, if the model specifies !myapp, this method
        will try to find myapp in the list of existing apps, skipping over version-qualified names
        like myapp#1.0 or myapp#1.0@1.1.3.
        :param app: the app or library name to be checked, with '!' still prepended
        :param existing_apps: the list of existing apps from WLST
        :param type: the type for logging, 'app' for app, library otherwise
        :return: True if the item is in the list, False otherwise
        """
        _method_name = '__verify_delete_versioned_app'

        if type == 'app':
            err_key_list = 'WLSDPLY-09332'
            err_key = 'WLSDPLY-09334'
        else:
            err_key_list = 'WLSDPLY-09331'
            err_key = 'WLSDPLY-09333'

        found_app = True
        app_name = model_helper.get_delete_item_name(app)
        if not app_name in existing_apps:
            found_app = False
            tokens = re.split(r'[#@]', app_name)
            re_expr = '^' + tokens[0] + '[#@]*'
            r = re.compile(re_expr)
            matched_list = filter(r.match, existing_apps)
            if len(matched_list) > 0:
                self.logger.warning(err_key_list, app_name, matched_list, self._class_name, method_name=_method_name)
            else:
                self.logger.warning(err_key, app_name,self._class_name, method_name=_method_name)
        return found_app

    def __get_uses_path_tokens_attribute_names(self, app_location):
        location = LocationContext(app_location)
        token_name = self.aliases.get_name_token(location)
        if token_name is not None:
            location.add_name_token(token_name, 'dummy-app')

        return self.aliases.get_model_uses_path_tokens_attribute_names(location)

    def __get_file_hash(self, filename):
        _method_name = '__get_file_hash'

        try:
            if filename is None:
                return None

            if File(filename).isDirectory():  # can't calculate for exploded apps, libraries, etc.
                return None

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
            if self.archive_helper.contains_path(path):
                # if path is a directory in the archive, it is an exploded entry.
                # hash can't be calculated, return -1 to ensure this will not match existing hash.
                hash_value = -1
            else:
                hash_value = self.archive_helper.get_file_hash(path)
        else:
            path =  self.model_context.get_domain_home() + '/' + path
            if os.path.isabs(path):
                hash_value = self.__get_file_hash(path)
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

    def __remove_app_from_deployment(self, model_dict, app_name, reason="delete"):
        if "superset" == reason:
            self.logger.info('WLSDPLY-09338', app_name,
                             class_name=self._class_name, method_name='remove_app_from_deployment')
        elif "emptyset" == reason:
            self.logger.info('WLSDPLY-09339', app_name,
                             class_name=self._class_name, method_name='remove_app_from_deployment')
        else:
            self.logger.info('WLSDPLY-09337', app_name,
                             class_name=self._class_name, method_name='remove_app_from_deployment')

        model_dict.pop(app_name)

    def __remove_lib_from_deployment(self, model_dict, lib_name):
        _method_name = '__remove_lib_from_deployment'
        self.logger.info('WLSDPLY-09311', lib_name, class_name=self._class_name, method_name=_method_name)
        model_dict.pop(lib_name)

    def __stop_app(self, application_name, partition_name=None):
        _method_name = '__stop_app'

        self.logger.info('WLSDPLY-09312', application_name, class_name=self._class_name, method_name=_method_name)
        progress = self.wlst_helper.stop_application(
            application_name, partition=partition_name,
            timeout=self.model_context.get_model_config().get_stop_app_timeout())
        while progress.isRunning():
            continue
        if progress.isFailed():
            ex = exception_helper.create_deploy_exception('WLSDPLY-09327', application_name, progress.getMessage())
            self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

    def __start_app(self, application_name, partition_name=None):
        _method_name = '__start_app'

        self.logger.info('WLSDPLY-09313', application_name, class_name=self._class_name, method_name=_method_name)
        self.wlst_helper.start_application(application_name, partition=partition_name,
                                           timeout=self.model_context.get_model_config().get_start_app_timeout())

    def __undeploy_app(self, application_name, library_module='false', partition_name=None,
                       resource_group_template=None, targets=None):
        _method_name = '__undeploy_app'

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

    def __deploy_model_libraries(self, model_libs, lib_location):
        if model_libs is not None and len(model_libs) > 0:
            uses_path_tokens_attribute_names = self.__get_uses_path_tokens_attribute_names(lib_location)
            deploy_ordered_keys = self.__get_deployment_ordering(model_libs)
            location = LocationContext(lib_location)
            token_name = self.aliases.get_name_token(location)
            for lib_name in deploy_ordered_keys:
                if not model_helper.is_delete_name(lib_name):
                    lib_dict = model_libs[lib_name]
                    src_path = dictionary_utils.get_element(lib_dict, SOURCE_PATH)
                    plan_file = dictionary_utils.get_element(lib_dict, PLAN_PATH)
                    targets = dictionary_utils.get_element(lib_dict, TARGET)
                    stage_mode = dictionary_utils.get_element(lib_dict, STAGE_MODE)
                    options, sub_module_targets = _get_deploy_options(model_libs, lib_name, library_module='true',
                                                                      application_version_helper=self.version_helper)
                    for uses_path_tokens_attribute_name in uses_path_tokens_attribute_names:
                        if uses_path_tokens_attribute_name in lib_dict:
                            path = lib_dict[uses_path_tokens_attribute_name]
                            if deployer_utils.is_path_into_archive(path):
                                self.__extract_source_path_from_archive(path, LIBRARY, lib_name)

                    location.add_name_token(token_name, lib_name)
                    resource_group_template_name, resource_group_name, partition_name = \
                        self.__get_mt_names_from_location(location)
                    self.__deploy_app_online(lib_name, src_path, targets, plan=plan_file, stage_mode=stage_mode,
                                             partition=partition_name, resource_group=resource_group_name,
                                             resource_group_template=resource_group_template_name, options=options)
                    location.remove_name_token(token_name)

    def __deploy_model_applications(self, model_apps, app_location, deployed_applist):
        if model_apps is not None:
            uses_path_tokens_attribute_names = self.__get_uses_path_tokens_attribute_names(app_location)
            deploy_ordered_keys = self.__get_deployment_ordering(model_apps)
            location = LocationContext(app_location)
            token_name = self.aliases.get_name_token(location)
            for app_name in deploy_ordered_keys:
                if not model_helper.is_delete_name(app_name):
                    app_dict = model_apps[app_name]
                    src_path = dictionary_utils.get_element(app_dict, SOURCE_PATH)
                    plan_file = dictionary_utils.get_element(app_dict, PLAN_PATH)
                    stage_mode = dictionary_utils.get_element(app_dict, STAGE_MODE)
                    targets = dictionary_utils.get_element(app_dict, TARGET)
                    options, sub_module_targets  = _get_deploy_options(model_apps, app_name, library_module='false',
                                                                       application_version_helper=self.version_helper)

                    # any attribute with 'uses_path_tokens' may be in the archive (such as SourcePath)
                    for uses_path_tokens_attribute_name in uses_path_tokens_attribute_names:
                        if uses_path_tokens_attribute_name in app_dict:
                            path = app_dict[uses_path_tokens_attribute_name]
                            if deployer_utils.is_path_into_archive(path):
                                self.__extract_source_path_from_archive(path, APPLICATION, app_name)
                    location.add_name_token(token_name, app_name)
                    resource_group_template_name, resource_group_name, partition_name = \
                        self.__get_mt_names_from_location(location)

                    module_type = dictionary_utils.get_element(app_dict, MODULE_TYPE)

                    new_app_name = self.__deploy_app_online(app_name, src_path, targets, plan=plan_file,
                                                            stage_mode=stage_mode, partition=partition_name,
                                                            resource_group=resource_group_name,
                                                            resource_group_template=resource_group_template_name,
                                                            module_type=module_type,
                                                            sub_module_targets=sub_module_targets,
                                                            options=options)
                    location.remove_name_token(token_name)
                    deployed_applist.append(new_app_name)
                    self.__substitute_appmodule_token(path, module_type)


    def __get_mt_names_from_location(self, app_location):
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

    def __deploy_app_online(self, application_name, source_path, targets, stage_mode=None, plan=None, partition=None,
                            resource_group=None, resource_group_template=None, sub_module_targets=None,
                            module_type = None, options=None):
        """
        Deploy an application or shared library in online mode.
        :param application_name: the name of the app or library from the model
        :param source_path: the source path of the app or library
        :param targets: the intended targets
        :param plan: optional, the path to the plan
        :param partition: optional, the partition
        :param resource_group: optional, the resource group
        :param resource_group_template: optional, the resource group template
        :param options: optional, extra options for the WLST deploy() call
        """
        _method_name = '__deploy_app_online'

        is_library = False
        if options is not None:
            is_library = dictionary_utils.get_element(options, 'libraryModule') == 'true'

        type_name = APPLICATION
        if is_library:
            type_name = LIBRARY

        self.logger.info('WLSDPLY-09316', type_name, application_name, class_name=self._class_name,
                         method_name=_method_name)

        if string_utils.is_empty(source_path):
            ex = exception_helper.create_deploy_exception('WLSDPLY-09317', type_name, application_name, SOURCE_PATH)
            self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

        full_source_path = source_path
        if not os.path.isabs(full_source_path):
            full_source_path = self.model_context.get_domain_home() + '/' + source_path

        if not os.path.exists(full_source_path):
            ex = exception_helper.create_deploy_exception('WLSDPLY-09318', type_name, application_name,
                                                          str_helper.to_string(full_source_path))
            self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

        if is_library:
            computed_name = self.version_helper.get_library_versioned_name(source_path, application_name)
        else:
            computed_name = self.version_helper.get_application_versioned_name(source_path, application_name,
                                                                               module_type=module_type)

        application_name = computed_name

        # build the dictionary of named arguments to pass to the deploy_application method
        args = list()
        kwargs = {'path': str_helper.to_string(full_source_path), 'targets': str_helper.to_string(targets)}
        if plan is not None:
            if not os.path.isabs(plan):
                plan = self.model_context.get_domain_home() + '/' + plan

            if not os.path.exists(plan):
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
        return application_name

    def __extract_source_path_from_archive(self, source_path, model_type, model_name):
        """
        Extract contents from the archive set for the specified source path.
        The contents may be a single file, or a directory with exploded content.
        :param source_path: the path to be extracted (previously checked to be under wlsdeploy)
        :param model_type: the model type (Application, etc.), used for logging
        :param model_name: the element name (my-app, etc.), used for logging
        """
        _method_name = '__extract_source_path_from_archive'
        # source path may be may be a single file (jar, war, etc.)
        if self.archive_helper.contains_file(source_path):
            self.archive_helper.extract_file(source_path)

        # source path may be exploded directory in archive
        elif self.archive_helper.contains_path(source_path):
            self.archive_helper.extract_directory(source_path)

        else:
            ex = exception_helper.create_deploy_exception('WLSDPLY-09330', model_type, model_name, source_path)
            self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

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
        result_deploy_order.extend(ordered_list)
        if name_sorted_keys is not None:
            result_deploy_order.extend(name_sorted_keys)

        self.logger.fine('WLSDPLY-09326', str_helper.to_string(result_deploy_order),
                         class_name=self._class_name, method_name=_method_name)
        return result_deploy_order

    def _fix_plan_file(self, plan_dir, plan_path):
        plan_file_name = 'plan.xml'
        if plan_path is not None and len(str_helper.to_string(plan_path)) > 0:
            plan_file_name = plan_path
        
        plan_file = os.path.join(self.model_context.get_domain_home(), plan_dir, plan_file_name)
        dbf = DocumentBuilderFactory.newInstance()
        db = dbf.newDocumentBuilder()
        document = db.parse(File(plan_file))
        document.normalizeDocument()
        elements = document.getElementsByTagName("config-root")

        if elements is not None and elements.getLength() > 0:
            element = elements.item(0)
            element.setNodeValue(plan_dir)
            element.setTextContent(plan_dir)
            ostream = FileOutputStream(plan_file)
            transformer_factory = TransformerFactory.newInstance()
            transformer = transformer_factory.newTransformer()
            transformer.setOutputProperty(OutputKeys.INDENT, "yes")
            transformer.setOutputProperty(OutputKeys.STANDALONE, "no")
            source = DOMSource(document)
            result = StreamResult(ostream)

            transformer.transform(source, result)

    def __start_all_apps(self, deployed_app_list, base_location):

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


def _get_deploy_options(model_apps, app_name, library_module, application_version_helper):
    """
    Get the deploy command options.
    :param model_apps: the apps dictionary
    :param app_name: the app name
    :param library_module: whether or not it is a library (as a string)
    :return: dictionary of the deploy options
    """
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

    if library_module == 'true':
        deploy_options['libraryModule'] = 'true'

    if len(deploy_options) == 0:
        deploy_options = None

    module_type = dictionary_utils.get_element(app, MODULE_TYPE)
    sub_module_targets = ''
    if application_version_helper.is_module_type_app_module(module_type):
        sub_deployments = dictionary_utils.get_element(app, SUB_DEPLOYMENT)
        if sub_deployments is not None:
            for sub_deployment in sub_deployments:
                if sub_module_targets != '':
                    sub_module_targets += ','
                name = sub_deployment
                target = sub_deployments[name][TARGET]
                sub_module_targets += '%s@%s' % (name, target)


    return deploy_options, sub_module_targets

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

def _add_ref_apps_to_stoplist(stop_and_undeploy_applist, lib_refs, lib_name):
    """
    Add the referencing apps for the specified shared library to the stop list.
    :param stop_and_undeploy_applist: the stop list
    :param lib_refs: the library references
    :param lib_name: the library name
    """
    if lib_refs[lib_name].has_key('referencingApp'):
        apps = lib_refs[lib_name]['referencingApp'].keys()
        for app in apps:
            if app not in stop_and_undeploy_applist:
                stop_and_undeploy_applist.append(app)

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
