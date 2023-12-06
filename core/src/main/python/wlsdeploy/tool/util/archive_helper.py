"""
Copyright (c) 2017, 2023, Oracle and/or its affiliates.  All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import os, sets
import shutil

from java.io import File
from java.lang import IllegalArgumentException
from java.lang import IllegalStateException

from oracle.weblogic.deploy.util import FileUtils
from oracle.weblogic.deploy.util import WLSDeployArchive
from oracle.weblogic.deploy.util import WLSDeployArchiveIOException

from wlsdeploy.exception import exception_helper
from wlsdeploy.util.cla_utils import CommandLineArgUtil
from wlsdeploy.util.weblogic_helper import WebLogicHelper

class ArchiveHelper(object):
    """
    Helper class for working with the archive file.
    This class should be the access point for any operation that makes use of multiple archives.
    """
    __class_name = 'ArchiveHelper'

    def __init__(self, archive_files_text, domain_home, logger, exception_type):
        """
        :param archive_files_text: a comma-separated list of one or more file names
        :param domain_home: the domain home
        :param logger: the logger to use
        :param exception_type: the exception type for the associated tool
        """
        _method_name = '__init__'

        self.__weblogic_helper = WebLogicHelper(logger)
        # used for logging only, comma-separated text is OK
        self.__archive_files_text = archive_files_text

        self.__domain_home = None
        if domain_home:
            self.__domain_home = File(domain_home)

        self.__logger = logger
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
            if location is None:
                result = archive_file.extractFile(path, self.__domain_home)
            else:
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
                result = archive_file.extractDirectory(path, self.__domain_home)
            else:
                extract_location = FileUtils.getCanonicalFile(File(location))
                result = archive_file.extractDirectory(path, extract_location, True)
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

    def extract_domain_library(self, lib_path):
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
                archive.extractDomainLibLibrary(lib_path, File(self.__domain_home, 'lib'))
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

    def extract_classpath_libraries(self):
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
                    archive_file.extractClasspathLibraries(self.__domain_home)
                    count += cp_libs.size()
            except (WLSDeployArchiveIOException, IllegalArgumentException), e:
                ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19307',
                                                       self.__archive_files_text, self.__domain_home.getAbsolutePath(),
                                                       e.getLocalizedMessage(), error=e)
                self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                raise ex

        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=count)
        return count

    def extract_custom_directory(self):
        """
        Extract any files in the archive's wlsdeploy/custom subdirectory to the $DOMAIN_HOME/wlsdeploy/custom
        directory.
        :return: the number of files extracted
        :raises: BundleAwareException of the appropriate type: if an error occurs
        """
        _method_name = 'extract_custom_directory'
        self.__logger.entering(class_name=self.__class_name, method_name=_method_name)

        count = 0
        for archive_file in self.__archive_files:
            try:
                cp_libs = archive_file.listCustomFiles()
                if cp_libs.size() > 0:
                    archive_file.extractCustomFiles(self.__domain_home)
                    count += cp_libs.size()
            except (WLSDeployArchiveIOException, IllegalArgumentException), e:
                ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19310',
                                                       self.__archive_files_text, self.__domain_home.getAbsolutePath(),
                                                       e.getLocalizedMessage(), error=e)
                self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                raise ex

        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=count)
        return count

    def extract_weblogic_remote_console_extension(self):
        """
        Extract the WebLogic Remote Console Extension to the $DOMAIN_HOME/management-services-ext directory.
        :raises: BundleAwareException of the appropriate type: if an error occurs
        """
        _method_name = 'extract_weblogic_remote_console_extension'

        self.__logger.entering(class_name=self.__class_name, method_name=_method_name)
        if self.__weblogic_helper.is_wrc_domain_extension_supported():
            extract_location = File(self.__domain_home, 'management-services-ext')
            archive_entry_type = WLSDeployArchive.ArchiveEntryType.WEBLOGIC_REMOTE_CONSOLE_EXTENSION
            for archive_file in self.__archive_files:
                current_entry = ''
                try:
                    entries = \
                        archive_file.getArchiveEntries(archive_entry_type)
                    for entry in entries:
                        current_entry = entry

                        if not extract_location.exists() and not extract_location.mkdirs():
                            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19315',
                                current_entry, self.__archive_files_text, extract_location.getPath())
                            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                            raise ex

                        self.__logger.info('WLSDPLY-19314', entry, extract_location.getPath())
                        archive_file.extractWrcExtensionFile(entry, extract_location, True)

                except (WLSDeployArchiveIOException, IllegalArgumentException), e:
                    ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19316',
                        current_entry, self.__archive_files_text, e.getLocalizedMessage(), error=e)
                    self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                    raise ex
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def extract_domain_bin_script(self, script_path):
        """
        Extract the specified domain bin script to the $DOMAIN_HOME/bin directory.
        :param script_path: the domain bin path and script into the archive file
        :raises: BundleAwareException of the appropriate type: if an error occurs
        """
        _method_name = 'extract_domain_bin_script'

        self.__logger.entering(script_path, class_name=self.__class_name, method_name=_method_name)
        try:
            archive = self._find_archive_for_path(script_path)
            if archive is not None:
                archive.extractDomainBinScript(script_path, File(self.__domain_home, 'bin'))
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

    def extract_database_wallet(self, wallet_name=WLSDeployArchive.DEFAULT_RCU_WALLET_NAME):
        """
        Extract the and unzip the named database wallet, if present, and return the path to
        the wallet directory.
        :return: the path to the extracted wallet, or None if no wallet was found
        :raises: BundleAwareException of the appropriate type: if an error occurs
        """
        _method_name = 'extract_database_wallet'
        self.__logger.entering(wallet_name, class_name=self.__class_name, method_name=_method_name)

        resulting_wallet_path = None
        for archive_file in self.__archive_files:
            wallet_path = archive_file.extractDatabaseWallet(self.__domain_home, wallet_name)
            # Allow iteration to continue through all archive files but
            # make sure to store off the path for a wallet that was extracted.
            #
            self.__logger.finer('extract wallet {0} from archive file {1} returned wallet path {2}',
                                wallet_name, archive_file.getArchiveFileName(), wallet_path,
                                class_name=self.__class_name, method_name=_method_name)
            if wallet_path is not None:
                # If multiple archives contain the same named wallet, they
                # will all have the same path.
                #
                resulting_wallet_path = wallet_path

        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=resulting_wallet_path)
        return resulting_wallet_path

    def extract_all_database_wallets(self):
        _method_name = 'extract_all_database_wallets'
        self.__logger.entering(class_name=self.__class_name, method_name=_method_name)

        # extract_database_wallet() loops through the archive files so just collect
        # the list of wallet names from the archive files and then loop through that list.

        wallet_names = sets.Set()
        for archive_file in self.__archive_files:
            self.__logger.finer('processing archive_file {0}', archive_file.getArchiveFileName(),
                                class_name=self.__class_name, method_name=_method_name)
            archive_wallet_names = archive_file.getDatabaseWalletNames()
            wallet_names.update(archive_wallet_names)

        for wallet_name in wallet_names:
            self.__logger.finer('extracting database wallet {0}', wallet_name,
                                class_name=self.__class_name, method_name=_method_name)
            self.extract_database_wallet(wallet_name)

        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)

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
            wallet_path = archive_file.extractOPSSWallet(self.__domain_home)
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
        :return: new ArchiveHelper for the new archive file(s)
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
        return ArchiveHelper(new_archive_file_text, self.__domain_home, self.__logger, self.__exception_type)

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
