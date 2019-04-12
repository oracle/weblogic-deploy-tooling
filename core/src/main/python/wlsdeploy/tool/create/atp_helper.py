"""
Copyright (c) 2017, 2019, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0


"""

import os, re

from xml.dom.minidom import parse

from java.io import File
from java.io import FileInputStream
from java.io import FileOutputStream
from java.util.zip import ZipInputStream
import jarray

from wlsdeploy.aliases import model_constants


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


def unzip_atp_wallet(wallet_file, location):

    if not os.path.exists(location):
        os.mkdir(location)

    buffer = jarray.zeros(1024, "b")
    fis = FileInputStream(wallet_file)
    zis = ZipInputStream(fis)
    ze = zis.getNextEntry()
    while ze:
        fileName = ze.getName()
        newFile = File(location + File.separator + fileName)
        File(newFile.getParent()).mkdirs()
        fos = FileOutputStream(newFile)
        len = zis.read(buffer)
        while len > 0:
            fos.write(buffer, 0, len)
            len = zis.read(buffer)

        fos.close()
        zis.closeEntry()
        ze = zis.getNextEntry()
    zis.closeEntry()
    zis.close()
    fis.close()


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


def extract_walletzip(model, model_context, archive_file, atp_zipentry):
    domain_parent = model_context.get_domain_parent_dir()
    if domain_parent is None:
        domain_path = model_context.get_domain_home()
    else:
        domain_path = domain_parent + os.sep + model[model_constants.TOPOLOGY][
            'Name']
    extract_path = domain_path +  os.sep + 'atpwallet'
    extract_dir = File(extract_path)
    extract_dir.mkdirs()
    wallet_zip = archive_file.extractFile(atp_zipentry, File(domain_path))
    unzip_atp_wallet(wallet_zip, extract_path)
    os.remove(wallet_zip)
    return extract_path
    # update the model to add the tns_admin
