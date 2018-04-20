"""
Copyright (c) 2017, 2018, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""
from java.io import File
from java.lang import IllegalArgumentException
from java.lang import IllegalStateException

from oracle.weblogic.deploy.util import FileUtils
from oracle.weblogic.deploy.util import WLSDeployArchive
from oracle.weblogic.deploy.util import WLSDeployArchiveIOException

from wlsdeploy.exception import exception_helper

class ArchiveHelper(object):
    """
    Helper class for working with the archive file.
    """
    __class_name = 'ArchiveHelper'

    def __init__(self, archive_file_name, domain_home, logger, exception_type):
        _method_name = '__init__'
        self.__archive_file_name = archive_file_name
        self.__domain_home = File(domain_home)
        self.__logger = logger
        self.__exception_type = exception_type

        try:
            self.__archive_file = WLSDeployArchive(archive_file_name)
        except (IllegalArgumentException, IllegalStateException), e:
            ex = exception_helper.create_exception(exception_type, 'WLSDPLY-19300', self.__archive_file_name,
                                                   e.getLocalizedMessage(), error=e)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return

    def contains_model(self):
        """
        Does the archive file contain a model file?
        :return: True, if a model file was found, False otherwise
        :raises: BundleAwareException of the appropriate type: if an error occurs
        """
        _method_name = 'contains_model'

        self.__logger.entering(class_name=self.__class_name, method_name=_method_name)
        try:
            result = self.__archive_file.containsModel()
        except WLSDeployArchiveIOException, e:
            ex = exception_helper.create_exception(self.__exception_type, "WLSDPLY-19301",
                                                   self.__archive_file_name, e.getLocalizedMessage(), error=e)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return

    def extract_model(self, program_name):
        """
        Extract the model from the archive.
        :param program_name: the program name (for logging purposes)
        :return: the temporary directory and the full path to the model file
        :raises: BundleAwareException of the appropriate type: if an error occurs
        """
        _method_name = 'extract_model'

        self.__logger.entering(program_name, class_name=self.__class_name, method_name=_method_name)
        try:
            tmp_model_dir = FileUtils.createTempDirectory(program_name)
            tmp_model_file = self.__archive_file.extractModel(tmp_model_dir)
        except (IllegalArgumentException, IllegalStateException, WLSDeployArchiveIOException), archex:
            ex = exception_helper.create_cla_exception('WLSDPLY-20010', program_name, self.__archive_file_name,
                                                       archex.getLocalizedMessage(), error=archex)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name,
                              result=(tmp_model_dir, tmp_model_file))
        return tmp_model_dir, tmp_model_file

    def contains_file(self, path):
        """
        Does the archive file contain the specified location?
        :param path: the path to test
        :return: True, if the path was found in the archive file and is a file, False otherwise
        :raises: BundleAwareException of the appropriate type: if an error occurs
        """
        _method_name = 'contains_file'

        self.__logger.entering(path, class_name=self.__class_name, method_name=_method_name)
        try:
            result = self.__archive_file.containsFile(path)
        except (IllegalArgumentException, WLSDeployArchiveIOException), e:
            ex = exception_helper.create_exception(self.__exception_type, "WLSDPLY-19302", path,
                                                   self.__archive_file_name, e.getLocalizedMessage(), error=e)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result

    def contains_path(self, path):
        """
        Check that the provided path is a path, not a file, contained inside the archive file
        :param path: the path to test
        :return: True, if the path was found in the archive file and is a path, False otherwise
        :raises: BundleAwareException of the appropriate type: if an error occurs
        """
        _method_name = 'contains_path'

        self.__logger.entering(path, class_name=self.__class_name, method_name=_method_name)
        try:
            result = self.__archive_file.containsPath(path)
        except (IllegalArgumentException, WLSDeployArchiveIOException), e:
            ex = exception_helper.create_exception(self.__exception_type, "WLSDPLY-19308", path,
                                                   self.__archive_file_name, e.getLocalizedMessage(), error=e)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result

    def contains_file_or_path(self, path):
        """
        Check that the provided path is a file or path contained inside the archive file
        :param path: the path to test
        :return: True, if the path was found in the archive file. False otherwise
        :raises: BundleAwareException of the appropriate type: if an error occurs
        """
        _method_name = 'contains_file_or_path'

        self.__logger.entering(path, class_name=self.__class_name, method_name=_method_name)
        try:
            result = self.__archive_file.containsFileOrPath(path)
        except (IllegalArgumentException, WLSDeployArchiveIOException), e:
            ex = exception_helper.create_exception(self.__exception_type, "WLSDPLY-19309", path,
                                                   self.__archive_file_name, e.getLocalizedMessage(), error=e)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result

    def extract_file(self, path, location=None):
        """
        Extract the specified file from the archive into the Domain Home directory.
        :param path: the path into the archive
        :param location: the location to which to extract the file
        :return: path to the extracted file
        :raises: BundleAwareException of the appropriate type: if an error occurs
        """
        _method_name = 'extract_file'

        self.__logger.entering(path, class_name=self.__class_name, method_name=_method_name)
        try:
            if location is None:
                result = self.__archive_file.extractFile(path, self.__domain_home)
            else:
                extract_location = FileUtils.getCanonicalFile(File(location))
                result = self.__archive_file.extractFile(path, extract_location, True)
        except (IllegalArgumentException, WLSDeployArchiveIOException), e:
            ex = exception_helper.create_exception(self.__exception_type, "WLSDPLY-19303", path,
                                                   self.__archive_file_name, e.getLocalizedMessage(), error=e)
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
            result = self.__archive_file.getFileHash(path)
        except (IllegalArgumentException, WLSDeployArchiveIOException), e:
            ex = exception_helper.create_exception(self.__exception_type, "WLSDPLY-19304", path,
                                                   self.__archive_file_name, e.getLocalizedMessage(), error=e)
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
            domain_libs = self.__archive_file.listDomainLibLibraries()
            if lib_path in domain_libs:
                self.__archive_file.extractDomainLibLibrary(lib_path, File(self.__domain_home, 'lib'))
            else:
                ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19305',
                                                       lib_path, self.__archive_file_name)
                self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                raise ex
        except (WLSDeployArchiveIOException, IllegalArgumentException), e:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19306', lib_path,
                                                   self.__archive_file_name, e.getLocalizedMessage(), error=e)
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
        try:
            cp_libs = self.__archive_file.listClasspathLibraries()
            if cp_libs.size() > 0:
                self.__archive_file.extractClasspathLibraries(self.__domain_home)
        except (WLSDeployArchiveIOException, IllegalArgumentException), e:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19307', self.__archive_file_name,
                                                   self.__domain_home.getAbsolutePath(), e.getLocalizedMessage(),
                                                   error=e)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=cp_libs.size())
        return cp_libs.size()

    def get_archive_entries(self):
        """
        Get the entries in the archive.
        :return: a list of archive entries
        :raises: BundleAwareException of the appropriate type: if an error occurs
        """
        _method_name = 'get_archive_entries'

        self.__logger.entering(class_name=self.__class_name, method_name=_method_name)
        try:
            entries = self.__archive_file.getArchiveEntries()
        except WLSDeployArchiveIOException, e:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19308', self.__archive_file_name,
                                                   e.getLocalizedMessage(), error=e)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=entries)
        return entries
