"""
Copyright (c) 2023, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import os.path

from oracle.weblogic.deploy.util import WLSDeployArchive

from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.util import dictionary_utils
from wlsdeploy.util import string_utils

DOMAIN_SECURITY_FOLDER = 'security'
IDP_FILE_PREFIX = 'saml2idppartner'
IDP_PARTNERS_KEY = 'saml2.idp.partners'
SP_FILE_PREFIX = 'saml2sppartner'
SP_PARTNERS_KEY = 'saml2.sp.partners'


class Saml2SecurityHelper(object):
    """
    Supports discover and create/deploy/update of SAML2 security initialization data files
    """
    _class_name = 'Saml2SecurityHelper'

    def __init__(self, domain_home, exception_type):
        """
        Initialize an instance of Saml2SecurityHelper.
        :param domain_home: used locate security files
        :param exception_type: the type of exception to be thrown
        """
        self._domain_home = domain_home
        self._domain_security_directory = os.path.join(self._domain_home, DOMAIN_SECURITY_FOLDER)
        self._exception_type = exception_type
        self._logger = PlatformLogger('wlsdeploy.tool.util')

    def extract_initialization_files(self, archive_helper):
        """
        Extract initialization files from the archive to the security directory.
        :param archive_helper: used to find initialization files in archive
        """
        self._extract_initialization_files(IDP_FILE_PREFIX, IDP_PARTNERS_KEY, archive_helper)
        self._extract_initialization_files(SP_FILE_PREFIX, SP_PARTNERS_KEY, archive_helper)

    def _extract_initialization_files(self, prefix, partners_key, archive_helper):
        """
        Extract initialization files for a specific prefix.
        Don't install any files if the <prefix>initialized file exists in the security directory
        :param prefix: the prefix of the "initialized" and "properties" file names
        :param partners_key: the key in the properties file that contains the partner IDs
        :param archive_helper: used to find initialization files
        """
        _method_name = '_install_initialization_files'

        properties_file_name = prefix + '.properties'
        properties_path = WLSDeployArchive.getSaml2DataArchivePath(properties_file_name)
        if archive_helper and archive_helper.contains_file(properties_path):
            # if the "initialized" file is present, don't extract files
            initialized_file = properties_file_name + '.initialized'
            initialized_path = os.path.join(self._domain_security_directory, initialized_file)
            if os.path.isfile(initialized_path):
                self._logger.info('WLSDPLY-23000', properties_file_name, initialized_file,
                                  class_name=self._class_name, method_name=_method_name)
            else:
                # extract the properties file, the read it to determine metadata files
                self._logger.info('WLSDPLY-23001', properties_file_name, class_name=self._class_name,
                                  method_name=_method_name)
                archive_helper.extract_file(properties_path, self._domain_security_directory)
                self._extract_metadata_files(properties_file_name, partners_key, archive_helper)

    def _extract_metadata_files(self, properties_file_name, partners_key, archive_helper):
        """
        Extract metadata files specified in the properties file.
        :param properties_file_name: the name of the properties file containing the metadata file names
        :param partners_key: the key in the properties file that contains the partner IDs
        :param archive_helper: used to find metadata files
        """
        _method_name = '_install_metadata_files'

        properties_file = os.path.join(self._domain_security_directory, properties_file_name)
        metadata_file_names = self._get_metadata_file_names(properties_file, partners_key)
        for metadata_file_name in metadata_file_names:
            metadata_file = WLSDeployArchive.getSaml2DataArchivePath(metadata_file_name)

            if archive_helper.contains_file(metadata_file):
                self._logger.info('WLSDPLY-23002', metadata_file_name, class_name=self._class_name,
                                  method_name=_method_name)
                archive_helper.extract_file(metadata_file, self._domain_security_directory)
            else:
                self._logger.severe('WLSDPLY-23003', metadata_file_name, properties_file,
                                    class_name=self._class_name, method_name=_method_name)

    def discover_initialization_files(self, archive, discoverer):
        """
        Add initialization files from the security directory to the archive.
        :param archive: WLSDeployArchive instance used to add files
        :param discoverer: used to collect remote files when no archive is specified
        """
        self._discover_initialization_files(IDP_FILE_PREFIX, IDP_PARTNERS_KEY, archive, discoverer)
        self._discover_initialization_files(SP_FILE_PREFIX, SP_PARTNERS_KEY, archive, discoverer)

    def _discover_initialization_files(self, prefix, partners_key, archive, discoverer):
        """
        Add initialization files for a specific prefix to the archive.
        :param prefix: the prefix of the "properties" file name
        :param partners_key: the key in the properties file that contains the partner IDs
        :param archive: WLSDeployArchive instance used to add files
        :param discoverer: used to collect remote files when no archive is specified
        """
        _method_name = '_discover_initialization_files'

        properties_file_name = prefix + '.properties'
        properties_file = os.path.join(self._domain_security_directory, properties_file_name)
        if os.path.isfile(properties_file):
            if archive:
                self._logger.info('WLSDPLY-23005', properties_file_name, class_name=self._class_name,
                                  method_name=_method_name)
                archive.addSaml2DataFile(properties_file, True)
            else:
                # if -skip_archive or -remote, add to the remote map for manual addition
                discoverer.add_to_remote_map(properties_file,
                                             WLSDeployArchive.getSaml2DataArchivePath(properties_file_name),
                                             WLSDeployArchive.ArchiveEntryType.SAML2_DATA.name())

            # check for metadata files, even if archive not specified
            self._discover_metadata_files(properties_file, partners_key, archive, discoverer)

    def _discover_metadata_files(self, properties_file_name, partners_key, archive, discoverer):
        """
        Add metadata files specified in the properties file to the archive.
        :param properties_file_name: the name of the "properties" file
        :param partners_key: the key in the properties file that contains the partner IDs
        :param archive: WLSDeployArchive instance used to add files
        :param discoverer: used to collect remote files when no archive is specified
        """
        _method_name = '_discover_metadata_files'

        properties_file = os.path.join(self._domain_security_directory, properties_file_name)
        metadata_file_names = self._get_metadata_file_names(properties_file, partners_key)
        for metadata_file_name in metadata_file_names:
            metadata_file = os.path.join(self._domain_security_directory, metadata_file_name)
            if not os.path.isfile(metadata_file):
                self._logger.severe('WLSDPLY-23007', metadata_file_name, properties_file_name,
                                    class_name=self._class_name, method_name=_method_name)
            elif archive:
                self._logger.info('WLSDPLY-23006', metadata_file_name, class_name=self._class_name,
                                  method_name=_method_name)
                archive.addSaml2DataFile(metadata_file, True)
            else:
                # if -skip_archive or -remote, add to the remote map for manual addition
                discoverer.add_to_remote_map(metadata_file,
                                             WLSDeployArchive.getSaml2DataArchivePath(metadata_file_name),
                                             WLSDeployArchive.ArchiveEntryType.SAML2_DATA.name())

    def _get_metadata_file_names(self, properties_file, partners_key):
        """
        Get the metadata files names from the specified properties file.
        :param properties_file: the properties file to be examined
        :param partners_key: the key in the properties file that contains the partner IDs
        :return: a list of metadata file names
        """
        _method_name = '_get_metadata_file_names'

        metadata_file_names = []
        properties = string_utils.load_properties(properties_file, self._exception_type)
        partners_text = dictionary_utils.get_element(properties, partners_key)
        if partners_text:
            partner_ids = partners_text.split(',')
            for partner_id in partner_ids:
                metadata_key = partner_id.strip() + '.metadata.file'
                metadata_file_name = dictionary_utils.get_element(properties, metadata_key)
                if metadata_file_name:
                    metadata_file_names.append(metadata_file_name)
                else:
                    self._logger.severe('WLSDPLY-23004', metadata_key, properties_file, class_name=self._class_name,
                                        method_name=_method_name)
        return metadata_file_names
