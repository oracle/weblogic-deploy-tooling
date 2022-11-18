"""
Copyright (c) 2021, 2022, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""

import aliastest.generate.generator_wlst as generator_wlst
import aliastest.generate.utils as generator_utils

import oracle.weblogic.deploy.aliases.TypeUtils as TypeUtils

ADJUDICATOR_TYPES = 'AdjudicatorTypes'
ADJUDICATOR_STRING = generator_utils.ADJUDICATOR_STRING
AUDITOR_TYPES = 'AuditorTypes'
AUDITOR_STRING = generator_utils.AUDITOR_STRING
AUTHENTICATION_PROVIDER_TYPES = 'AuthenticationProviderTypes'
AUTHENTICATION_PROVIDER_STRING = generator_utils.AUTHENTICATION_PROVIDER_STRING
AUTHORIZER_TYPES = 'AuthorizerTypes'
AUTHORIZER_STRING = generator_utils.AUTHORIZER_STRING
CERTPATH_PROVIDER_TYPES = 'CertPathProviderTypes'
CERTPATH_PROVIDER_STRING = generator_utils.CERTPATH_PROVIDER_STRING
CREDENTIAL_MAPPER_TYPES = 'CredentialMapperTypes'
CREDENTIAL_MAPPER_STRING = generator_utils.CREDENTIAL_MAPPER_STRING
PASSWORD_VALIDATOR_TYPES = 'PasswordValidatorTypes'
PASSWORD_VALIDATOR_STRING = generator_utils.PASSWORD_VALIDATOR_STRING
PROVIDERS = generator_utils.PROVIDERS
ROLE_MAPPER_TYPES = 'RoleMapperTypes'
ROLE_MAPPER_STRING = generator_utils.ROLE_MAPPER_STRING
TYPES = 'Types'


def populate_security_types(model_context):
    domain_name = model_context.get_domain_name()
    cd_security_configuration(domain_name)
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
    if plist is None or len(plist) < 2:
        return []
    result = TypeUtils.convertToObjectArray(plist[1], str(plist), ',')
    provider = []
    for item in result:
        provider.append(item)
    return provider


def cd_security_configuration(domain_name):
    path = '/SecurityConfiguration/%s/Realms/myrealm' % domain_name
    generator_wlst.cd_mbean(path)
