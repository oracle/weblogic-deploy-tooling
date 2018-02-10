"""
Copyright (c) 2017, 2018, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""
import copy
import os
from sets import Set
import zipfile

from java.lang import StringBuilder
from java.lang import String
from java.security import MessageDigest
from java.security import NoSuchAlgorithmException
from java.security import DigestException

import oracle.weblogic.deploy.util.PyWLSTException as PyWLSTException
import oracle.weblogic.deploy.util.FileUtils as FileUtils
import oracle.weblogic.deploy.util.PyOrderedDict as OrderedDict

from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import APPLICATION
from wlsdeploy.aliases.model_constants import LIBRARY
from wlsdeploy.aliases.model_constants import PARTITION
from wlsdeploy.aliases.model_constants import RESOURCE_GROUP
from wlsdeploy.aliases.model_constants import RESOURCE_GROUP_TEMPLATE
from wlsdeploy.aliases.model_constants import RESOURCES
from wlsdeploy.aliases.model_constants import TARGET
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception import exception_helper
from wlsdeploy.tool.deploy.deployer import Deployer
from wlsdeploy.tool.deploy import deployer_utils
from wlsdeploy.util import dictionary_utils
from wlsdeploy.util import string_utils


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
        if self.wlst_mode == WlstModes.ONLINE:
            deployer_utils.ensure_no_uncommitted_changes_or_edit_sessions()
            self.__deploy_with_model()
        else:
            self.__unzip_archive(self.model_context.get_archive_file_name(), self.model_context.get_domain_home())
            self.__add_shared_libraries()
            self.__add_applications()
        return

    def __deploy_with_model(self):
        """
        Deploy shared libraries and applications in online mode.

        This method tries to validate that the binaries have actually changed prior to deploy them.
        It also handles shared libraries that have changed by undeploying all of their referencing
        applications first, deploy the new shared library, and then redeploying the newest version
        of the referencing applications.
        :raises: DeployException: if an error occurs
        """
        _method_name = '__deploy_with_model'

        # Don't log the parent dictionary since it will be large
        self.logger.entering(self._parent_name, self._parent_type,
                             class_name=self._class_name, method_name=_method_name)

        model_shared_libraries = dictionary_utils.get_dictionary_element(self._parent_dict, LIBRARY)
        model_applications = dictionary_utils.get_dictionary_element(self._parent_dict, APPLICATION)

        if len(model_shared_libraries) == 0 and len(model_applications) == 0:
            # Nothing to do...
            return

        archive_file = FileUtils.fixupFileSeparatorsForJython(self.model_context.get_archive_file_name())
        unzip_root = FileUtils.fixupFileSeparatorsForJython(self.model_context.get_domain_home())

        existing_app_refs = self.__get_existing_apps()
        existing_lib_refs = self.__get_library_references()
        existing_libs = existing_lib_refs.keys()
        existing_apps = existing_app_refs.keys()

        stop_applist = []
        stopandundeploy_applist = []
        undate_librarylist = []

        # Go through the model library and find existing library that has been referenced and apps needs to have
        # different processing strategies
        self.__build_library_deploy_strategy(model_shared_libraries, existing_libs, existing_lib_refs,
                                             archive_file, stop_applist, undate_librarylist)


        # Go through the model applications and find different processing strategies
        self.__build_app_deploy_strategy(model_applications, existing_apps, existing_app_refs, archive_file,
                                         stopandundeploy_applist)


        # deployed_applist is list of apps that has been deployed and stareted again
        # redeploy_applist is list of apps that needs to be redeplyed
        deployed_applist = []
        redeploy_applist = []

        # shared library updated, app referenced must be redeployed first
        for app in stop_applist:
            self.__stop_app(app)
            # after stop must start again
            redeploy_applist.append(app)
            # add it to start list
            deployed_applist.append(app)

        # app is updated, it must be stopped and undeployed first
        for app in stopandundeploy_applist:
            self.__stop_app(app)
            self.__undeploy_app(app)

        # library is updated, it must be undeployed first
        for lib in undate_librarylist:
            self.__undeploy_app(lib)

        self.__deploy_model_libraries(model_shared_libraries, archive_file, unzip_root)
        self.__deploy_model_applications(model_applications, archive_file, unzip_root, deployed_applist)

        for app in redeploy_applist:
            self.__redeploy_app(app)

        self.__start_all_apps(deployed_applist)
        self.logger.exiting(class_name=self._class_name, method_name=_method_name)
        return

    def __add_shared_libraries(self):
        """
        Add shared libraries in WLST offline mode.
        :param parent_dict: the parent dictionary containing the library definitions
        :param parent_name: the name of the parent object
        :param parent_type: the type of the parent object
        :param base_location: the lase location of the parent object
        :raises: DeployException: if a WLST error occurs
        :raises: AliasException: if an error occurs while processing a call into the alias subsystem
        """
        _method_name = 'add_shared_libraries'

        # Don't log the parent dictionary since it will be large
        self.logger.entering(self._parent_name, self._parent_type,
                             class_name=self._class_name, method_name=_method_name)

        shared_libraries = dictionary_utils.get_dictionary_element(self._parent_dict, LIBRARY)
        if len(shared_libraries) == 0:
            self.logger.finer('WLSDPLY-09097', self._parent_type, self._parent_name,
                              class_name=self._class_name, method_name=_method_name)
            return

        root_path = self.alias_helper.get_wlst_subfolders_path(self._base_location)
        shared_library_location = LocationContext(self._base_location).append_location(LIBRARY)
        shared_library_token = self.alias_helper.get_name_token(shared_library_location)
        existing_shared_libraries = deployer_utils.get_existing_object_list(shared_library_location, self.alias_helper)

        for shared_library_name in shared_libraries:
            self.logger.info('WLSDPLY-09132', LIBRARY, shared_library_name, self._parent_type, self._parent_name,
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
            library_name = \
                self.__get_deployable_library_versioned_name(shared_library['SourcePath'], shared_library_name)
            quoted_library_name = self.wlst_helper.get_quoted_name_for_wlst(library_name)

            try:
                self.wlst_helper.cd(root_path)
            except PyWLSTException, pwe:
                ex = exception_helper.create_deploy_exception('WLSDPLY-09091', root_path, shared_library_name,
                                                              pwe.getLocalizedMessage(), error=pwe)
                self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                raise ex
            #
            # TODO(rkillen) - remove this special logic once deployer_utils handles merging of targets.
            #
            # The deploy operation, by default, is additive.  As such, we cannot blindly set the Target
            # attribute for an existing shared library or we will not adhere to the semantics.  This is
            # particularly important for shared libraries in the Oracle Home since other applications
            # may depend on them being deployed to the current set of targets.  For example, FMW Control
            # depends on the JSF and JSTL shared libraries shipped with WebLogic.
            #
            shared_library_location.add_name_token(shared_library_token, quoted_library_name)
            lib_attr_path = self.alias_helper.get_wlst_attributes_path(shared_library_location)
            if quoted_library_name in existing_shared_libraries:
                try:
                    self.wlst_helper.cd(lib_attr_path)
                    library_attrs = self.wlst_helper.lsa()
                except PyWLSTException, pwe:
                    ex = exception_helper.create_deploy_exception('WLSDPLY-09092', quoted_library_name,
                                                                  pwe.getLocalizedMessage(), error=pwe)
                    self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                    raise ex

                wlst_target_name = self.alias_helper.get_wlst_attribute_name(shared_library_location, TARGET)
                if wlst_target_name in library_attrs:
                    original_targets = library_attrs[wlst_target_name]
                    model_targets = shared_library[TARGET]
                    new_targets = deployer_utils.merge_lists(original_targets, model_targets)
                    shared_library[TARGET] = new_targets
            else:
                try:
                    self.wlst_helper.create(quoted_library_name, LIBRARY)
                    self.wlst_helper.cd(lib_attr_path)
                except PyWLSTException, pwe:
                    ex = exception_helper.create_deploy_exception('WLSDPLY-09093', quoted_library_name,
                                                                  pwe.getLocalizedMessage(), error=pwe)
                    self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                    raise ex

            self.set_attributes(shared_library_location, shared_library)
            shared_library_location.remove_name_token(shared_library_token)
        self.logger.exiting(class_name=self._class_name, method_name=_method_name)
        return

    def __add_applications(self):
        """
        Add applications in WLST offline mode.
        :param parent_dict: the parent dictionary containing the application definitions
        :param parent_name: the name of the parent object
        :param parent_type: the type of the parent object
        :param base_location: the lase location of the parent object
        :raises: DeployException: if a WLST error occurs
        :raises: AliasException: if an error occurs while processing a call into the alias subsystem
        """
        _method_name = 'add_applications'
        # Don't log the parent dictionary since it will be large
        self.logger.entering(self._parent_name, self._parent_type,
                             class_name=self._class_name, method_name=_method_name)

        applications = dictionary_utils.get_dictionary_element(self._parent_dict, APPLICATION)
        if len(applications) == 0:
            self.logger.finer('WLSDPLY-09098', self._parent_type, self._parent_name,
                              class_name=self._class_name, method_name=_method_name)
            return

        root_path = self.alias_helper.get_wlst_subfolders_path(self._base_location)
        application_location = LocationContext(self._base_location).append_location(APPLICATION)
        application_token = self.alias_helper.get_name_token(application_location)
        existing_applications = deployer_utils.get_existing_object_list(application_location, self.alias_helper)

        for application_name in applications:
            self.logger.info('WLSDPLY-09132', APPLICATION, application_name, self._parent_type, self._parent_name,
                             class_name=self._class_name, method_name=_method_name)

            application = \
                copy.deepcopy(dictionary_utils.get_dictionary_element(applications, application_name))
            quoted_application_name = self.wlst_helper.get_quoted_name_for_wlst(application_name)
            try:
                self.wlst_helper.cd(root_path)
            except PyWLSTException, pwe:
                ex = exception_helper.create_deploy_exception('WLSDPLY-09094', root_path, application_name,
                                                              pwe.getLocalizedMessage(), error=pwe)
                self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                raise ex
            #
            # TODO(rkillen) - remove this special logic once deployer_utils handles merging of targets.
            #
            # The deploy operation, by default, is additive.  As such, we cannot blindly set the Target
            # attribute for an existing application or we will not adhere to the semantics.
            #
            application_location.add_name_token(application_token, quoted_application_name)
            app_attr_path = self.alias_helper.get_wlst_attributes_path(application_location)
            if quoted_application_name in existing_applications:
                try:
                    self.wlst_helper.cd(app_attr_path)
                    application_attrs = self.wlst_helper.lsa()
                except PyWLSTException, pwe:
                    ex = exception_helper.create_deploy_exception('WLSDPLY-09095', quoted_application_name,
                                                                  pwe.getLocalizedMessage(), error=pwe)
                    self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                    raise ex

                wlst_target_name = self.alias_helper.get_wlst_attribute_name(application_location, TARGET)
                if wlst_target_name in application_attrs:
                    original_targets = application_attrs[wlst_target_name]
                    model_targets = application[TARGET]
                    new_targets = deployer_utils.merge_lists(original_targets, model_targets)
                    application[TARGET] = new_targets
            else:
                try:
                    self.wlst_helper.create(quoted_application_name, APPLICATION)
                    self.wlst_helper.cd(app_attr_path)
                except PyWLSTException, pwe:
                    ex = exception_helper.create_deploy_exception('WLSDPLY-09096', quoted_application_name,
                                                                  pwe.getLocalizedMessage(), error=pwe)
                    self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                    raise ex

            self.set_attributes(application_location, application)
            application_location.remove_name_token(application_token)
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
                ex = exception_helper.create_deploy_exception('WLSDPLY-09107', RESOURCE_GROUP_TEMPLATE, RESOURCES)
                self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                raise ex

            rgt_token = self.alias_helper.get_name_token(location)
            rgt_name = location.get_name_for_token(rgt_token)
            if rgt_name is None:
                ex = exception_helper.create_deploy_exception('WLSDPLY-09108', rgt_token, RESOURCE_GROUP_TEMPLATE)
                self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                raise ex
            elif rgt_name not in resources[RESOURCE_GROUP]:
                ex = exception_helper.create_deploy_exception('WLSDPLY-09109', rgt_name,
                                                              RESOURCE_GROUP_TEMPLATE, RESOURCES)
                self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                raise ex

            result_dict = resources[RESOURCE_GROUP_TEMPLATE][rgt_name]
            result_name = rgt_name
            result_type = RESOURCE_GROUP_TEMPLATE

        elif top_folder == PARTITION:
            if PARTITION not in resources:
                ex = exception_helper.create_deploy_exception('WLSDPLY-09107', PARTITION, RESOURCES)
                self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                raise ex

            part_location = LocationContext().append_location(PARTITION)
            part_token = self.alias_helper.get_name_token(part_location)
            part_name = location.get_name_for_token(part_token)
            if part_name is None:
                ex = exception_helper.create_deploy_exception('WLSDPLY-09108', part_token, PARTITION)
                self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                raise ex
            elif part_name not in resources[PARTITION]:
                ex = exception_helper.create_deploy_exception('WLSDPLY-09109', part_name, PARTITION, RESOURCES)
                self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                raise ex

            part_dict = resources[PARTITION][part_name]
            path = RESOURCES + '/' + PARTITION + '/' + part_name
            result_dict, result_name = self.__get_parent_dict_and_name_for_resource_group(location, part_dict, path)
            result_type = RESOURCE_GROUP

        else:
            ex = exception_helper.create_deploy_exception('WLSDPLY-09106', top_folder)
            self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

        self.logger.exiting(class_name=self._class_name, method_name=_method_name,
                            result=[result_name, result_type])
        return result_dict, result_name, result_type

    def __get_parent_dict_and_name_for_resource_group(self, location, parent_dict, parent_path):
        _method_name = '__get_parent_dict_and_name_for_resource_group'

        self.logger.entering(str(location), parent_path, class_name=self._class_name, method_name=_method_name)
        if RESOURCE_GROUP not in parent_dict:
            ex = exception_helper.create_deploy_exception('WLSDPLY-09107', RESOURCE_GROUP, parent_path)
            self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

        rg_token = self.alias_helper.get_name_token(location)
        rg_name = location.get_name_for_token(rg_token)
        if rg_name is None:
            ex = exception_helper.create_deploy_exception('WLSDPLY-09108', rg_token, RESOURCE_GROUP)
            self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex
        elif rg_name not in parent_dict[RESOURCE_GROUP]:
            ex = exception_helper.create_deploy_exception('WLSDPLY-09109', rg_name, RESOURCE_GROUP, parent_path)
            self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex
        return parent_dict[RESOURCE_GROUP][rg_name], rg_name

    # This method throws an error if called for MT resources.  If we ever want to support MT online
    # deployment, we will need to enhance this method accordingly.
    def __get_library_references(self):
        _method_name = '__get_library_references'

        self.logger.entering(class_name=self._class_name, method_name=_method_name)
        if self._base_location.get_folder_path() != '/':
            ex = exception_helper.create_deploy_exception('WLSDPLY-09110')
            self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

        existing_libraries = OrderedDict()
        try:
            server_runtime_path = 'domainRuntime:/ServerRuntimes/'
            server_runtimes = self.wlst_helper.get_existing_object_list('domainRuntime:/ServerRuntimes')

            for serverruntime in server_runtimes:
                this_libraryruntime_path = server_runtime_path + serverruntime + '/LibraryRuntimes/'
                libs = self.wlst_helper.get_existing_object_list(this_libraryruntime_path)

                for lib in libs:
                    attrs = self.__list_attributes_with_fixes(this_libraryruntime_path + lib)
                    attr_configs = self.__list_attributes_with_fixes('serverConfig:/Libraries/' + lib)

                    config_targets = self.wlst_helper.lsc('serverConfig:/Libraries/' + lib + '/Targets')
                    absolute_source_path = attr_configs['AbsoluteSourcePath']
                    deployment_order = attr_configs['DeploymentOrder']
                    libmd5 = self.__get_filemd5(absolute_source_path)

                    if string_utils.to_boolean(attrs['Referenced']) is True:
                        referenced_path = this_libraryruntime_path + lib + '/ReferencingRuntimes/'
                        referenced_by = self.wlst_helper.get_existing_object_list(referenced_path)
                        self.wlst_helper.cd(this_libraryruntime_path + lib + '/ReferencingRuntimes/')
                        for app_ref in referenced_by:
                            # what if it is partitioned ?
                            ref_attrs = self.__list_attributes_with_fixes(app_ref)
                            app_type = ref_attrs['Type']
                            app_id = None
                            if app_type == 'ApplicationRuntime':
                                app_id = ref_attrs['ApplicationName']
                            if app_type == 'WebAppComponentRuntime':
                                app_id = ref_attrs['ApplicationIdentifier']

                            self.__update_ref_dictionary(existing_libraries, lib, absolute_source_path, libmd5,
                                                         config_targets,
                                                         deployorder=deployment_order, app_name=app_id)
                    else:
                        self.__update_ref_dictionary(existing_libraries, lib, absolute_source_path, libmd5,
                                                     config_targets)

        except PyWLSTException, e:
            ex = exception_helper.create_deploy_exception('WLSDPLY-09013', e.getLocalizedMessage(), error=e)
            self.logger.throwing(ex, class_name=self._class_name, method_name='get_library_references')
            raise ex
        return existing_libraries

    def __update_ref_dictionary(self, ref_dictionary, lib_name, absolute_sourcepath, libmd5,
                                configured_targets, absolute_planpath=None,
                                planmd5=None, app_name=None, source_path=None, deployorder=None):
        if ref_dictionary.has_key(lib_name) is False:
            ref_dictionary[lib_name] = OrderedDict()
            ref_dictionary[lib_name]['sourcePath'] = absolute_sourcepath
            ref_dictionary[lib_name]['md5'] = libmd5
            ref_dictionary[lib_name]['planPath'] = absolute_planpath
            ref_dictionary[lib_name]['planmd5'] = planmd5
            ref_dictionary[lib_name]['target'] = configured_targets

        if app_name is not None:
            lib = ref_dictionary[lib_name]
            if lib.has_key('referencingApp') is False:
                lib['referencingApp'] = OrderedDict()
            referencing_app = lib['referencingApp']
            if referencing_app.has_key(app_name) is False:
                referencing_app[app_name] = OrderedDict()
            referencing_app[app_name]['DeploymentOrder'] = deployorder
        return

    def __stop_app(self, application_name, partition_name=None, timeout=None):
        _method_name = '__stop_app'

        try:
            self.logger.info('WLSDPLY-09005', application_name, class_name=self._class_name, method_name=_method_name)
            progress = self.wlst_helper.stop_application(application_name, partition=partition_name, timeout=timeout)
            while progress.isRunning():
                continue
        except PyWLSTException, e:
            ex = exception_helper.create_deploy_exception('WLSDPLY-09021', application_name,
                                                          e.getLocalizedMessage(), error=e)
            self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

    def __start_app(self, application_name, partition_name=None):
        _method_name = '__start_app'

        try:
            self.logger.info('WLSDPLY-09006', application_name, class_name=self._class_name, method_name=_method_name)
            self.wlst_helper.start_application(application_name, partition=partition_name)
        except PyWLSTException, e:
            ex = exception_helper.create_deploy_exception('WLSDPLY-09022', application_name,
                                                          e.getLocalizedMessage(), error=e)
            self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

    def __deploy_app_online(self, application_name, source_path, targets, unzip_root, plan=None, partition=None,
                            resource_group=None, resourcegroup_template=None, options=None):
        _method_name = '__deploy_app_online'

        self.logger.info('WLSDPLY-09009', application_name, class_name=self._class_name, method_name=_method_name)

        if os.path.isabs(source_path) is False and unzip_root is not None:
            source_path = unzip_root + '/' + source_path

        if source_path is not None and not os.path.exists(source_path):
            ex = exception_helper.create_deploy_exception('WLSDPLY-09026', application_name, str(source_path))
            self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

        if options is not None and 'libraryModule' in options and string_utils.to_boolean(options['libraryModule']):
            computed_name = self.__get_deployable_library_versioned_name(source_path, application_name)
            application_name = computed_name

        # build the dictionary of named arguments to pass to the deploy_application method
        kwargs = {'path': str(source_path), 'targets': str(targets)}
        if plan is not None:
            if not os.path.isabs(plan) and unzip_root is not None:
                plan = unzip_root + '/' + plan

            if not os.path.exists(plan):
                ex = exception_helper.create_deploy_exception('WLSDPLY-09027', application_name, str(plan))
                self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                raise ex
            kwargs['planPath'] = str(plan)
        if resource_group is not None:
            kwargs['resouceGroup'] = str(resource_group)
        if resourcegroup_template is not None:
            kwargs['resourceGroupTemplate'] = str(resourcegroup_template)
        if partition is not None:
            kwargs['partition'] = str(partition)
        if options is not None:
            kwargs.update(options)

        self.logger.fine('WLSDPLY-09010', application_name, kwargs,
                         class_name=self._class_name, method_name=_method_name)
        try:
            self.wlst_helper.deploy_application(application_name, **kwargs)
        except PyWLSTException, e:
            ex = exception_helper.create_deploy_exception('WLSDPLY-09025', application_name,
                                                          e.getLocalizedMessage(), error=e)
            self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex
        return

    def __undeploy_app(self, application_name, library_module='false', partition_name=None,
                       resource_group_template=None, timeout=None):
        _method_name = '__undeploy_app'

        self.logger.info('WLSDPLY-09007', application_name, class_name=self._class_name, method_name=_method_name)
        try:
            self.wlst_helper.undeploy_application(application_name, libraryModule=library_module,
                                                  partition=partition_name,
                                                  resourceGroupTemplate=resource_group_template, timeout=timeout)
        except PyWLSTException, e:
            ex = exception_helper.create_deploy_exception('WLSDPLY-09023', application_name,
                                                          e.getLocalizedMessage(), error=e)
            self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex
        return

    def __redeploy_app(self, application_name):
        _method_name = '__redeploy_app'

        self.logger.info('WLSDPLY-09008', application_name, class_name=self._class_name, method_name=_method_name)
        try:
            self.wlst_helper.redeploy_application(application_name)
        except PyWLSTException, e:
            ex = exception_helper.create_deploy_exception('WLSDPLY-09024', application_name,
                                                          e.getLocalizedMessage(), error=e)
            self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex
        return

    def __is_app_configured(self, application_name, shared_lib=False):
        found = False
        if shared_lib:
            libs = self.wlst_helper.get_existing_object_list('serverConfig:/Libraries')
            if application_name in libs:
                found = True
        else:
            apps = self.wlst_helper.get_existing_object_list('serverConfig:/AppDeployments')
            if application_name in apps:
                found = True

        return found

    def __is_app_running(self, running_apps, app):
        return running_apps is not None and app in running_apps

    def __get_existing_apps(self):
        _method_name = '__get_existing_apps'

        ref_dictionary = OrderedDict()
        try:
            # cannot use ApplicationRuntime since it includes datasources as ApplicationRuntime
            #
            apps = self.wlst_helper.get_existing_object_list('serverConfig:/AppDeployments')
            runningapps = \
                self.wlst_helper.get('domainRuntime:/AppRuntimeStateRuntime/AppRuntimeStateRuntime/ApplicationIds')

            for app in apps:
                if self.__is_app_running(runningapps, app):
                    attrconfigs = self.__list_attributes_with_fixes('serverConfig:/AppDeployments/' + app)

                    absolute_sourcepath = attrconfigs['AbsoluteSourcePath']
                    absolute_planpath = attrconfigs['AbsolutePlanPath']
                    deployment_order = attrconfigs['DeploymentOrder']
                    appmd5 = self.__get_filemd5(absolute_sourcepath)
                    if absolute_planpath != None:
                        planmd5 = self.__get_filemd5(absolute_planpath)
                    else:
                        planmd5 = None

                    self.__update_ref_dictionary(ref_dictionary, app, absolute_sourcepath, appmd5, None,
                                                 absolute_planpath=absolute_planpath, deployorder=deployment_order,
                                                 planmd5=planmd5)
        except PyWLSTException, e:
            ex = exception_helper.create_deploy_exception('WLSDPLY-09014', e.getLocalizedMessage(), error=e)
            self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex
        return ref_dictionary

    def __unzip_archive(self, zipname, unzip_root, zipentries=None):
        __method_name = '__unzip_archive'

        try:
            # no unzip_root specified skip unzip

            if unzip_root is None:
                return

            if not os.path.exists(unzip_root):
                os.makedirs(unzip_root)
            archive = zipfile.ZipFile(zipname)

            if zipentries is None:
                zipentries = archive.namelist()

            for entry in zipentries:
                if entry is None:
                    continue
                if os.path.isabs(entry) is False:
                    index = entry.rfind('/')
                    basepath = unzip_root + os.sep + entry[0:index]
                    if not os.path.exists(basepath):
                        os.makedirs(basepath)

                    filename = entry[index+1:]
                    data = archive.read(entry)
                    targetfile = basepath + os.sep + filename

                    if os.path.isdir(targetfile):
                        if not os.path.exists(targetfile):
                            os.makedirs(targetfile)
                    else:
                        fh = open(targetfile, "wb")
                        fh.write(data)
                        fh.close()
        except KeyError, ke:
            ex = exception_helper.create_deploy_exception('WLSDPLY-09015', str(ke), error=ke)
            self.logger.throwing(ex, class_name=self._class_name, method_name=__method_name)
            raise ex
        except (zipfile.BadZipfile, IOError), ioe:
            ex = exception_helper.create_deploy_exception('WLSDPLY-09016', str(ioe), error=ioe)
            self.logger.throwing(ex, class_name=self._class_name, method_name=__method_name)
            raise ex
        return

    def __handle_buildin_libraries(self, targets_not_changed, modellibs, lib, existing_lib_targets_set,
                                   model_targets_set):
        if targets_not_changed or existing_lib_targets_set.issuperset(model_targets_set):
            self.__remove_lib_from_deployment(modellibs, lib)
        else:
            # adjust the targets to only the new ones
            # no need to check md5 for weblogic distributed libraries
            adjusted_set = model_targets_set.difference(existing_lib_targets_set)
            adjusted_targets = ','.join(adjusted_set)
            modellibs[lib]['Target'] = adjusted_targets

    def __build_library_deploy_strategy(self, modellibs, existing_libs, existing_lib_refs,
                                        archive_file, stop_applist, undate_librarylist):
        if modellibs is not None:
            for lib, lib_dict in modellibs.iteritems():
                for param in ['SourcePath', 'PlanDir', 'PlanPath', 'InstallDir']:
                    self.model_context.replace_tokens('Library', lib, param, lib_dict)

                if lib in existing_libs:
                    existing_lib_ref = dictionary_utils.get_dictionary_element(existing_lib_refs, lib)

                    # skipping absolute path libraries if they are the same
                    model_src_path = dictionary_utils.get_element(lib_dict, 'SourcePath')
                    model_targets = dictionary_utils.get_element(lib_dict, 'Target')

                    existing_lib_targets = dictionary_utils.get_element(existing_lib_ref, 'target')
                    model_targets_set = Set(model_targets.split(','))
                    existing_lib_targets_set = Set(existing_lib_targets)

                    targets_not_changed = existing_lib_targets_set == model_targets_set
                    # if it is weblogic distributed libraries and the targets are the same then no need to deploy

                    existing_src_path = dictionary_utils.get_element(existing_lib_ref, 'sourcePath')
                    if os.path.isabs(model_src_path) and existing_src_path == model_src_path:
                        self.__handle_buildin_libraries(targets_not_changed, modellibs, lib, existing_lib_targets_set,
                                                        model_targets_set)
                        continue

                    # user libraries
                    model_libmd5 = self.__get_archive_binarymd5(archive_file, model_src_path)
                    existing_libmd5 = self.__get_filemd5(existing_src_path)
                    if model_libmd5 != existing_libmd5:
                        # updated library add referncing apps to stop list
                        #
                        #   the target needs to be set to the union to avoid changing target in subsequent deploy
                        #   affecting existing referencing apps,
                        #
                        union_targets_set = existing_lib_targets_set.union(model_targets_set)
                        lib_dict['Target'] = ','.join(union_targets_set)

                        self.__add_ref_apps_to_stoplist(stop_applist, existing_lib_refs, lib)
                        undate_librarylist.append(lib)
                    else:
                        # same as before no need to deploy, nothing change and same targets
                        if existing_lib_targets_set.issuperset(model_targets_set):
                            self.__remove_lib_from_deployment(modellibs, lib)
                        else:
                            # adjust the targets to only the new targets
                            adjusted_set = model_targets_set.difference(existing_lib_targets_set)
                            adjusted_targets = ','.join(adjusted_set)
                            lib_dict['Target'] = adjusted_targets

    def __build_app_deploy_strategy(self, modelapps, existing_apps, existing_app_refs, archive_file,
                                    stopandundeploy_applist):
        if modelapps is not None:
            for app, app_dict in modelapps.iteritems():
                for param in ['SourcePath', 'PlanDir', 'PlanPath', 'InstallDir']:
                    if param in app_dict:
                        self.model_context.replace_tokens('Application', app, param, app_dict)

                if app in existing_apps:
                    existing_app_ref = dictionary_utils.get_dictionary_element(existing_app_refs, app)
                    plan_path = dictionary_utils.get_element(existing_app_ref, 'planPath')
                    src_path = dictionary_utils.get_element(existing_app_ref, 'sourcePath')
                    model_srcmd5 = \
                        self.__get_archive_binarymd5(archive_file, dictionary_utils.get_element(app_dict, 'SourcePath'))
                    model_planmd5 = \
                        self.__get_archive_binarymd5(archive_file, dictionary_utils.get_element(app_dict, 'PlanPath'))

                    existing_srcmd5 = self.__get_filemd5(src_path)
                    existing_planmd5 = self.__get_filemd5(plan_path)
                    if model_srcmd5 == existing_srcmd5:
                        if model_planmd5 == existing_planmd5:
                            self.__remove_app_from_deployment(modelapps, app)
                        else:
                            self.__add_refapps_to_stopandundeploylist(stopandundeploy_applist, app)
                    else:
                        # updated app
                        self.__add_refapps_to_stopandundeploylist(stopandundeploy_applist, app)
        return

    def __deploy_model_libraries(self, modellibs, archive_file, unzip_root):
        if modellibs is not None:
            deploy_ordered_keys = self.__get_deploy_orders(modellibs)
            for lib in deploy_ordered_keys:
                lib_dict = modellibs[lib]
                src_path = dictionary_utils.get_element(lib_dict, 'SourcePath')
                plan_file = dictionary_utils.get_element(lib_dict, 'PlanPath')
                targets = dictionary_utils.get_element(lib_dict, 'Target')
                options = self.__get_deploy_options(modellibs, lib, library_module='true')
                self.__unzip_archive(archive_file, unzip_root, [src_path, plan_file])
                self.__deploy_app_online(lib, src_path, targets, plan=plan_file,
                                         unzip_root=unzip_root, options=options)
        return

    def __deploy_model_applications(self, modelapps, archive_file, unzip_root, deployed_applist):
        if modelapps is not None:
            deploy_ordered_keys = self.__get_deploy_orders(modelapps)
            for app in deploy_ordered_keys:
                app_dict = modelapps[app]
                src_path = dictionary_utils.get_element(app_dict, 'SourcePath')
                plan_file = dictionary_utils.get_element(app_dict, 'PlanPath')
                targets = dictionary_utils.get_element(app_dict, 'Target')
                options = self.__get_deploy_options(modelapps, app, library_module='false')
                self.__unzip_archive(archive_file, unzip_root, [src_path, plan_file])
                self.__deploy_app_online(app, src_path, targets, plan=plan_file,
                                         unzip_root=unzip_root, options=options)
                deployed_applist.append(app)
        return

    def __get_deploy_options(self, model_apps, app_name, library_module='false'):

        deploy_options = OrderedDict()
        # not sure about altDD, altWlsDD
        for option in ['DeploymentOrder', 'SecurityDDModel', 'PlanStageMode']:
            app = dictionary_utils.get_dictionary_element(model_apps, app_name)
            value = dictionary_utils.get_element(app, option)

            option_name = ''
            if option == 'DeploymentOrder':
                option_name = 'deploymentOrder'
            elif option == 'SecurityDDModel':
                option_name = 'securityModel'
            elif option == 'PlanStageMode':
                option_name = 'planStageMode'

            if value is not None:
                deploy_options[option_name] = str(value)

        if library_module == 'true':
            deploy_options['libraryModule'] = 'true'

        if len(deploy_options) == 0:
            return None
        return deploy_options

    def __start_all_apps(self, deployed_applist):

        temp_app_dict = OrderedDict()
        app_wlst_path = 'serverConfig:/AppDeployments/'
        for app in deployed_applist:

            self.wlst_helper.cd(app_wlst_path + app)
            deployment_order = self.wlst_helper.get('DeploymentOrder')

            if temp_app_dict.has_key(app) is False:
                temp_app_dict[app] = OrderedDict()
            temp_app_dict[app]['DeploymentOrder'] = deployment_order

        start_order = self.__get_deploy_orders(temp_app_dict)
        for app in start_order:
            self.__start_app(app)
        return

    def __add_ref_apps_to_stoplist(self, stop_applist, lib_refs, lib_name):
        if lib_refs[lib_name].has_key('referencingApp'):
            apps = lib_refs[lib_name]['referencingApp'].keys()
            for app in apps:
                stop_applist.append(app)
        return

    def __add_refapps_to_stopandundeploylist(self, stopandundeploy_applist, app_name):
        stopandundeploy_applist.append(app_name)
        return

    def __remove_lib_from_deployment(self, modeldict, libname):
        self.logger.info('WLSDPLY-09012', libname,
                         class_name=self._class_name, method_name='remove_lib_from_deployment')
        modeldict.pop(libname)
        return

    def __remove_app_from_deployment(self, modeldict, appname):
        self.logger.info('WLSDPLY-09012', appname,
                         class_name=self._class_name, method_name='remove_app_from_deployment')
        modeldict.pop(appname)
        return

    def __get_archive_entrypath(self, sourcepath, itemmap):
        if sourcepath is None:
            return None
        tokens = sourcepath.split('/')
        basename = tokens[len(tokens)-1]
        if itemmap is not None:
            return itemmap.get(basename)

        return None

    def __get_archive_binarymd5(self, archivefile, binarypath):
        _method_name = '__get_archive_binarymd5'
        try:
            if binarypath is None:
                md5 = None
            elif os.path.isabs(binarypath):
                md5 = self.__get_filemd5(binarypath)
            else:
                archive = zipfile.ZipFile(archivefile)
                file_bytes = archive.read(binarypath)
                md5 = self.__get_bytesmd5(file_bytes)
        except (zipfile.BadZipfile, IOError), ioe:
            ex = exception_helper.create_deploy_exception('WLSDPLY-09017', str(ioe), error=ioe)
            self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex
        except KeyError, ke:
            ex = exception_helper.create_deploy_exception('WLSDPLY-09019', str(ke), error=ke)
            self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex
        except (NoSuchAlgorithmException, DigestException), ee:
            ex = exception_helper.create_deploy_exception('WLSDPLY-09018', ee.getLocalizedMessage(), error=ee)
            self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex
        return md5

    def __list_attributes_with_fixes(self, path):
        try:
            result_map = self.wlst_helper.lsa(path)
            for item in result_map:
                if result_map[item] is not None:
                    result_map[item] = result_map[item].rstrip()
                    if result_map[item] == 'null':
                        result_map[item] = None
                else:
                    result_map[item] = None
            return result_map
        except PyWLSTException, e:
            raise e

    def __get_filemd5(self, filename):
        _method_name = '__get_filemd5'

        md5 = None
        if filename is not None:
            try:
                md = MessageDigest.getInstance('MD5')
                data = open(filename, 'rb').read()
                md.update(data)
                md5array = md.digest()
                buf = StringBuilder()
                for md5byte in md5array:
                    buf.append(String.format('%02x', [0xff & md5byte]))

                md5 = buf.toString()
            except IOError, ioe:
                ex = exception_helper.create_deploy_exception('WLSDPLY-09020', str(ioe), error=ioe)
                self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                raise ex
            except (NoSuchAlgorithmException, DigestException), ee:
                ex = exception_helper.create_deploy_exception('WLSDPLY-09018', ee.getLocalizedMessage(), error=ee)
                self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                raise ex
        return md5

    def __get_bytesmd5(self, inputbytes):
        _method_name = '__get_bytesmd5'

        md5 = None
        if inputbytes is not None:
            try:
                md = MessageDigest.getInstance('MD5')
                md.update(inputbytes)
                md5array = md.digest()
                buf = StringBuilder()
                for md5byte in md5array:
                    buf.append(String.format('%02x', [0xff & md5byte]))

                md5 = buf.toString()
            except (NoSuchAlgorithmException, DigestException), ee:
                ex = exception_helper.create_deploy_exception('WLSDPLY-09018', ee.getLocalizedMessage(), error=ee)
                self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                raise ex
        return md5

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
        versioned_name = ''

        old_name_tuple = self.__get_library_name_components(model_name)
        try:
            source_path = self.model_context.replace_token_string(source_path)
            archive = zipfile.ZipFile(source_path)
            manifest = archive.read('META-INF/MANIFEST.MF')
            tokens = manifest.split()
            extension_index = tokens.index('Extension-Name:')
            spec_index = tokens.index('Specification-Version:')
            impl_index = tokens.index('Implementation-Version:')

            if extension_index < 0:
                # No extension specified so use the first element of the supplied name as the extension name
                versioned_name += old_name_tuple[self._EXTENSION_INDEX]
            elif len(tokens) > extension_index:
                versioned_name += tokens[extension_index + 1]
            else:
                ex = exception_helper.create_deploy_exception('WLSDPLY-09099', model_name, source_path, tokens)
                self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                raise ex

            if spec_index != -1:
                if len(tokens) > spec_index:
                    versioned_name += '#' + tokens[spec_index + 1]

                    # Cannot specify an impl version without a spec version
                    if impl_index != -1:
                        if len(tokens) > impl_index:
                            versioned_name += '@' + tokens[impl_index + 1]
                        else:
                            ex = exception_helper.create_deploy_exception('WLSDPLY-09101', model_name,
                                                                          source_path, tokens)
                            self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                            raise ex
                else:
                    ex = exception_helper.create_deploy_exception('WLSDPLY-09100', model_name, source_path, tokens)
                    self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                    raise ex

            self.logger.info('WLSDPLY-09061', model_name, versioned_name,
                             class_name=self._class_name, method_name=_method_name)
        except (zipfile.BadZipfile, IOError), e:
            ex = exception_helper.create_deploy_exception('WLSDPLY-09104', model_name, source_path, str(e), error=e)
            self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

        self.logger.exiting(class_name=self._class_name, method_name=_method_name, result=versioned_name)
        return versioned_name

    def __get_library_name_components(self, name):
        _method_name = '__get_library_name_components'

        self.logger.entering(name, class_name=self._class_name, method_name=_method_name)
        items = name.split('#')
        name_tuple = [items[0]]
        if len(items) == 2:
            ver_items = items[1].split('@')
            name_tuple.append(ver_items[0])
            if len(ver_items) == 2:
                name_tuple.append(ver_items[1])
            elif len(ver_items) == 1:
                # no implementation version specified...
                pass
            else:
                ex = exception_helper.create_deploy_exception('WLSDPLY-09103', name, len(ver_items) - 1)
                self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                raise ex
        elif len(items) == 1:
            #
            # In WLST online mode, WLST will go figure out the right name for us so we can just use the existing name.
            if self.wlst_mode == WlstModes.ONLINE:
                self.logger.exiting(class_name=self._class_name, method_name=_method_name, result=name)
                return name
            else:
                # Otherwise, no spec version specified so nothing to add to name_tuple
                pass
        else:
            ex = exception_helper.create_deploy_exception('WLSDPLY-09102', name, len(items) - 1)
            self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex
        self.logger.exiting(class_name=self._class_name, method_name=_method_name, result=name_tuple)
        return name_tuple

    def __find_deployorder_list(self, app_dict, ordered_list, order):
        result = []
        for item in ordered_list:
            if order == app_dict[item]['DeploymentOrder']:
                result.append(item)
        return result

    def __get_deploy_orders(self, myapps):
        name_sorted_keys = myapps.keys()
        name_sorted_keys.sort()

        has_deploy_order_apps = []

        pop_keys = []
        for key in name_sorted_keys:
            if myapps[key].has_key('DeploymentOrder'):
                has_deploy_order_apps.append(key)
                pop_keys.append(key)

        for key in pop_keys:
            name_sorted_keys.remove(key)

        # now sort the has_deploy_order_apps

        deployorder_list = []

        for item in has_deploy_order_apps:
            deploy_order = myapps[item]['DeploymentOrder']
            if deploy_order not in deployorder_list:
                deployorder_list.append(deploy_order)

        deployorder_list.sort()
        ordered_list = []
        for order in deployorder_list:
            thislist = self.__find_deployorder_list(myapps, has_deploy_order_apps, order)
            ordered_list.extend(thislist)

        result_deploy_order = []

        if ordered_list is not None:
            result_deploy_order.extend(ordered_list)

        if name_sorted_keys is not None:
            result_deploy_order.extend(name_sorted_keys)

        self.logger.fine('WLSDPLY-09028', str(result_deploy_order), class_name=self._class_name,
                         method_name='get_deploy_orders')

        return result_deploy_order

