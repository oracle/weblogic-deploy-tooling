"""
Copyright (c) 2020, Oracle Corporation and/or its affiliates.  All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""

from wlsdeploy.aliases.model_constants import RCU_DB_INFO
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_USER_PROPERTY
from wlsdeploy.aliases.model_constants import JDBC_DRIVER_PARAMS_PROPERTIES
from wlsdeploy.aliases.model_constants import JDBC_SYSTEM_RESOURCE
from wlsdeploy.aliases.model_constants import PASSWORD_ENCRYPTED
from wlsdeploy.tool.create.rcudbinfo_helper import RcuDbInfo
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.tool.deploy import deployer_utils
from wlsdeploy.tool.deploy.deployer import Deployer
from wlsdeploy.exception.expection_types import ExceptionType

from wlsdeploy.aliases.wlst_modes import WlstModes

class RCUHelper(Deployer):

    def __init__(self, model, model_context, aliases, modifyBootStrapCredential=True):
        Deployer.__init__(self, model, model_context, aliases, wlst_mode=WlstModes.OFFLINE)
        self._exception_type = ExceptionType.DEPLOY
        self._modifyBootStrapCredential = modifyBootStrapCredential

    def update_rcu_password(self):
        """
        Update the password of each rcu schema and then update the bootstrap password
        """

        _method_name = 'update_rcu_password'

        domain_info = self.model.get_model_domain_info()
        if RCU_DB_INFO in domain_info:
            rcu_db_info = RcuDbInfo(self.model_context, self.aliases, domain_info[RCU_DB_INFO])
            rcu_schema_pass = rcu_db_info.get_rcu_schema_password()
            # upper case the prefix, the user may specify prefix as lower case
            # but the prefix will always be upper case in the db.
            rcu_prefix = rcu_db_info.get_rcu_prefix().upper()

            location = LocationContext()
            location.append_location(JDBC_SYSTEM_RESOURCE)

            folder_path = self.aliases.get_wlst_list_path(location)
            self.wlst_helper.cd(folder_path)
            ds_names = self.wlst_helper.lsc()
            domain_typedef = self.model_context.get_domain_typedef()
            rcu_schemas = domain_typedef.get_rcu_schemas()
            if len(rcu_schemas) == 0:
                return
            schemas_len = len(rcu_schemas)

            for i in range(0,schemas_len):
                rcu_schemas[i] = rcu_prefix + '_' + rcu_schemas[i]

            for ds_name in ds_names:
                location = deployer_utils.get_jdbc_driver_params_location(ds_name, self.aliases)
                password_location = LocationContext(location)
                list_path = self.aliases.get_wlst_list_path(location)
                if not self.wlst_helper.path_exists(list_path):
                    # For update case when a new custom data source has not been persisted,
                    # the driver params location is just a placeholder and will result in error
                    # if we try to get the attribute list from the location.
                    # Since we only care about rcu stock data sources from the template for changing
                    # rcu schema password; we can skip for any new custom data source.
                    continue

                wlst_path = self.aliases.get_wlst_attributes_path(location)
                self.wlst_helper.cd(wlst_path)

                location.append_location(JDBC_DRIVER_PARAMS_PROPERTIES)
                deployer_utils.set_flattened_folder_token(location, self.aliases)
                token_name = self.aliases.get_name_token(location)
                if token_name is not None:
                    location.add_name_token(token_name, DRIVER_PARAMS_USER_PROPERTY)
                wlst_path = self.aliases.get_wlst_attributes_path(location)
                self.wlst_helper.cd(wlst_path)
                ds_user = self.wlst_helper.get('Value')

                if ds_user in rcu_schemas:
                    wlst_path = self.aliases.get_wlst_attributes_path(password_location)
                    self.wlst_helper.cd(wlst_path)
                    wlst_name, wlst_value = \
                        self.aliases.get_wlst_attribute_name_and_value(password_location, PASSWORD_ENCRYPTED,
                                                                            rcu_schema_pass, masked=True)
                    self.wlst_helper.set(wlst_name, wlst_value, masked=True)

                domain_home = self.model_context.get_domain_home()
                config_file = domain_home + '/config/fmwconfig/jps-config-jse.xml'
                opss_user = rcu_prefix + '_OPSS'
                if self._modifyBootStrapCredential:
                    self.wlst_helper.modify_bootstrap_credentials(jps_configfile=config_file, username=opss_user, password=rcu_schema_pass)


