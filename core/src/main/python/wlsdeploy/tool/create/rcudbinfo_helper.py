"""
Copyright (c) 2017, 2020, Oracle Corporation and/or its affiliates.  All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
from wlsdeploy.aliases import alias_utils
from wlsdeploy.aliases.model_constants import ATP_ADMIN_USER
from wlsdeploy.aliases.model_constants import ATP_DEFAULT_TABLESPACE
from wlsdeploy.aliases.model_constants import ATP_TEMPORARY_TABLESPACE
from wlsdeploy.aliases.model_constants import ATP_TNS_ENTRY
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_KEYSTOREPWD_PROPERTY
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_NET_TNS_ADMIN
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_TRUSTSTOREPWD_PROPERTY
from wlsdeploy.aliases.model_constants import RCU_ADMIN_PASSWORD
from wlsdeploy.aliases.model_constants import RCU_COMP_INFO
from wlsdeploy.aliases.model_constants import RCU_DB_CONN
from wlsdeploy.aliases.model_constants import RCU_DB_USER
from wlsdeploy.aliases.model_constants import RCU_PREFIX
from wlsdeploy.aliases.model_constants import RCU_SCHEMA_PASSWORD
from wlsdeploy.aliases.model_constants import RCU_STG_INFO
from wlsdeploy.aliases.model_constants import RCU_VARIABLES
from wlsdeploy.aliases.model_constants import USE_ATP
from wlsdeploy.util.model_context import ModelContext


class RcuDbInfo(object):
    """
    Accesses the fields of the domainInfo/RCUDbInfo section of the model.
    Decrypts fields if the model was encrypted.
    Returns default values for some unspecified fields.
    """

    def __init__(self, model_context, aliases, rcu_properties_map):
        self.model_context = model_context
        self.aliases = aliases
        self.rcu_properties_map = rcu_properties_map

    def get_atp_tns_admin(self):
        return self.rcu_properties_map[DRIVER_PARAMS_NET_TNS_ADMIN]

    def get_atp_entry(self):
        return self.rcu_properties_map[ATP_TNS_ENTRY]

    def get_rcu_prefix(self):
        return self.rcu_properties_map[RCU_PREFIX]

    def get_rcu_schema_password(self):
        password = self.rcu_properties_map[RCU_SCHEMA_PASSWORD]
        return self.aliases.decrypt_password(password)

    def get_keystore_password(self):
        password = self.rcu_properties_map[DRIVER_PARAMS_KEYSTOREPWD_PROPERTY]
        return self.aliases.decrypt_password(password)

    def get_truststore_password(self):
        password = self.rcu_properties_map[DRIVER_PARAMS_TRUSTSTOREPWD_PROPERTY]
        return self.aliases.decrypt_password(password)

    def get_admin_password(self):
        password = self.rcu_properties_map[RCU_ADMIN_PASSWORD]
        return self.aliases.decrypt_password(password)

    def get_rcu_regular_db_conn(self):
        return self.rcu_properties_map[RCU_DB_CONN]

    def get_atp_default_tablespace(self):
        if ATP_DEFAULT_TABLESPACE in self.rcu_properties_map:
            return self.rcu_properties_map[ATP_DEFAULT_TABLESPACE]
        else:
            return 'DATA'

    def get_atp_temporary_tablespace(self):
        if ATP_TEMPORARY_TABLESPACE in self.rcu_properties_map:
            return self.rcu_properties_map[ATP_TEMPORARY_TABLESPACE]
        else:
            return 'TEMP'

    def get_atp_admin_user(self):
        if ATP_ADMIN_USER in self.rcu_properties_map:
            return self.rcu_properties_map[ATP_ADMIN_USER]
        else:
            return 'admin'

    def get_rcu_db_user(self):
        if RCU_DB_USER in self.rcu_properties_map:
            return self.rcu_properties_map[RCU_DB_USER]
        else:
            return 'SYS'

    def get_comp_info_location(self):
        if RCU_COMP_INFO in self.rcu_properties_map:
            return self.model_context.replace_token_string(self.rcu_properties_map[RCU_COMP_INFO])
        return None

    def get_storage_location(self):
        if RCU_STG_INFO in self.rcu_properties_map:
            return self.model_context.replace_token_string(self.rcu_properties_map[RCU_STG_INFO])
        return None

    def get_rcu_variables(self):
        if RCU_VARIABLES in self.rcu_properties_map:
            return self.rcu_properties_map[RCU_VARIABLES]
        else:
            return None

    # has_tns_admin is used to find the extract location if it is already extracted by the user
    # its an optional field, so insufficient to determine whether it has atp
    def has_tns_admin(self):
        return DRIVER_PARAMS_NET_TNS_ADMIN in self.rcu_properties_map

    def has_atpdbinfo(self):
        return self.is_use_atp()

    def is_regular_db(self):
        is_regular = 0
        if not self.is_use_atp():
            is_regular = 1
        if RCU_DB_CONN in self.rcu_properties_map:
            is_regular = 1
        return is_regular

    def is_use_atp(self):
        """
        Determine if the RCU DB info uses the ATP database.
        The model should allow all the values allowed by boolean alias model elements.
        The default when not specified is False.
        :return: True if the model value is present and indicates true, False otherwise
        """
        if USE_ATP in self.rcu_properties_map:
            model_value = self.rcu_properties_map[USE_ATP]
            value = alias_utils.convert_to_type('boolean', model_value)
            return value == 'true'
        return False
