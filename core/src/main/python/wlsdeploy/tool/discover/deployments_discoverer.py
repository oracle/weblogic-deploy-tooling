"""
Copyright (c) 2017, 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import os

from java.io import BufferedReader
from java.io import BufferedWriter
from java.io import FileReader
from java.io import FileWriter
from java.lang import IllegalArgumentException
from java.lang import StringBuilder
from java.util.regex import Pattern

from oracle.weblogic.deploy.util import PyOrderedDict as OrderedDict
from oracle.weblogic.deploy.util import FileUtils
from oracle.weblogic.deploy.util import StringUtils
from oracle.weblogic.deploy.util import WLSDeployArchiveIOException
from oracle.weblogic.deploy.util import WLSDeployArchive

from wlsdeploy.aliases.alias_constants import PASSWORD_TOKEN
from wlsdeploy.aliases import model_constants
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import PLAN_DIR
from wlsdeploy.aliases.model_constants import PLAN_PATH
from wlsdeploy.aliases.model_constants import SOURCE_PATH
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception import exception_helper
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.discover import discoverer
from wlsdeploy.tool.discover.discoverer import Discoverer
from wlsdeploy.util import dictionary_utils
from wlsdeploy.util import path_helper

_class_name = 'DeploymentsDiscoverer'
_logger = PlatformLogger(discoverer.get_discover_logger_name())


class DeploymentsDiscoverer(Discoverer):
    """
    Discover the application and shared library deployments from the weblogic domain. Collect all deployment
    binaries and plans into the discovery archive file.
    """

    def __init__(self, model_context, deployments_dictionary, base_location,
                 wlst_mode=WlstModes.OFFLINE, aliases=None, credential_injector=None, extra_tokens=None):
        Discoverer.__init__(self, model_context, base_location, wlst_mode, aliases, credential_injector)
        self._dictionary = deployments_dictionary
        self._extra_tokens = extra_tokens

    def discover(self):
        """
        Discover the deployment information from the domain. This is the API method to discover all
        deployment information from the domain.
        :return: dictionary containing the deployment information
        """
        _method_name = 'discover'
        _logger.entering(class_name=_class_name, method_name=_method_name)
        _logger.info('WLSDPLY-06380', class_name=_class_name, method_name=_method_name)
        model_top_folder_name, libraries = self.get_shared_libraries()
        discoverer.add_to_model_if_not_empty(self._dictionary, model_top_folder_name, libraries)
        model_top_folder_name, applications = self.get_applications()
        discoverer.add_to_model_if_not_empty(self._dictionary, model_top_folder_name, applications)
        _logger.exiting(class_name=_class_name, method_name=_method_name)
        return self._dictionary

    def get_shared_libraries(self):
        """
        Discover the shared library deployment information from the domain. Collect any shared library binaries into
        the discovered archive file. If the shared library cannot be collected into the archive, the shared library
        source path will be removed from the model and the shared library un-targeted.
        :return: model name for the dictionary and the dictionary containing the shared library information
        """
        _method_name = 'get_shared_libraries'
        _logger.entering(class_name=_class_name, method_name=_method_name)
        result = OrderedDict()
        model_top_folder_name = model_constants.LIBRARY
        location = LocationContext(self._base_location)
        location.append_location(model_top_folder_name)
        libraries = self._find_names_in_folder(location)
        if libraries:
            _logger.info('WLSDPLY-06381', len(libraries), class_name=_class_name, method_name=_method_name)
            typedef = self._model_context.get_domain_typedef()
            name_token = self._aliases.get_name_token(location)
            for library in libraries:
                if typedef.is_filtered(location, library):
                    _logger.info('WLSDPLY-06401', typedef.get_domain_type(), library, class_name=_class_name,
                                 method_name=_method_name)
                else:
                    _logger.info('WLSDPLY-06382', library, class_name=_class_name, method_name=_method_name)
                    location.add_name_token(name_token, library)
                    result[library] = OrderedDict()
                    self._populate_model_parameters(result[library], location)
                    self._add_shared_libraries_to_archive(library, result[library])
                    self._discover_subfolders(result[library], location)
                    location.remove_name_token(name_token)

        _logger.exiting(class_name=_class_name, method_name=_method_name, result=model_top_folder_name)
        return model_top_folder_name, result

    def _add_shared_libraries_to_archive(self, library_name, library_dict):
        """
        Add the binary or directory referenced by the shared library to the archive file.
        If the binary can not be located and added to the archive file, un-target the library and log the problem.
        :param library_name: name of the shared library
        :param library_dict: containing the shared library information
        :raise DiscoverException: An unexpected exception occurred trying to write the library to the archive
        """
        _method_name = 'add_shared_library_to_archive'
        _logger.entering(library_name, class_name=_class_name, method_name=_method_name)

        archive_file = self._model_context.get_archive_file()
        if model_constants.SOURCE_PATH in library_dict:
            file_name = library_dict[model_constants.SOURCE_PATH]
            if file_name:
                file_name_path = file_name
                if not self._model_context.is_remote():
                    file_name_path = self._convert_path(file_name)
                if self._is_file_to_exclude_from_archive(file_name_path):
                    _logger.info('WLSDPLY-06383', library_name, class_name=_class_name, method_name=_method_name)
                else:
                    new_source_name = None
                    if self._model_context.is_remote():
                        new_source_name = WLSDeployArchive.getSharedLibraryArchivePath(file_name_path)
                        self.add_to_remote_map(file_name_path, new_source_name,
                                           WLSDeployArchive.ArchiveEntryType.SHARED_LIBRARY.name())
                    elif not self._model_context.is_skip_archive():
                        _logger.info('WLSDPLY-06384', library_name, file_name_path, class_name=_class_name,
                                     method_name=_method_name)
                        try:

                            if self._model_context.is_ssh():
                                file_name_path = self.download_deployment_from_remote_server(file_name_path,
                                                                                            self.download_temporary_dir,
                                                                                            "sharedLibraries")

                            new_source_name = archive_file.addSharedLibrary(file_name_path)
                        except IllegalArgumentException, iae:
                            if model_constants.TARGET in library_dict:
                                target = library_dict[model_constants.TARGET]
                                del library_dict[model_constants.TARGET]
                                _logger.warning('WLSDPLY-06385', library_name, target, iae.getLocalizedMessage(),
                                                file_name_path, class_name=_class_name, method_name=_method_name)
                            else:
                                _logger.warning('WLSDPLY-06386', library_name, iae.getLocalizedMessage(), file_name_path,
                                                class_name=_class_name, method_name=_method_name)
                        except WLSDeployArchiveIOException, wioe:
                            de = exception_helper.create_discover_exception('WLSDPLY-06387', library_name, file_name_path,
                                                                            wioe.getLocalizedMessage())
                            _logger.throwing(class_name=_class_name, method_name=_method_name, error=de)
                            raise de
                    if new_source_name is not None:
                        library_dict[model_constants.SOURCE_PATH] = new_source_name
                        _logger.finer('WLSDPLY-06388', library_name, new_source_name, class_name=_class_name,
                                      method_name=_method_name)
                    self._add_shared_libray_plan_to_archive(library_name, library_dict)

        _logger.exiting(class_name=_class_name, method_name=_method_name)

    def _add_shared_libray_plan_to_archive(self, library_name, library_dict):
        """
        Add the shared library deployment plan to the archive file. Create a unique name for the deployment plan from
        the library binary name and the plan name. If the plan cannot be added to the archive file, the plan
        information will remain in the model library entry, but a warning will be generated.
        :param library_name: shared library name in the model
        :param library_dict: containing the library information
        :raise: DiscoverException: An unexpected exception occurred trying to write the plan to the archive file
        """
        _method_name = 'add_application_plan_to_archive'
        _logger.entering(library_name, class_name=_class_name, method_name=_method_name)
        archive_file = self._model_context.get_archive_file()
        if model_constants.PLAN_PATH in library_dict:
            library_source_name = library_dict[model_constants.SOURCE_PATH]
            plan_path = library_dict[model_constants.PLAN_PATH]
            if plan_path:
                _logger.info('WLSDPLY-06389', library_name, plan_path, class_name=_class_name, method_name=_method_name)
                new_plan_name = self.get_shlib_plan(plan_path, library_dict, library_source_name, archive_file)
                if new_plan_name is not None:
                    _logger.finer('WLSDPLY-06390', library_name, new_plan_name,
                                  class_name=_class_name, method_name=_method_name)
                    library_dict[model_constants.PLAN_PATH] = new_plan_name
        _logger.exiting(class_name=_class_name, method_name=_method_name)

    def get_shlib_plan(self, plan_path, library_dict, library_source_name, archive_file):
        _method_name = 'get_shlib_plan'

        plan_file_name = plan_path
        if not self._model_context.is_remote():
            plan_path = self._convert_path(plan_path)
            plan_dir = None
            if model_constants.PLAN_DIR in library_dict:
                plan_dir = library_dict[model_constants.PLAN_DIR]
                del library_dict[model_constants.PLAN_DIR]
            plan_file_name = self._resolve_deployment_plan_path(plan_dir, plan_path)
        new_plan_name = None
        if self._model_context.is_remote():
            new_plan_name = WLSDeployArchive.getShLibArchivePath(plan_path)
            self.add_to_remote_map(plan_path, new_plan_name,
                                   WLSDeployArchive.ArchiveEntryType.SHLIB_PLAN.name())
        elif not self._model_context.is_skip_archive():
            try:
                if self._model_context.is_ssh():
                    plan_file_name = self.download_deployment_from_remote_server(plan_file_name,
                                                                              self.download_temporary_dir,
                                                                              "sharedLibraries")

                new_plan_name = archive_file.addApplicationDeploymentPlan(plan_file_name,
                                                                          _generate_new_plan_name(
                                                                              library_source_name,
                                                                              plan_file_name))
            except IllegalArgumentException, iae:
                _logger.warning('WLSDPLY-06385', library_source_name, plan_file_name,
                                iae.getLocalizedMessage(), class_name=_class_name,
                                method_name=_method_name)
            except WLSDeployArchiveIOException, wioe:
                de = exception_helper.create_discover_exception('WLSDPLY-06387', library_source_name,
                                                                plan_file_name,
                                                                wioe.getLocalizedMessage())
                _logger.throwing(class_name=_class_name, method_name=_method_name, error=de)
                raise de
        return new_plan_name

    def get_applications(self):
        """
        Discover application deployment information from the domain. Collect the application deployment binaries into
        the discovery archive file. If an application binary cannot be collected into the archive file, remove
        the application source path from the model and un-target the application.
        :return: model name for the dictionary and the dictionary containing the applications information
        """
        _method_name = 'get_applications'
        _logger.entering(class_name=_class_name, method_name=_method_name)

        result = OrderedDict()
        model_top_folder_name = model_constants.APPLICATION
        location = LocationContext(self._base_location)
        location.append_location(model_top_folder_name)
        applications = self._find_names_in_folder(location)
        if applications:
            _logger.info('WLSDPLY-06391', len(applications), class_name=_class_name, method_name=_method_name)
            typedef = self._model_context.get_domain_typedef()
            name_token = self._aliases.get_name_token(location)
            for application in applications:
                if typedef.is_filtered(location, application):
                    _logger.info('WLSDPLY-06400', typedef.get_domain_type(), application, class_name=_class_name,
                                 method_name=_method_name)
                else:
                    _logger.info('WLSDPLY-06392', application, class_name=_class_name, method_name=_method_name)
                    location.add_name_token(name_token, application)
                    result[application] = OrderedDict()
                    self._populate_model_parameters(result[application], location)

                    # At this point, we have enough information in the model to know whether this
                    # is a structured application folder deployment or not.
                    #
                    # Note that when using the optional version directory underneath the install-root
                    # the config.xml entry for plan-dir is incorrect and does not agree with the plan-path
                    #
                    #   <app-deployment>
                    #     <name>webapp1</name>
                    #     <target>AdminServer</target>
                    #     <module-type>war</module-type>
                    #     <source-path>/tmp/structuredApps/webapp1/1.0/app/webapp1</source-path>
                    #     <plan-dir>/tmp/structuredApps/webapp1/plan</plan-dir>
                    #     <plan-path>/tmp/structuredApps/webapp1/1.0/plan/Plan.xml</plan-path>
                    #     <security-dd-model>DDOnly</security-dd-model>
                    #     <staging-mode xsi:nil="true"></staging-mode>
                    #     <plan-staging-mode xsi:nil="true"></plan-staging-mode>
                    #     <cache-in-app-directory>false</cache-in-app-directory>
                    #   </app-deployment>
                    #
                    # But what is put into the model agrees with config.xml:
                    #
                    #          webapp1:
                    #             PlanPath: wlsdeploy/structuredApplications/webapp1/1.0/plan/plan.xml
                    #             SourcePath: wlsdeploy/structuredApplications/webapp1/1.0/app/webapp1/
                    #             ModuleType: war
                    #             SecurityDDModel: DDOnly
                    #             PlanDir: wlsdeploy/structuredApplications/webapp1/plan
                    #             Target: AdminServer
                    #
                    is_struct_app, install_root = self._is_structured_app(application, result[application])
                    if is_struct_app:
                        self._add_structured_application_to_archive(application, result[application],
                                                                    location, install_root)
                    else:
                        self._add_application_to_archive(application, result[application])
                    self._discover_subfolders(result[application], location)
                    location.remove_name_token(name_token)

        _logger.exiting(class_name=_class_name, method_name=_method_name, result=result)
        return model_top_folder_name, result

    def _add_application_to_archive(self, application_name, application_dict):
        """
        Add the binary or directory referenced by the application to the archive file.
        If the binary can not be located and added to the archive file, un-target the application and log the problem.
        :param application_name: name of the application in the model
        :param application_dict: containing the application information
        :raise DiscoverException: An unexpected exception occurred trying to write the application to the archive
        """
        _method_name = 'add_application_to_archive'
        _logger.entering(application_name, class_name=_class_name, method_name=_method_name)

        archive_file = self._model_context.get_archive_file()
        file_name = self._get_dictionary_attribute_with_path_tokens_replaced(application_dict, SOURCE_PATH)
        if file_name is not None:
            file_name_path = file_name
            if not self._model_context.is_remote():
                file_name_path = self._convert_path(file_name)
            if self._is_file_to_exclude_from_archive(file_name_path):
                _logger.info('WLSDPLY-06393', application_name,
                             class_name=_class_name, method_name=_method_name)
            else:
                new_source_name = None
                if self._model_context.is_remote():
                    new_source_name = WLSDeployArchive.getApplicationArchivePath(file_name_path)
                    self.add_to_remote_map(file_name_path, new_source_name,
                                           WLSDeployArchive.ArchiveEntryType.APPLICATION.name())
                elif not self._model_context.is_skip_archive():
                    _logger.info('WLSDPLY-06394', application_name, file_name_path,
                                 class_name=_class_name, method_name=_method_name)
                    try:
                        if self._model_context.is_ssh():
                            file_name_path = \
                                self.download_deployment_from_remote_server(file_name_path,
                                                                            self.download_temporary_dir,
                                                                            "applications")

                        new_source_name = archive_file.addApplication(file_name_path)
                        module_type = dictionary_utils.get_dictionary_element(application_dict,
                                                                              model_constants.MODULE_TYPE)
                        if module_type == 'jdbc':
                            self._jdbc_password_fix(new_source_name)

                    except IllegalArgumentException, iae:
                        self._disconnect_target(application_name, application_dict, iae.getLocalizedMessage())
                    except WLSDeployArchiveIOException, wioe:
                        de = exception_helper.create_discover_exception('WLSDPLY-06397', application_name,
                                                                    file_name_path, wioe.getLocalizedMessage())
                        _logger.throwing(class_name=_class_name, method_name=_method_name, error=de)
                        raise de
                if new_source_name is not None:
                    _logger.finer('WLSDPLY-06398', application_name, new_source_name, class_name=_class_name,
                                  method_name=_method_name)
                    application_dict[model_constants.SOURCE_PATH] = new_source_name
                self.add_application_plan_to_archive(application_name, application_dict)

        _logger.exiting(class_name=_class_name, method_name=_method_name)

    def add_application_plan_to_archive(self, application_name, application_dict):
        """
        Add the application deployment plan to the archive file. Create a unique name for the deployment plan from
        the application name and the plan name. If the plan cannot be located and added to the archive file, the
        plan will remain in the model, but a warning message will be generated about the problem.
        :param application_name: name of the application in the model
        :param application_dict: containing the application information
        :raise: DiscoverException: An unexpected exception occurred trying to write the plan to the archive file
        """
        _method_name = 'add_application_plan_to_archive'
        _logger.entering(application_name, class_name=_class_name, method_name=_method_name)
        archive_file = self._model_context.get_archive_file()

        model_plan_path = self._get_dictionary_attribute_with_path_tokens_replaced(application_dict, PLAN_PATH)
        if model_plan_path is not None:
            app_source_name = self._get_dictionary_attribute_with_path_tokens_replaced(application_dict, SOURCE_PATH)
            model_plan_dir = self._get_dictionary_attribute_with_path_tokens_replaced(application_dict, PLAN_DIR)

            if model_plan_dir is not None and self.path_helper.is_relative_path(model_plan_path):
                plan_path = self.path_helper.join(model_plan_dir, model_plan_path)
            else:
                plan_path = model_plan_path

            if plan_path:
                if not self._model_context.is_remote():
                    plan_path = self._convert_path(plan_path)
                _logger.info('WLSDPLY-06402', application_name, plan_path, class_name=_class_name,
                             method_name=_method_name)
                new_plan_name = self._get_plan_path(plan_path, archive_file, app_source_name, application_name, application_dict)
                if new_plan_name is not None:
                    _logger.finer('WLSDPLY-06399', application_name, new_plan_name,
                                  class_name=_class_name, method_name=_method_name)
                    application_dict[model_constants.PLAN_PATH] = new_plan_name
        _logger.exiting(class_name=_class_name, method_name=_method_name)

    def _add_structured_application_to_archive(self, application_name, application_dict, location, install_root):
        _method_name = '_add_structured_application_to_archive'
        _logger.entering(application_name, location, install_root,
                         class_name=_class_name, method_name=_method_name)
        archive_file = self._model_context.get_archive_file()

        install_root_path = install_root
        if install_root:
            if not self._model_context.is_remote():
                install_root_path = self._convert_path(install_root)

            if not self._is_file_to_exclude_from_archive(install_root_path):
                new_install_root_path = None
                if self._model_context.is_remote():
                    new_install_root_path = WLSDeployArchive.getStructuredApplicationArchivePath(install_root_path)
                    self.add_to_remote_map(install_root_path, new_install_root_path,
                                           WLSDeployArchive.ArchiveEntryType.STRUCTURED_APPLICATION.name())
                elif not self._model_context.is_skip_archive():
                    try:
                        if self._model_context.is_ssh():
                            install_root_path = self.download_deployment_from_remote_server(install_root_path,
                                                                                          self.download_temporary_dir,
                                                                                          "applications")
                        new_install_root_path = archive_file.addStructuredApplication(install_root_path)
                    except IllegalArgumentException, iae:\
                        self._disconnect_target(application_name, application_dict, iae.getLocalizedMessage())
                    except WLSDeployArchiveIOException, wioe:
                        de = exception_helper.create_discover_exception('WLSDPLY-06397', application_name,
                                                                        install_root_path, wioe.getLocalizedMessage())
                        _logger.throwing(class_name=_class_name, method_name=_method_name, error=de)
                        raise de

                if new_install_root_path:
                    path_attributes = \
                        self._aliases.get_model_uses_path_tokens_attribute_names(location, only_readable=True)
                    for key, value in application_dict.iteritems():
                        if key in path_attributes:
                            # In the SSH case, the install_root_path and value do not share a common path.
                            #
                            if self._model_context.is_ssh():
                                value = self._convert_value_to_ssh_download_location(key, value, install_root_path)
                            application_dict[key] = \
                                WLSDeployArchive.getStructuredApplicationArchivePath(install_root_path,
                                                                                     new_install_root_path, value)
            else:
                _logger.info('WLSDPLY-06393', application_name, class_name=_class_name, method_name=_method_name)

        _logger.exiting(class_name=_class_name, method_name=_method_name)

    def _is_structured_app(self, application_name, application_dict):
        _method_name = '_is_structured_app'
        _logger.entering(application_dict, class_name=_class_name, method_name=_method_name)

        source_path = self._get_dictionary_attribute_with_path_tokens_replaced(application_dict, SOURCE_PATH)
        plan_dir = self._get_dictionary_attribute_with_path_tokens_replaced(application_dict, PLAN_DIR)
        plan_path = self._get_dictionary_attribute_with_path_tokens_replaced(application_dict, PLAN_PATH)

        _logger.finer('WLSDPLY-06405', application_name, source_path, plan_dir, plan_path,
                      class_name=_class_name, method_name=_method_name)

        if source_path is None:
            de = exception_helper.create_discover_exception('WLSDPLY-06404', application_name)
            _logger.throwing(class_name=_class_name, method_name=_method_name, error=de)
            raise de
        if plan_path is None:
            _logger.exiting(class_name=_class_name, method_name=_method_name, result=[False, None])
            return False, None

        if self.path_helper.is_relative_path(source_path):
            source_path = self.path_helper.join(self._model_context.get_domain_home(), source_path)
            source_path = self.path_helper.get_canonical_path(source_path)

        source_path_parent = self.path_helper.get_parent_directory(source_path)
        _logger.finer('WLSDPLY-06406', application_name, source_path_parent,
                      class_name=_class_name, method_name=_method_name)
        if source_path_parent is None or \
                self.path_helper.basename(source_path_parent) != 'app' or \
                self.path_helper.get_parent_directory(source_path_parent) == source_path_parent:
            _logger.exiting(class_name=_class_name, method_name=_method_name, result=[False, None])
            return False, None

        # _get_app_install_root() only needs a path to either the PlanDir or the PlanPath to determine
        # if this application is a structured app.
        #
        if plan_dir is None:
            if self.path_helper.is_relative_path(plan_path):
                plan_path = self.path_helper.join(self._model_context.get_domain_home(), plan_path)
                plan_path = self.path_helper.get_canonical_path(plan_path)
            effective_plan = plan_path
        else:
            if self.path_helper.is_relative_path(plan_dir):
                plan_dir = self.path_helper.join(self._model_context.get_domain_home(), plan_dir)
                plan_dir = self.path_helper.get_canonical_path(plan_dir)
            effective_plan = plan_dir

        install_root_dir = self._get_app_install_root(source_path_parent, effective_plan)
        if install_root_dir is not None:
            _logger.exiting(class_name=_class_name, method_name=_method_name,
                            result=[True, install_root_dir])
            return True, install_root_dir

        _logger.exiting(class_name=_class_name, method_name=_method_name, result=[False, None])
        return False, None

    def _convert_value_to_ssh_download_location(self, key, value, install_root_path):
        _method_name = '_convert_value_to_ssh_download_location'
        _logger.entering(key, value, install_root_path, class_name=_class_name, method_name=_method_name)

        new_value = value
        if not StringUtils.isEmpty(value):
            # strip off any trailing separator so that Jython basename works properly...
            if install_root_path.endswith('/') or install_root_path.endswith('\\'):
                install_root_path = install_root_path[0:-1]
            install_directory_name = self.path_helper.local_basename(install_root_path)

            add_trailing_slash = False
            if value.endswith('/') or value.endswith('\\'):
                add_trailing_slash = True
                new_value = value[0:-1]

            trailing_path_components = list()
            value_path, value_current_dir_name = self.path_helper.remote_split(new_value)

            # Skip over the first occurrence in case it is an exploded app directory
            # (e.g., servers/AdminServer/upload/OtdApp/app/OtdApp)
            #
            if value_current_dir_name == install_directory_name:
                trailing_path_components.append(value_current_dir_name)
                value_path, value_current_dir_name = self.path_helper.remote_split(value_path)

            found_match = False
            while not StringUtils.isEmpty(value_current_dir_name):
                if value_current_dir_name == install_directory_name:
                    found_match = True
                    break
                elif StringUtils.isEmpty(value_path):
                    break
                else:
                    trailing_path_components.append(value_current_dir_name)

                value_path, value_current_dir_name = self.path_helper.remote_split(value_path)

            if found_match:
                trailing_path_components.append(install_root_path)
                trailing_path_components.reverse()
                new_value = self.path_helper.local_join(*trailing_path_components)
                if add_trailing_slash:
                    new_value += os.sep
            else:
                new_value = value

        _logger.exiting(class_name=_class_name, method_name=_method_name, result=new_value)
        return new_value

    def _jdbc_password_fix(self, source_name):
        """
        This will look for password and userid in the jdbc standalone xml and
        replace with either fix password token or a token in the xml and variable file.
        It extracts the jdbc xml from the archive and then replaces it with the updated file.
        :param source_name: Name of the path and file for the standalone xml file
        """
        _method_name = '_jdbc_password_fix'
        _logger.entering(source_name, class_name=_class_name, method_name=_method_name)
        archive_file = self._model_context.get_archive_file()
        tmp_dir = FileUtils.getTmpDir();
        temp_file = FileUtils.createTempDirectory(tmp_dir, 'jdbc-xml')
        jdbc_file = archive_file.extractFile(source_name, temp_file)
        jdbc_out = FileUtils.createTempDirectory(tmp_dir, 'jdbc-out')
        jdbc_out = archive_file.extractFile(source_name, jdbc_out)
        bis = BufferedReader(FileReader(jdbc_file))
        bos = BufferedWriter(FileWriter(jdbc_out))
        cache = StringBuilder()
        while bis.ready():
            cache.append(bis.readLine()).append("\n")
        bis.close()
        pattern = Pattern.compile("<name>(\s?)user(\s?)</name>")
        matcher = pattern.matcher(cache.toString())
        end = -1
        if matcher.find():
            end = matcher.end()
        result = cache.toString()
        if end >= 0:
            pattern = Pattern.compile("<value>(.+?)</value>")
            matcher = pattern.matcher(result[end:])
            matcher.find()
            username = matcher.group()
            username = username[len('<value>'):len(username) - len('</value>')]
            pattern = Pattern.compile(matcher.group())
            matcher = pattern.matcher(cache.toString())
            result = matcher.replaceFirst(self._get_pass_replacement(jdbc_file, '-user:username',
                                                                     'value', username=username))

        pattern = Pattern.compile('<password-encrypted>(.+?)</password-encrypted>')
        matcher = pattern.matcher(result)
        result = matcher.replaceFirst(self._get_pass_replacement(jdbc_file, '-user:password', 'password-encrypted'))

        pattern = Pattern.compile('<url>(\s*)(.+?)(\s*)</url>')
        matcher = pattern.matcher(result)
        matcher.find()
        result = matcher.replaceFirst(self._get_pass_replacement(jdbc_file, '-url', 'url',
                                                                 properties=matcher.group(2)))

        pattern = Pattern.compile('<ons-wallet-password-encrypted>(.+?)</ons-wallet-password-encrypted>')
        matcher = pattern.matcher(result)
        result = matcher.replaceFirst(self._get_pass_replacement(jdbc_file, '-ons-pass-encrypt:password',
                                                                 'ons-wallet-password-encrypted'))
        bos.write(result)
        bos.close()
        archive_file.replaceApplication(source_name, jdbc_out)
        _logger.exiting(class_name=_class_name, method_name=_method_name)

    def _get_pass_replacement(self, jdbc_file, name, type, properties=None, username=''):
        if self._credential_injector is not None:
            token = self.path_helper.get_local_filename_no_ext_from_path(jdbc_file)
            token = token + name
            if properties is not None:
                self._extra_tokens[token] = properties
                result = self._credential_injector.get_property_token(None, token)
            else:
                result = self._credential_injector.injection_out_of_model(token, username)
        else:
            result = PASSWORD_TOKEN
        result = '<' + type + '>' + result + '</' + type + '>'
        return result

    def _disconnect_target(self, application_name, application_dict, message):
        _method_name = '_disconnect_target'
        if model_constants.TARGET in application_dict:
            target = application_dict[model_constants.TARGET]
            del application_dict[model_constants.TARGET]
            _logger.warning('WLSDPLY-06395', application_name, target, message,
                            class_name=_class_name, method_name=_method_name)
        else:
            _logger.warning('WLSDPLY-06396', application_name, message,
                            class_name=_class_name, method_name=_method_name)

    def _get_plan_path(self, plan_path, archive_file, app_source_name, application_name, application_dict):
        _method_name = '_get_plan_path'
        plan_dir = None
        if model_constants.PLAN_DIR in application_dict:
            plan_dir = application_dict[model_constants.PLAN_DIR]
            del application_dict[model_constants.PLAN_DIR]
        plan_file_name = self._resolve_deployment_plan_path(plan_dir, plan_path)
        if self._model_context.is_remote():
            new_plan_name = WLSDeployArchive.getApplicationPlanArchivePath(plan_file_name)
            self.add_to_remote_map(plan_path, new_plan_name,
                                   WLSDeployArchive.ArchiveEntryType.APPLICATION_PLAN.name())
        elif not self._model_context.is_skip_archive():
            try:
                if self._model_context.is_ssh():
                    plan_file_name = self.download_deployment_from_remote_server(plan_file_name,
                                                                                  self.download_temporary_dir,
                                                                                  "applications")

                new_plan_name = archive_file.addApplicationDeploymentPlan(plan_file_name,
                                                                          _generate_new_plan_name(
                                                                              app_source_name,
                                                                              plan_file_name))
            except IllegalArgumentException, iae:
                _logger.warning('WLSDPLY-06395', application_name, plan_file_name,
                                iae.getLocalizedMessage(), class_name=_class_name,
                                method_name=_method_name)
                new_plan_name = None
            except WLSDeployArchiveIOException, wioe:
                de = exception_helper.create_discover_exception('WLSDPLY-06397', application_dict, plan_file_name,
                                                                wioe.getLocalizedMessage())
                _logger.throwing(class_name=_class_name, method_name=_method_name, error=de)
                raise de

            return new_plan_name

    def _resolve_deployment_plan_path(self, plan_dir, plan_path):
        """
        Find the deployment plan absolute file path.

        This is a private helper method.

        :param plan_dir: directory discovered from the domain, which is concatenated to the plan path
        :param plan_path: plan path discovered from the domain
        :return: absolute file path for the plan from the plan_dir and plan_paht
        """
        if not StringUtils.isEmpty(plan_path):
            if not StringUtils.isEmpty(plan_dir):
                relative_to = plan_dir
            else:
                relative_to = self._model_context.get_domain_home()
            return self.path_helper.get_canonical_path(plan_path, relative_to=relative_to)
        return plan_path

    def _get_app_install_root(self, app_dir, plan_dir):
        _method_name = '_get_app_install_root'
        _logger.entering(app_dir, plan_dir, class_name=_class_name, method_name=_method_name)

        app_install_root = self.path_helper.get_parent_directory(app_dir)
        if plan_dir.startswith(app_install_root):
            install_root = app_install_root
        else:
            install_root = None

        _logger.exiting(class_name=_class_name, method_name=_method_name, result=install_root)
        return install_root

    def _get_dictionary_attribute_with_path_tokens_replaced(self, model_dict, attribute_name):
        _method_name = '_get_dictionary_attribute_with_path_tokens_replaced'
        _logger.entering(model_dict, attribute_name, class_name=_class_name, method_name=_method_name)

        result = dictionary_utils.get_element(model_dict, attribute_name)
        if result is not None:
            result = self._model_context.replace_token_string(result)

        _logger.exiting(class_name=_class_name, method_name=_method_name, result=result)
        return result

def _generate_new_plan_name(binary_path, plan_path):
    """
    Generate a new plan name from the plan path and binary path.

    This is a private helper method.

    :param binary_path: source path of the deployment file
    :param plan_path: path of the plan from the domain
    :return: newly generated plan name for the archive file
    """
    _path_helper = path_helper.get_path_helper()
    new_name = _path_helper.get_filename_from_path(plan_path)
    if binary_path is not None:
        prefix = _path_helper.get_filename_no_ext_from_path(binary_path)
        new_name = prefix + '-' + new_name
    return new_name
