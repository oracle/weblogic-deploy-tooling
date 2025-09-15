"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import os.path

from oracle.weblogic.deploy.util import WLSDeployArchive

from wlsdeploy.exception import exception_helper
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.util import dictionary_utils

_class_name = 'WalletCache'
_logger = PlatformLogger('wlsdeploy.discover')

class WalletCache(object):
    """
    Maintain a map of wallet directories to associated data.
    This helps to ensure that a wallet directory is only added to the archive once.
    Cache entry key is absolute source directory, entry value is this structure:
    {
        'wallet_name' : wallet_name,  # set to new value when a new entry is created
        'archive_path': archive_directory_path,  # derived when a new entry is created
        'added_to_archive': add_to_archive  # True only if wallet has been added to archive
    }
    """
    def __init__(self, model_context):
        """
        :param model_context: used to get tool configuration
        """
        self._model_context = model_context
        self._directory_path_cache = {}  # directory path to cache entry
        self._single_file_cache = {}     # single file path to archive path
        self._last_dir_name_index = 0

    def find_or_add_wallet(self, wallet_path):
        """
        Find archive path for the specified wallet path, adding its directory to the archive if needed.
        :param wallet_path: absolute path of the wallet (file or directory)
        :return: the archive path to use in the model
        """
        return self._get_wallet_archive_path(wallet_path, True)

    def get_wallet_archive_path(self, wallet_path):
        """
        Get the archive path associated with the specified wallet path.
        This will not add its directory to the archive.
        This is used by discovery with -remote option.
        :param wallet_path: absolute path of the wallet (file or directory)
        :return: the archive path to use in the model
        """
        return self._get_wallet_archive_path(wallet_path, False)

    def get_wallet_name(self, wallet_path):
        """
        Get the new or existing wallet name associated with the specified wallet path.
        This will not add the wallet to the archive.
        This is used to determine the download path for SSH discovery.
        :param wallet_path: absolute path of the wallet (file or directory)
        :return: the wallet name associated with the path
        """
        wallet_dict = self._find_or_add_wallet_entry(wallet_path, False)
        return wallet_dict['wallet_name']

    def _get_wallet_archive_path(self, wallet_path, add_to_archive):
        """
        Get the archive path for the specified wallet path, possibly adding its directory to the archive.
        :param wallet_path: absolute path of the wallet (file or directory)
        :param add_to_archive: if True, add the wallet's directory to the archive if needed
        :return: the archive path to use in the model
        """
        wallet_entry = self._find_or_add_wallet_entry(wallet_path, add_to_archive)
        archive_path = wallet_entry['archive_path']
        if os.path.isfile(wallet_path):
            archive_path += WLSDeployArchive.ZIP_SEP + os.path.basename(wallet_path)
        return archive_path

    def _find_or_add_wallet_entry(self, wallet_path, add_to_archive):
        """
        Find the wallet entry for the specified wallet path, possibly adding the path or its directory to the archive.
        :param wallet_path: absolute path of the wallet (file or directory)
        :param add_to_archive: if True, add the wallet's directory to the archive if needed
        :return: the archive path to use in the model
        """
        wallet_directory = self._get_wallet_directory(wallet_path)
        wallet_entry = dictionary_utils.get_dictionary_element(self._directory_path_cache, wallet_directory)
        already_added = dictionary_utils.get_element(wallet_entry, 'added_to_archive')
        needs_archive_add = add_to_archive and not already_added
        treat_as_single_file = _treat_as_single_file(wallet_directory, wallet_path)

        if needs_archive_add or treat_as_single_file or not wallet_entry:
            wallet_name = dictionary_utils.get_element(wallet_entry, 'wallet_name')
            wallet_name = wallet_name or self._get_next_directory_name()
            if treat_as_single_file:  # collect only the specific file
                archive_path = dictionary_utils.get_element(self._single_file_cache, wallet_path)
                if not archive_path:
                    archive_path = self._get_archive_path(
                        wallet_name, wallet_path, add_to_archive, treat_as_single_file=True)
                    self._single_file_cache[wallet_path] = archive_path
                archive_directory_path = os.path.dirname(archive_path)
            else:
                archive_directory_path = self._get_archive_path(wallet_name, wallet_directory, add_to_archive)

            wallet_entry = {
                'wallet_name' : wallet_name,
                'archive_path': archive_directory_path,
                'added_to_archive': add_to_archive
            }
            self._directory_path_cache[wallet_directory] = wallet_entry

        return wallet_entry

    def _get_archive_path(self, wallet_name, wallet_path, add_to_archive, treat_as_single_file=False):
        _method_name = '_get_archive_path'

        if add_to_archive:
            archive_file = self._model_context.get_archive_file()
            archive_path = archive_file.addDatabaseWallet(wallet_name, wallet_path)
            archive_path = archive_path.rstrip(WLSDeployArchive.ZIP_SEP)

            if treat_as_single_file:
                # log info message that only the specified file is collected and not the entire wallet directory
                _logger.info('WLSDPLY-07201', wallet_path, method_name=_method_name, class_name=_class_name)

            _logger.info('WLSDPLY-07202', wallet_path, archive_path,
                         method_name=_method_name, class_name=_class_name)
            return archive_path
        else:
            path = WLSDeployArchive.getDatabaseWalletArchivePath(wallet_name, wallet_path)
            return os.path.dirname(path)  # don't include appended name

    def _get_next_directory_name(self):
        self._last_dir_name_index += 1
        return 'wallet' + str(self._last_dir_name_index)

    def _get_wallet_directory(self, wallet_path):
        """
        Get the directory of the wallet.
        If the path is a directory, return the path.
        If the path is a file, return the parent path.
        Throw an exception if the wallet directory matches the Oracle home.
        :param wallet_path: the absolute path of the wallet (file or directory)
        :return: the directory of the wallet
        """
        _method_name = '_get_wallet_directory'

        # fix up name just in case
        if os.path.isdir(wallet_path):
            wallet_directory = os.path.abspath(wallet_path)
        else:
            wallet_directory = os.path.dirname(os.path.abspath(wallet_path))

        oracle_home = self._model_context.get_oracle_home()
        if oracle_home == wallet_directory:
            de = exception_helper.create_discover_exception('WLSDPLY-07200', wallet_path, oracle_home)
            _logger.throwing(de, class_name=_class_name, method_name=_method_name)
            raise de

        return wallet_directory


def _treat_as_single_file(wallet_directory, wallet_path):
    """
    Determine if the wallet path should be added to the archive as a single file,
    instead of adding the contents of its parent directory.
    If the path is a file in a directory with subdirectories,
    it is not in a normal wallet package, and should be added as a single file,
    to prevent adding unrelated files and directory structures to the archive.
    :param wallet_directory: the directory containing the wallet
    :param wallet_path: the absolute path of the wallet (file or directory)
    :return: True if the wallet path should be added as a single file, False otherwise
    """
    _method_name = '_treat_as_single_file'

    is_match = False
    if os.path.isfile(wallet_path):
        dir_list = os.listdir(wallet_directory)
        for item in dir_list:
            if os.path.isdir(os.path.join(wallet_directory, item)):
                is_match = True
                break
    return is_match
