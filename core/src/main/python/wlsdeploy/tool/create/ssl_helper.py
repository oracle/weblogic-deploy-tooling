"""
Copyright (c) 2022, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.


"""
import re
from java.lang import String
from xml.dom.minidom import parse
from wlsdeploy.exception import exception_helper

from wlsdeploy.logging.platform_logger import PlatformLogger

_logger = PlatformLogger('wlsdeploy.create')

def set_ssl_properties(xmlDoc, atp_creds_path, truststore, truststore_type, truststore_password):
    '''
    Add SSL config properties to the specified XML document.
    :param xmlDoc:                  The XML document
    :param db_keystore_password:    The DB keystore/truststore password (assumed to be same)
    :return: void
    '''
    DOMTree = parse(xmlDoc)
    collection = DOMTree.documentElement
    props = collection.getElementsByTagName("propertySet")

    for prop in props:
        if prop.getAttribute('name') == 'props.db.1':
            set_property(DOMTree, prop, 'javax.net.ssl.trustStoreType', truststore_type)
            set_property(DOMTree, prop, 'javax.net.ssl.trustStore', atp_creds_path + '/' + truststore)
            set_property(DOMTree, prop, 'oracle.net.tns_admin', atp_creds_path)
            if truststore_password is not None:
                set_property(DOMTree, prop, 'javax.net.ssl.trustStorePassword', truststore_password)
            # Persist the changes in the xml file
            file_handle = open(xmlDoc,"w")
            DOMTree.writexml(file_handle)
            file_handle.close()

def set_property(DOMTree, prop, name, value):
    '''
    Sets the property child element under prop parent node.
    :param DOMTree: The DOM document handle
    :param prop:    The propertySet parent handle
    :param name:    The property name
    :param value:   The property value
    :return: void
    '''
    property = DOMTree.createElement('property')
    property.setAttribute("name", name)
    property.setAttribute("value", value)
    prop.appendChild(property)
    newline = DOMTree.createTextNode('\n')
    prop.appendChild(newline)

def fix_jps_config(rcu_db_info, model_context):
    tns_admin = rcu_db_info.get_atp_tns_admin()
    truststore = rcu_db_info.get_truststore()
    truststore_type = rcu_db_info.get_truststore_type()
    truststore_password = rcu_db_info.get_truststore_password()

    jsp_config = model_context.get_domain_home() + '/config/fmwconfig/jps-config.xml'
    jsp_config_jse = model_context.get_domain_home() + '/config/fmwconfig/jps-config-jse.xml'
    set_ssl_properties(jsp_config, tns_admin, truststore, truststore_type, truststore_password)
    set_ssl_properties(jsp_config_jse, tns_admin, truststore, truststore_type, truststore_password)


def get_ssl_connect_string(tnsnames_ora_path, tns_sid_name):
    try:
        f = open(tnsnames_ora_path, "r")
        try:
            text = f.read()
        finally:
            f.close()
        # The regex below looks for the <dbName>_<level><whitespaces>=<whitespaces> and grabs the
        # tnsConnectString from the current and the next line as tnsnames.ora file has the connect string
        # being printed on 2 lines.
        pattern = tns_sid_name + '\s*=\s*([(].*\n.*)\s*([(].*\n.*)\s*([(].*\n.*)\s*([(].*\n.*)\s*([(].*\n.*)'
        match = re.search(pattern, text)
        if match:
            connect_string1 = match.group(1)
            connect_string2 = match.group(2)
            connect_string3 = match.group(3)
            connect_string4 = match.group(4)
            connect_string5 = match.group(5)

            tnsConnectString = connect_string1.replace('\r','').replace('\n','')
            tnsConnectString += connect_string2.replace('\r','').replace('\n','')
            tnsConnectString += connect_string3.replace('\r','').replace('\n','')
            tnsConnectString += connect_string4.replace('\r','').replace('\n','')
            tnsConnectString += connect_string5.replace('\r','').replace('\n','')
            tnsConnectString += ')'

            connect_string = cleanup_connect_string(tnsConnectString)
            return connect_string, None
        else:
            ex = exception_helper.create_create_exception("WLSDPLY-12563", tns_sid_name)
            _logger.throwing(ex, class_name='ssl_helper', method_name='get_ssl_connect_string')
            raise ex
    except IOError, ioe:
        ex = exception_helper.create_create_exception("WLSDPLY-12570", str(ioe))
        _logger.throwing(ex, class_name='ssl_helper', method_name='get_ssl_connect_string')
        raise ex
    except Exception, ex:
        ex = exception_helper.create_create_exception("WLSDPLY-12570", str(ex))
        _logger.throwing(ex, class_name='ssl_helper', method_name='get_ssl_connect_string')
        raise ex

def cleanup_connect_string(connect_string):
    """
    Formats connect string for SSL DB by removing unwanted whitespaces.
    :return:
    """
    connect_string = String(connect_string).replace(' ', '')
    return connect_string
