"""
Copyright (c) 2017, 2019, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""

from wlsdeploy.aliases import model_constants


def get_atp_tns_admin(rcu_properties_map):
    return rcu_properties_map[model_constants.DRIVER_PARAMS_NET_TNS_ADMIN]


def get_atp_entry(rcu_properties_map):
    return rcu_properties_map[model_constants.ATP_TNS_ENTRY]


def get_rcu_prefix(rcu_properties_map):
    return rcu_properties_map[model_constants.RCU_PREFIX]


def get_rcu_schema_password(rcu_properties_map):
    return rcu_properties_map[model_constants.RCU_SCHEMA_PASSWORD]


def get_keystore_password(rcu_properties_map):
    return rcu_properties_map[model_constants.DRIVER_PARAMS_KEYSTOREPWD_PROPERTY]


def get_truststore_password(rcu_properties_map):
    return rcu_properties_map[model_constants.DRIVER_PARAMS_TRUSTSTOREPWD_PROPERTY]


def get_admin_password(rcu_properties_map):
    return rcu_properties_map[model_constants.RCU_ADMIN_PASSWORD]


def get_rcu_regular_db_conn(rcu_properties_map):
    return rcu_properties_map[model_constants.RCU_DB_CONN]


def get_atp_default_tablespace(rcu_properties_map):
    if model_constants.ATP_DEFAULT_TABLESPACE in rcu_properties_map:
        return rcu_properties_map[model_constants.ATP_DEFAULT_TABLESPACE]
    else:
        return 'DATA'


def get_atp_temporary_tablespace(rcu_properties_map):
    if model_constants.ATP_TEMPORARY_TABLESPACE in rcu_properties_map:
        return rcu_properties_map[model_constants.ATP_TEMPORARY_TABLESPACE]
    else:
        return 'TEMP'


def get_atp_admin_user(rcu_properties_map):
    if model_constants.ATP_ADMIN_USER in rcu_properties_map:
        return rcu_properties_map[model_constants.ATP_ADMIN_USER]
    else:
        return 'admin'


def get_rcu_variables(rcu_properties_map):
    if model_constants.RCU_VARIABLES in rcu_properties_map:
        return rcu_properties_map[model_constants.RCU_VARIABLES]
    else:
        return None
