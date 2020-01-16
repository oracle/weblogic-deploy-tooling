"""
Copyright (c) 2017, 2020, Oracle Corporation and/or its affiliates.  All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
from java.io import File
from java.lang import IllegalArgumentException
from java.lang import IllegalStateException

from oracle.weblogic.deploy.util import FileUtils
from oracle.weblogic.deploy.util import WLSDeployArchive
from oracle.weblogic.deploy.util import WLSDeployArchiveIOException

from wlsdeploy.exception import exception_helper
from wlsdeploy.util.cla_utils import CommandLineArgUtil


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

        return

    def contains_model(self):
        """
        Determine if an archive file contain a model file.  Search in reverse order
        :return: True, if a model file was found, False otherwise
        :raises: BundleAwareException of the appropriate type: if an error occurs
        """
        _method_name = 'contains_model'
        self.__logger.entering(class_name=self.__class_name, method_name=_method_name)

        result = False
        for archive_file in self.__archive_files[::-1]:
            try:
                result = archive_file.containsModel()
                if result:
                    break
            except WLSDeployArchiveIOException, e:
                ex = exception_helper.create_exception(self.__exception_type, "WLSDPLY-19301",
                                                       self.__archive_files_text, e.getLocalizedMessage(), error=e)
                self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                raise ex

        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result

    def extract_model(self, program_name):
        """
        Extract the model from an archive.  Search in reverse order
        :param program_name: the program name (for logging purposes)
        :return: the temporary directory and the full path to the model file, or None if not found
        :raises: BundleAwareException of the appropriate type: if an error occurs
        """
        _method_name = 'extract_model'
        self.__logger.entering(program_name, class_name=self.__class_name, method_name=_method_name)

        try:
            tmp_model_dir = FileUtils.createTempDirectory(program_name)
            tmp_model_file = None
            for archive_file in self.__archive_files[::-1]:
                tmp_model_file = archive_file.extractModel(tmp_model_dir)
                if tmp_model_file:
                    break

        except (IllegalArgumentException, IllegalStateException, WLSDeployArchiveIOException), archex:
            ex = exception_helper.create_cla_exception('WLSDPLY-20010', program_name, self.__archive_files_text,
                                                       archex.getLocalizedMessage(), error=archex)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex

        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name,
                              result=(tmp_model_dir, tmp_model_file))
        return tmp_model_dir, tmp_model_file

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

    def extract_file(self, path, location=None):
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
                result = archive_file.extractFile(path, extract_location, True)
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
        return

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
        return

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

    def extract_atp_wallet(self):
        """
        Extract the and unzip the ATP wallet, if present, and return the path to the wallet directory.
        :return: the path to the extracted wallet, or None if no wallet was found
        :raises: BundleAwareException of the appropriate type: if an error occurs
        """
        _method_name = 'extract_atp_wallet'
        self.__logger.entering(class_name=self.__class_name, method_name=_method_name)

        wallet_path = None
        for archive_file in self.__archive_files[::-1]:
            atp_wallet_zipentry = archive_file.getATPWallet()
            if atp_wallet_zipentry:
                wallet_dir = File(self.__domain_home, 'atpwallet')
                wallet_dir.mkdirs()
                wallet_path = wallet_dir.getPath()
                FileUtils.extractZipFileContent(archive_file, atp_wallet_zipentry, wallet_path)
                break

        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=wallet_path)
        return wallet_path

    def extract_opss_wallet(self):
        """
        Extract the and unzip the OPSS wallet, if present, and return the path to the wallet directory.
        :return: the path to the extracted wallet, or None if no wallet was found
        :raises: BundleAwareException of the appropriate type: if an error occurs
        """
        _method_name = 'extract_opss_wallet'
        self.__logger.entering(class_name=self.__class_name, method_name=_method_name)

        wallet_path = None
        for archive_file in self.__archive_files[::-1]:
            atp_wallet_zipentry = archive_file.getOPSSWallet()
            if atp_wallet_zipentry:
                wallet_dir = File(self.__domain_home, 'opsswallet')
                wallet_dir.mkdirs()
                wallet_path = wallet_dir.getPath()
                FileUtils.extractZipFileContent(archive_file, atp_wallet_zipentry, wallet_path)
                break

        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=wallet_path)
        return wallet_path

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
