"""
Copyright (c) 2017, 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import os
import sets
import shutil

from java.io import File
from java.lang import IllegalArgumentException
from java.lang import IllegalStateException

from oracle.weblogic.deploy.util import FileUtils
from oracle.weblogic.deploy.util import WLSDeployArchive
from oracle.weblogic.deploy.util import WLSDeployArchiveIOException

from wlsdeploy.exception import exception_helper
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.util.cla_utils import CommandLineArgUtil

class ArchiveList(object):
    """
    Helper class for working with multiple archive files.
    This class should be the access point for any operation that makes use of multiple archives.
    """
    __class_name = 'ArchiveList'
    __logger = PlatformLogger('wlsdeploy.tool.util')

    def __init__(self, archive_files_text, model_context, exception_type):
        """
        :param archive_files_text: a comma-separated list of one or more file names
        :param model_context: the model context to use
        :param exception_type: the exception type for the associated tool
        """
        _method_name = '__init__'

        self.__weblogic_helper = model_context.get_weblogic_helper()
        # used for logging only, comma-separated text is OK
        self.__archive_files_text = archive_files_text

        self.__model_context = model_context
        self.__exception_type = exception_type

        self.__archive_files = []
        file_names = archive_files_text.split(CommandLineArgUtil.ARCHIVE_FILES_SEPARATOR)
        for file_name in file_names:
            try:
                self.__archive_files.append(WLSDeployArchive(file_name))
            except (IllegalArgumentException, IllegalStateException), e:
                ex = exception_helper.create_exception(exception_type, 'WLSDPLY-19300', file_name,
                                                       e.getLocalizedMessage(), error=e)
                self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                raise ex

    def is_path_into_archive(self, path):
        _method_name = 'is_path_into_archive'
        self.__logger.entering(path, class_name=self.__class_name, method_name=_method_name)

        result = WLSDeployArchive.isPathIntoArchive(path)
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result

    def contains_file(self, path):
        """
        Does an archive file contain the specified location?
        :param path: the path to test
        :return: True, if the path was found in an archive file and is a file, False otherwise
        :raises: BundleAwareException of the appropriate type: if an error occurs
        """
        _method_name = 'contains_file'
        self.__logger.entering(path, class_name=self.__class_name, method_name=_method_name)

        result = False
        for archive_file in self.__archive_files:
            try:
                result = archive_file.containsFile(path)
                if result:
                    break
            except (IllegalArgumentException, WLSDeployArchiveIOException), e:
                ex = exception_helper.create_exception(self.__exception_type, "WLSDPLY-19302", path,
                                                       self.__archive_files_text, e.getLocalizedMessage(), error=e)
                self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                raise ex

        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result

    def contains_path(self, path):
        """
        Check that the provided path is a path, not a file, contained inside an archive file
        :param path: the path to test
        :return: True, if the path was found in an archive file and is a path, False otherwise
        :raises: BundleAwareException of the appropriate type: if an error occurs
        """
        _method_name = 'contains_path'
        self.__logger.entering(path, class_name=self.__class_name, method_name=_method_name)

        result = False
        for archive_file in self.__archive_files:
            try:
                result = archive_file.containsPath(path)
                if result:
                    break
            except (IllegalArgumentException, WLSDeployArchiveIOException), e:
                ex = exception_helper.create_exception(self.__exception_type, "WLSDPLY-19302", path,
                                                       archive_file, e.getLocalizedMessage(), error=e)
                self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                raise ex

        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result

    def contains_file_or_path(self, path):
        """
        Check that the provided path is a file or path contained inside one of the archive files
        :param path: the path to test
        :return: True, if the path was found in an archive file. False otherwise
        :raises: BundleAwareException of the appropriate type: if an error occurs
        """
        _method_name = 'contains_file_or_path'
        self.__logger.entering(path, class_name=self.__class_name, method_name=_method_name)

        result = False
        for archive_file in self.__archive_files:
            try:
                result = archive_file.containsFileOrPath(path)
                if result:
                    break
            except (IllegalArgumentException, WLSDeployArchiveIOException), e:
                ex = exception_helper.create_exception(self.__exception_type, "WLSDPLY-19309", path,
                                                       self.__archive_files_text, e.getLocalizedMessage(), error=e)
                self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                raise ex

        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result

    def is_path_forbidden_for_remote_update(self, path):
        """
        Check that the provided path in the archive is forbidden for remote domain update
        :param path: the path to test
        :return: True, if the path is forbidden for remote update. False otherwise
        :raises: BundleAwareException of the appropriate type: if an error occurs
        """
        _method_name = 'is_path_forbidden_for_remote_update'
        self.__logger.entering(path, class_name=self.__class_name, method_name=_method_name)

        result = False
        for archive_file in self.__archive_files:
            try:
                if archive_file.containsFileOrPath(path):
                    if (not path.startswith(WLSDeployArchive.ARCHIVE_SHLIBS_TARGET_DIR) and
                            not path.startswith(WLSDeployArchive.ARCHIVE_APPS_TARGET_DIR)):
                        result = True
                        break
            except (IllegalArgumentException), e:
                ex = exception_helper.create_exception(self.__exception_type, "WLSDPLY-19309", path,
                                                       self.__archive_files_text, e.getLocalizedMessage(), error=e)
                self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                raise ex

        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result

    def read_xacml_role_content(self, path):
        _method_name = 'get_xacml_role_content'
        self.__logger.entering(path, class_name=self.__class_name, method_name=_method_name)

        try:
            archive_file = self._find_archive_for_path(path, True)
            result = archive_file.readXACMLRoleFromArchive(path)
        except (IllegalArgumentException, WLSDeployArchiveIOException), e:
            ex = exception_helper.create_exception(self.__exception_type, "WLSDPLY-19318", path,
                                                   self.__archive_files_text, e.getLocalizedMessage(), error=e)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex

        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return result

    def read_xacml_policy_content(self, path):
        _method_name = 'read_xacml_policy_content'
        self.__logger.entering(path, class_name=self.__class_name, method_name=_method_name)

        try:
            archive_file = self._find_archive_for_path(path, True)
            result = archive_file.readXACMLPolicyFromArchive(path)
        except (IllegalArgumentException, WLSDeployArchiveIOException), e:
            ex = exception_helper.create_exception(self.__exception_type, "WLSDPLY-19318", path,
                                                   self.__archive_files_text, e.getLocalizedMessage(), error=e)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex

        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return result

    def extract_file(self, path, location=None, strip_leading_path=True):
        """
        Extract the specified file from the archive into the specified directory, or into Domain Home.
        :param path: the path into the archive
        :param location: the location to which to extract the file
        :return: path to the extracted file
        :raises: BundleAwareException of the appropriate type: if an error occurs
        """
        _method_name = 'extract_file'

        self.__logger.entering(path, class_name=self.__class_name, method_name=_method_name)
        try:
            archive_file = self._find_archive_for_path(path, True)
            # location is None means it is using local domain home
            if location is None:
                result = archive_file.extractFile(path, self.get_domain_home_file())
            else:
                # When an actual location is passed, the file (not the full path from the archive) is extracted
                # to the location
                extract_location = FileUtils.getCanonicalFile(File(location))
                result = archive_file.extractFile(path, extract_location, strip_leading_path)
        except (IllegalArgumentException, WLSDeployArchiveIOException), e:
            ex = exception_helper.create_exception(self.__exception_type, "WLSDPLY-19303", path,
                                                   self.__archive_files_text, e.getLocalizedMessage(), error=e)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result

    def extract_directory(self, path, location=None):
        """
        Extract the specified directory from the archive into the specified directory, or into Domain Home.
        :param path: the path into the archive
        :param location: the location to which to extract the directory
        :return: path to the extracted directory
        :raises: BundleAwareException of the appropriate type: if an error occurs
        """
        _method_name = 'extract_directory'
        self.__logger.entering(path, class_name=self.__class_name, method_name=_method_name)

        try:
            archive_file = self._find_archive_for_path(path, True)
            if location is None:
                result = archive_file.extractDirectory(path, self.get_domain_home_file())
            else:
                extract_location = FileUtils.getCanonicalFile(File(location))
                result = archive_file.extractDirectory(path, extract_location)
        except (IllegalArgumentException, WLSDeployArchiveIOException), e:
            ex = exception_helper.create_exception(self.__exception_type, "WLSDPLY-19303", path,
                                                   self.__archive_files_text, e.getLocalizedMessage(), error=e)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result

    def get_file_hash(self, path):
        """
        Get the Base64-encoded hash value for the file at the specified path within the archive.
        :param path: the path in the archive
        :return: the Base64-encoded hash value
        :raises: BundleAwareException of the appropriate type: if an error occurs
        """
        _method_name = 'get_file_hash'
        self.__logger.entering(path, class_name=self.__class_name, method_name=_method_name)

        try:
            archive_file = self._find_archive_for_path(path, True)
            result = archive_file.getFileHash(path)
        except (IllegalArgumentException, WLSDeployArchiveIOException), e:
            ex = exception_helper.create_exception(self.__exception_type, "WLSDPLY-19304", path,
                                                   self.__archive_files_text, e.getLocalizedMessage(), error=e)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result

    def extract_domain_library(self, lib_path, extract_location=None):
        """
        Extract the specified domain library to the $DOMAIN_HOME/lib directory.
        :param lib_path: the domain library path into the archive file
        :raises: BundleAwareException of the appropriate type: if an error occurs
        """
        _method_name = 'extract_domain_library'
        self.__logger.entering(lib_path, class_name=self.__class_name, method_name=_method_name)
        try:
            archive = self._find_archive_for_path(lib_path)
            if archive is not None:
                if extract_location is None:
                    archive.extractDomainLibLibrary(lib_path, File(self.get_domain_home_file(), 'lib'))
                else:
                    if not os.path.exists(os.path.join(extract_location, 'lib')):
                        os.makedirs(os.path.join(extract_location, 'lib'))
                    archive.extractDomainLibLibrary(lib_path, File(extract_location, 'lib'))
            else:
                ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19305',
                                                       lib_path, self.__archive_files_text)
                self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                raise ex
        except (WLSDeployArchiveIOException, IllegalArgumentException), e:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19306', lib_path,
                                                   self.__archive_files_text, e.getLocalizedMessage(), error=e)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def extract_classpath_libraries(self, extract_location=None):
        """
        Extract all of the classpath libraries in the archive to the $DOMAIN_HOME/wlsdeploy/classpathLibraries
        directory.
        :return: the number of classpath libraries extracted
        :raises: BundleAwareException of the appropriate type: if an error occurs
        """
        _method_name = 'extract_classpath_libraries'
        self.__logger.entering(class_name=self.__class_name, method_name=_method_name)

        count = 0
        for archive_file in self.__archive_files:
            try:
                cp_libs = archive_file.listClasspathLibraries()
                if cp_libs.size() > 0:
                    if extract_location is None:
                        archive_file.extractClasspathLibraries(self.get_domain_home_file())
                    else:
                        archive_file.extractClasspathLibraries(File(extract_location))
                    count += cp_libs.size()
            except (WLSDeployArchiveIOException, IllegalArgumentException), e:
                ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19307',
                                                       self.__archive_files_text,
                                                       self.get_domain_home_file().getAbsolutePath(),
                                                       e.getLocalizedMessage(), error=e)
                self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                raise ex

        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=count)
        return count

    def extract_custom_directory(self, extract_location=None):
        """
        Extract any files in the archive's wlsdeploy/custom subdirectory to the $DOMAIN_HOME/wlsdeploy/custom
        directory.
        :param extract_location: the location to extract to
        :return: the number of files extracted
        :raises: BundleAwareException of the appropriate type: if an error occurs
        """
        _method_name = 'extract_custom_directory'
        self.__logger.entering(class_name=self.__class_name, method_name=_method_name)

        count = 0
        for archive_file in self.__archive_files:
            try:
                custom_files = archive_file.listCustomFiles()
                if custom_files.size() > 0:
                    if extract_location is None:
                        archive_file.extractCustomFiles(self.get_domain_home_file())
                    else:
                        archive_file.extractCustomFiles(File(extract_location))

                    count += custom_files.size()
            except (WLSDeployArchiveIOException, IllegalArgumentException), e:
                ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19310',
                                                       self.__archive_files_text,
                                                       self.get_domain_home_file().getAbsolutePath(),
                                                       e.getLocalizedMessage(), error=e)
                self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                raise ex

        # warn if the size of the /config/wlsdeploy/custom directory exceeds the configured limit.
        # this is done after looping through the archive files.
        custom_file = File(self.get_domain_home_file(), WLSDeployArchive.ARCHIVE_CUSTOM_TARGET_DIR)
        if custom_file.isDirectory():
            size_limit = self.__model_context.get_model_config().get_archive_custom_folder_size_limit()
            directory_size = FileUtils.getDirectorySize(custom_file)
            if directory_size > size_limit:
                self.__logger.warning("WLSDPLY-19314", directory_size, size_limit)

        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=count)
        return count

    def extract_weblogic_remote_console_extension(self, extract_location=None):
        """
        Extract the WebLogic Remote Console Extension to the $DOMAIN_HOME/management-services-ext directory.
        :raises: BundleAwareException of the appropriate type: if an error occurs
        """
        _method_name = 'extract_weblogic_remote_console_extension'

        self.__logger.entering(class_name=self.__class_name, method_name=_method_name)
        current_entry = ''
        if self.__weblogic_helper.is_wrc_domain_extension_supported():
            if extract_location is None:
                target_location = File(self.get_domain_home_file(), WLSDeployArchive.WRC_EXTENSION_TARGET_DIR_NAME)
            else:
                target_location = File(File(extract_location), WLSDeployArchive.WRC_EXTENSION_TARGET_DIR_NAME)

            archive_entry_type = WLSDeployArchive.ArchiveEntryType.WEBLOGIC_REMOTE_CONSOLE_EXTENSION
            for archive_file in self.__archive_files:
                try:
                    entries = \
                        archive_file.getArchiveEntries(archive_entry_type)
                    for entry in entries:
                        # Skip directory entries, if they exist.
                        if entry.endswith(WLSDeployArchive.ZIP_SEP):
                            continue

                        current_entry = entry

                        if not target_location.exists() and not target_location.mkdirs():
                            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19316',
                                current_entry, self.__archive_files_text, target_location.getPath())
                            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                            raise ex

                        self.__logger.info('WLSDPLY-19315', entry, target_location.getPath())
                        archive_file.extractWrcExtensionFile(entry, target_location, True)

                except (WLSDeployArchiveIOException, IllegalArgumentException), e:
                    ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19317',
                        current_entry, self.__archive_files_text, e.getLocalizedMessage(), error=e)
                    self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                    raise ex

        found = current_entry != ''
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=found)
        return found

    def extract_domain_bin_script(self, script_path, extract_location=None):
        """
        Extract the specified domain bin script to the $DOMAIN_HOME/bin directory.
        :param script_path: the domain bin path and script into the archive file
        :param extract_location: the location to which to extract if not the default
        :raises: BundleAwareException of the appropriate type: if an error occurs
        """
        _method_name = 'extract_domain_bin_script'

        self.__logger.entering(script_path, class_name=self.__class_name, method_name=_method_name)
        try:
            archive = self._find_archive_for_path(script_path)
            if archive is not None:
                if extract_location is None:
                    archive.extractDomainBinScript(script_path, File(self.get_domain_home_file(), 'bin'))
                else:
                    if not os.path.exists(os.path.join(extract_location, 'bin')):
                        os.makedirs(os.path.join(extract_location, 'bin'))
                    archive.extractDomainBinScript(script_path, File(extract_location, 'bin'))
            else:
                ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19308',
                                                       script_path, self.__archive_files_text)
                self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                raise ex
        except (WLSDeployArchiveIOException, IllegalArgumentException), e:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19309', script_path,
                                                   self.__archive_files_text, e.getLocalizedMessage(), error=e)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def remove_domain_scripts(self):
        """
        Remove any domain bin scripts from the archive.
        :raises: BundleAwareException of the appropriate type: if an error occurs
        """
        _method_name = 'remove_domain_scripts'

        self.__logger.entering(class_name=self.__class_name, method_name=_method_name)
        for archive_file in self.__archive_files:
            try:
                archive_file.removeDomainBinScripts()
            except (WLSDeployArchiveIOException, IllegalArgumentException), e:
                ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19311',
                                                       archive_file.getArchiveFileName(), e.getLocalizedMessage(),
                                                       error=e)
                self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                raise ex
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def get_archive_entries(self):
        """
        Get the entries from all the archives.
        :return: a list of archive entries
        :raises: BundleAwareException of the appropriate type: if an error occurs
        """
        _method_name = 'get_archive_entries'
        self.__logger.entering(class_name=self.__class_name, method_name=_method_name)

        all_entries = list()
        for archive_file in self.__archive_files:
            try:
                entries = archive_file.getArchiveEntries()
                for entry in entries:
                    all_entries.append(entry)
            except WLSDeployArchiveIOException, e:
                ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19308',
                                                       self.__archive_files_text, e.getLocalizedMessage(), error=e)
                self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                raise ex

        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=all_entries)
        return all_entries

    def extract_database_wallet(self, wallet_archive_path, location=None):
        """
        Extract and unzip the database wallet archive path, if present,
        and return the full path of the wallet directory.
        :param wallet_archive_path Path of the database wallet in the archive
        :param location  extract location
        :return: the path to the extracted wallet, or None if no wallet was found
        :raises: BundleAwareException of the appropriate type: if an error occurs
        """
        _method_name = 'extract_database_wallet'
        self.__logger.entering(wallet_archive_path, class_name=self.__class_name, method_name=_method_name)
        resulting_wallet_path = None
        for archive_file in self.__archive_files:
            # get_domain_home_file is a java File
            destination = self.get_domain_home_file()
            validate_domain_home = True
            # if ssh then location is passed in,  we don't validate the domain home
            if location is not None:
                destination = File(location)
                validate_domain_home = False
            wallet_path = archive_file.extractDatabaseWallet(destination, wallet_archive_path, validate_domain_home)
            # Allow iteration to continue through all archive files but
            # make sure to store off the path for a wallet that was extracted.
            #
            self.__logger.finer('extract wallet {0} from archive file {1} returned wallet path {2}',
                                wallet_archive_path, archive_file.getArchiveFileName(), wallet_path,
                                class_name=self.__class_name, method_name=_method_name)
            if wallet_path is not None:
                # If multiple archives contain the same named wallet,
                # overwrite with the one that is latest in the archive list
                #
                resulting_wallet_path = wallet_path

        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=resulting_wallet_path)
        return resulting_wallet_path

    def extract_all_database_wallets(self, location=None):
        _method_name = 'extract_all_database_wallets'
        self.__logger.entering(class_name=self.__class_name, method_name=_method_name)

        # extract_database_wallet() loops through the archive files so just collect
        # the list of wallet names from the archive files and then loop through that list.
        found_wallets = False
        wallet_paths = sets.Set()
        for archive_file in self.__archive_files:
            self.__logger.finer('processing archive_file {0}', archive_file.getArchiveFileName(),
                                class_name=self.__class_name, method_name=_method_name)
            archive_wallet_paths = archive_file.getDatabaseWalletPaths()
            wallet_paths.update(archive_wallet_paths)

        for wallet_path in wallet_paths:
            self.__logger.finer('extracting database wallet {0}', wallet_path,
                                class_name=self.__class_name, method_name=_method_name)
            self.extract_database_wallet(wallet_path, location=location)
            found_wallets = True
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return found_wallets

    def get_all_database_wallet_paths(self):
        _method_name = 'get_all_database_wallet_paths'
        self.__logger.entering(class_name=self.__class_name, method_name=_method_name)

        found_wallets = []
        for archive_file in self.__archive_files:
            self.__logger.finer('processing archive_file {0}', archive_file.getArchiveFileName(),
                                class_name=self.__class_name, method_name=_method_name)
            archive_wallet_paths = archive_file.getDatabaseWalletPaths()
            path = { 'archive': archive_file.getArchiveFileName(), 'paths': archive_wallet_paths}
            if path not in found_wallets:
                found_wallets.append(path)

        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return found_wallets

    def has_rcu_wallet_path(self):
        """
        Determine if any archive contains an RCU wallet path.
        :return: True if an RCU wallet path is found, False otherwise
        """
        for archive_file in self.__archive_files:
            if (archive_file.containsPath(WLSDeployArchive.DEFAULT_RCU_WALLET_PATH)
                    or archive_file.containsPath(WLSDeployArchive.DEPRECATED_RCU_WALLET_PATH)):
                return True

    def get_wallet_entries(self, wallet_path):
        _method_name = 'get_wallet_entries'
        self.__logger.entering(class_name=self.__class_name, method_name=_method_name)

        archive = None
        entries = []
        for archive_file in self.__archive_files[::-1]:
            wallet_entries = archive_file.getDatabaseWalletEntries(wallet_path)
            if wallet_entries:
                archive = archive_file
                entries = wallet_entries
                break

        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=(archive, entries))
        return archive, entries

    def extract_opss_wallet(self):
        """
        Extract the and unzip the OPSS wallet, if present, and return the path to the wallet directory.
        :return: the path to the extracted wallet, or None if no wallet was found
        :raises: BundleAwareException of the appropriate type: if an error occurs
        """
        _method_name = 'extract_opss_wallet'
        self.__logger.entering(class_name=self.__class_name, method_name=_method_name)

        resulting_wallet_path = None
        for archive_file in self.__archive_files:
            wallet_path = archive_file.extractOPSSWallet(self.get_domain_home_file())
            # Allow iteration to continue through all archive files but
            # make sure to store off the path for a wallet that was extracted.
            #
            if wallet_path is not None:
                # If multiple archives contain the same named wallet, they
                # will all have the same path.
                #
                resulting_wallet_path = wallet_path

        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=resulting_wallet_path)
        return resulting_wallet_path

    def get_manifest(self, source_path):
        """
        Return the manifest for the specified source path, if available.
        Source path may refer to a file (nested jar) or path (exploded directory) within the archive.
        :param source_path: the source path to be checked
        :return: the manifest for the source path, or None
        """
        archive = self._find_archive_for_path(source_path)
        if archive is not None:
            return archive.getManifest(source_path)
        return None

    def copy_archives_to_target_directory(self, target_directory):
        """
        Makes a copy of the specified archive file(s) to the target directory.
        :param target_directory: the directory to which the archive file(s) will be copied
        :return: new ArchiveList for the new archive file(s)
        :raises: BundleAwareException of the appropriate type: if an error occurred while copying the file
        """
        _method_name = 'copy_archives_to_target_directory'
        self.__logger.entering(target_directory, class_name=self.__class_name, method_name=_method_name)

        file_names = self.__archive_files_text.split(CommandLineArgUtil.ARCHIVE_FILES_SEPARATOR)
        new_file_names = []
        for file_name in file_names:
            new_file_name = self._copy_file(file_name, target_directory)
            new_file_names.append(new_file_name)
        new_archive_file_text = CommandLineArgUtil.ARCHIVE_FILES_SEPARATOR.join(new_file_names)
        return ArchiveList(new_archive_file_text, self.__model_context, self.__exception_type)

    def _copy_file(self, source_file_name, target_directory):
        """
        Make a copy of the source file to the target directory
        :param source_file_name: source file name
        :param target_directory: target directory name
        :return: file name of the new file in the target directory
        :raises: BundleAwareException of the appropriate type: if an error occurred while copying the file
        """
        _method_name = '_copy_file'

        self.__logger.entering(source_file_name, target_directory, class_name=self.__class_name, method_name=_method_name)
        base_name = os.path.basename(source_file_name)
        target_file_name = os.path.join(target_directory, base_name)
        try:
            shutil.copyfile(source_file_name, target_file_name)
        except Exception, e:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19312', source_file_name,
                                                   target_file_name, e.getLocalizedMessage(), error=e)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return target_file_name

    def _find_archive_for_path(self, path, required=False):
        """
        Find the archive file containing the specified path.
        Search from the end of the list, as later entries override previous ones.
        :param path: the path to find
        :param required: if True, throw an exception if path is not found
        :return: the archive containing the path, or None
        :raises: WLSDeployArchiveIOException if required is True, and path not found
        """
        _method_name = '_find_archive_for_path'

        for archive_file in self.__archive_files[::-1]:
            if archive_file.containsFileOrPath(path):
                return archive_file

        if required:
            args = [path, self.__archive_files_text]
            ex = WLSDeployArchiveIOException("WLSDPLY-01403", args)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex

        return None

    def get_domain_home_file(self):
        # don't initialize in constructor, online home may not be established
        return File(self.__model_context.get_domain_home())
