"""
Copyright (c) 2021, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""

import java.util.List as List
import java.lang.reflect.Array as Array
import java.lang.String
import aliastest.generate.generator_wlst as generator_wlst
import aliastest.util.all_utils as all_utils

import oracle.weblogic.deploy.aliases.TypeUtils as TypeUtils

TYPES = 'Types'
ADJUDICATOR_STRING = 'Adjudicator'
AUDITOR_STRING = 'Auditor'
AUTHENTICATION_PROVIDER_STRING = 'AuthenticationProvider'
AUTHORIZER_STRING = 'Authorizer'
CERTPATH_PROVIDER_STRING = 'CertPathProvider'
PASSWORD_VALIDATOR_STRING = 'PasswordValidator'
ROLE_MAPPER_STRING = 'RoleMapper'

PROVIDERS = [ADJUDICATOR_STRING, AUDITOR_STRING, AUTHENTICATION_PROVIDER_STRING, AUTHORIZER_STRING,
             CERTPATH_PROVIDER_STRING, PASSWORD_VALIDATOR_STRING, ROLE_MAPPER_STRING]

providers_map = None


def populate_security_types():
    generator_wlst.connect('weblogic', 'welcome1', 't3://localhost:7001')
    cd_security_configuration()
    provider_map = dict()
    provider_map[ADJUDICATOR_STRING]  = get_jarray(ADJUDICATOR_STRING + TYPES)
    provider_map[AUDITOR_STRING] = get_jarray(AUDITOR_STRING + TYPES)
    provider_map[AUTHENTICATION_PROVIDER_STRING] = get_jarray(AUTHENTICATION_PROVIDER_STRING + TYPES)
    provider_map[AUTHORIZER_STRING] = get_jarray(AUTHORIZER_STRING + TYPES)
    provider_map[CERTPATH_PROVIDER_STRING] = get_jarray(CERTPATH_PROVIDER_STRING + TYPES)
    provider_map[PASSWORD_VALIDATOR_STRING] = get_jarray(PASSWORD_VALIDATOR_STRING + TYPES)
    provider_map[ROLE_MAPPER_STRING] = get_jarray(ROLE_MAPPER_STRING + TYPES)
    return provider_map


def get_jarray(name):
    list = generator_wlst.get(name)
    result = TypeUtils.convertToObjectArray(list[1], None, None)
    provider = []
    for item in result:
        provider.append(item)
    return provider


def cd_security_configuration():
    #generator_wlst.cd_mbean('/SecurityConfiguration/system_test_doman/Realms/myrealm')
    generator_wlst.cd_mbean('/SecurityConfiguration')
    print generator_wlst.lsa()
    generator_wlst.cd_mbean('system_test_domain')
    generator_wlst.cd_mbean('Realms')
    generator_wlst.cd_mbean('myrealm')


def get_last_node(package):
    result = package
    idx = package.rfind('.')
    if idx > 0:
        result = package[idx+1:]
    return result
