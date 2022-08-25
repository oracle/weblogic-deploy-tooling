"""
Copyright (c) 2017, 2022, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
from wlsdeploy.aliases import alias_utils
from wlsdeploy.aliases.model_constants import ATP_ADMIN_USER
from wlsdeploy.aliases.model_constants import ATP_DEFAULT_TABLESPACE
from wlsdeploy.aliases.model_constants import ATP_TEMPORARY_TABLESPACE
from wlsdeploy.aliases.model_constants import ATP_TNS_ENTRY
from wlsdeploy.aliases.model_constants import DOMAIN_INFO
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_kEYSTORE_PROPERTY
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_KEYSTORETYPE_PROPERTY
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_KEYSTOREPWD_PROPERTY
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_NET_TNS_ADMIN
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_TRUSTSTORE_PROPERTY
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_TRUSTSTOREPWD_PROPERTY
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_TRUSTSTORETYPE_PROPERTY
from wlsdeploy.aliases.model_constants import RCU_ADMIN_PASSWORD
from wlsdeploy.aliases.model_constants import RCU_COMP_INFO
from wlsdeploy.aliases.model_constants import RCU_DB_CONN
from wlsdeploy.aliases.model_constants import RCU_DB_INFO
from wlsdeploy.aliases.model_constants import RCU_DB_USER
from wlsdeploy.aliases.model_constants import RCU_PREFIX
from wlsdeploy.aliases.model_constants import RCU_SCHEMA_PASSWORD
from wlsdeploy.aliases.model_constants import RCU_STG_INFO
from wlsdeploy.aliases.model_constants import RCU_VARIABLES
from wlsdeploy.aliases.model_constants import SSL_ADMIN_USER
from wlsdeploy.aliases.model_constants import SSL_TNS_ENTRY
from wlsdeploy.aliases.model_constants import USE_ATP
from wlsdeploy.aliases.model_constants import USE_SSL
from wlsdeploy.util import dictionary_utils
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
        return dictionary_utils.get_element(self.rcu_properties_map, DRIVER_PARAMS_NET_TNS_ADMIN)

    def get_ssl_tns_admin(self):
        return dictionary_utils.get_element(self.rcu_properties_map, DRIVER_PARAMS_NET_TNS_ADMIN)

    def get_atp_entry(self):
        return dictionary_utils.get_element(self.rcu_properties_map, ATP_TNS_ENTRY)

    def get_ssl_entry(self):
        return dictionary_utils.get_element(self.rcu_properties_map, SSL_TNS_ENTRY)

    def get_rcu_prefix(self):
        return dictionary_utils.get_element(self.rcu_properties_map, RCU_PREFIX)

    def get_rcu_schema_password(self):
        password = dictionary_utils.get_element(self.rcu_properties_map, RCU_SCHEMA_PASSWORD)
        return self.aliases.decrypt_password(password)

    def get_keystore(self):
        return dictionary_utils.get_element(self.rcu_properties_map, DRIVER_PARAMS_kEYSTORE_PROPERTY)

    def get_keystore_type(self):
        return dictionary_utils.get_element(self.rcu_properties_map, DRIVER_PARAMS_KEYSTORETYPE_PROPERTY)

    def get_keystore_password(self):
        password = dictionary_utils.get_element(self.rcu_properties_map, DRIVER_PARAMS_KEYSTOREPWD_PROPERTY)
        return self.aliases.decrypt_password(password)

    def get_truststore(self):
        return dictionary_utils.get_element(self.rcu_properties_map, DRIVER_PARAMS_TRUSTSTORE_PROPERTY)

    def get_truststore_type(self):
        return dictionary_utils.get_element(self.rcu_properties_map, DRIVER_PARAMS_TRUSTSTORETYPE_PROPERTY)

    def get_truststore_password(self):
        password = dictionary_utils.get_element(self.rcu_properties_map, DRIVER_PARAMS_TRUSTSTOREPWD_PROPERTY)
        return self.aliases.decrypt_password(password)

    def get_admin_password(self):
        password = dictionary_utils.get_element(self.rcu_properties_map, RCU_ADMIN_PASSWORD)
        return self.aliases.decrypt_password(password)

    def get_rcu_regular_db_conn(self):
        return dictionary_utils.get_element(self.rcu_properties_map, RCU_DB_CONN)

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

    def get_ssl_admin_user(self):
        if SSL_ADMIN_USER in self.rcu_properties_map:
            return self.rcu_properties_map[SSL_ADMIN_USER]
        else:
            return 'admin'

    def get_rcu_db_user(self):
        if RCU_DB_USER in self.rcu_properties_map:
            return self.rcu_properties_map[RCU_DB_USER]
        else:
            return ModelContext.DB_USER_DEFAULT

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

    def has_ssldbinfo(self):
        return self.is_use_ssl()

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

    def is_use_ssl(self):
        """
        Determine if the RCU DB info uses SSL.user
        :return: True if the model value is present and set to true
        """
        if USE_SSL in self.rcu_properties_map:
            model_value = self.rcu_properties_map[USE_SSL]
            value = alias_utils.convert_to_type('boolean', model_value)
            return value == 'true'
        return False
        
    def get_preferred_db(self):
        """
        Return the regular db connect string from command line or model.
        :return: the db connect string
        """
        cli_value = self.model_context.get_rcu_database()
        if cli_value is not None:
            return cli_value
        return self.get_rcu_regular_db_conn()

    def get_preferred_db_user(self):
        """
        Return the db user from command line or model.
        :return: the db user
        """
        cli_value = self.model_context.get_rcu_db_user()
        if cli_value != ModelContext.DB_USER_DEFAULT:
            return cli_value
        return self.get_rcu_db_user()

    def get_preferred_prefix(self):
        """
        Return the prefix from command line or model.
        :return: the prefix
        """
        cli_value = self.model_context.get_rcu_prefix()
        if cli_value is not None:
            return cli_value
        return self.get_rcu_prefix()

    def get_preferred_schema_pass(self):
        """
        Return the schema password from command line or model.
        :return: the schema password
        """
        cli_value = self.model_context.get_rcu_schema_pass()
        if cli_value is not None:
            return cli_value
        return self.get_rcu_schema_password()

    def get_preferred_sys_pass(self):
        """
        Return the system password from command line or model.
        :return: the system password
        """
        cli_value = self.model_context.get_rcu_sys_pass()
        if cli_value is not None:
            return cli_value
        return self.get_admin_password()


def create(model_dictionary, model_context, aliases):
    """
    Create an RcuDbInfo object from the model dictionary.
    If domainInfo / RCUDbInfo section, create using those values,
    otherwise create from an empty dictionary to use empty or default values.
    :param model_dictionary: the model dictionary to be checked
    :param model_context: used to resolve paths, check CLI arguments
    :param aliases: used for decryption
    :return: a new RcuDbInfo object
    """
    domain_info = dictionary_utils.get_dictionary_element(model_dictionary, DOMAIN_INFO)
    rcu_properties_map = {}
    if RCU_DB_INFO in domain_info:
        rcu_properties_map = domain_info[RCU_DB_INFO]

    return RcuDbInfo(model_context, aliases, rcu_properties_map)
