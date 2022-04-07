"""
Copyright (c) 2017, 2022, Oracle Corporation and/or its affiliates.  All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.aliases.model_constants import JDBC_RESOURCE
from wlsdeploy.aliases.model_constants import JDBC_SYSTEM_RESOURCE
from wlsdeploy.tool.deploy.deployer import Deployer
from wlsdeploy.util import dictionary_utils


class DatasourceDeployer(Deployer):
    """
    Deploy data sources to JDBCSystemResource(s) using WLST.  Entry point, add_data_sources()
    """
    _class_name = "DatasourceDeployer"

    def __init__(self, model, model_context, aliases, wlst_mode=WlstModes.OFFLINE):
        Deployer.__init__(self, model, model_context, aliases, wlst_mode)

    def add_data_sources(self, parent_dict, location):
        """
        Using the provided dictionary, add the data sources from the model to the WLST location.
        :param parent_dict: model dictionary containing data sources
        :param location: the location context for these data sources, such as Domain or ResourceGroup
        """
        data_sources = dictionary_utils.get_dictionary_element(parent_dict, JDBC_SYSTEM_RESOURCE)
        self._add_named_elements(JDBC_SYSTEM_RESOURCE, data_sources, location)

    # Override
    def set_attributes(self, location, model_nodes, excludes=None):
        """
        Override this method to set the Name attribute in JDBCResource folder for online deployment.
        Bug 27091687 requires this value to be explicitly set.
        :param location: the location to set attributes
        :param model_nodes: model nodes containing attributes to be set
        :param excludes: names of attributes to avoid setting
        """
        type_name = self.get_location_type(location)
        if type_name == JDBC_RESOURCE and self.wlst_mode == WlstModes.ONLINE:
            existing_name = self.wlst_helper.get('Name')
            if existing_name is None:
                parent_location = LocationContext(location)
                parent_location.pop_location()
                data_source_token = self.aliases.get_name_token(parent_location)
                data_source_name = location.get_name_for_token(data_source_token)
                self.wlst_helper.set('Name', data_source_name)
            # continue

        Deployer.set_attributes(self, location, model_nodes, excludes)
