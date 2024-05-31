"""
Copyright (c) 2017, 2024, Oracle Corporation and/or its affiliates.  All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import os
import re

from wlsdeploy.exception import exception_helper
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.deploy import deployer_utils
from wlsdeploy.util import string_utils
from wlsdeploy.util import unicode_helper as str_helper


class TnsNamesHelper(object):
    _logger = PlatformLogger('wlsdeploy.create')
    _class_name = 'TnsNamesHelper'

    def __init__(self, model_context, tnsnames_ora_path):
        self._model_context = model_context
        self._tnsnames_ora_path = self.__get_tnsnames_ora_path(tnsnames_ora_path)

    def get_connect_string(self, tns_alias):
        _method_name = 'get_connect_string'
        self._logger.entering(tns_alias, class_name=self._class_name, method_name=_method_name)

        try:
            f = open(self._tnsnames_ora_path, "r")
            try:
                text = f.read()
            finally:
                f.close()

            lines = text.split('\n')

            entry_lines = list()
            found_entry = False
            for line in lines:
                clean_line = line.strip()
                if found_entry:
                    if string_utils.is_empty(clean_line):
                        break
                    else:
                        entry_lines.append(line)
                        continue

                if string_utils.is_empty(clean_line) or clean_line.startswith('#'):
                    continue
                elif re.match('^%s\s*=\s*(?:[(].*)?$' % tns_alias, clean_line):
                    found_entry = True
                    entry_lines.append(line)

            if found_entry and len(entry_lines) > 0:
                connect_string = ''.join(entry_lines)
                first_paren_index = connect_string.index('(')
                tns_connect_string = connect_string[first_paren_index:]
                connect_string = self._cleanup_connect_string(tns_connect_string)

                self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=connect_string)
                return connect_string
            else:
                ex = exception_helper.create_create_exception("WLSDPLY-12263", tns_alias)
                self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                raise ex
        except (IOError, Exception), ex:
            ex = exception_helper.create_create_exception("WLSDPLY-12270", str_helper.to_string(ex))
            self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

    def __get_tnsnames_ora_path(self, tnsnames_ora_path):
        _method_name = '__get_tnsnames_ora_path'
        self._logger.entering(tnsnames_ora_path, class_name=self._class_name, method_name=_method_name)

        result = tnsnames_ora_path
        if deployer_utils.is_path_into_archive(tnsnames_ora_path) or not os.path.isabs(tnsnames_ora_path):
            result = os.path.join(self._model_context.get_domain_home(), tnsnames_ora_path)

        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=result)
        return result

    def _cleanup_connect_string(self, connect_string):
        """
        Formats connect string by removing unwanted whitespaces. It appears the wallet's tnsnames.ora file in
        the wallet has various whitespaces from various periods.  The cie code somehow parses this connection string,
        so this is the best effort to remove the spaces.

        Input:
            (description= (address=(protocol=tcps)(port=1522)(host=*******.oraclecloud.com))(connect_data=(service_name=someservice-in.oraclecloud.com))(security=(ssl_server_cert_dn= "CN=somewhere-in.oraclecloud.com,OU=Oracle BMCS US,O=Oracle Corporation,L=Redwood City,ST=California,C=US")) )
           or
            (description= (retry_count=20)(retry_delay=3)(address=(protocol=tcps)(port=1522)(host=*******.oraclecloud.com))(connect_data=(service_name=someservice-in.oraclecloud.com))(security=(ssl_server_dn_match=yes)))
        Output Parts:
            1.      (description=(address=(protocol=tcps)(port=1522)(host=*******.oraclecloud.com))(connect_data=(service_name=someservice-in.oraclecloud.com))(security=(
            2.      ssl_server_cert_dn=
            3.      "CN=somewhere-in.oraclecloud.com,OU=Oracle BMCS US,O=Oracle Corporation,L=Redwood City,ST=California,C=US"
            4.      )))
        :param connect_string:
        :return: fixed connection string without white spaces
        """
        _method_name = '__cleanup_connect_string'
        self._logger.entering(connect_string, class_name=self._class_name, method_name=_method_name)

        result = ''
        if connect_string.find('(ssl_server_cert_dn=') > 0:
            toks = connect_string.split('(description=')
            # can have multiples
            pattern = '(.*)(ssl_server_cert_dn=)\s*(\".*\")(.*)'
            for token in toks:
                if token.find('(ssl_server_cert_dn=') > 0:
                    match = re.search(pattern, token)
                    if match:
                        part1 = match.group(1).replace(' ','')
                        part2 = match.group(2).replace(' ', '')
                        # We don't want to remove the spaces from serverDN part.
                        part3 = match.group(3)
                        part4 = match.group(4).replace(' ', '')
                        result += '(description=%s%s%s%s' % (part1, part2, part3, part4)
                else:
                    result += token.replace(' ', '')
        else:
            result = connect_string.replace(' ','')

        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=result)
        return result
