"""
Copyright (c) 2017, 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import os
from java.io import File
from oracle.weblogic.deploy.util import WLSDeployArchive
from shutil import copy

from wlsdeploy.aliases import alias_utils
from wlsdeploy.aliases.model_constants import DOMAIN_SCRIPTS
from wlsdeploy.aliases.model_constants import DOMAIN_LIBRARIES
from wlsdeploy.aliases.model_constants import MODEL_LIST_DELIMITER
from wlsdeploy.exception import exception_helper
from wlsdeploy.tool.util.archive_helper import ArchiveList
from wlsdeploy.tool.util.wlst_helper import WlstHelper

from wlsdeploy.util import dictionary_utils
from wlsdeploy.util import path_helper
import wlsdeploy.util.unicode_helper as str_helper


class LibraryHelper(object):
    """
    Shared code for updating domain and classpath libraries. Domain create and update use this code.
    """
    __class_name = 'LibraryHelper'

    def __init__(self, model, model_context, aliases, domain_home, exception_type, logger, upload_temporary_dir=None):
        self.logger = logger
        self.model = model
        self.model_context = model_context
        self.domain_home = domain_home
        self.aliases = aliases
        self.wlst_helper = WlstHelper(exception_type)
        self.upload_temporary_dir = upload_temporary_dir
        self.path_helper = path_helper.get_path_helper()
        self.archive_helper = None
        archive_file_name = self.model_context.get_archive_file_name()
        if archive_file_name is not None:
            self.archive_helper = ArchiveList(archive_file_name, self.model_context, exception_type)

    def install_domain_libraries(self):
        """
        Extract the domain libraries listed in the model, if any, to the <DOMAIN_HOME>/lib directory.
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'install_domain_libraries'

        self.logger.entering(self.domain_home, class_name=self.__class_name, method_name=_method_name)
        domain_info_dict = self.model.get_model_domain_info()
        domain_libs = dictionary_utils.get_element(domain_info_dict, DOMAIN_LIBRARIES)

        if not domain_libs:  # not present or empty list
            self.logger.info('WLSDPLY-12213', class_name=self.__class_name, method_name=_method_name)
        else:
            domain_libs_list = alias_utils.convert_to_type('list', domain_libs,
                                                           delimiter=MODEL_LIST_DELIMITER)
            if self.archive_helper is None:
                ex = exception_helper.create_create_exception('WLSDPLY-12214', domain_libs_list)
                self.logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                raise ex

            for domain_lib in domain_libs_list:
                if WLSDeployArchive.isPathIntoArchive(domain_lib):
                    self.logger.info('WLSDPLY-12215', domain_lib, self.domain_home,
                                     class_name=self.__class_name, method_name=_method_name)
                    self.archive_helper.extract_domain_library(domain_lib, self.upload_temporary_dir)
                    if self.model_context.is_ssh():
                        self._upload_extracted_file(domain_lib, 'lib')
                else:
                    self.logger.info('WLSDPLY-12235', domain_lib, self.domain_home,
                                     class_name=self.__class_name, method_name=_method_name)
                    self._copy_domain_library(domain_lib)

        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def extract_classpath_libraries(self):
        """
        Extract any classpath libraries in the archive to the domain home.
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'extract_classpath_libraries'

        self.logger.entering(self.domain_home, class_name=self.__class_name, method_name=_method_name)
        if self.archive_helper is None:
            self.logger.info('WLSDPLY-12216', class_name=self.__class_name, method_name=_method_name)
        else:
            num_cp_libs = self.archive_helper.extract_classpath_libraries(self.upload_temporary_dir)
            if num_cp_libs > 0:
                self.logger.info('WLSDPLY-12217', num_cp_libs, self.domain_home,
                                 class_name=self.__class_name, method_name=_method_name)

                if self.model_context.is_ssh():
                    self._upload_extracted_directory(WLSDeployArchive.ARCHIVE_CPLIB_TARGET_DIR,
                                                     WLSDeployArchive.WLSDPLY_ARCHIVE_BINARY_DIR)
            else:
                self.logger.info('WLSDPLY-12218', self.model_context.get_archive_file_name(),
                                 class_name=self.__class_name, method_name=_method_name)
        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def install_domain_scripts(self):
        """
        Extract the scripts from domain bin listed in the model, if any, to the <DOMAIN_HOME>/bin directory.
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'install_domain_scripts'

        self.logger.entering(self.domain_home, class_name=self.__class_name, method_name=_method_name)
        domain_info_dict = self.model.get_model_domain_info()
        domain_scripts = dictionary_utils.get_element(domain_info_dict, DOMAIN_SCRIPTS)

        if not domain_scripts:  # not present or empty list
            self.logger.info('WLSDPLY-12241', class_name=self.__class_name, method_name=_method_name)
        else:
            domain_scripts_list = alias_utils.convert_to_type('list', domain_scripts,
                                                              delimiter=MODEL_LIST_DELIMITER)
            if self.archive_helper is None:
                ex = exception_helper.create_create_exception('WLSDPLY-12250', domain_scripts_list)
                self.logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                raise ex

            for domain_script in domain_scripts_list:
                if WLSDeployArchive.isPathIntoArchive(domain_script):
                    self.logger.info('WLSDPLY-12251', domain_script, self.domain_home,
                                     class_name=self.__class_name, method_name=_method_name)
                    self.archive_helper.extract_domain_bin_script(domain_script, self.upload_temporary_dir)
                    if self.model_context.is_ssh():
                        self._upload_extracted_file(domain_script, 'bin')

                else:
                    self.logger.info('WLSDPLY-12252', domain_script, self.domain_home,
                                     class_name=self.__class_name, method_name=_method_name)
                    self._copy_domain_bin(domain_script)

        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def _copy_domain_library(self, domain_lib):
        """
        Copy the specified domain library to the domain's lib directory.
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = '_copy_domain_library'

        source_path = File(domain_lib).getAbsolutePath()
        target_dir = File(self.domain_home, 'lib').getPath()

        try:
            copy(str_helper.to_string(source_path), str_helper.to_string(target_dir))
        except IOError:
            ex = exception_helper.create_create_exception('WLSDPLY-12234', source_path, target_dir)
            self.logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex

    def _copy_domain_bin(self, domain_bin):
        """
        Copy the specified domain user script to the domain's bin directory.
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = '_copy_domain_bin'

        source_path = File(domain_bin).getAbsolutePath()
        target_dir = File(self.domain_home, 'bin').getPath()

        try:
            copy(str_helper.to_string(source_path), str_helper.to_string(target_dir))
        except IOError:
            ex = exception_helper.create_create_exception('WLSDPLY-12253', source_path, target_dir)
            self.logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex

    def _upload_extracted_directory(self, archive_path, target_parent_dir):
        """
        Convenient method to upload the extracted directories - classpathLibraries, custom
        :param archive_path:  path from the archive wlsdeploy/classpathLibraries, wlsdeploy/custom
        :param target_parent_dir:  wlsdeploy
        """
        if self.model_context.is_ssh():
            self.model_context.get_ssh_context().create_directories_if_not_exist(self.path_helper.remote_join(
                self.model_context.get_domain_home(), archive_path))
            self.model_context.get_ssh_context().upload(
                self.path_helper.local_join(self.upload_temporary_dir, archive_path),
                self.path_helper.remote_join(self.model_context.get_domain_home(), target_parent_dir))


    def _upload_extracted_file(self, name, path_from_domain):
        """
        Convenient method to upload a single file for domainInfo.domainBin,  domainInfo.domainLib
        :param name:   individual name in domainInfo.domainBin or domainInfo.domainLib
        :param path_from_domain: destination folder after $domain_home - bin or lib
        """
        base_name = name[name.rfind('/')+1:]
        # file is extracted to destination/lib
        self.model_context.get_ssh_context().upload(
            self.path_helper.local_join(self.upload_temporary_dir, path_from_domain, base_name),
            self.path_helper.remote_join(self.model_context.get_domain_home(), path_from_domain, base_name))
