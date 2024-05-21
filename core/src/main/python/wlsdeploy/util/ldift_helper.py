"""
Copyright (c) 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at https://oss.oracle.com/licenses/upl.

Module that contains the base class for working with LDIFT files of various types.
"""
import os
import re

from java.lang import String
from java.nio.charset import StandardCharsets

from com.bea.common.security.utils.encoders import BASE64Decoder
from com.bea.common.security.utils.encoders import BASE64Encoder

from oracle.weblogic.deploy.encrypt import EncryptionUtils
from oracle.weblogic.deploy.json import JsonException
from oracle.weblogic.deploy.json import JsonStreamTranslator
from oracle.weblogic.deploy.util import FileUtils
from oracle.weblogic.deploy.validate import PasswordValidator

from wlsdeploy.aliases.alias_constants import PASSWORD_TOKEN
from wlsdeploy.exception import exception_helper
from wlsdeploy.exception.exception_types import ExceptionType
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.util import path_helper
from wlsdeploy.util import string_utils

_logger = PlatformLogger('wlsdeploy.ldift')


class LdiftLine(object):
    __class_name = 'LDiftLine'
    __line_splitter_regex = re.compile('^([a-zA-Z]+)([:][:]?)\s+([^\s].*)$')
    __b64decoder = BASE64Decoder()
    __b64encoder = BASE64Encoder()

    def __init__(self, line):
        self._original_line = line
        self._key = None
        self._value = None

        self.__initialize()

    def __initialize(self):
        matcher = self.__line_splitter_regex.match(self._original_line)
        if matcher:
            self._key = matcher.group(1)
            if matcher.group(2) == '::':
                self._value = String(self.__b64decoder.decodeBuffer(String(matcher.group(3))), StandardCharsets.UTF_8)
            else:
                self._value = matcher.group(3)

    def get_key(self):
        return self._key

    def get_value(self):
        return self._value

    def set_value(self, new_value):
        self._value = new_value

    def to_encoded_string(self):
        return '%s:: %s' % (self._key, self.__b64encoder.encodeBuffer(String(self._value).getBytes('UTF-8')))

    def to_string(self):
        return '%s: %s' % (self._key, self._value)


class LdiftBase(object):
    __class_name = 'LdiftBase'
    __security_provider_defaults_dir_name_template = 'oracle/weblogic/deploy/security/%sDefaults/'
    __LDIFT_HASHING_MARKERS = [
        PasswordValidator.PASSWORD_ENCODING_MARKER,
        PasswordValidator.OLD_PASSWORD_ENCODING_MARKER
    ]
    __WLS_ENCRYPTION_MARKERS = [ '{AES}', '{AES256}' ]

    def __init__(self, model_context, exception_type=ExceptionType.DISCOVER, download_temporary_dir=None):
        self._model_context = model_context
        self._exception_type = exception_type
        self._download_temporary_dir = download_temporary_dir
        self._weblogic_helper = model_context.get_weblogic_helper()

    def read_ldift_file(self, ldift_file_name):
        """
        Read the LDIFT file and return a list of lists of lines where each entry in the topmost list
        represents an "entry" in the LDIFT file and each entry is a list of lines for that particular entry.
        :return: a list of lists of lines
        """
        _method_name = 'read_ldift_file'
        _logger.entering(ldift_file_name, class_name=self.__class_name, method_name=_method_name)

        if string_utils.is_empty(ldift_file_name):
            ex = exception_helper.create_exception(self._exception_type, 'WLSDPLY-07100')
            _logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        elif not os.path.isfile(ldift_file_name):
            ex = exception_helper.create_exception(self._exception_type, 'WLSDPLY-07101', ldift_file_name)
            _logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex

        reader = None
        all_lines = None
        try:
            try:
                reader = open(ldift_file_name, 'r')
                all_lines = reader.readlines()
            except IOError, err:
                ex = exception_helper.create_exception(self._exception_type, 'WLSDPLY-07102',
                                                       ldift_file_name, err.message, error=err)
                _logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                raise ex
        finally:
            if reader is not None:
                try:
                    reader.close()
                except IOError:
                    # best effort only
                    pass

        entries = list()
        current_entry = None
        for line in all_lines:
            # TODO - LDIFT files support line continuation by starting the following line with a single space.
            #  For example, the following entry:
            #      cn: ou=abcdef
            #       ghi,realm=myrealm
            #  is the same as:
            #      cn: ou=abcdefghi,realm=myrealm
            #
            line_text = line.strip()
            if string_utils.is_empty(line_text):
                current_entry = None
            else:
                if current_entry is None:
                    current_entry = list()
                    entries.append(current_entry)
                current_entry.append(line_text)

        _logger.exiting(class_name=self.__class_name, method_name=_method_name, result=len(entries))
        return entries

    def load_provider_defaults_file(self, provider_type, file_name):
        _method_name = 'load_provider_defaults_file'
        _logger.entering(provider_type, file_name, class_name=self.__class_name, method_name=_method_name)

        defaults_file_dir = self.__security_provider_defaults_dir_name_template % provider_type
        defaults_file_path = '%s%s' % (defaults_file_dir, file_name)
        _logger.fine('WLSDPLY-07105', provider_type, defaults_file_path,
                     class_name=self.__class_name, method_name=_method_name)
        defaults_input_stream = FileUtils.getResourceAsStream(defaults_file_path)
        if defaults_input_stream is None:
            ex = exception_helper.create_exception(self._exception_type, 'WLSDPLY-07106',
                                                   provider_type, defaults_file_path)
            _logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex

        try:
            json_translator = JsonStreamTranslator('%s/%s' % (provider_type, file_name), defaults_input_stream)
            result = json_translator.parse()
        except JsonException, jex:
            ex = exception_helper.create_exception(self._exception_type, 'WLSDPLY-07124', provider_type,
                                                   defaults_file_path, jex.getLocalizedMessage(), error=jex)
            _logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex

        _logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result

    def get_password_for_model(self, password):
        _method_name = 'get_password_for_model'
        _logger.entering(class_name=self.__class_name, method_name=_method_name)

        result = PASSWORD_TOKEN
        if not string_utils.is_empty(password):
            # Only proceed if either WDT encryption is supported or the user has
            # specified to not encrypt passwords in the model
            if self._model_context.is_encryption_supported() or not self._model_context.is_encrypt_discovered_passwords():
                decrypted_password = self._decrypt_password(password)

                store_in_cipher_text = self._model_context.is_encrypt_discovered_passwords()
                if decrypted_password == PASSWORD_TOKEN:
                    result = PASSWORD_TOKEN
                elif self._model_context.is_encryption_supported():
                    if store_in_cipher_text:
                        wdt_encryption_passphrase = self._model_context.get_encryption_passphrase()
                        encryption_passphrase = String(wdt_encryption_passphrase).toCharArray()
                        result = EncryptionUtils.encryptString(decrypted_password, encryption_passphrase)
                    else:
                        result = decrypted_password
                else:
                    if not store_in_cipher_text:
                        result = decrypted_password
                    else:
                        _logger.warning('WLSDPLY-07114', PASSWORD_TOKEN,
                                        class_name=self.__class_name, method_name=_method_name)
            else:
                _logger.warning('WLSDPLY-07114', PASSWORD_TOKEN,
                                class_name=self.__class_name, method_name=_method_name)

        _logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return result

    def _decrypt_password(self, password):
        _method_name = '_decrypt_password'
        _logger.entering(class_name=self.__class_name, method_name=_method_name)

        if self._is_encrypted_password(password):
            base_dir = self._get_domain_decryption_base_dir()
            result = self._weblogic_helper.decrypt(password, base_dir)
        else:
            result = password

        _logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return result

    def _is_encrypted_password(self, password):
        result = False
        for encryption_marker in self.__WLS_ENCRYPTION_MARKERS:
            if password.startswith(encryption_marker):
                result = True
                break
        return result

    def _get_domain_decryption_base_dir(self):
        _method_name = '_get_domain_decryption_base_dir'
        _logger.entering(class_name=self.__class_name, method_name=_method_name)

        if self._model_context.is_ssh():
            base_dir = self._download_temporary_dir
            # need to download the SSI.dat file to support decryption
            self._ensure_salt_file_downloaded(base_dir)
        else:
            base_dir = self._model_context.get_domain_home()

        _logger.exiting(class_name=self.__class_name, method_name=_method_name, result=base_dir)
        return base_dir

    def _ensure_salt_file_downloaded(self, base_dir):
        _method_name = '_ensure_salt_file_downloaded'
        _logger.entering(base_dir, class_name=self.__class_name, method_name=_method_name)

        helper = path_helper.get_path_helper()
        domain_home = self._model_context.get_domain_home()
        local_salt_file_name = helper.local_join(base_dir, 'security', 'SerializedSystemIni.dat')
        remote_salt_file_name = helper.remote_join(domain_home, 'security', 'SerializedSystemIni.dat')
        if not os.path.exists(local_salt_file_name):
            helper.download_file_from_remote_server(self._model_context, remote_salt_file_name, base_dir, 'security')

        _logger.exiting(class_name=self.__class_name, method_name=_method_name)
