"""
Copyright (c) 2017, 2024, Oracle Corporation and/or its affiliates.  All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import os
from xml.dom.minidom import parse

from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_KEYSTORE_PROPERTY
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_KEYSTOREPWD_PROPERTY
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_KEYSTORETYPE_PROPERTY
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_NET_SERVER_DN_MATCH_PROPERTY
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_NET_SSL_VERSION
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_NET_SSL_VERSION_VALUE
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_NET_TNS_ADMIN
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_TRUSTSTORE_PROPERTY
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_TRUSTSTOREPWD_PROPERTY
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_TRUSTSTORETYPE_PROPERTY
from wlsdeploy.logging.platform_logger import get_logged_value
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.util import string_utils

class JpsConfigHelper(object):
    _logger = PlatformLogger('wlsdeploy.create')
    _class_name = 'JpsConfigHelper'

    def __init__(self, model_context, rcu_db_info):
        self._model_context = model_context
        self._rcu_db_info = rcu_db_info
        self._use_ssl = rcu_db_info.is_use_atp() or rcu_db_info.is_use_ssl()

    def fix_jps_config(self):
        _method_name = 'fix_jps_config'
        self._logger.entering(class_name=self._class_name, method_name=_method_name)

        if self._use_ssl:
            tns_admin = self._rcu_db_info.get_tns_admin()
            keystore = self._rcu_db_info.get_keystore()
            keystore_type = self._rcu_db_info.get_keystore_type()
            keystore_password = self._rcu_db_info.get_keystore_password()

            truststore = self._rcu_db_info.get_truststore()
            truststore_type = self._rcu_db_info.get_truststore_type()
            truststore_password = self._rcu_db_info.get_truststore_password()

            jps_config = os.path.join(self._model_context.get_domain_home(), 'config', 'fmwconfig', 'jps-config.xml')
            jps_config_jse = \
                os.path.join(self._model_context.get_domain_home(), 'config', 'fmwconfig', 'jps-config-jse.xml')
            self.__set_ssl_properties(jps_config, tns_admin, truststore, truststore_type, truststore_password,
                                      keystore, keystore_type, keystore_password)
            self.__set_ssl_properties(jps_config_jse, tns_admin, truststore, truststore_type, truststore_password,
                                      keystore, keystore_type, keystore_password)

        self._logger.exiting(class_name=self._class_name, method_name=_method_name)

    def __set_ssl_properties(self, xml_doc, tns_admin, truststore, truststore_type, truststore_password,
                             keystore, keystore_type, keystore_password):
        """
        Add SSL config properties to the specified XML document.  This method should only be called
        if using an Oracle database and using SSL connections to the RCU database.

        :param xml_doc:                 The XML document
        :param tns_admin:               The TNS admin directory, if set
        :param truststore:              The trust store keystore/wallet, if set
        :param truststore_type:         The trust store keystore/wallet type, if set
        :param truststore_password:     The trust store keystore/wallet passphrase, if set
        :param keystore:                The identity store keystore/wallet, if set
        :param keystore_type:           The identity store keystore/wallet type, if set
        :param keystore_password:       The identity store keystore/wallet passphrase, if set
        """
        _method_name = '__set_ssl_properties'
        self._logger.entering(xml_doc, tns_admin, truststore, truststore_type, get_logged_value(truststore_password),
                              keystore, keystore_type, get_logged_value(keystore_password),
                              class_name=self._class_name, method_name=_method_name)

        dom_tree = parse(xml_doc)
        collection = dom_tree.documentElement
        props = collection.getElementsByTagName("propertySet")

        for prop in props:
            if prop.getAttribute('name') == 'props.db.1':
                self.__set_property(dom_tree, prop, DRIVER_PARAMS_NET_SERVER_DN_MATCH_PROPERTY, 'true')
                self.__set_property(dom_tree, prop, DRIVER_PARAMS_NET_SSL_VERSION, DRIVER_PARAMS_NET_SSL_VERSION_VALUE)
                self.__set_property(dom_tree, prop, DRIVER_PARAMS_NET_TNS_ADMIN, tns_admin)
                self.__set_property(dom_tree, prop, DRIVER_PARAMS_TRUSTSTORETYPE_PROPERTY, truststore_type)
                self.__set_property(dom_tree, prop, DRIVER_PARAMS_KEYSTORETYPE_PROPERTY, keystore_type)
                self.__set_property(dom_tree, prop, DRIVER_PARAMS_KEYSTORE_PROPERTY, keystore)
                self.__set_property(dom_tree, prop, DRIVER_PARAMS_TRUSTSTORE_PROPERTY, truststore)

                if keystore_type != 'SSO':
                    self.__set_property(dom_tree, prop, DRIVER_PARAMS_KEYSTOREPWD_PROPERTY, keystore_password, True)

                if truststore_type != 'SSO':
                    self.__set_property(dom_tree, prop, DRIVER_PARAMS_TRUSTSTOREPWD_PROPERTY, truststore_password, True)

                # Persist the changes in the xml file
                file_handle = None
                try:
                    file_handle = open(xml_doc, "w")
                    dom_tree.writexml(file_handle)
                finally:
                    if file_handle is not None:
                        file_handle.close()
                break

        self._logger.exiting(class_name=self._class_name, method_name=_method_name)

    def __set_property(self, dom_tree, prop, name, value, logMask=False):
        """
        Sets the property child element under prop parent node.
        :param dom_tree: The DOM document handle
        :param prop:    The propertySet parent handle
        :param name:    The property name
        :param value:   The property value
        """
        _method_name = '__set_property'
        if logMask:
            self._logger.entering(name, get_logged_value(value), logMask,
                                  class_name=self._class_name, method_name=_method_name)
        else:
            self._logger.entering(name, value, logMask, class_name=self._class_name, method_name=_method_name)

        if not string_utils.is_empty(value):
            property_element = dom_tree.createElement('property')
            property_element.setAttribute("name", name)
            property_element.setAttribute("value", value)
            prop.appendChild(property_element)
            newline = dom_tree.createTextNode('\n')
            prop.appendChild(newline)

        self._logger.exiting(class_name=self._class_name, method_name=_method_name)
