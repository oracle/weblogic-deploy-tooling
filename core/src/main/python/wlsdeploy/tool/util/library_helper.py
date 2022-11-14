"""
Copyright (c) 2017, 2022, Oracle Corporation and/or its affiliates.  All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
from java.io import File
from oracle.weblogic.deploy.util import WLSDeployArchive
from shutil import copy

from wlsdeploy.aliases.model_constants import DOMAIN_SCRIPTS
from wlsdeploy.aliases.model_constants import DOMAIN_LIBRARIES
from wlsdeploy.exception import exception_helper
from wlsdeploy.tool.util.archive_helper import ArchiveHelper
from wlsdeploy.tool.util.wlst_helper import WlstHelper

from wlsdeploy.util import dictionary_utils
import wlsdeploy.util.unicode_helper as str_helper


class LibraryHelper(object):
    """
    Shared code for updating domain and classpath libraries. Domain create and update use this code.
    """
    __class_name = 'LibraryHelper'

    def __init__(self, model, model_context, aliases, domain_home, exception_type, logger):
        self.logger = logger
        self.model = model
        self.model_context = model_context
        self.domain_home = domain_home
        self.aliases = aliases
        self.wlst_helper = WlstHelper(exception_type)

        self.archive_helper = None
        archive_file_name = self.model_context.get_archive_file_name()
        if archive_file_name is not None:
            self.archive_helper = ArchiveHelper(archive_file_name, self.domain_home, self.logger, exception_type)

    def install_domain_libraries(self):
        """
        Extract the domain libraries listed in the model, if any, to the <DOMAIN_HOME>/lib directory.
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'install_domain_libraries'

        self.logger.entering(self.domain_home, class_name=self.__class_name, method_name=_method_name)
        domain_info_dict = self.model.get_model_domain_info()
        if DOMAIN_LIBRARIES not in domain_info_dict or len(domain_info_dict[DOMAIN_LIBRARIES]) == 0:
            self.logger.info('WLSDPLY-12213', class_name=self.__class_name, method_name=_method_name)
        elif DOMAIN_LIBRARIES in domain_info_dict:
            domain_libs = dictionary_utils.get_dictionary_element(domain_info_dict, DOMAIN_LIBRARIES)
            if self.archive_helper is None:
                ex = exception_helper.create_create_exception('WLSDPLY-12214', domain_libs)
                self.logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                raise ex

            for domain_lib in domain_libs:
                if WLSDeployArchive.isPathIntoArchive(domain_lib):
                    self.logger.info('WLSDPLY-12215', domain_lib, self.domain_home,
                                     class_name=self.__class_name, method_name=_method_name)
                    self.archive_helper.extract_domain_library(domain_lib)
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
            num_cp_libs = self.archive_helper.extract_classpath_libraries()
            if num_cp_libs > 0:
                self.logger.info('WLSDPLY-12217', num_cp_libs, self.domain_home,
                                 class_name=self.__class_name, method_name=_method_name)
            else:
                self.logger.info('WLSDPLY-12218', self.model_context.get_archive_file_name(),
                                 class_name=self.__class_name, method_name=_method_name)
        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def extract_custom_files(self):
        """
        Extract any custom files in the archive to the domain home.
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'extract_custom_files'

        self.logger.entering(self.domain_home, class_name=self.__class_name, method_name=_method_name)
        if self.archive_helper is None:
            self.logger.info('WLSDPLY-12565', class_name=self.__class_name, method_name=_method_name)
        else:
            num_cp_libs = self.archive_helper.extract_custom_archive()
            if num_cp_libs > 0:
                self.logger.info('WLSDPLY-12566', num_cp_libs, self.domain_home,
                                 class_name=self.__class_name, method_name=_method_name)
            else:
                self.logger.info('WLSDPLY-12567', self.model_context.get_archive_file_name(),
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
        if DOMAIN_SCRIPTS not in domain_info_dict or len(domain_info_dict[DOMAIN_SCRIPTS]) == 0:
            self.logger.info('WLSDPLY-12241', class_name=self.__class_name, method_name=_method_name)
        elif DOMAIN_SCRIPTS in domain_info_dict:
            domain_scripts = dictionary_utils.get_dictionary_element(domain_info_dict, DOMAIN_SCRIPTS)
            if self.archive_helper is None:
                ex = exception_helper.create_create_exception('WLSDPLY-12250', domain_scripts)
                self.logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                raise ex

            for domain_script in domain_scripts:
                if WLSDeployArchive.isPathIntoArchive(domain_script):
                    self.logger.info('WLSDPLY-12251', domain_script, self.domain_home,
                                     class_name=self.__class_name, method_name=_method_name)
                    self.archive_helper.extract_domain_bin_script(domain_script)
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
