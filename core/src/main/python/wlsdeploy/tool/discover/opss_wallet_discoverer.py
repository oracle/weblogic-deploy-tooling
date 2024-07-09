"""
Copyright (c) 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
from java.lang import String

from oracle.weblogic.deploy.encrypt import EncryptionUtils
from oracle.weblogic.deploy.util import WLSDeployArchiveIOException

from wlsdeploy.aliases.alias_constants import PASSWORD_TOKEN
from wlsdeploy.aliases.model_constants import DOMAIN_INFO
from wlsdeploy.aliases.model_constants import OPSS_WALLET_PASSPHRASE
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception import exception_helper
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.discover import discoverer
from wlsdeploy.tool.discover.discoverer import Discoverer

_class_name = 'OpssWalletDiscoverer'
_logger = PlatformLogger(discoverer.get_discover_logger_name())


class OpssWalletDiscoverer(Discoverer):
    """
    Discover the weblogic resources that are common across global, resource group template, and
    partition resource group.

    """
    def __init__(self, model_context, domain_info, base_location, wlst_mode=WlstModes.OFFLINE,
                 aliases=None, credential_injector=None):
        """
        The constructor
        :param model_context:
        :param domain_info:
        :param base_location:
        :param wlst_mode:
        :param aliases:
        :param credential_injector:
        """
        Discoverer.__init__(self, model_context, base_location, wlst_mode, aliases, credential_injector)
        self._domain_info_dictionary = domain_info

    def discover(self):
        _method_name = 'discover'
        _logger.entering(class_name=_class_name, method_name=_method_name)

        if self._wlst_mode == WlstModes.OFFLINE or not self._model_context.is_discover_opss_wallet():
            _logger.exiting(class_name=_class_name, method_name=_method_name)
            return

        # Because we were not able to validate JRF is installed while processing the command-line arguments,
        # we check here and generate a warning...
        #
        if self._model_context.is_discover_opss_wallet() and \
                not self._model_context.get_domain_typedef().is_jrf_installed():
            _logger.warning('WLSDPLY-06920', self._model_context.get_domain_type())
            _logger.exiting(class_name=_class_name, method_name=_method_name)
            return

        self._export_tmp_directory, self._local_tmp_directory = self._create_tmp_directories('WLSDPLY-06916')

        try:
            self._export_opss_wallet()
        finally:
            self._clean_up_tmp_directories('WLSDPLY-06917')

        _logger.exiting(class_name=_class_name, method_name=_method_name)

    def _export_opss_wallet(self):
        _method_name = '_export_opss_wallet'
        _logger.entering(class_name=_class_name, method_name=_method_name)

        domain_home = self._model_context.get_domain_home()
        jps_config_file = self.path_helper.join(domain_home, 'config', 'fmwconfig', 'jps-config.xml')
        opss_wallet_passphrase = self._model_context.get_opss_wallet_passphrase()
        self._wlst_helper.export_encryption_key(jps_config_file, self._export_tmp_directory, opss_wallet_passphrase)

        if self._model_context.is_ssh():
            remote_opss_wallet_file = self.path_helper.remote_join(self._export_tmp_directory, 'ewallet.p12')
            self.download_deployment_from_remote_server(remote_opss_wallet_file, self._local_tmp_directory, 'opss')
            opss_wallet_file = self.path_helper.join(self._local_tmp_directory, 'opss', 'ewallet.p12')
        else:
            opss_wallet_file = self.path_helper.join(self._local_tmp_directory, 'ewallet.p12')

        archive_file = self._model_context.get_archive_file()
        try:
            archive_file.addOPSSWallet(opss_wallet_file)
        except WLSDeployArchiveIOException, ioe:
            ex = exception_helper.create_discover_exception('WLSDPLY-06918', opss_wallet_file,
                                                            ioe.getLocalizedMessage(), errpr=ioe)
            _logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex

        self._domain_info_dictionary[OPSS_WALLET_PASSPHRASE] = \
            self._get_opss_wallet_passphrase_for_model(opss_wallet_passphrase)

        if self._credential_injector is not None:
            location = self._aliases.get_model_section_attribute_location(DOMAIN_INFO)
            self._credential_injector.check_and_tokenize(self._domain_info_dictionary, OPSS_WALLET_PASSPHRASE,
                                                         location)

        _logger.exiting(class_name=_class_name, method_name=_method_name)

    def _get_opss_wallet_passphrase_for_model(self, password):
        _method_name = '_get_opss_wallet_passphrase_for_model'
        _logger.entering(class_name=_class_name, method_name=_method_name)

        result = PASSWORD_TOKEN
        if self._model_context.is_encryption_supported() or not self._model_context.is_encrypt_discovered_passwords():
            store_in_cipher_text = self._model_context.is_encrypt_discovered_passwords()
            if self._model_context.is_encryption_supported():
                if store_in_cipher_text:
                    wdt_encryption_passphrase = self._model_context.get_encryption_passphrase()
                    encryption_passphrase = String(wdt_encryption_passphrase).toCharArray()
                    result = EncryptionUtils.encryptString(password, encryption_passphrase)
                else:
                    result = password
            else:
                if not store_in_cipher_text:
                    result = password
                else:
                    _logger.warning('WLSDPLY-06919', PASSWORD_TOKEN,
                                    class_name=_class_name, method_name=_method_name)
        else:
            _logger.warning('WLSDPLY-06919', PASSWORD_TOKEN,
                            class_name=_class_name, method_name=_method_name)

        _logger.exiting(class_name=_class_name, method_name=_method_name)
        return result
