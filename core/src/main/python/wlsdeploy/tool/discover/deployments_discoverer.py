"""
Copyright (c) 2017, 2020, Oracle Corporation and/or its affiliates.  All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import os

from java.io import BufferedReader
from java.io import BufferedWriter
from java.io import File
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
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception import exception_helper
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.discover import discoverer
from wlsdeploy.tool.discover.discoverer import Discoverer
from wlsdeploy.util import dictionary_utils
from wlsdeploy.util import path_utils

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
                if typedef.is_system_shared_library(library):
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
                if self._is_oracle_home_file(file_name_path):
                    _logger.info('WLSDPLY-06383', library_name, class_name=_class_name, method_name=_method_name)
                else:
                    new_source_name = None
                    if self._model_context.is_remote():
                        new_source_name = archive_file.getSharedLibraryArchivePath(file_name_path)
                        self.add_to_remote_map(file_name_path, new_source_name,
                                           WLSDeployArchive.ArchiveEntryType.SHARED_LIBRARIES.name())
                    elif not self._model_context.skip_archive():
                        _logger.info('WLSDPLY-06384', library_name, file_name_path, class_name=_class_name,
                                     method_name=_method_name)
                        try:
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
        return

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
        return

    def get_shlib_plan(self, plan_path, library_dict, library_source_name, archive_file):
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
            new_plan_name = archive_file.getShLibArchivePath(plan_path)
            self.add_to_remote_map(plan_path, new_plan_name,
                                   WLSDeployArchive.ArchiveEntryType.SHLIB_PLAN.name())
        elif not self._model_context.skip_archive():
            try:
                new_plan_name = archive_file.addApplicationDeploymentPlan(plan_file_name,
                                                                          _generate_new_plan_name(
                                                                              library_source_name,
                                                                              plan_file_name))
            except IllegalArgumentException, iae:
                _logger.warning('WLSDPLY-06385', library_name, plan_file_name,
                                iae.getLocalizedMessage(), class_name=_class_name,
                                method_name=_method_name)
            except WLSDeployArchiveIOException, wioe:
                de = exception_helper.create_discover_exception('WLSDPLY-06387', library_name,
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
                if typedef.is_system_app(application):
                    _logger.info('WLSDPLY-06400', typedef.get_domain_type(), application, class_name=_class_name,
                                 method_name=_method_name)
                else:
                    _logger.info('WLSDPLY-06392', application, class_name=_class_name, method_name=_method_name)
                    location.add_name_token(name_token, application)
                    result[application] = OrderedDict()
                    self._populate_model_parameters(result[application], location)
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
        if model_constants.SOURCE_PATH in application_dict:
            if model_constants.PLAN_DIR in application_dict and \
                self._test_app_folder(application_dict[model_constants.SOURCE_PATH],
                                      application_dict[model_constants.PLAN_DIR]):
                return self._create_app_folder(application_name, application_dict)
            file_name = application_dict[model_constants.SOURCE_PATH]
            if file_name:
                file_name_path = file_name
                if not self._model_context.is_remote():
                    file_name_path = self._convert_path(file_name)
                if self._is_oracle_home_file(file_name_path):
                    _logger.info('WLSDPLY-06393', application_name, class_name=_class_name, method_name=_method_name)
                else:
                    new_source_name = None
                    if self._model_context.is_remote():
                        new_source_name = archive_file.getApplicationArchivePath(file_name_path)
                        self.add_to_remote_map(file_name_path, new_source_name,
                                               WLSDeployArchive.ArchiveEntryType.APPLICATIONS.name())
                    elif not self._model_context.skip_archive():
                        _logger.info('WLSDPLY-06394', application_name, file_name_path, class_name=_class_name,
                                     method_name=_method_name)
                        try:
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
        return

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
        if model_constants.PLAN_PATH in application_dict:
            app_source_name = application_dict[model_constants.SOURCE_PATH]
            plan_path = application_dict[model_constants.PLAN_PATH]
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
        return

    def _create_app_folder(self, application_name, application_dict):
        """
        Create a well-formed application and plan directory
        :param application_name: name of application
        :param application_dict: model dictionary with application parameters
        :return: newly constructed source name
        """
        _method_name = '_create_app_folder'

        _logger.entering(application_name, class_name=_class_name, method_name=_method_name)

        self._create_application_directory(application_name, application_dict)
        self._create_plan_directory(application_name, application_dict)

        _logger.exiting(class_name=_class_name, method_name=_method_name)

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
            head, tail = os.path.split(jdbc_file)
            token = tail[:len(tail) - len('.xml')]
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

    def _test_app_folder(self, source_path, plan_dir):
        app_folder = False
        app_dir = File(source_path).getParent()
        if app_dir.endswith('app') and plan_dir.endswith('plan'):
            app_folder = True
        return app_folder

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

    def _create_application_directory(self, application_name, application_dict):
        _method_name = '_create_application_directory'
        new_source_name = None
        app_dir = application_dict[model_constants.SOURCE_PATH]
        archive_file = self._model_context.get_archive_file()
        if self._model_context.is_remote():
            new_source_name = archive_file.getApplicationDirectoryArchivePath(application_name, app_dir)

            self.add_to_remote_map(app_dir, new_source_name,
                                   WLSDeployArchive.ArchiveEntryType.APPLICATIONS.name())
        elif not self._model_context.skip_archive():
            if not os.path.abspath(app_dir):
                app_dir = os.path.join(self._model_context.get_domain_home(), app_dir)
            try:
                new_source_name = archive_file.addApplicationFolder(application_name, app_dir)
            except IllegalArgumentException, iae:
                self._disconnect_target(application_name, application_dict, iae.getLocalizedMessage())
            except WLSDeployArchiveIOException, wioe:
                de = exception_helper.create_discover_exception('WLSDPLY-06403', application_name,
                                                                file_name_path, wioe.getLocalizedMessage())
                _logger.throwing(class_name=_class_name, method_name=_method_name, error=de)
                raise de
        if new_source_name is not None:
            _logger.finer('WLSDPLY-06398', application_name, new_source_name, class_name=_class_name,
                          method_name=_method_name)
            application_dict[model_constants.SOURCE_PATH] = new_source_name

    def _create_plan_directory(self, application_name, application_dict):
        _method_name = '_create_plan_directory'
        new_source_name = None
        plan_dir = application_dict[model_constants.PLAN_DIR]
        archive_file = self._model_context.get_archive_file()
        if not os.path.abspath(plan_dir):
            plan_dir = os.path.join(self._model_context.get_domain_home(), plan_dir)
        if self._model_context.is_remote():
            new_source_name = archive_file.getApplicationPlanDirArchivePath(application_name, plan_dir)
            self.add_to_remote_map(plan_dir, new_source_name,
                                   WLSDeployArchive.ArchiveEntryType.APPLICATION_PLAN.name())
        elif not self._model_context.skip_archive():
            try:
                new_source_name = archive_file.addApplicationPlanFolder(application_name, plan_dir)
            except IllegalArgumentException, iae:
                _logger.warning('WLSDPLY-06395', application_name, plan_dir,
                                iae.getLocalizedMessage(), class_name=_class_name,
                                method_name=_method_name)
                new_source_name = None
            except WLSDeployArchiveIOException, wioe:
                de = exception_helper.create_discover_exception('WLSDPLY-06397', application_dict, plan_dir,
                                                                wioe.getLocalizedMessage())
                _logger.throwing(class_name=_class_name, method_name=_method_name, error=de)
                raise de
        if new_source_name is not None:
            _logger.finer('WLSDPLY-06398', application_name, new_source_name, class_name=_class_name,
                          method_name=_method_name)
            application_dict[model_constants.PLAN_DIR] = new_source_name

    def _get_plan_path(self, plan_path, archive_file, app_source_name, application_name, application_dict):
        _method_name = '_get_plan_path'
        plan_dir = None
        if model_constants.PLAN_DIR in application_dict:
            plan_dir = application_dict[model_constants.PLAN_DIR]
            del application_dict[model_constants.PLAN_DIR]
        plan_file_name = self._resolve_deployment_plan_path(plan_dir, plan_path)
        if self._model_context.is_remote():
            if plan_file_name.endswith('plan'):
                new_plan_name = archive_file.getApplicationPlanDirArchivePath(plan_file_name)
            else:
                new_plan_name = archive_file.getApplicationPlanArchivePath(plan_file_name)
            self.add_to_remote_map(plan_path, new_plan_name,
                                   WLSDeployArchive.ArchiveEntryType.APPLICATION_PLAN.name())
        elif not self._model_context.skip_archive():
            try:
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
            return discoverer.convert_to_absolute_path(relative_to, plan_path)
        return plan_path


def _generate_new_plan_name(binary_path, plan_path):
    """
    Generate a new plan name from the plan path and binary path.

    This is a private helper method.

    :param binary_path: source path of the deployment file
    :param plan_path: path of the plan from the domain
    :return: newly generated plan name for the archive file
    """
    new_name = path_utils.get_filename_from_path(plan_path)
    if binary_path is not None:
        prefix = path_utils.get_filename_no_ext_from_path(binary_path)
        new_name = prefix + '-' + new_name
    return new_name
