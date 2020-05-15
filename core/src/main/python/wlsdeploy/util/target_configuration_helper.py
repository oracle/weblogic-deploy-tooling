# Copyright (c) 2020, Oracle Corporation and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
#
#

import os

#
#  Generate a shell script for creating k8s secrets
#
def generate_k8s_script(file_location, token_dictionary):
    if file_location:
        NL = '\n'
        par_dir = os.path.abspath(os.path.join(file_location,os.pardir))
        k8s_file = os.path.join(par_dir, "create_k8s_secrets.sh")
        k8s_create_script_handle = open(k8s_file, 'w')
        k8s_create_script_handle.write('#!/bin/bash')
        k8s_create_script_handle.write(NL)
        k8s_create_script_handle.write('set -eu')
        k8s_create_script_handle.write(NL)
        k8s_create_script_handle.write('NAMESPACE=default')
        k8s_create_script_handle.write(NL)
        k8s_create_script_handle.write('DOMAIN_UID=domain1')
        k8s_create_script_handle.write(NL)
        k8s_create_script_handle.write('ADMIN_USER=wlsAdminUser')
        k8s_create_script_handle.write(NL)
        k8s_create_script_handle.write('ADMIN_PWD=wlsAdminPwd')
        k8s_create_script_handle.write(NL)
        k8s_create_script_handle.write('function create_k8s_secret {')
        k8s_create_script_handle.write(NL)
        k8s_create_script_handle.write('kubectl -n $NAMESPACE delete secret ${DOMAIN_UID}-$1 --ignore-not-found')
        k8s_create_script_handle.write(NL)
        k8s_create_script_handle.write('kubectl -n $NAMESPACE create secret generic ${DOMAIN_UID}-$1 ' +
                                       '--from-literal=$2=$3')
        k8s_create_script_handle.write(NL)
        k8s_create_script_handle.write('kubectl -n $NAMESPACE label secret ${DOMAIN_UID}-$1 ' +
                                       'weblogic.domainUID=${DOMAIN_UID}')
        k8s_create_script_handle.write(NL)
        k8s_create_script_handle.write('}')
        k8s_create_script_handle.write(NL)
        k8s_create_script_handle.write(NL)
        for property_name in token_dictionary:
            if property_name in [ 'AdminUserName', 'AdminPassword']:
                continue
            secret_names = property_name.lower().replace('.', '-').split('-')
            command_string = "create_k8s_secret %s %s %s " %( '-'.join(secret_names[:-1]), secret_names[-1],
                                                              "<changeme>")
            k8s_create_script_handle.write(command_string)
            k8s_create_script_handle.write(NL)

        k8s_create_script_handle.write(NL)
        k8s_create_script_handle.write("kubectl -n $NAMESPACE delete secret ${DOMAIN_UID}-weblogic-credential "
                                       + "--ignore-not-found")
        k8s_create_script_handle.write(NL)
        k8s_create_script_handle.write("kubectl -n $NAMESPACE create secret generic "
                                       +  "${DOMAIN_UID}-weblogic-credential "
                                       +   "--from-literal=username=${ADMIN_USER} --from-literal=password=${ADMIN_PWD}")
        k8s_create_script_handle.write(NL)
        k8s_create_script_handle.write('kubectl -n $NAMESPACE label secret ${DOMAIN_UID}-weblogic-credential ' +
                                       'weblogic.domainUID=${DOMAIN_UID}')
        k8s_create_script_handle.write(NL)
        k8s_create_script_handle.close()
