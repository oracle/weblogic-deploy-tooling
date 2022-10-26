"""
Copyright (c) 2021, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""

import aliastest.generate.generator_wlst as generator_wlst

import oracle.weblogic.deploy.aliases.TypeUtils as TypeUtils

TYPES = 'Types'
ADJUDICATOR_TYPES = 'AdjudicatorTypes'
ADJUDICATOR_STRING = 'Adjudicator'
AUDITOR_TYPES = 'AuditorTypes'
AUDITOR_STRING = 'Auditors'
AUTHENTICATION_PROVIDER_TYPES = 'AuthenticationProviderTypes'
AUTHENTICATION_PROVIDER_STRING = 'AuthenticationProviders'
AUTHORIZER_TYPES = 'AuthorizerTypes'
AUTHORIZER_STRING = 'Authorizers'
CERTPATH_PROVIDER_TYPES = 'CertPathProviderTypes'
CERTPATH_PROVIDER_STRING = 'CertPathProviders'
CREDENTIAL_MAPPER_TYPES = 'CredentialMapperTypes'
CREDENTIAL_MAPPER_STRING = 'CredentialMappers'
PASSWORD_VALIDATOR_TYPES = 'PasswordValidatorTypes'
PASSWORD_VALIDATOR_STRING = 'PasswordValidators'
ROLE_MAPPER_TYPES = 'RoleMapperTypes'
ROLE_MAPPER_STRING = 'RoleMappers'

PROVIDERS = [ADJUDICATOR_STRING, AUDITOR_STRING, AUTHENTICATION_PROVIDER_STRING, AUTHORIZER_STRING,
             CERTPATH_PROVIDER_STRING, CREDENTIAL_MAPPER_STRING, PASSWORD_VALIDATOR_STRING, ROLE_MAPPER_STRING]

providers_map = None


def populate_security_types():
    generator_wlst.connect('weblogic', 'welcome1', 't3://localhost:7001')
    cd_security_configuration()
    provider_map = dict()
    provider_map[ADJUDICATOR_STRING] = get_jarray(ADJUDICATOR_TYPES)
    provider_map[AUDITOR_STRING] = get_jarray(AUDITOR_TYPES)
    provider_map[AUTHENTICATION_PROVIDER_STRING] = get_jarray(AUTHENTICATION_PROVIDER_TYPES)
    provider_map[AUTHORIZER_STRING] = get_jarray(AUTHORIZER_TYPES)
    provider_map[CERTPATH_PROVIDER_STRING] = get_jarray(CERTPATH_PROVIDER_TYPES)
    provider_map[CREDENTIAL_MAPPER_STRING] = get_jarray(CREDENTIAL_MAPPER_TYPES)
    provider_map[PASSWORD_VALIDATOR_STRING] = get_jarray(PASSWORD_VALIDATOR_TYPES)
    provider_map[ROLE_MAPPER_STRING] = get_jarray(ROLE_MAPPER_TYPES)
    return provider_map


def get_jarray(name):
    plist = generator_wlst.get(name)
    if plist is None or len(plist) == 0:
        return []
    result = TypeUtils.convertToObjectArray(plist[1], str(plist), ',')
    provider = []
    for item in result:
        provider.append(item)
    return provider


def cd_security_configuration():
    generator_wlst.cd_mbean('/SecurityConfiguration')
    generator_wlst.cd_mbean('system_test_domain')
    generator_wlst.cd_mbean('Realms')
    generator_wlst.cd_mbean('myrealm')


def get_last_node(package):
    result = package
    idx = package.rfind('.')
    if idx > 0:
        result = package[idx+1:]
    return result
