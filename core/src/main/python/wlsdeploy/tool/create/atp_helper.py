"""
Copyright (c) 2017, 2019, Oracle Corporation and/or its affiliates.  All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.


"""
import re
from xml.dom.minidom import parse


def set_ssl_properties(xmlDoc, atp_creds_path, keystore_password, truststore_password):
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
            set_property(DOMTree, prop, 'javax.net.ssl.trustStoreType', 'JKS')
            set_property(DOMTree, prop, 'javax.net.ssl.trustStore', atp_creds_path + '/truststore.jks')
            set_property(DOMTree, prop, 'oracle.net.tns_admin', atp_creds_path)
            set_property(DOMTree, prop, 'javax.net.ssl.keyStoreType', 'JKS')
            set_property(DOMTree, prop, 'javax.net.ssl.keyStore', atp_creds_path + '/keystore.jks')
            set_property(DOMTree, prop, 'javax.net.ssl.keyStorePassword', keystore_password)
            set_property(DOMTree, prop, 'javax.net.ssl.trustStorePassword', truststore_password)
            set_property(DOMTree, prop, 'oracle.net.ssl_server_dn_match', 'true')
            set_property(DOMTree, prop, 'oracle.net.ssl_version', '1.2')
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
    keystore_password = rcu_db_info.get_keystore_password()
    truststore_password = rcu_db_info.get_truststore_password()

    jsp_config = model_context.get_domain_home() + '/config/fmwconfig/jps-config.xml'
    jsp_config_jse = model_context.get_domain_home() + '/config/fmwconfig/jps-config-jse.xml'
    set_ssl_properties(jsp_config, tns_admin, keystore_password, truststore_password)
    set_ssl_properties(jsp_config_jse, tns_admin, keystore_password, truststore_password)


def get_atp_connect_string(tnsnames_ora_path, tns_sid_name):


    try:
        f = open(tnsnames_ora_path, "r+")
        try:
            text = f.read()
        finally:
            f.close()
        # The regex below looks for the <dbName>_<level><whitespaces>=<whitespaces> and grabs the
        # tnsConnectString from the current and the next line as tnsnames.ora file has the connect string
        # being printed on 2 lines.
        pattern = tns_sid_name + '\s*=\s*([(].*\n.*)'
        match = re.search(pattern, text)
        if match:
            str = match.group(1)
            tnsConnectString=str.replace('\r','').replace('\n','')
            str = format_connect_string(tnsConnectString)
            return str
    except:
        pass

    return None


def format_connect_string(connect_string):
    """
    Formats connect string for ATP DB by removing unwanted whitespaces.
    Input:
        (description= (address=(protocol=tcps)(port=1522)(host=adb-preprod.us-phoenix-1.oraclecloud.com))(connect_data=(service_name=uq7p1eavz8qlvts_watsh01_medium.atp.oraclecloud.com))(security=(ssl_server_cert_dn= "CN=adwc-preprod.uscom-east-1.oraclecloud.com,OU=Oracle BMCS US,O=Oracle Corporation,L=Redwood City,ST=California,C=US")) )
    Output Parts:
        1.      (description=(address=(protocol=tcps)(port=1522)(host=adb-preprod.us-phoenix-1.oraclecloud.com))(connect_data=(service_name=uq7p1eavz8qlvts_watsh01_medium.atp.oraclecloud.com))(security=(
        2.      ssl_server_cert_dn=
        3.      "CN=adwc-preprod.uscom-east-1.oraclecloud.com,OU=Oracle BMCS US,O=Oracle Corporation,L=Redwood City,ST=California,C=US"
        4.      )))
    :param connect_string:
    :return:
    """
    pattern = "(.*)(ssl_server_cert_dn=)\s*(\".*\")(.*)"
    match = re.search(pattern, connect_string)

    if match:
        part1 = match.group(1).replace(' ','')
        part2 = match.group(2).replace(' ', '')
        # We don't want to remove the spaces from serverDN part.
        part3 = match.group(3)
        part4 = match.group(4).replace(' ', '')
        connect_string = "%s%s%s%s" % (part1, part2, part3, part4)

    return connect_string
